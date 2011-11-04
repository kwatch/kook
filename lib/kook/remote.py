# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###
import sys, os, re, time
import getpass
import atexit

from kook import KookCommandError
import kook.utils
from kook.utils import setattrs

def _print_at_exit(message):
    stderr = sys.stderr
    atexit.register(lambda: stderr.write(message + "\n"))

try:
    import paramiko
except ImportError:
    _print_at_exit("*** ERROR: you must install 'paramiko' to use kook.remote module.")
    raise


__all__ = ('Remote', 'Password')


python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3


class Remote(object):

    _session = None
    SESSION  = None    # set later

    def __init__(self, hosts=None, port=22, user=None, password=None, privatekey=None, passphrase=None, sudo_password=None):
        if hosts is None:
            hosts = []
        elif isinstance(hosts, str):
            hosts = [hosts]
        if user is None: user = os.environ.get('LOGNAME')
        setattrs(self, hosts=hosts, port=port, user=user, password=password,
                       privatekey=privatekey, passphrase=passphrase, sudo_password=sudo_password)
        #self.hosts = hosts
        #self.port  = port
        #self.user  = user or os.environ.get('LOGNAME')
        #self.password    = password
        #self.privatekey  = privatekey
        #self.passphrase  = passphrase
        #self.sudo_password = sudo_password

    def new_session(self, host=None):
        if host is None: host = self.hosts and self.hosts[0] or None
        d = dict(host=host, port=self.port,
                 user=self.user, password=self.password,
                 privatekey=self.privatekey, passphrase=self.passphrase,
                 sudo_password=self.sudo_password)
        if isinstance(host, dict):
            d.update(host)
        else:
            d['host'] = host
        for k in ('password', 'passphrase', 'sudo_password'):
            v = d[k]
            if isinstance(v, Password):
                d[k] = v.get()
        m = re.match(r'^(.+?@)?(.+?)(:\d+)?$', d['host'] or '')
        if m:
            m1, m2, m3 = m.groups()
            if m1: d['user'] = m1[:-1]
            if m2: d['host'] = m2
            if m3: d['port'] = int(m3[1:])
        return setattrs(self.SESSION(**d), _remote=self)
        #session = self.SESSION(**d)
        #session._remote = self
        #return session

    def __enter__(self):
        self._session = self.new_session()
        return self._session

    def __exit__(self, *args):
        return self._session.__exit__(*args)

    def __iter__(self):
        for host in self.hosts:
            yield self.new_session(host)

    def __call__(self, func):
        def deco(c, *args, **kwargs):
            session = getattr(c, 'session', None)
            if session:
                func(c, *args, **kwargs)
            else:
                for session in self:
                    c.session = session
                    c.ssh = c.sftp = Commands(session)
                    try:
                        #with session:
                        #    func(c, *args, **kwargs)
                        session.__enter__()
                        try:
                            func(c, *args, **kwargs)
                        finally:
                            session.__exit__(*sys.exc_info())
                    finally:
                        c.session = None
                        c.ssh = c.ftp = None
        setattrs(deco, __name__=func.__name__, __doc__=func.__doc__)
        #deco.__name__ = func.__name__
        #deco.__doc__ = func.__doc__
        for k in func.__dict__:
            if k.startswith('_kook_'):
                setattr(deco, k, func.__dict__[k])
        return deco


class Password(object):

    def __init__(self, target=None, prompt=None):
        self.target = target
        self.prompt = prompt
        if prompt:    self.prompt = prompt
        elif target:  self.prompt = 'Password for %s: ' % (target, )
        else:         self.prompt = 'Password: '
        self.value = None

    def get(self, prompt=None):
        if self.value is None:
            if not prompt: prompt = self.prompt
            self.value = getpass.getpass(prompt, sys.stdout)
        return self.value


class Session(object):

    def __init__(self, host, port=22, user=None, password=None, privatekey=None, passphrase=None, sudo_password=None):
        self.host = host
        self.port = port
        self.user = user
        self.password   = password
        self.privatekey = privatekey
        self.passphrase = passphrase
        self.sudo_password = sudo_password
        #
        self._remote = None
        self._transport = None
        self._ssh_client = None
        self._sftp_client = None
        self._paths = []
        self._moved = False
        self._pwd = None

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, *args):
        self._close()

    def _open(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.load_system_host_keys()
        if self.password:
            ssh.connect(hostname=self.host, port=self.port,
                        username=self.user, password=self.password)
        else:
            self.privatekey = self._get_privatekey()
            ssh.connect(hostname=self.host, port=self.port,
                        username=self.user, pkey=self.privatekey)
        self._ssh_client = ssh
        self._sftp_client = ssh.open_sftp()
        return self

    def _close(self):
        ssh, sftp = self._ssh_client, self._sftp_client
        self._ssh_client = self._sftp_client = None
        try:
            if sftp: sftp.close()
        finally:
            if ssh: ssh.close()

    def _echoback(self, command):
        sys.stdout.write("[%s@%s]$ %s\n" % (self.user, self.host, command))

    def _get_privatekey(self):
        for fname in ('~/.ssh/id_rsa', '~/.ssh/id_dsa'):
            fpath = os.path.expanduser(fname)
            if os.path.exists(fpath):
                break
        else:
            raise ValueError("private key file ('~/.ssh/id_rsa' or '~/.ssh/id_dsa') not found.")
        try:
            #pkey = paramiko.RSAKey.from_private_key_file(fpath, self.passphrase)
            pkey = paramiko.RSAKey(filename=fpath, password=self.passphrase)
        except paramiko.PasswordRequiredException:  # 'Private key file is encrypted'
            if self.passphrase:
                raise
            self.passphrase = getpass.getpass("Enter passphrase for key '%s': " % fname)
            if self._remote and not self._remote.passphrase:
                self._remote.passphrase = self.passphrase
            try:
                #pkey = paramiko.RSAKey.from_private_key_file(fpath, self.passphrase)
                pkey = paramiko.RSAKey(filename=fpath, password=self.passphrase)
            except paramiko.SSHException:  # 'Unable to parse key file'
                ex = sys.exc_info()[1]
                if ex.message == 'Unable to parse key file':
                    _print_at_exit("*** ERROR: passphrase for '%s' may be wrong." % fname)
                elif ex.message == 'Not a valid RSA private key file (bad ber encoding)':
                    _print_at_exit("*** ERROR: passphrase for '%s' may be not entered." % fname)
                raise
        return pkey

    ##
    ## pushd, getcwd, pwd, ...
    ##

    def pushd(self, path):
        self._moved = True
        return PushDir(path, self)

    def _chdir(self, path):
        self._sftp_client.chdir(path)

    def cd(self, path):
        cwd = self.getcwd()
        self._moved = True
        self._echoback("cd %s" % (path))
        self._chdir(path)
        return cwd

    def getcwd(self):
        return self._sftp_client.getcwd() or self._sftp_client.normalize('.')

    def pwd(self):
        self._echoback("pwd")
        sys.stdout.write(self.getcwd() + "\n")


class Commands(object):

    def __init__(self, session):
        self._session = session
        self.sudo_password = session.sudo_password

    ##
    ## cd, pushd, ...
    ##

    def cd(self, path):
        return self._session.cd(path)

    def pushd(self, path):
        return self._session.pushd(path)

    def getcwd(self):
        return self._session.getcwd()

    def pwd(self):
        return self._session.pwd()

    ##
    ## sftp
    ##

    def listdir(self, path='.'):
        sftp = self._session._sftp_client
        return sftp.listdir(path)

    def listdir_f(self, path='.'):
        sftp = self._session._sftp_client
        try:
            return sftp.listdir(path)
        except IOError:
            return []

    def get(self, remote_path, local_path=None):
        echo = self._session._echoback
        sftp = self._session._sftp_client
        echo("sftp get %s %s" % (remote_path, local_path or ""))
        sftp.get(remote_path, local_path or os.path.basename(remote_path))

    def put(self, local_path, remote_path=None):
        echo = self._session._echoback
        sftp = self._session._sftp_client
        echo("sftp put %s %s" % (local_path, remote_path or ""))
        sftp.put(local_path, remote_path or os.path.basename(local_path))

    def mget(self, *remote_patterns):
        echo = self._session._echoback
        sftp = self._session._sftp_client
        remote_patterns = kook.utils.flatten(remote_patterns)
        echo("sftp mget %s" % " ".join(remote_patterns))
        for pattern in remote_patterns:
            pat_dirname, pat_basename = os.path.split(pattern)
            remote_filenames = sftp.listdir(pat_dirname or '.')
            rexp = re.compile(kook.utils.meta2rexp(pat_basename))
            for fname in remote_filenames:
                if rexp.match(fname):
                    remote_path = pat_dirname and pat_dirname + '/' + fname or fname
                    local_path = fname
                    sftp.get(remote_path, local_path)

    def mput(self, *local_patterns):
        echo = self._session._echoback
        sftp = self._session._sftp_client
        local_patterns = kook.utils.flatten(local_patterns)
        echo("sftp mput %s" % " ".join(local_patterns))
        for pattern in local_patterns:
            for local_path in kook.utils.glob2(pattern):
                remote_path = os.path.basename(local_path)
                sftp.put(local_path, remote_path)

    ##
    ## ssh
    ##

    def run(self, command, show_output=True):
        output, error, status = self.run_f(command, show_output)
        if status != 0:
            raise KookCommandError("remote command failed (status=%s)." % status)
        return (output, error, status)

    def run_f(self, command, show_output=True):
        echo = self._session._echoback
        ssh  = self._session._ssh_client
        echo(command)
        if self._session._moved:
            command = "cd %s; %s" % (self.getcwd(), command)
        sin, sout, serr = ssh.exec_command(command)
        status = sout.channel.recv_exit_status()
        output = sout.read()
        error  = serr.read()
        if show_output:
            if output: sys.stdout.write(output)
            if error:  sys.stderr.write(error)
        return (output, error, status)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    ##
    ## sudo
    ##

    def sudo(self, command, show_output=True):
        """run gracefully; throws exception when commaind is failed"""
        output, error, status = self.sudo_f(command, show_output)
        if status != 0:
            raise KookCommandError("remote command failed (status=%s)." % status)
        return (output, error, status)

    def sudo_f(self, command, show_output=True):
        """run forcedly; ignores status code of command"""
        echo = self._session._echoback
        ssh  = self._session._ssh_client
        command = "sudo " + command
        echo(command)
        self._check_sudo_password()
        if self._session._moved:
            command = "cd %s; %s" % (self.getcwd(), command)
        sin, sout, serr = ssh.exec_command(command)
        output = sout.read()
        error  = serr.read()
        status = sout.channel.recv_exit_status()
        if show_output:
            if output: sys.stdout.write(output)
            if error:  sys.stderr.write(error)
        return (output, error, status)

    def sudo_v(self, sudo_password=None):
        """do 'sudo -v'"""
        echo = self._session._echoback
        ssh  = self._session._ssh_client
        echo("sudo -v")
        if sudo_password: self.sudo_password = sudo_password
        self._check_sudo_password()    # set self._sudo_password
        return self.sudo_password

    def _check_sudo_password(self):
        echo = self._session._echoback
        ssh  = self._session._ssh_client
        ## run dummy command in non-interactive mode
        sin, sout, serr = ssh.exec_command("sudo -n echo OK")  # non-interactive
        status = sout.channel.recv_exit_status()
        if status == 0:
            return
        ## enter passowrd for sudo command
        if not self.sudo_password:
            self.sudo_password = self._session.password or self._get_sudo_password()
        sin, sout, serr = ssh.exec_command("sudo -v")   # validate
        sin.write(self.sudo_password + "\n")
        sin.flush()  #sin.close()
        ## command will be timeout when password is wrong
        channel = sout.channel
        self._wait_for_status_ready(channel)
        if not channel.exit_status_ready():
            channel.close()
            raise KookCommandError("wrong password for sudo command.")
        ## status code should be zero
        status = channel.recv_exit_status()
        if status != 0:
            errmsg = serr.read().strip()
            raise KookCommandError(self._add_hint_about_sudo_settings(errmsg))

    def _get_sudo_password(self):
        prompt = "[sudo] password for %s@%s: " % (self.user, self.host)
        return getpass.getpass(prompt)

    def _wait_for_status_ready(self, channel, sec=1.0):
        max = int(sec * 10)   # 10 == 1/0.1
        i = 0
        while not channel.exit_status_ready():
            i += 1
            if i > max:
                break
            time.sleep(0.1)

    def _add_hint_about_sudo_settings(self, errmsg):
        if errmsg.find("no tty present and no askpass program specified") >= 0:
            errmsg += "\n (Hint: add 'Defaults visiblepw' into '/etc/sudoers' with 'visudo' command)"
        elif errmsg.find("sorry, you must have a tty to run sudo") >= 0:
            errmsg += "\n (Hint: add 'Defaults !requiretty' into '/etc/sudoers' with 'visudo' command)"
        return errmsg


Remote.SESSION = Session


#class Chdir(object):
#
#    def __init__(self, back_to, session):
#        self.back_to = back_to
#        self.session = session
#
#    def __enter__(self):
#        return self
#
#    def __exit__(self, *args):
#        self.session._chdir(self.back_to)
#        self.session._echoback("cd -    # pwd=%s" % (self.back_to, ))


class PushDir(object):

    def __init__(self, path, session):
        self.path    = path
        self.session = session
        self.back_to = None
        self._is_abspath = path[0] == '/'

    def __enter__(self):
        session = self.session
        self.back_to = session.getcwd()
        session._chdir(self.path)
        if self._is_abspath:
            session._echoback("pushd %s" % (self.path))
        else:
            session._echoback("pushd %s  # pwd=%s" % (self.path, session.getcwd()))

    def __exit__(self, *args):
        session = self.session
        session._chdir(self.back_to)
        session._echoback("popd    # pwd=%s" % (self.back_to, ))
