###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re, time, shutil
from os.path import exists, isfile, isdir, getmtime
from glob import glob
try:
    from StringIO import StringIO      # 2.x
except ImportError:
    from io import StringIO            # 3.x


from kook import KookCommandError
from kook.commands import *
import kook.commands
from kook.utils import read_file, write_file
import kook.config as config

def _getvalues(set=False):
    pair = (config.stdout.getvalue(), config.stderr.getvalue())
    if set:
        config.stdout = StringIO()
        config.stderr = StringIO()
    return pair

HELLO_C = """\
#include <stdio.h>

int main(int argc, char *argv[]) {
    int i;
    for (i = 0; i < argc; i++) {
        printf("argv[%d]: %s\n", i, argv[i]);
    }
    return 0;
}
"""

HELLO_H = """\
char *command = "hello";
char *release = "$_RELEASE_$";
"""


class KookCommandsTest(object):


    def before_each(self):
        config.stdout = StringIO()
        config.stderr = StringIO()
        #
        write_file('hello.c', HELLO_C)
        write_file('hello.h', HELLO_H)
        t = time.time() - 99
        os.utime('hello.c', (t, t))
        os.utime('hello.h', (t, t))
        #
        os.makedirs('hello.d/src/lib')
        os.makedirs('hello.d/src/include')
        write_file('hello.d/src/lib/hello.c', HELLO_C)
        write_file('hello.d/src/include/hello.h', HELLO_H)
        write_file('hello.d/src/include/hello2.h', HELLO_H)
        os.utime('hello.d/src/lib/hello.c', (t, t))
        os.utime('hello.d/src/include/hello.h', (t, t))
        os.utime('hello.d/src/include/hello2.h', (t, t))

    def after_each(self):
        config.stdout = sys.stdout
        config.stderr = sys.stderr
        #
        for f in glob('hello*'):
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.unlink(f)


    def test_system(command):
        ok('hello2.c', isfile, False)
        system('cat -n hello.c > hello2.c')
        ok('hello2.c', isfile)
        i = 0
        buf = []
        for line in read_file('hello.c').splitlines(True):
            i += 1
            buf.append("%6d\t%s" % (i, line))
        ok(read_file('hello2.c'), '==', "".join(buf))
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ cat -n hello.c > hello2.c\n")
        ok(serr, '==', "")
        # raises KookCommandError
        def f():
            system('cat -n hello999.c 2>/dev/null')
        ok(f, 'raises', KookCommandError, "command failed (status=256).")

    def test_system_f(command):
        # raises KookCommandError
        def f():
            system_f('cat -n hello999.c 2>/dev/null')
        ok(f, 'not raise', Exception)


    def test_cp(self):
        ok('hello2.c', isfile, False)
        time.sleep(1)
        cp('hello.c', 'hello2.c')
        ok('hello2.c', isfile, True)
        ok(getmtime('hello2.c'), '>', getmtime('hello.c'))
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ cp hello.c hello2.c\n")
        ok(serr, '==', "")

    def test_cp_p(self):
        ok('hello2.c', isfile, False)
        cp_p('hello.c', 'hello2.c')
        ok('hello2.c', isfile, True)
        ok(getmtime('hello2.c'), '==', getmtime('hello.c'))
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ cp -p hello.c hello2.c\n")
        ok(serr, '==', "")

    def test_cp_r(self):
        ok('hello.d/src2', isfile, False)
        cp_r('hello.d/src', 'hello.d/src2')
        ok('hello.d/src2/include/hello.h', isfile, True)
        ok(getmtime('hello.d/src2/include/hello.h'), '>', getmtime('hello.d/src/include/hello.h'))
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ cp -r hello.d/src hello.d/src2\n")
        ok(serr, '==', "")

    def test_cp_pr(self):
        ok('hello.d/src2', isfile, False)
        cp_pr('hello.d/src', 'hello.d/src2')
        ok('hello.d/src2/include/hello.h', isfile)
        ok(getmtime('hello.d/src2/include/hello.h'), '==', getmtime('hello.d/src/include/hello.h')) # BUG
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ cp -pr hello.d/src hello.d/src2\n")
        ok(serr, '==', "")


    def test_mkdir(self):
        path = "hello.d/test"
        ok(path, exists, False)
        mkdir(path)
        ok(path, isdir, True)
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ mkdir %s\n" % path)
        ok(serr, '==', "")
        #
        def f():
            mkdir(path)
        ok(f, 'raises', KookCommandError, "mkdir: %s: already exists." % path)
        #
        path = "hello.notexist/test"
        def f():
            mkdir(path)
        ok(f, 'raises', OSError, "[Errno 2] No such file or directory: '%s'" % path)

    def test_mkdir_p(self):
        path = "hello.d/test/data/d1"
        ok(path, exists, False)
        mkdir_p(path)
        ok(path, isdir, True)
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ mkdir -p %s\n" % path)
        ok(serr, '==', "")
        #
        def f():
            mkdir(path)
        ok(f, 'raises', KookCommandError, "mkdir: %s: already exists." % path)


    def test_rm(self):
        if (isdir('hello.d')):
            shutil.rmtree('hello.d')
        #
        ok('hello.c', isfile)
        ok('hello.h', isfile)
        rm('hello.*')
        ok('hello.c', exists, False)
        ok('hello.h', exists, False)
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ rm hello.*\n")
        ok(serr, '==', "")
        #
        def f():
            rm('hello.*')
        ok(f, 'raises', KookCommandError, "rm: hello.*: not found.")
        #
        mkdir("hello.d")
        def f():
            rm('hello.d')
        ok(f, 'raises', KookCommandError, "rm: hello.d: can't remove directry (try 'rm_r' instead).")

    def test_rm_r(self):
        ok('hello.d', isdir, True)
        rm_r('hello.d')
        ok('hello.d', exists, False)
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ rm -r hello.d\n")
        ok(serr, '==', "")
        #
        def f():
            rm_r('hello.d')
        ok(f, 'raises', KookCommandError, "rm_r: hello.d: not found.")

    def test_rm_f(self):
        if (isdir('hello.d')):
            shutil.rmtree('hello.d')
        #
        ok('hello.c', isfile, True)
        ok('hello.h', isfile, True)
        rm_f('hello.*')
        ok('hello.c', isfile, False)
        ok('hello.h', isfile, False)
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ rm -f hello.*\n")
        ok(serr, '==', "")
        #
        def f():
            rm_f('hello.*')
        ok(f, 'not raise', Exception)
        #
        mkdir('hello.d')
        def f():
            rm_f('hello.d')
        ok(f, 'raises', KookCommandError, "rm_f: hello.d: can't remove directry (try 'rm_r' instead).")

    def test_rm_rf(self):
        ok('hello.c', isfile, True)
        ok('hello.h', isfile, True)
        ok('hello.d', isdir,  True)
        rm_rf('hello.*')
        ok('hello.c', exists, False)
        ok('hello.h', exists, False)
        ok('hello.d', exists, False)
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ rm -rf hello.*\n")
        ok(serr, '==', "")
        #
        def f():
            rm_f('hello.*')
        ok(f, 'not raise', Exception)


    def test_mv(self):
        # move file
        ok('hello.c',  isfile, True)
        ok('hello2.c', isfile, False)
        mv('hello.c', 'hello2.c')
        ok('hello.c',  isfile, False)
        ok('hello2.c', isfile, True)
        # move directory
        ok('hello.d',  isdir, True)
        ok('hello2.d', isdir, False)
        mv('hello.d', 'hello2.d')
        ok('hello.d',  isdir, False)
        ok('hello2.d', isdir, True)
        #
        expected = r"""
$ mv hello.c hello2.c
$ mv hello.d hello2.d
"""[1:]
        sout, serr = _getvalues()
        ok(sout, '==', expected)
        ok(serr, '==', "")
        #
        def f():
            mv('hello.notexist', 'hello.new')
        ok(f, 'raises', KookCommandError, "mv: hello.notexist: not found.")

    def test_mv2(self):
        # move some files into directory
        os.mkdir("hello2.d")
        os.mkdir("hello2.d/backup")
        mv("hello.*", "hello2.d/backup")
        ok("hello.c", exists, False)
        ok("hello.h", exists, False)
        ok("hello.d", exists, False)
        ok("hello2.d/backup/hello.c", isfile)
        ok("hello2.d/backup/hello.h", isfile)
        ok("hello2.d/backup/hello.d", isdir)
        sout, serr = _getvalues()
        ok(sout, '==', "$ mv hello.* hello2.d/backup\n")
        ok(serr, '==', "")
        #
        def f():
            mv('notexist.*', 'hello2.d')
        ok(f, 'raises', KookCommandError, "mv: notexist.*: not found.")


    def test_echo(self):
        echo("YES")
        echo("hello.*")
        expected = r"""
$ echo YES
YES
$ echo hello.*
hello.c hello.d hello.h
"""[1:]
        sout, serr = _getvalues()
        ok(sout, '==', expected)
        ok(serr, '==', "")

    def test_echo_n(self):
        echo_n("YES")
        echo_n("hello.*")
        expected = r"""
$ echo -n YES
YES$ echo -n hello.*
hello.c hello.d hello.h
"""[1:-1]
        sout, serr = _getvalues()
        ok(sout, '==', expected)
        ok(serr, '==', "")


    def test_store(self):
        os.mkdir('hello2.d')
        time.sleep(1)
        store('**/*.h', 'hello2.d')
        ok('hello2.d/hello.h',                      isfile, True)
        ok('hello2.d/hello.d/src/include/hello.h',  isfile, True)
        ok('hello2.d/hello.d/src/include/hello2.h', isfile, True)
        #
        base = 'hello.h'
        ok(getmtime('hello2.d/'+base), '>', getmtime(base))
        base = 'hello.d/src/include/hello.h'
        ok(getmtime('hello2.d/'+base), '>', getmtime(base))
        base = 'hello.d/src/include/hello2.h'
        ok(getmtime('hello2.d/'+base), '>', getmtime(base))
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ store **/*.h hello2.d\n")
        ok(serr, '==', "")
        #
        def f():
            store('**/*.h', 'hello999.d')
        ok(f, 'raises', KookCommandError, "store: hello999.d: directory not found.")

    def test_store_p(self):
        os.mkdir('hello2.d')
        time.sleep(1)
        store_p('**/*.h', 'hello2.d')
        ok('hello2.d/hello.h',                      isfile, True)
        ok('hello2.d/hello.d/src/include/hello.h',  isfile, True)
        ok('hello2.d/hello.d/src/include/hello2.h', isfile, True)
        #
        base = 'hello.h'
        ok(getmtime('hello2.d/'+base), '==', getmtime(base))
        base = 'hello.d/src/include/hello.h'
        ok(getmtime('hello2.d/'+base), '==', getmtime(base))
        base = 'hello.d/src/include/hello2.h'
        ok(getmtime('hello2.d/'+base), '==', getmtime(base))
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ store -p **/*.h hello2.d\n")
        ok(serr, '==', "")


    def test_chdir(self):
        obj = chdir('hello.d')
        ok(obj, 'is a', kook.commands.Chdir)
        ok(hasattr(obj, '__enter__'), '==', True)
        ok(hasattr(obj, '__exit__'),  '==', True)
        #
        major, minor = sys.version_info[0:2]
        with_stmt_available = major >= 3 or (major == 2 and minor >= 5)
        if with_stmt_available:
            input = r"""
import os
from kook.commands import chdir
def test_chdir():
    obj = inner_dir = outer_dir = None
    with chdir('hello.d') as d:
        obj = d
        inner_dir = os.getcwd()
    outer_dir = os.getcwd()
    return (obj, inner_dir, outer_dir)
"""
            if major == 2 and minor == 5:
                input = "from __future__ import with_statement\n" + input
            write_file("hello_.py", input)
            import hello_
            obj, inner_dir, outer_dir = hello_.test_chdir()
            ok(obj, 'is a', kook.commands.Chdir)
            cwd = os.getcwd()
            ok(inner_dir, '==', os.path.join(cwd, 'hello.d'))
            ok(outer_dir, '==', cwd)
            #
            expected = r"""
$ chdir hello.d
$ chdir -   # back to %s
"""[1:] % cwd
            sout, serr = _getvalues()
            ok(sout, '==', expected)
            ok(serr, '==', "")

    def test_chdir2(self):
        curr_dir = os.getcwd()
        if "function is passed as 2nd argument":
            inner_dir = [None]
            def f():
                inner_dir[0] = os.getcwd()
            obj = chdir('hello.d', f)
            outer_dir = os.getcwd()
            ok(outer_dir, '==', curr_dir)
            ok(inner_dir[0], '==', os.path.join(curr_dir, 'hello.d'))
            #
            expected = r"""
$ chdir hello.d
$ chdir -   # back to %s
"""[1:]     % curr_dir
            sout, serr = _getvalues()
            ok(sout, '==', expected)
            ok(serr, '==', "")
        #
        if "function passed as 2nd argument raises exception":
            inner_dir = [None]
            def f():
                inner_dir[0] = os.getcwd()
                raise TypeError('***')
            def should_raise():
                obj = chdir('hello.d', f)
            ok(should_raise, 'raises', TypeError, '***')
            #
            outer_dir = os.getcwd()
            ok(outer_dir, '==', curr_dir)
            ok(inner_dir[0], '==', os.path.join(curr_dir, 'hello.d'))

    def test_ch(self):
        cwd = os.getcwd()
        try:
            path = cd('hello.d')
            ok(path, '==', cwd)
            ok(os.getcwd(), '==', os.path.join(cwd, 'hello.d'))
            #
            sout, serr = _getvalues()
            ok(sout, '==', "$ cd hello.d\n")
            ok(serr, '==', "")
        finally:
            cd(cwd)


    def _test_edit(self):
        content = read_file('hello.h')
        ok(content.find('1.2.3'), '>', 0)
        content = read_file('hello.d/src/include/hello.h')
        ok(content.find('1.2.3'), '>', 0)
        content = read_file('hello.d/src/include/hello2.h')
        ok(content.find('1.2.3'), '>', 0)
        #
        sout, serr = _getvalues()
        ok(sout, '==', "$ edit **/*.h\n")
        ok(serr, '==', "")

    def test_edit(self):
        # edit by callable
        def f(content):
            return re.sub(r'\$_RELEASE_\$', '1.2.3', content)
        edit("**/*.h", by=f)
        self._test_edit()

    def test_edit2(self):
        # edit by tuples
        by = [
            (r'\$_RELEASE_\$', '1.2.3'),
        ]
        edit("**/*.h", by=by)
        self._test_edit()


    def test_noexec(self):
        noexec = config.noexec
        config.noexec = True
        try:
            # system
            for f in (system, system_f):
                f("cat -n hello.c > hello2.c")
                ok("hello2.c", exists, False)
                sout, serr = _getvalues(True)
                ok(sout, '==', "$ cat -n hello.c > hello2.c\n")
                ok(serr, '==', "")
            # cp
            for f in (cp, cp_p, cp_r, cp_pr):
                f("hello.c", "hello2.c")
                ok("hello2.c", exists, False)
                name = kook.utils.get_funcname(f)
                sout, serr = _getvalues(True)
                ok(sout, '==', "$ %s hello.c hello2.c\n" % re.sub('_', ' -', name))
                ok(serr, '==', "")
            # mkdir
            for f in (mkdir, mkdir_p):
                f("hello2.d")
                ok("hello2.d", exists, False)
                name = kook.utils.get_funcname(f)
                sout, serr = _getvalues(True)
                ok(sout, '==', "$ %s hello2.d\n" % re.sub('_', ' -', name))
                ok(serr, '==', "")
            # rm
            for f in (rm, rm_r, rm_f, rm_rf):
                f("hello.*")
                ok("hello.c", isfile, True)
                name = kook.utils.get_funcname(f)
                sout, serr = _getvalues(True)
                ok(sout, '==', "$ %s hello.*\n" % re.sub('_', ' -', name))
                ok(serr, '==', "")
            # mv
            mv("hello.c", "hello2.c")
            ok("hello2.c", exists, False)
            sout, serr = _getvalues(True)
            ok(sout, '==', "$ mv hello.c hello2.c\n")
            ok(serr, '==', "")
            mv("hello.c", "hello.h", "hello.d")
            ok("hello.c", exists, True)
            ok("hello.h", exists, True)
            sout, serr = _getvalues(True)
            ok(sout, '==', "$ mv hello.c hello.h hello.d\n")
            ok(serr, '==', "")
            # echo
            for f in (echo, echo_n):
                f("YES")
                sout, serr = _getvalues(True)
                name = kook.utils.get_funcname(f)
                ok(sout, '==', "$ %s YES\n" % re.sub('_', ' -', name))
                ok(serr, '==', "")
            # store
            for f in (store, store_p):
                f("**/*.h", "hello2.d")
                ok("hello2.d/hello.h", exists, False)
                sout, serr = _getvalues(True)
                name = kook.utils.get_funcname(f)
                ok(sout, '==', "$ %s **/*.h hello2.d\n" % re.sub('_', ' -', name))
                ok(serr, '==', "")
            # cd
            cwd = cd('hello.d')
            try:
                ok(os.getcwd(), '==', os.path.join(cwd, 'hello.d'))
                sout, serr = _getvalues(True)
                ok(sout, '==', "$ cd hello.d\n")
                ok(serr, '==', "")
            finally:
                cd(cwd)
                _getvalues(True)
            # edit
            def f(content):
                return re.sub('\$_RELEASE_\$', '1.2.3', content)
            edit("hello.h", by=f)
            s = read_file("hello.h")
            ok(s.find("1.2.3"), '==', -1)
            ok(s.find("$_RELEASE_$"), '>', 0)
            #
        finally:
            config.noexec = noexec


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
