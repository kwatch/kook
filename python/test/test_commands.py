###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re, time, shutil
from os.path import isfile, isdir, getmtime
from glob import glob
try:
    from StringIO import StringIO      # 2.x
except ImportError:
    from io import StringIO            # 3.x


from kook.commands import *
from kook.utils import read_file, write_file
import kook.config as config

def _setup_stdio():
    config.stdout = StringIO()
    config.stderr = StringIO()

def _teardown_stdio():
    config.stdout = sys.stdout
    config.stderr = sys.stderr

def _getvalues():
    return (config.stdout.getvalue(), config.stderr.getvalue())

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


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
