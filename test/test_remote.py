###
### $Release: $
### $Copyright$
### $License$
###

from __future__ import with_statement

import sys, os, re
import getpass
import oktest
from oktest import ok, NG, test, skip
import oktest.tracer
from oktest.dummy import dummy_io

import_failed = False
reason = None
try:
    import kook.remote
    from kook.remote import Remote, Password, SshSession, Chdir, PushDir
except ImportError:
    import_failed = True
    reason = str(sys.exc_info()[1])
    class Remote(object):
        SESSION = object
from kook.cookbook import Cookbook
from kook.kitchen import Kitchen



class DummySession(Remote.SESSION):

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def dummy_getpass(prompt, stream):
    stream.write(prompt)
    stream.write("\n")
    line = sys.stdin.readline()
    return re.sub(r'\r?\n$', '', line)


_orig_session_class = Remote.SESSION

def provide_dummy_session_class(self):
    Remote.SESSION = DummySession

def release_dummy_session_class(*arg):
    Remote.SESSION = _orig_session_class


_orig_getpass = getpass.getpass

def provide_dummy_getpass(self):
    getpass.getpass = dummy_getpass

def release_dummy_getpass(*args):
    getpass.getpass = _orig_getpass



class KookRemoteTest(object):


    def before(self):
        self.at_end = None

    def after(self):
        if self.at_end:
            self.at_end()


    @test("#__init__(): accepts arguments.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(
            hosts=['host1', 'host2'],
            port=10022,
            user='user1',
            password='password1',
            privatekey='privatekey1',
            passphrase='passphrase1',
            sudo_password='sudo_password1'
            )
        ok (r.hosts) == ['host1', 'host2']
        ok (r.port)  == 10022
        ok (r.user)  == 'user1'
        ok (r.password) == 'password1'
        ok (r.privatekey) == 'privatekey1'
        ok (r.passphrase) == 'passphrase1'
        ok (r.sudo_password) == 'sudo_password1'

    @test("#__init__(): sets an empty list as hosts when host is None.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=None)
        ok (r.hosts) == []
        r = Remote()
        ok (r.hosts) == []

    @test("#__init__(): converts into a list when host is a string.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts='host1')
        ok (r.hosts) == ['host1']

    @test("#__init__(): uses $LOGNAME as user name when not specified.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote()
        r.user = os.environ.get('LOGNAME')


    @test("#new_session(): returns session object.")
    @skip.when(import_failed, reason)
    def _(self):
        sess = Remote().new_session('host1')
        ok (sess).is_a(kook.remote.SshSession)

    @test("#new_session(): accepts host.")
    @skip.when(import_failed, reason)
    def _(self):
        sess = Remote().new_session('host1')
        ok (sess.host) == 'host1'

    @test("#new_session(): accepts dict object.")
    @skip.when(import_failed, reason)
    def _(self):
        sess = Remote().new_session({'host':'host2', 'sudo_password':'sudo_password2'})
        ok (sess.host) == 'host2'
        ok (sess.sudo_password) == 'sudo_password2'

    @test("#new_session(): sets user and port when host string contains them.")
    @skip.when(import_failed, reason)
    def _(self):
        sess = Remote().new_session('user2@host2:1234')
        ok (sess.host) == 'host2'
        ok (sess.user) == 'user2'
        ok (sess.port) == 1234

    @test("#new_session(): asks to user password when password value is Password object.")
    @skip.when(import_failed, reason)
    def _(self, dummy_session_class, dummy_getpass):
        input = r"""
from kook.remote import Remote, Password
remote = Remote(
    hosts = ['localhost:22'],
    password      = Password('login'),
    passphrase    = Password('~/.ssh/id_rsa'),
    sudo_password = Password('sudo')
)
#
@recipe
@remote
def remote_test(c):
    ssh = c.ssh
    print('ssh.password=%r' % (ssh.password,))
    print('ssh.passphrase=%r' % (ssh.passphrase,))
    print('ssh.sudo_password=%r' % (ssh.sudo_password,))
"""
        expected = r"""
### * remote_test (recipe=remote_test)
Password for login: 
Password for ~/.ssh/id_rsa: 
Password for sudo: 
ssh.password='AAA'
ssh.passphrase='BBB'
ssh.sudo_password='CCC'
"""[1:]
        stdin = "AAA\nBBB\nCCC\n" # password, passphrase, sudo password
        with dummy_io(stdin) as dio:
            kook.config.stdout = sys.stdout
            kook.config.stderr = sys.stderr
            kookbook = Cookbook().load(input)
            kitchen = Kitchen(kookbook)
            kitchen.start_cooking('remote_test')
        sout, serr = dio
        ok (sout) == expected
        ok (serr) == ''


    @test("#__enter__(): returns session object.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        sess = r.__enter__()
        ok (sess).is_a(kook.remote.SshSession)
        ok (sess.host) == 'host1'

    @test("#__enter__(): (internal) sets session object to ivar '_session'.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        sess = r.__enter__()
        ok (r).has_attr('_session')
        ok (r._session).is_a(kook.remote.SshSession)


    @test("#__exit__(): (internal) calls SshSession#_close().")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        sess = r.__enter__()
        tr = oktest.tracer.Tracer()
        tr.trace_method(sess, '_close')
        r.__exit__()
        ok (tr.calls[0]) == (sess, '_close', (), {}, None)


    @test("#__iter__(): iterates with new sessions.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        i = 0
        for sess in r:
            i += 1
            ok (sess).is_a(kook.remote.SshSession)
            ok (sess.host) == 'host%d' % i


    @test("#__call__(): acts as decorator.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        def foo(c):
            """doc"""
            pass
        ok (r(foo)).is_a(type(lambda: None))
        ok (r(foo)).is_not(foo)
        ok (r(foo).__name__) == 'foo'
        ok (r(foo).__doc__)  == 'doc'

    @test("#__call__(): copies kook attributes into decorator.")
    @skip.when(import_failed, reason)
    def _(self):
        input = r"""from __future__ import with_statement
@recipe
@product('sos.html')
@ingreds('sos.txt')
@byprods('sos.tmp')
@coprods('sos.toc')
@spices('-p: keep timestamp')
@priority(123)
def file_sos_html(c, *args, **kwargs):
     return args, kwargs
"""
        kookbook = Cookbook().load(input)
        recipe = kookbook.find_recipe('sos.html')
        func = recipe.method
        remote = Remote(hosts=['host1'])
        deco = remote(func)
        ok (deco).attr('_kook_recipe', recipe)
        ok (deco).attr('_kook_ingreds', ['sos.txt'])
        ok (deco).attr('_kook_byprods', ['sos.tmp'])
        ok (deco).attr('_kook_coprods', ['sos.toc'])
        ok (deco).attr('_kook_spices', ['-p: keep timestamp'])
        ok (deco).attr('_kook_priority', 123)

    @test("#__call__(): connects to hosts.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass



class KookPasswordTest(object):


    @test("#__init__(): takes 'target' and 'prompt' arguments.")
    @skip.when(import_failed, reason)
    def _(self):
        password = Password('target1', 'prompt1')
        ok (password.target) == 'target1'
        ok (password.prompt) == 'prompt1'

    @test("#__init__(): sets 'prompt' from 'target' when 'prompt' is not specified.")
    @skip.when(import_failed, reason)
    def _(self):
        password = Password('target1')
        ok (password.target) == 'target1'
        ok (password.prompt) == 'Password for target1: '

    @test("#__init__(): sets default prompt when neigther 'target' nor 'prompt' specified.")
    @skip.when(import_failed, reason)
    def _(self):
        password = Password()
        ok (password.target) == None
        ok (password.prompt) == 'Password: '


    @test("#get(): asks password to user and keeps it.")
    @skip.when(import_failed, reason)
    def _(self, dummy_getpass):
        stdin = "AAA\nBBB\n"
        with dummy_io(stdin) as dio:
            password = Password()
            ok (password.value) == None
            val = password.get()
            ok (val) == "AAA"
            ok (password.value) == "AAA"
            val = password.get()
            ok (password.value) == "AAA"
        sout, serr = dio
        ok (sout) == "Password: \n"
        ok (serr) == ""



class KookSshSessionTest(object):


    @test("#__call__(): accepts arguments.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__enter__(): (internal) calls '_open()'.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__enter__(): returns self.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__exit__(): (internal) calls '_close()'.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_open(): connects to host.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_close(): close connection.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_echoback(): prints user, host, and command.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_get_privatekey(): returns private key.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_get_privatekey(): asks passphrase for private key file.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#pushd(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_chdir(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#cd(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#getcwd(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#pwd(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#listdir(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#listdir_f(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#get(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#pus(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#mget(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#mput(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#run(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#run_f(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#sudo(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#sudo_f(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#sudo_v(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_check_sudo_password(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_get_sudo_password(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_wait_for_status_ready(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#_add_hint_about_sudo_settings(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass



class KookChdirTest(object):


    @test("#__init__(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__enter__(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__exit__(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass



class KookPushDirTest(object):


    @test("#__init__(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__enter__(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__exit__(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass



if __name__ == '__main__':
    oktest.run()
