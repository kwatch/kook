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


    def test_error_when_ingredients_not_found(self):
        content = r"""
@product("*.o")
@ingreds("$(1).c", "$(1).h")    # *.h not found
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")
"""
        if os.path.isfile("hello.h"): os.unlink("hello.h")
        self.assertFileExists("hello.c")
        def _f():
            self._start(content, "hello.o")
        ex = self.assertRaises2(kook.KookRecipeError, _f)
        self.assertTextEqual("hello.h: can't find any recipe to produce.", str(ex))


    def test_if_exists1(self):
        content = r"""
@product("*.o")
@ingreds("$(1).c", if_exists("$(1).h"))    # *.h may not exist
def file_ext_o(c):
    if len(c.ingreds) == 2:
        system(c%"gcc -c $(ingreds[0]) $(ingreds[1])")
    else:
        system(c%"gcc -c $(ingreds[0])")
"""
        ## when hello.h not exist
        if os.path.exists("hello.o"): os.unlink("hello.o")
        if os.path.exists("hello.h"): os.unlink("hello.h")
        self._start(content, "hello.o")
        self.assertFileExists("hello.o")
        self.assertTextEqual("", _stdout())
        self.assertTextEqual("### * hello.o (func=file_ext_o)\n$ gcc -c hello.c\n", _stderr())
        ## when hello.h exists (and newer than product)
        _setup_stdio()
        time.sleep(1)
        write_file("hello.h", "#include <stdio.h>\n")
        self._start(content, "hello.o")
        self.assertFileExists("hello.o")
        self.assertTextEqual("", _stdout())
        self.assertTextEqual("### * hello.o (func=file_ext_o)\n$ gcc -c hello.c hello.h\n", _stderr())


    def test_looped_cooking_tree1(self):
        content = r"""
@product("hello")
@ingreds("hello.o")
def file_hello(c):
    system(c%"gcc -o $(product) $(ingred)")

@product("*.o")
@ingreds("$(1).c")
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")

@product("*.c")
@ingreds("$(1)")            # looped ("$(1)" == "hello")
def file_ext_c(c):
    system(c%"cp $(ingred) $(product)")

@ingreds("hello")
def task_all(c):
    pass
"""
        ex = self.assertRaises2(KookRecipeError, lambda: self._start(content, "all"))
        self.assertTextEqual("hello: recipe is looped (hello->hello.o->hello.c->hello).", str(ex))


    def test_recipe_cmdopts1(self):
        content = r"""
import kook
@options("-h: help", "-D[N]: debug level (default N is 1)", "-f file: filename",
         "--help: help", "--debug[=N]: debug", "--file=filename: file")
def task_build(c, *args):
    opts, rests = c.parse_args(args)
    kook._stdout.write("opts=%s\n" % repr(opts))
    kook._stdout.write("rests=%s\n" % repr(rests))
    for key in sorted(opts.keys()):
        kook._stdout.write("opts[%s]=%s\n" % (repr(key), opts[key]))
"""
        self._start(content, "build", "-hf foo.txt", "-D999", "--help", "--debug", "--file=bar.txt", "aaa", "bbb")
        expected = """\
opts={'help': None, 'f': ' foo.txt', 'h': True, 'file': 'bar.txt', 'debug': True, 'D': 999}
rests=('aaa', 'bbb')
opts['D']=999
opts['debug']=True
opts['f']= foo.txt
opts['file']=bar.txt
opts['h']=True
opts['help']=None
"""
        self.assertTextEqual(expected, _stdout())
        self.assertTextEqual("### * build (func=task_build)\n", _stderr())
        ## command option error
        from kook.util import CommandOptionError
        ex = self.assertRaises2(CommandOptionError, lambda: self._start(content, "build", "-f"))
        self.assertTextEqual("task_build(): -f: file required.", str(ex))


    def test_content_compared1(self):
        content = r"""
@product("hello")
@ingreds("hello.o")
def file_command(c):
    system(c%"gcc -o $(product) $(ingred)")

@product("*.o")
@ingreds("$(1).c")
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")
"""
        ## 1st
        self._start(content, "hello")
        self.assertFileExists("hello")
        self.assertEqual("", _stdout())
        expected = (
            "### ** hello.o (func=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "### * hello (func=file_command)\n"
            "$ gcc -o hello hello.o\n"
        )
        self.assertTextEqual(expected, _stderr())
        ## 2nd (content compared)
        old_utime = os.path.getmtime("hello")
        time.sleep(1)
        os.utime("hello.c", None)
        _setup_stdio()
        self._start(content, "hello")
        self.assertTrue(os.path.getmtime("hello") > old_utime, "hello's mtime is not changed.")
        self.assertFileExists("hello")
        self.assertEqual("", _stdout())
        expected = (
            "### ** hello.o (func=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "### * hello (func=file_command)\n"
            "$ touch hello   # skipped\n"             # content compared and skipped
        )
        self.assertTextEqual(expected, _stderr())


    def test_complicated_cooking1(self):
        content = r"""
command = "hello"

@ingreds(command)
def task_build(c):
    echo("task_build() invoked.")

@product(command)
@ingreds("%s.o" % command)
def file_command(c):
    system(c%"gcc -o $(product) $(ingred)")

@product("*.o")
@ingreds("$(1).c", if_exists("$(1).h"))
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")
    system(c%"gcc -g -c $(1).c")

@ingreds('build')
def task_all(c):
    echo("task_all() invoked.")
"""
        ## 1st
        self._start(content, "all")
        self.assertFileExists("hello")
        self.assertEqual("task_build() invoked.\ntask_all() invoked.\n", _stdout())
        expected = (
            "### **** hello.o (func=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "$ gcc -g -c hello.c\n"
            "### *** hello (func=file_command)\n"
            "$ gcc -o hello hello.o\n"
            "### ** build (func=task_build)\n"
            "$ echo task_build() invoked.\n"
            "### * all (func=task_all)\n"
            "$ echo task_all() invoked.\n"
        )
        self.assertTextEqual(expected, _stderr())
        ## 2nd
        _setup_stdio()
        self._start(content, "all")
        self.assertEqual("task_build() invoked.\ntask_all() invoked.\n", _stdout())
        expected = (
            "### ** build (func=task_build)\n"
            "$ echo task_build() invoked.\n"
            "### * all (func=task_all)\n"
            "$ echo task_all() invoked.\n"
        )
        self.assertTextEqual(expected, _stderr())
        ## 3rd, content compared, if_exists()
        time.sleep(1)
        write_file("hello.h", "#include <stdio.h>\n")
        _setup_stdio()
        self._start(content, "all")
        self.assertEqual("task_build() invoked.\ntask_all() invoked.\n", _stdout())
        expected = (
            "### **** hello.o (func=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "$ gcc -g -c hello.c\n"
            "### *** hello (func=file_command)\n"
            "$ touch hello   # skipped\n"                   # skipped
            "### ** build (func=task_build)\n"
            "$ echo task_build() invoked.\n"
            "### * all (func=task_all)\n"
            "$ echo task_all() invoked.\n"
        )
        self.assertTextEqual(expected, _stderr())


KookKitchenTest.remove_tests_except(os.environ.get('TEST'))


def test_main():
    test_support.run_unittest(KookKitchenTest)


if __name__ == '__main__':
    test_main()

