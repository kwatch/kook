###
### $Release: $
### $Copyright$
### $License$
###

from oktest import *
import sys, os, re, time, shutil
from os.path import isfile, isdir, getmtime
from glob import glob

from kook.commands import *
from kook.utils import read_file, write_file


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

    def test_cp_p(self):
        ok('hello2.c', isfile, False)
        cp_p('hello.c', 'hello2.c')
        ok('hello2.c', isfile, True)
        ok(getmtime('hello2.c'), '==', getmtime('hello.c'))

    def test_cp_r(self):
        ok('hello.d/src2', isfile, False)
        cp_r('hello.d/src', 'hello.d/src2')
        ok('hello.d/src2/include/hello.h', isfile, True)
        ok(getmtime('hello.d/src2/include/hello.h'), '>', getmtime('hello.d/src/include/hello.h'))

    def test_cp_pr(self):
        ok('hello.d/src2', isfile, False)
        cp_r('hello.d/src', 'hello.d/src2')
        ok('hello.d/src2/include/hello.h', isfile)
        #ok(getmtime('hello.d/src2/include/hello.h'), '==', getmtime('hello.d/src/include/hello.h')) # BUG

    def test_glob2(self):
        from kook.utils import glob2
        expected = ["hello.d/src/include/hello.h", "hello.d/src/include/hello2.h"]
        ok(glob2("hello.d/**/*.h"), '==', expected)
        expected = ["hello.h", "hello.d/src/include/hello.h", "hello.d/src/include/hello2.h"]
        ok(glob2("**/*.h"), '==', expected)
        expected = [
            "hello.d/src",
            "hello.d/src/include",
            "hello.d/src/lib",
            "hello.d/src/include/hello.h",
            "hello.d/src/include/hello2.h",
            "hello.d/src/lib/hello.c",
        ]
        ok(glob2("hello.d/**/*"), '==', expected)


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
