###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import sys, os, re
import getpass
import oktest
from oktest import ok, NG, test, skip
import oktest.tracer
from oktest.dummy import dummy_io

import kook.remote
from kook.remote import Remote, Password, Session, Commands, PushDir
from kook.cookbook import Cookbook, Recipe
from kook.kitchen import Kitchen, RecipeCooking

import_failed = None
reason = None
try:
    import paramiko
    import_failed = False
except ImportError:
    import_failed = True
    reason = str(sys.exc_info()[1])

import _testhelper
from _testhelper import _invoke_kookbook



class DummySession(Remote.SESSION):

    def open(self):
        self._ssh_client = True
        self._sftp_client = True

    def close(self, *args):
        self._ssh_client = True
        self._sftp_client = True


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
        self._session_class = Remote.SESSION
        Remote.SESSION = DummySession
        self.at_end = None

    def after(self):
        Remote.SESSION = self._session_class
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
        ok (sess).is_a(kook.remote.Session)

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
@remotes(remote)
def remote_test(c):
    sess = c.session
    ssh = c.ssh
    print('ssh.password=%r' % (sess.password,))
    print('ssh.passphrase=%r' % (sess.passphrase,))
    print('ssh.sudo_password=%r' % (sess.sudo_password,))
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
        sout, serr = _invoke_kookbook(input, 'remote_test', stdin=stdin)
        ok (sout) == expected
        ok (serr) == ''


    @test("#__enter__(): returns session object.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        sess = r.__enter__()
        ok (sess).is_a(kook.remote.Session)
        ok (sess.host) == 'host1'

    @test("#__enter__(): (internal) sets session object to ivar '_session'.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        sess = r.__enter__()
        ok (r).has_attr('_session')
        ok (r._session).is_a(kook.remote.Session)


    @test("#__exit__(): (internal) calls Session#close().")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        sess = r.__enter__()
        tr = oktest.tracer.Tracer()
        tr.trace_method(sess, 'close')
        r.__exit__()
        ok (tr.calls[0]) == (sess, 'close', (), {}, None)


    @test("#__iter__(): iterates with new sessions.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        i = 0
        for sess in r:
            i += 1
            ok (sess).is_a(kook.remote.Session)
            ok (sess.host) == 'host%d' % i


    @test("#__call__(): acts as decorator.")
    @skip.when(import_failed, reason)
    def _(self):
        r = Remote(hosts=['host1', 'host2'])
        def foo(c):
            """doc"""
            pass
        ok (r(foo)).is_(foo)

    @test("#__call__(): sets '_kook_recipes'.")
    @skip.when(import_failed, reason)
    def _(self):
        r1 = Remote(hosts=['host1'])
        r2 = Remote(hosts=['host2'])
        @r1
        @r2
        def foo(c):
            pass
        ok (foo._kook_remotes) == [r1, r2]


    @test("#_invoke(): invokes recipe function with sesion object.")
    def _(self):
        remote = Remote(hosts=['host1'])
        session_list = []
        @remote
        def foo(c, *args, **kwargs):
            session_list.append(c.session)
        recipe = Recipe(kind='task')
        c = RecipeCooking(recipe)
        #
        remote._invoke(foo, c, (), {})
        #
        ok (session_list).length(1)
        ok (session_list[0]).is_a(Session)
        ok (session_list[0].host) == 'host1'

    @test("#_invoke(): invokes recipe function for each host.")
    def _(self):
        remote = Remote(hosts=['host1', 'host2', 'host3'])
        args_, kwargs_ = (1,2), {'x':10}
        ctr = [0]
        host_list = []
        @remote
        def foo(c, *args, **kwargs):
            ctr[0] += 1
            host_list.append(c.session.host)
            ok (args) == args_
            ok (kwargs) == kwargs_
        recipe = Recipe(kind='task')
        c = RecipeCooking(recipe)
        #
        remote._invoke(foo, c, args_, kwargs_)
        #
        ok (ctr[0]) == 3
        ok (host_list) == ['host1', 'host2', 'host3']


    @test("several remote objects can decoreate a recipe.")
    def _(self):
        input = r"""
from kook.remote import Remote
remote_web = Remote(hosts = ['www1', 'www2'])
remote_db  = Remote(hosts = ['db1', 'db2'])
#
@recipe
@remotes(remote_web, remote_db)
def remote_task(c):
    print(c.session.host)
"""
        expected = r"""
### * remote_task (recipe=remote_task)
www1
www2
db1
db2
"""[1:]
        sout, serr = _invoke_kookbook(input, "remote_task")
        ok (sout) == expected
        ok (serr) == ""

    @test("dependencies between remote recipe and normal recipe are solved correctly.")
    def _(self):
        input = r"""
from kook.remote import Remote
remote = Remote(hosts = ['host1', 'host2', 'host3'])
#
@recipe
@ingreds('remote_task')
def task_all(c):
    print("all: hasattr(c, 'session') = %r" % hasattr(c, 'session'))
#
@recipe
@remotes(remote)
@ingreds('prepare')
def remote_task(c):
    print('remote_task: ' + c.session.host)
#
@recipe
def prepare(c):
    print("prepare: hasattr(c, 'session') = %r" % hasattr(c, 'session'))
"""
        expected = r"""
### *** prepare (recipe=prepare)
prepare: hasattr(c, 'session') = False
### ** remote_task (recipe=remote_task)
remote_task: host1
remote_task: host2
remote_task: host3
### * all (recipe=task_all)
all: hasattr(c, 'session') = False
"""[1:]
        sout, serr = _invoke_kookbook(input, "all")
        ok (sout) == expected
        ok (serr) == ""

    @test("dependencies between remote recipes are not solved correctly yet.")
    def _(self):
        input = r"""
from kook.remote import Remote
remote = Remote(hosts = ['host1', 'host2', 'host3'])
#
@recipe
@remotes(remote)
@ingreds('remote_pre')
def remote_task(c):
    print('remote_task: ' + c.session.host)

@recipe
@remotes(remote)
def remote_pre(c):
    print('remote_pre: ' + c.session.host)
"""
        expected = r"""
### ** remote_pre (recipe=remote_pre)
remote_pre: host1
remote_pre: host2
remote_pre: host3
### * remote_task (recipe=remote_task)
remote_task: host1
remote_task: host2
remote_task: host3
"""[1:]
        sout, serr = _invoke_kookbook(input, "remote_task")
        ok (sout) == expected
        ok (serr) == ""



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
        @dummy_io(stdin)
        def d_io():
            password = Password()
            ok (password.value) == None
            val = password.get()
            ok (val) == "AAA"
            ok (password.value) == "AAA"
            val = password.get()
            ok (password.value) == "AAA"
        sout, serr = d_io
        ok (sout) == "Password: \n"
        ok (serr) == ""



class KookSessionTest(object):

    def provide_tr(self):
        return oktest.tracer.Tracer()


    @test("#__call__(): accepts arguments.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__enter__(): (internal) calls 'open()'.")
    @skip.when(import_failed, reason)
    def _(self, tr):
        sess = Session('host1')
        tr.fake_method(sess, open="OPEN")
        sess.__enter__()
        ok (tr.calls[0]) == (sess, 'open', (), {}, "OPEN")

    @test("#__enter__(): returns self.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__exit__(): (internal) calls 'close()'.")
    @skip.when(import_failed, reason)
    def _(self, tr):
        sess = Session('host1')
        tr.fake_method(sess, close="CLOSE")
        sess.__exit__()
        ok (tr.calls[0]) == (sess, 'close', (), {}, "CLOSE")


    @test("#open(): connects to host.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#close(): close connection.")
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



class KookCommandsTest(object):


    def provide_session(self):
        return Session(host='host1')

    def provide_tracer(self):
        return oktest.tracer.Tracer()


    @test("#__init__(): takes session object.")
    @skip.when(import_failed, reason)
    def _(self, session):
        c = Commands(session)
        ok (c._session).is_(session)


    @test("#pushd(): calls Session#pushd().")
    @skip.when(import_failed, reason)
    def _(self, session, tracer):
        tracer.fake_method(session, pushd='PUSHD')
        c = Commands(session)
        ret = c.pushd('PATH1')
        ok (tracer.calls[0]) == (session, 'pushd', ('PATH1',), {}, 'PUSHD')


    @test("#cd(): calls Session#cd()")
    @skip.when(import_failed, reason)
    def _(self, session, tracer):
        tracer.fake_method(session, cd='CD')
        c = Commands(session)
        ret = c.cd('PATH1')
        ok (tracer.calls[0]) == (session, 'cd', ('PATH1',), {}, 'CD')


    @test("#getcwd(): calls Session#getcwd()")
    @skip.when(import_failed, reason)
    def _(self, session, tracer):
        tracer.fake_method(session, getcwd='GETCWD')
        c = Commands(session)
        ret = c.getcwd()
        ok (tracer.calls[0]) == (session, 'getcwd', (), {}, 'GETCWD')


    @test("#pwd(): calls Session#pwd()")
    @skip.when(import_failed, reason)
    def _(self, session, tracer):
        tracer.fake_method(session, pwd='PWD')
        c = Commands(session)
        ret = c.pwd()
        ok (tracer.calls[0]) == (session, 'pwd', (), {}, 'PWD')


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


    @test("#system(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#system_f(): TODO")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass


    @test("#__call__(): TODO")
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



#class KookChdirTest(object):
#
#
#    @test("#__init__(): TODO")
#    @skip.when(import_failed, reason)
#    def _(self):
#        ## TODO:
#        pass
#
#
#    @test("#__enter__(): TODO")
#    @skip.when(import_failed, reason)
#    def _(self):
#        ## TODO:
#        pass
#
#
#    @test("#__exit__(): TODO")
#    @skip.when(import_failed, reason)
#    def _(self):
#        ## TODO:
#        pass



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
    oktest.main()
