###
### $Release: $
### $Copyright$
### $License$
###

from __future__ import with_statement

import sys, os
import oktest
from oktest import ok, NG, test, skip
import oktest.tracer

import_failed = False
reason = None
try:
    import kook.remote
    from kook.remote import *
except ImportError:
    import_failed = True
    reason = sys.exc_info()[1].message



class KookRemoteTest(object):


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


    @test("#new_session(): returns Session object.")
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


    @test("#__exit__(): (internal) calls Session#_close().")
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
            ok (sess).is_a(kook.remote.Session)
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

    @test("#__call__(): connects to hosts.")
    @skip.when(import_failed, reason)
    def _(self):
        ## TODO:
        pass



class KookSessionTest(object):


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
