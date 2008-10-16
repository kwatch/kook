###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

import unittest
from test import test_support
import sys, os, re, time
from glob import glob
from StringIO import StringIO

#from testcase_helper import *
import kook
from kook import *
from kook.kitchen import *
from kook.cookbook import *
from kook.commands import *
from kook.util import read_file, write_file

from _testcase_helper import TestCaseHelper


def _setup_stdio():
    kook._stdout = StringIO()
    kook._stderr = StringIO()

def _teardown_stdio():
    kook._stdout = sys.stdout
    kook._stderr = sys.stderr

def _stdout():
    return kook._stdout.getvalue()

def _stderr():
    return kook._stderr.getvalue()


HELLO_C = r"""
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


class KookKitchenTest(unittest.TestCase, TestCaseHelper):


    def setUp(self):
        _setup_stdio()
        write_file('hello.c', HELLO_C)
        write_file('hello.h', HELLO_H)

    def tearDown(self):
        for x in glob('hello*'):
            os.unlink(x)
        _teardown_stdio()

    def _start(self, content, *targets):
        kookbook = Cookbook()
        kookbook.load(content)
        kitchen = Kitchen(kookbook)
        kitchen.start_cooking(*targets)
        return kitchen

    def test_specific_file_cooking1(self):
        content = r"""\
@product('hello.o')
@ingreds('hello.c', 'hello.h')
def file_hello_o(c):
    system('gcc -c %s' % c.ingred)
    echo("invoked.")
"""
        self._start(content, 'hello.o')
        self.assertFileExists('hello.o')
        self.assertEqual("invoked.\n", _stdout())
        expected = "### * hello.o (func=file_hello_o)\n$ gcc -c hello.c\n$ echo invoked.\n"
        self.assertTextEqual(expected, _stderr())

    def test_generic_file_cooking1(self):
        content = r"""\
@product('*.o')
@ingreds('$(1).c', '$(1).h')
def file_ext_o(c):
    system('gcc -c %s' % c.ingred)
    echo("invoked.")
"""
        self._start(content, 'hello.o')
        self.assertFileExists('hello.o')
        self.assertEqual("invoked.\n", _stdout())
        expected = "### * hello.o (func=file_ext_o)\n$ gcc -c hello.c\n$ echo invoked.\n"
        self.assertTextEqual(expected, _stderr())

    def test_specific_task_cooking1(self):
        content = r"""\
def task_build(c):
    system('gcc -o hello hello.c')
    echo("invoked.")
"""
        self._start(content, 'build')
        self.assertFileExists('hello')
        self.assertEqual("invoked.\n", _stdout())
        expected = "### * build (func=task_build)\n$ gcc -o hello hello.c\n$ echo invoked.\n"
        self.assertTextEqual(expected, _stderr())

    def test_generic_task_cooking1(self):
        content = r"""\
@product('build_*')
def task_build(c):
    system('gcc -o %s %s.c' % (c.m[1], c.m[1]))
    echo("invoked.")
"""
        self._start(content, 'build_hello')
        self.assertFileExists('hello')
        self.assertEqual("invoked.\n", _stdout())
        expected = "### * build_hello (func=task_build)\n$ gcc -o hello hello.c\n$ echo invoked.\n"
        self.assertTextEqual(expected, _stderr())

    def test_generic_task_cooking1(self):
        content = r"""\
@product('build_*')
def task_build(c):
    system('gcc -o %s %s.c' % (c.m[1], c.m[1]))
    echo("invoked.")
"""
        self._start(content, 'build_hello')
        self.assertFileExists('hello')
        self.assertEqual("invoked.\n", _stdout())
        expected = "### * build_hello (func=task_build)\n$ gcc -o hello hello.c\n$ echo invoked.\n"
        self.assertTextEqual(expected, _stderr())


def test_main():
    test_support.run_unittest(KookKitchenTest)


if __name__ == '__main__':
    test_main()

