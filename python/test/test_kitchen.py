###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re, time
from os.path import isfile, isdir
from glob import glob
try:
    from StringIO import StringIO      # 2.x
except ImportError:
    from io import StringIO            # 3.x

import kook
from kook import *
from kook.kitchen import *
from kook.cookbook import *
from kook.commands import *
from kook.utils import read_file, write_file


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


class KookKitchenTest(object):


    def before_each(self):
        _setup_stdio()
        write_file('hello.c', HELLO_C)
        write_file('hello.h', HELLO_H)

    def after_each(self):
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
        ok('hello.o', isfile)
        ok(_stdout(), '==', "invoked.\n")
        expected = "### * hello.o (func=file_hello_o)\n$ gcc -c hello.c\n$ echo invoked.\n"
        ok(_stderr(), '==', expected)


    def test_generic_file_cooking1(self):
        content = r"""\
@product('*.o')
@ingreds('$(1).c', '$(1).h')
def file_ext_o(c):
    system('gcc -c %s' % c.ingred)
    echo("invoked.")
"""
        self._start(content, 'hello.o')
        ok('hello.o', isfile)
        ok(_stdout(), '==', "invoked.\n")
        expected = "### * hello.o (func=file_ext_o)\n$ gcc -c hello.c\n$ echo invoked.\n"
        ok(_stderr(), '==', expected)


    def test_specific_task_cooking1(self):
        content = r"""\
def task_build(c):
    system('gcc -o hello hello.c')
    echo("invoked.")
"""
        self._start(content, 'build')
        ok('hello', isfile)
        ok(_stdout(), '==', "invoked.\n")
        expected = "### * build (func=task_build)\n$ gcc -o hello hello.c\n$ echo invoked.\n"
        ok(_stderr(), '==', expected)


    def test_generic_task_cooking1(self):
        content = r"""\
@product('build_*')
def task_build(c):
    system('gcc -o %s %s.c' % (c.m[1], c.m[1]))
    echo("invoked.")
"""
        self._start(content, 'build_hello')
        ok('hello', isfile)
        ok(_stdout(), '==', "invoked.\n")
        expected = "### * build_hello (func=task_build)\n$ gcc -o hello hello.c\n$ echo invoked.\n"
        ok(_stderr(), '==', expected)


    def test_error_when_ingredients_not_found(self):
        content = r"""
@product("*.o")
@ingreds("$(1).c", "$(1).h")    # *.h not found
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")
"""
        if os.path.isfile("hello.h"): os.unlink("hello.h")
        ok("hello.c", isfile)
        def _f():
            self._start(content, "hello.o")
        errmsg = "hello.h: can't find any recipe to produce."
        ok(_f, 'raises', kook.KookRecipeError, errmsg)


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
        ok("hello.o", isfile)
        ok(_stdout(), '==', "")
        ok(_stderr(), '==', "### * hello.o (func=file_ext_o)\n$ gcc -c hello.c\n")
        ## when hello.h exists (and newer than product)
        _setup_stdio()
        time.sleep(1)
        write_file("hello.h", "#include <stdio.h>\n")
        self._start(content, "hello.o")
        ok("hello.o", isfile)
        ok(_stdout(), '==', "")
        ok(_stderr(), '==', "### * hello.o (func=file_ext_o)\n$ gcc -c hello.c hello.h\n")


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
        func = lambda: self._start(content, "all")
        errmsg = "hello: recipe is looped (hello->hello.o->hello.c->hello)."
        ok(func, 'raises', KookRecipeError, errmsg)


    def test_recipe_cmdopts1(self):
        content = r"""
import kook
@optdefs("-h: help", "-D[N]: debug level (default N is 1)", "-f file: filename",
         "--help: help", "--debug[=N]: debug", "--file=filename: file")
def task_build(c, *args):
    opts, rests = c.parse_cmdopts(args)
    kook._stdout.write("opts=%s\n" % repr(opts))
    kook._stdout.write("rests=%s\n" % repr(rests))
    for key in sorted(opts.keys()):
        kook._stdout.write("opts[%s]=%s\n" % (repr(key), opts[key]))
"""
        self._start(content, "build", "-hf foo.txt", "-D999", "--help", "--debug", "--file=bar.txt", "aaa", "bbb")
        expected = """\
opts={'help': True, 'f': ' foo.txt', 'h': True, 'file': 'bar.txt', 'debug': True, 'D': 999}
rests=('aaa', 'bbb')
opts['D']=999
opts['debug']=True
opts['f']= foo.txt
opts['file']=bar.txt
opts['h']=True
opts['help']=True
"""
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "### * build (func=task_build)\n")
        ## command option error
        from kook.utils import CommandOptionError
        func = lambda: self._start(content, "build", "-f")
        errmsg = "task_build(): -f: file required."
        ok(func, 'raises', CommandOptionError, errmsg)
        #
        func = lambda: self._start(content, "build", "-Dx")
        errmsg = "task_build(): -Dx: integer required."
        ok(func, 'raises', CommandOptionError, errmsg)
        #
        func = lambda: self._start(content, "build", "--debug=x")
        errmsg = "task_build(): --debug=x: integer required."
        ok(func, 'raises', CommandOptionError, errmsg)


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
        ok("hello", isfile)
        ok(_stdout(), '==', "")
        expected = (
            "### ** hello.o (func=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "### * hello (func=file_command)\n"
            "$ gcc -o hello hello.o\n"
        )
        ok(_stderr(), '==', expected)
        ## 2nd (content compared)
        old_utime = os.path.getmtime("hello")
        time.sleep(1)
        os.utime("hello.c", None)
        _setup_stdio()
        self._start(content, "hello")
        ok(os.path.getmtime("hello"), '>', old_utime)
        ok("hello", isfile)
        ok(_stdout(), '==', "")
        expected = (
            "### ** hello.o (func=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "### * hello (func=file_command)\n"
            "$ touch hello   # skipped\n"             # content compared and skipped
        )
        ok(_stderr(), '==', expected)


    def test_remove_produt_when_recipe_failed1(self):
        content = r"""
@product('hello.h')
@ingreds('hello.c')
def file_hello_txt(c):
    open(c.product, "w").write("abc")
    #import sys, os
    #sys.stderr.write("*** debug: os.path.exists('hello.h')=%s\n" % (os.path.exists('hello.h')))
    system(c%"gcc HOGE.c")
    #system(c%"gcc HOGE.c 2>&1 /dev/null")
"""
        ok("hello.h", isfile)
        time.sleep(1)
        os.utime("hello.c", None)
        func = lambda: self._start(content, "hello.h")
        ok(func, 'raises', kook.KookCommandError)
        ok(_stdout(), '==', "")
        expected = (
            "### * hello.h (func=file_hello_txt)\n"
            "$ gcc HOGE.c\n"
            "### * (remove hello.h because unexpected error raised (func=file_hello_txt))\n"
        )
        ok(_stderr(), '==', expected)
        ok("hello.h", isfile, False)         # product should be removed


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
        ok("hello", isfile)
        ok(_stdout(), '==', "task_build() invoked.\ntask_all() invoked.\n")
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
        ok(_stderr(), '==', expected)
        ## 2nd
        _setup_stdio()
        self._start(content, "all")
        ok(_stdout(), '==', "task_build() invoked.\ntask_all() invoked.\n")
        expected = (
            "### ** build (func=task_build)\n"
            "$ echo task_build() invoked.\n"
            "### * all (func=task_all)\n"
            "$ echo task_all() invoked.\n"
        )
        ok(_stderr(), '==', expected)
        ## 3rd, content compared, if_exists()
        time.sleep(1)
        write_file("hello.h", "#include <stdio.h>\n")
        _setup_stdio()
        self._start(content, "all")
        ok(_stdout(), '==', "task_build() invoked.\ntask_all() invoked.\n")
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
        ok(_stderr(), '==', expected)


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
