###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re, time, shutil
#from os.path import isfile, isdir, getmtime
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


class KookUtilsTest(object):


    def test_glob2(self):
        try:
            #
            write_file('hello.c', HELLO_C)
            write_file('hello.h', HELLO_H)
            os.makedirs('hello.d/src/lib')
            os.makedirs('hello.d/src/include')
            write_file('hello.d/src/lib/hello.c', HELLO_C)
            write_file('hello.d/src/include/hello.h', HELLO_H)
            write_file('hello.d/src/include/hello2.h', HELLO_H)
            #
            from kook.utils import glob2
            expected = [
                "hello.d/src/include/hello.h",
                "hello.d/src/include/hello2.h",
            ]
            ok(glob2("hello.d/**/*.h"), '==', expected)
            #
            expected = [
                "hello.h",
                "hello.d/src/include/hello.h",
                "hello.d/src/include/hello2.h",
            ]
            ok(glob2("**/*.h"), '==', expected)
            #
            expected = [
                "hello.d/src",
                "hello.d/src/include",
                "hello.d/src/lib",
                "hello.d/src/include/hello.h",
                "hello.d/src/include/hello2.h",
                "hello.d/src/lib/hello.c",
            ]
            ok(glob2("hello.d/**/*"), '==', expected)
            #
        finally:
            for f in glob('hello*'):
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.unlink(f)


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
