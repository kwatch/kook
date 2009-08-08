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
from kook.kitchen import Kitchen
from kook.cookbook import Cookbook
from kook.utils import read_file, write_file, CommandOptionError
import kook.config as config


def _setup_stdio():
    config.stdout = StringIO()
    config.stderr = StringIO()

def _teardown_stdio():
    config.stdout = sys.stdout
    config.stderr = sys.stderr

def _stdout():
    val = config.stdout.getvalue()
    config.stdout.close()
    config.stdout = StringIO()
    return val

def _stderr():
    val = config.stderr.getvalue()
    config.stderr.close()
    config.stderr = StringIO()
    return val


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

    def _kitchen(self, kookbook_py):
        kookbook = Cookbook()
        kookbook.load(kookbook_py)
        kitchen = Kitchen(kookbook)
        return kitchen

    def test_specific_file_cooking1(self):
        content = r"""\
@recipe
@product('hello.o')
@ingreds('hello.c', 'hello.h')
def file_hello_o(c):
    system('gcc -c %s' % c.ingred)
    echo("invoked.")
"""
        expected = ( "### * hello.o (recipe=file_hello_o)\n"
                     "$ gcc -c hello.c\n$ echo invoked.\n"
                     "invoked.\n" )
        ## without @recipe
        self._start(content, 'hello.o')
        ok('hello.o', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## with @recipe
        self.after_each(); self.before_each()
        self._start("@recipe\n" + content, 'hello.o')
        ok('hello.o', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


    def test_generic_file_cooking1(self):
        content = r"""\
@recipe
@product('*.o')
@ingreds('$(1).c', '$(1).h')
def file_ext_o(c):
    system('gcc -c %s' % c.ingred)
    echo("invoked.")
"""
        expected = ( "### * hello.o (recipe=file_ext_o)\n"
                     "$ gcc -c hello.c\n$ echo invoked.\n"
                     "invoked.\n" )
        ## without @recipe
        self._start(content, 'hello.o')
        ok('hello.o', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## with @recipe
        self.after_each(); self.before_each()
        self._start("@recipe\n" + content, 'hello.o')
        ok('hello.o', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


    def test_specific_task_cooking1(self):
        content = r"""\
@recipe
def build(c):
    system('gcc -o hello hello.c')
    echo("invoked.")
"""
        expected = ( "### * build (recipe=build)\n"
                     "$ gcc -o hello hello.c\n$ echo invoked.\n"
                     "invoked.\n" )
        ## without @recipe
        self._start(content, 'build')
        ok('hello', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## with @recipe
        self.after_each(); self.before_each()
        self._start("@recipe\n" + content, 'build')
        ok('hello', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


    def test_generic_task_cooking1(self):
        content = r"""\
@recipe
@product('build_*')
def task_build(c):
    system('gcc -o %s %s.c' % (c.m[1], c.m[1]))
    echo("invoked.")
"""
        expected = ( "### * build_hello (recipe=task_build)\n"
                     "$ gcc -o hello hello.c\n$ echo invoked.\n"
                     "invoked.\n" )
        ## without @recipe
        self._start(content, 'build_hello')
        ok('hello', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## without @recipe
        self.after_each(); self.before_each()
        self._start("@recipe\n" + content, 'build_hello')
        ok('hello', isfile)
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


#    def test_recipe_decorator_without_task_prefix(self):
#        ## without 'task_' prefix
#        content = r"""\
#@recipe
#def build(c):
#    system('gcc -o hello hello.c')
#    echo("invoked.")
#"""
#        expected = ( "### * build (recipe=build)\n"
#                     "$ gcc -o hello hello.c\n$ echo invoked.\n"
#                     "invoked.\n" )
#        self._start(content, 'build')
#        ok('hello', isfile)
#        ok(_stdout(), '==', expected)
#        ok(_stderr(), '==', "")
#
#
#    def test_recipe_decorator_without_file_prefix(self):
#        ## without 'file_' prefix
#        content = r"""
#@recipe
#@product('hello.o')
#def hello_o(c):
#    system('gcc -c hello.c')
#    echo("invoked.")
#"""[1:]
#        expected = r"""
#### * hello.o (recipe=hello_o)
#$ gcc -c hello.c
#$ echo invoked.
#invoked.
#"""[1:]
#        self._start(content, 'hello.o')
#        ok('hello.o', isfile)
#        ok(_stdout(), '==', expected)
#        ok(_stderr(), '==', "")


    def test_error_when_ingredients_not_found(self):
        content = r"""
@recipe
@product("*.o")
@ingreds("$(1).c", "$(1).h")    # *.h not found
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")
"""
        if os.path.isfile("hello.h"): os.unlink("hello.h")
        ok("hello.c", isfile)
        def _f():
            self._start(content, "hello.o")
        errmsg = "hello.h: no such recipe or material (required for 'hello.o')."
        ok(_f, 'raises', kook.KookRecipeError, errmsg)
        #
        def _f():
            self._start(content, "notfound")
        errmsg = "notfound: no such recipe or material."
        ok(_f, 'raises', kook.KookRecipeError, errmsg)


    def test_if_exists1(self):
        content = r"""
@recipe
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
        expected = ( "### * hello.o (recipe=file_ext_o)\n"
                     "$ gcc -c hello.c\n" )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## when hello.h exists (and newer than product)
        _setup_stdio()
        time.sleep(1)
        write_file("hello.h", "#include <stdio.h>\n")
        self._start(content, "hello.o")
        ok("hello.o", isfile)
        expected = ( "### * hello.o (recipe=file_ext_o)\n"
                     "$ gcc -c hello.c hello.h\n" )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


    def test_looped_cooking_tree1(self):
        content = r"""
@recipe
@product("hello")
@ingreds("hello.o")
def file_hello(c):
    system(c%"gcc -o $(product) $(ingred)")

@recipe
@product("*.o")
@ingreds("$(1).c")
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")

@recipe
@product("*.c")
@ingreds("$(1)")            # looped ("$(1)" == "hello")
def file_ext_c(c):
    system(c%"cp $(ingred) $(product)")

@recipe
@ingreds("hello")
def all(c):
    pass
"""
        func = lambda: self._start(content, "all")
        errmsg = "hello: recipe is looped (hello->hello.o->hello.c->hello)."
        ok(func, 'raises', KookRecipeError, errmsg)


    def test_recipe_spices1(self):
        content = r"""
import kook.config as config
@recipe
@spices("-h: help", "-D[N]: debug level (default N is 1)", "-f file: filename",
         "--help: help", "--debug[=N]: debug", "--file=filename: file")
def build(c, *args, **kwargs):
    rests, opts = args, kwargs
    keys = list(opts.keys()); keys.sort()
    s = '{' + ', '.join([ "%s: %s" % (repr(k), repr(opts[k])) for k in keys ]) + '}'
    config.stdout.write("opts=%s\n" % s)
    config.stdout.write("rests=%s\n" % repr(rests))
    for key in sorted(opts.keys()):
        config.stdout.write("opts[%s]=%s\n" % (repr(key), opts[key]))
"""
        self._start(content, "build", "-hf foo.txt", "-D999", "--help", "--debug", "--file=bar.txt", "aaa", "bbb")
        expected = """\
### * build (recipe=build)
opts={'D': 999, 'debug': True, 'f': ' foo.txt', 'file': 'bar.txt', 'h': True, 'help': True}
rests=('aaa', 'bbb')
opts['D']=999
opts['debug']=True
opts['f']= foo.txt
opts['file']=bar.txt
opts['h']=True
opts['help']=True
"""
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## command option error
        func = lambda: self._start(content, "build", "-f")
        errmsg = "build(): -f: file required."
        ok(func, 'raises', CommandOptionError, errmsg)
        #
        func = lambda: self._start(content, "build", "-Dx")
        errmsg = "build(): -Dx: integer required."
        ok(func, 'raises', CommandOptionError, errmsg)
        #
        func = lambda: self._start(content, "build", "--debug=x")
        errmsg = "build(): --debug=x: integer required."
        ok(func, 'raises', CommandOptionError, errmsg)


    def test_content_compared1(self):
        content = r"""
@recipe
@product("hello")
@ingreds("hello.o")
def file_command(c):
    system(c%"gcc -o $(product) $(ingred)")

@recipe
@product("*.o")
@ingreds("$(1).c")
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")
"""
        ## 1st
        self._start(content, "hello")
        ok("hello", isfile)
        expected = (
            "### ** hello.o (recipe=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "### * hello (recipe=file_command)\n"
            "$ gcc -o hello hello.o\n"
        )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## 2nd (content compared)
        old_utime = os.path.getmtime("hello")
        time.sleep(1)
        os.utime("hello.c", None)
        _setup_stdio()
        self._start(content, "hello")
        ok(os.path.getmtime("hello"), '>', old_utime)
        ok("hello", isfile)
        expected = (
            "### ** hello.o (recipe=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "### * hello (recipe=file_command)\n"
            "$ touch hello   # skipped\n"             # content compared and skipped
        )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


    def test_remove_produt_when_recipe_failed1(self):
        content = r"""
@recipe
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
        expected = (
            "### * hello.h (recipe=file_hello_txt)\n"
            "$ gcc HOGE.c\n"
            "### * (remove hello.h because unexpected error raised (recipe=file_hello_txt))\n"
        )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ok("hello.h", isfile, False)         # product should be removed


    def test_complicated_cooking1(self):
        content = r"""
command = "hello"

@recipe
@ingreds(command)
def build(c):
    echo("build() invoked.")

@recipe
@product(command)
@ingreds("%s.o" % command)
def file_command(c):
    system(c%"gcc -o $(product) $(ingred)")

@recipe
@product("*.o")
@ingreds("$(1).c", if_exists("$(1).h"))
def file_ext_o(c):
    system(c%"gcc -c $(ingred)")
    system(c%"gcc -g -c $(1).c")

@recipe
@ingreds('build')
def task_all(c):
    echo("all() invoked.")
"""
        ## 1st
        self._start(content, "all")
        ok("hello", isfile)
        expected = (
            "### **** hello.o (recipe=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "$ gcc -g -c hello.c\n"
            "### *** hello (recipe=file_command)\n"
            "$ gcc -o hello hello.o\n"
            "### ** build (recipe=build)\n"
            "$ echo build() invoked.\n"
            "build() invoked.\n"
            "### * all (recipe=task_all)\n"
            "$ echo all() invoked.\n"
            "all() invoked.\n"
        )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## 2nd
        _setup_stdio()
        self._start(content, "all")
        expected = (
            "### ** build (recipe=build)\n"
            "$ echo build() invoked.\n"
            "build() invoked.\n"
            "### * all (recipe=task_all)\n"
            "$ echo all() invoked.\n"
            "all() invoked.\n"
        )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## 3rd, content compared, if_exists()
        time.sleep(1)
        write_file("hello.h", "#include <stdio.h>\n")
        _setup_stdio()
        self._start(content, "all")
        expected = (
            "### **** hello.o (recipe=file_ext_o)\n"
            "$ gcc -c hello.c\n"
            "$ gcc -g -c hello.c\n"
            "### *** hello (recipe=file_command)\n"
            "$ touch hello   # skipped\n"                   # skipped
            "### ** build (recipe=build)\n"
            "$ echo build() invoked.\n"
            "build() invoked.\n"
            "### * all (recipe=task_all)\n"
            "$ echo all() invoked.\n"
            "all() invoked.\n"
        )
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


    def test_complicated_cooking2(self):   # DAG

        for x in glob("hello*"):
            os.unlink(x)

        hello_h_txt = r'''
/*extern char *command;*/
#define COMMAND "hello"
void print_args(int argc, char *argv[]);
'''[1:]
        hello1_c = r'''
#include "hello.h"
/*char *command = "hello";*/
int main(int argc, char *argv[]) {
    print_args(argc, argv);
    return 0;
}
'''[1:]
        hello2_c = r'''
#include <stdio.h>
#include "hello.h"
void print_args(int argc, char *argv[]) {
    int i;
    printf("%s: argc=%d\n", COMMAND, argc);
    for (i = 0; i < argc; i++) {
        printf("%s: argv[%d]: %s\n", COMMAND, i, argv[i]);
    }
}
'''[1:]
        write_file("hello.h.txt", hello_h_txt)
        write_file("hello1.c", hello1_c)
        write_file("hello2.c", hello2_c)
        #
        kookbook_py = r'''
@recipe
@ingreds('hello')
def build(c):
  "build all files"
  pass

@recipe
@product('hello')
@ingreds('hello1.o', 'hello2.o')
def file_hello(c):
  system(c%'gcc -o $(product) $(ingreds)')

@recipe
@product('*.o')
@ingreds('$(1).c', 'hello.h')
def file_o(c):
  system(c%'gcc -c $(ingred)')

@recipe
@product('hello.h')
@ingreds('hello.h.txt')
def file_hello_h(c):
  system(c%'cp $(ingred) $(product)')
'''[1:]
        kitchen = self._kitchen(kookbook_py)
        #
        ## 1st
        ok('hello.h',  isfile, False)
        ok('hello1.o', isfile, False)
        ok('hello1.o', isfile, False)
        ok('hello',    isfile, False)
        kitchen.start_cooking('build')
        ok('hello.h',  isfile, True)
        ok('hello1.o', isfile, True)
        ok('hello1.o', isfile, True)
        ok('hello',    isfile, True)
        expected = r'''
### **** hello.h (recipe=file_hello_h)
$ cp hello.h.txt hello.h
### *** hello1.o (recipe=file_o)
$ gcc -c hello1.c
### *** hello2.o (recipe=file_o)
$ gcc -c hello2.c
### ** hello (recipe=file_hello)
$ gcc -o hello hello1.o hello2.o
### * build (recipe=build)
'''[1:]
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## 2nd (sleep 1 sec, all recipes should be skipped)
        ts_hello    = os.path.getmtime("hello")
        ts_hello1_o = os.path.getmtime("hello1.o")
        ts_hello2_o = os.path.getmtime("hello2.o")
        ts_hello_h  = os.path.getmtime("hello.h")
        time.sleep(1)
        kitchen.start_cooking('build')
        ok(os.path.getmtime('hello'),    '==', ts_hello)
        ok(os.path.getmtime('hello1.o'), '==', ts_hello1_o)
        ok(os.path.getmtime('hello2.o'), '==', ts_hello2_o)
        ok(os.path.getmtime('hello.h'),  '==', ts_hello_h)
        expected = r'''
### * build (recipe=build)
'''[1:]
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## 3rd (touch hello.h, hello should be skipped)
        now = time.time()
        os.utime('hello.h', (now, now))   # update intermediates
        kitchen.start_cooking('build')
        ok(os.path.getmtime('hello.h.txt'), '<', now)
        ok(os.path.getmtime('hello'),    '>', ts_hello)
        ok(os.path.getmtime('hello1.o'), '>', ts_hello1_o)
        ok(os.path.getmtime('hello2.o'), '>', ts_hello2_o)
        expected = r'''
### *** hello1.o (recipe=file_o)
$ gcc -c hello1.c
### *** hello2.o (recipe=file_o)
$ gcc -c hello2.c
### ** hello (recipe=file_hello)
$ touch hello   # skipped
### * build (recipe=build)
'''[1:]
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")
        ## 4th (edit hello.h.txt, hello should not be skipped)
        ts_hello    = os.path.getmtime("hello")
        ts_hello1_o = os.path.getmtime("hello1.o")
        ts_hello2_o = os.path.getmtime("hello2.o")
        time.sleep(1)
        write_file('hello.h.txt', hello_h_txt.replace('hello', 'HELLO'))
        try:
            config.debug_level = 2
            kitchen.start_cooking('build')
        finally:
            config.debug_level = 0
        ok(os.path.getmtime('hello'),    '>', ts_hello)
        ok(os.path.getmtime('hello1.o'), '>', ts_hello1_o)
        ok(os.path.getmtime('hello2.o'), '>', ts_hello2_o)
#        expected = r'''
#### **** hello.h (recipe=file_hello_h)
#$ cp hello.h.txt hello.h
#### *** hello1.o (recipe=file_o)
#$ gcc -c hello1.c
#### *** hello2.o (recipe=file_o)
#$ gcc -c hello2.c
#### ** hello (recipe=file_hello)
#$ gcc -o hello hello1.o hello2.o
#### * build (recipe=build)
#'''[1:]
        expected = r'''
*** debug: Cookbook#find_recipe(): target='build', func=build, product='build'
*** debug: Cookbook#find_recipe(): target='hello', func=file_hello, product='hello'
*** debug: Cookbook#find_recipe(): target='hello1.o', func=file_o, product='*.o'
*** debug: Cookbook#find_recipe(): target='hello.h', func=file_hello_h, product='hello.h'
*** debug: Cookbook#find_recipe(): target='hello2.o', func=file_o, product='*.o'
*** debug: start_cooking(): root.product='build', root.ingreds=('hello',)
*** debug: + begin build
*** debug: ++ begin hello
*** debug: +++ begin hello1.o
*** debug: ++++ material hello1.c
*** debug: ++++ begin hello.h
*** debug: +++++ material hello.h.txt
*** debug: ++++ child file 'hello.h.txt' is newer than product 'hello.h'.
*** debug: ++++ cannot skip: there is newer file in children than product 'hello.h'.
*** debug: ++++ create hello.h (recipe=file_hello_h)
### **** hello.h (recipe=file_hello_h)
$ cp hello.h.txt hello.h
*** debug: ++++ end hello.h (content changed)
*** debug: +++ cannot skip: there is newer file in children than product 'hello1.o'.
*** debug: +++ create hello1.o (recipe=file_o)
### *** hello1.o (recipe=file_o)
$ gcc -c hello1.c
*** debug: +++ end hello1.o (content not changed, mtime updated)
*** debug: +++ begin hello2.o
*** debug: ++++ material hello2.c
*** debug: ++++ begin hello.h
*** debug: +++++ material hello.h.txt
*** debug: ++++ skip hello.h (recipe=file_hello_h)
*** debug: +++ child file 'hello.h' is newer than product 'hello2.o'.
*** debug: +++ cannot skip: there is newer file in children than product 'hello2.o'.
*** debug: +++ create hello2.o (recipe=file_o)
### *** hello2.o (recipe=file_o)
$ gcc -c hello2.c
*** debug: +++ end hello2.o (content changed)
*** debug: ++ cannot skip: there is newer file in children than product 'hello'.
*** debug: ++ create hello (recipe=file_hello)
### ** hello (recipe=file_hello)
$ gcc -o hello hello1.o hello2.o
*** debug: ++ end hello (content changed)
*** debug: + cannot skip: task recipe should be invoked in any case.
*** debug: + perform build (recipe=build)
### * build (recipe=build)
*** debug: + end build (content changed)
'''[1:]
        ok(_stdout(), '==', expected)
        ok(_stderr(), '==', "")


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
