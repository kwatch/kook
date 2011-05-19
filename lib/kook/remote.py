# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import sys, os, re
getpass = None         # on-demand import

from kook import KookCommandError
import kook.utils

try:
    import paramiko
except ImportError:
    sys.stderr.write("*** ERROR: you must install 'paramiko' to use kook.remote module.")
    sys.exit(1)


__all__ = ('Remote', )


python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3


def setattrs(obj, **kwargs):
    for k in kwargs:
        setattr(obj, k, kwargs[k])
    return obj


## ref. http://media.commandline.org.uk/code/ssh.txt


class Remote(object):

    _session = None
    SESSION  = None    # set later

    def __init__(self, hosts=None, port=22, user=None, password=None, privatekey=None, passphrase=None):
        if hosts is None:
            hosts = []
        elif isinstance(hosts, str):
            hosts = [hosts]
        if user is None: user = os.environ.get('LOGNAME')
        setattrs(self, hosts=hosts, port=port, user=user, password=password,
                       privatekey=privatekey, passphrase=passphrase)
        #self.hosts = hosts
        #self.port  = port
        #self.user  = user or os.environ.get('LOGNAME')
        #self.password    = password
        #self.privatekey  = privatekey
        #self.passphrase  = passphrase

    def new_session(self, host=None):
        if host is None: host = self.hosts and self.hosts[0] or None
        d = dict(host=host, port=self.port,
                 user=self.user, password=self.password,
                 privatekey=self.privatekey, passphrase=self.passphrase)
        if isinstance(host, dict):
            d.update(dict)
        else:
            d['host'] = host
        m = re.match(r'^(.+?)@(.+)$', d['host'] or '')
        if m:
            d['user'] = m.group(1)
            d['host'] = m.group(2)
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
            ssh = getattr(c, 'remote_session', None)
            if ssh:
                func(c, *args, **kwargs)
            else:
                for ssh in self:
                    c.remote_session = ssh
                    try:
                        with ssh:
                            func(c, *args, **kwargs)
                    finally:
                        c.remote_session = None
        return setattrs(deco, __name__=func.__name__, __doc__=func.__doc__)
        #deco.__name__ = func.__name__
        #deco.__doc__ = func.__doc__
        #return deco


class Session(object):

    def __init__(self, host, port=22, user=None, password=None, privatekey=None, passphrase=None):
        self.host = host
        self.port = port
        self.user = user
        self.password   = password
        self.privatekey = privatekey
        self.passphrase = passphrase
        #
        self._remote = None
        self._transport = None
        self._sftp = None
        self._paths = []
        self._moved = False
        self._pwd = None

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, *args):
        self._close()

    def _open(self):
        self._transport = paramiko.Transport((self.host, self.port))
        if self.password:
            self._transport.connect(username=self.user, password=self.password)
        else:
            pkey = self.privatekey
            if not pkey:
                pkey = self.privatekey = self._get_privatekey()
            self._transport.connect(username=self.user, pkey=pkey)
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        return self

    def _close(self):
        conn1 = self._sftp
        conn2 = self._transport
        self._sftp      = None
        self._transport = None
        try:
            if conn1: conn1.close()
        finally:
            if conn2: conn2.close()

    def _get_privatekey(self):
        home = os.environ.get('HOME')
        for base in ('id_rsa', 'id_dsa'):
            fname = "~/.ssh/" + base
            fpath = os.path.expanduser(fname)
            if os.path.exists(fpath):
                break
        else:
            raise ValueError("private key file ('~/.ssh/id_rsa' or '~/.ssh/id_dsa') not found.")
        try:
            pkey = paramiko.RSAKey.from_private_key_file(fpath, self.passphrase)
        except paramiko.PasswordRequiredException:
            if self.passphrase:
                raise
            global getpass
            if not getpass: import getpass
            self.passphrase = getpass.getpass("Passphrase for %s: " % fname)
            if self._remote and not self._remote.passphrase:
                self._remote.passphrase = self.passphrase
            pkey = paramiko.RSAKey.from_private_key_file(fpath, self.passphrase)
        return pkey

    def _echoback(self, command):
        sys.stdout.write("[%s@%s]$ %s\n" % (self.user, self.host, command))

    def sftp_get(self, remote_path, local_path=None):
        self._echoback("sftp get %s %s" % (remote_path, local_path or ""))
        self._sftp.get(remote_path, local_path or os.path.basename(remote_path))

    def sftp_put(self, local_path, remote_path=None):
        self._echoback("sftp put %s %s" % (local_path, remote_path or ""))
        self._sftp.put(local_path, remote_path or os.path.basename(local_path))

    def sftp_mget(self, *remote_patterns):
        remote_patterns = kook.utils.flatten(remote_patterns)
        self._echoback("sftp mget %s" % " ".join(remote_patterns))
        for pattern in remote_patterns:
            pat_dirname, pat_basename = os.path.split(pattern)
            remote_filenames = self._sftp.listdir(pat_dirname or '.')
            rexp = re.compile(kook.utils.meta2rexp(pat_basename))
            for fname in remote_filenames:
                if rexp.match(fname):
                    remote_path = pat_dirname and pat_dirname + '/' + fname or fname
                    local_path = fname
                    self._sftp.get(remote_path, local_path)

    def sftp_mput(self, *local_patterns):
        local_patterns = kook.utils.flatten(local_patterns)
        self._echoback("sftp mput %s" % " ".join(local_patterns))
        for pattern in local_patterns:
            for local_path in kook.utils.glob2(pattern):
                remote_path = os.path.basename(local_path)
                self._sftp.put(local_path, remote_path)

    get  = sftp_get
    put  = sftp_put
    mget = sftp_mget
    mput = sftp_mput

    def ssh_run(self, command, show_output=True):
        out, err, status = self._ssh_run(command, show_output)
        if status != 0:
            raise KookCommandError("remote command failed (status=%s)." % status)
        return (out, err, status)

    def ssh_run_f(self, command, show_output=True):
        out, err, status = self._ssh_run(command, show_output)
        return (out, err, status)

    run   = ssh_run
    run_f = ssh_run_f

    def _ssh_run(self, command, show_output):
        self._echoback(command)
        if self._moved:
            command = "cd %s; %s" % (self.getcwd(), command)
        channel = self._transport.open_session()
        ret = channel.exec_command(command)
        status = channel.recv_exit_status()
        out_lines = channel.makefile('rb', -1).readlines()
        err_lines = channel.makefile_stderr('rb', -1).readlines()
        out = "".join(out_lines)
        err = "".join(err_lines)
        if show_output:
            if out: sys.stdout.write("".join(out))
            if err: sys.stderr.write("".join(err))
        return (out, err, status)

    def pushd(self, path):
        self._moved = True
        return PushDir(path, self)

    def _chdir(self, path):
        self._sftp.chdir(path)

    def getcwd(self):
        return self._sftp.getcwd() or self._sftp.normalize('.')

    def pwd(self, forcedly=False):
        self._echoback("pwd")
        sys.stdout.write(self.getcwd() + "\n")

    def listdir(self, path='.'):
        return self._sftp.listdir(path)


Remote.SESSION = Session


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
