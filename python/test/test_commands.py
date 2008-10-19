###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

import unittest
from test import test_support
import sys, os, re, time, shutil
from glob import glob

from testcase_helper import *
from kook.commands import *
from kook.utils import read_file, write_file
from _testcase_helper import *


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


class KookCommandsTest(unittest.TestCase, TestCaseHelper):


    def setUp(self):
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

    def tearDown(self):
        for f in glob('hello*'):
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.unlink(f)


    def test_cp(self):
        self.assertFileNotExist('hello2.c')
        time.sleep(1)
        cp('hello.c', 'hello2.c')
        self.assertFileExists('hello2.c')
        self.assertFileNewerThan('hello2.c', 'hello.c')

    def test_cp_p(self):
        self.assertFileNotExist('hello2.c')
        cp_p('hello.c', 'hello2.c')
        self.assertFileExists('hello2.c')
        self.assertSameTimestampWith('hello2.c', 'hello.c')

    def test_cp_r(self):
        self.assertFileNotExist('hello.d/src2')
        cp_r('hello.d/src', 'hello.d/src2')
        self.assertFileExists('hello.d/src2/include/hello.h')
        self.assertFileNewerThan('hello.d/src2/include/hello.h', 'hello.d/src/include/hello.h')

    def test_cp_pr(self):
        self.assertFileNotExist('hello.d/src2')
        cp_r('hello.d/src', 'hello.d/src2')
        self.assertFileExists('hello.d/src2/include/hello.h')
        #self.assertSameTimestampWith('hello.d/src2/include/hello.h', 'hello.d/src/include/hello.h') # BUG


    def test_glob2(self):
        from kook.utils import glob2
        expected = ["hello.d/src/include/hello.h", "hello.d/src/include/hello2.h"]
        self.assertEquals(expected, glob2("hello.d/**/*.h"))
        expected = ["hello.h", "hello.d/src/include/hello.h", "hello.d/src/include/hello2.h"]
        #self.assertEquals(expected, glob2("**/*.h")) # BUG
        expected = [
            "hello.d/src",
            "hello.d/src/include",
            "hello.d/src/lib",
            "hello.d/src/include/hello.h",
            "hello.d/src/include/hello2.h",
            "hello.d/src/lib/hello.c",
        ]
        self.assertEquals(expected, glob2("hello.d/**/*"))


def test_main():
    test_support.run_unittest(KookCommandsTest)


if __name__ == '__main__':
    test_main()

