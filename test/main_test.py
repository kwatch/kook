###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import oktest
from oktest import *
import sys, os, re, shutil, random
from glob import glob
try:
    from StringIO import StringIO      # 2.x
except ImportError:
    from io import StringIO            # 3.x

from kook.main import MainCommand, MainApplication
import kook.config as config
from kook.utils import write_file

import _testhelper
from _testhelper import _setup_stdio, _teardown_stdio

def _stdout():
    return config.stdout.getvalue()

def _stderr():
    return config.stderr.getvalue()

def _main_command(argv):
    return _main(MainCommand, argv)

def _main_app(argv):
    return _main(MainApplication, argv)

def _main(klass, argv):
    if isinstance(argv, str):
        argv = argv.split(' ')
    _setup_stdio()
    try:
        status  = klass(argv).main()
        soutput = config.stdout.getvalue()
        eoutput = config.stderr.getvalue()
    finally:
        _teardown_stdio()
    return soutput, eoutput, status

def _write(content, bookname='Kookbook.py'):
    write_file(bookname, content)

def _del_tips(s):
    return re.sub(r'\n\(Tips:.*)\n', "\n", s)


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


class KookMainCommandTest(object):

    def before(self):
        self._currdir = os.getcwd()
        self._tmpdir  = str(random.random())
        os.mkdir(self._tmpdir)
        os.chdir(self._tmpdir)
        #_setup_stdio()
        write_file('hello.c', HELLO_C)
        write_file('hello.h', HELLO_H)

    def after(self):
        #_teardown_stdio()
        os.chdir(self._currdir)
        shutil.rmtree(self._tmpdir)


    def test_init(self):
        argv = ['/usr/local/bin/pykook', '-h', '-f', 'foo.py']
        obj = MainCommand(argv)
        ok (obj.command) == 'pykook'
        ok (obj.args) == ['-h', '-f', 'foo.py']

    def test_nokookbook(self):  # 'Kookbook.py' not found
        soutput, eoutput, status = _main_command("pykook")
        ok (soutput) == ""
        ok (eoutput) == "pykook: Kookbook.py: not found.\n"
        ok (status) == 1

    def test_noargs(self):  # 'Kookbook.py' not found
        input = r"""
"""[1:]
        _write(input)
        expected = r"""
*** pykook: target is not given
*** 'pykook -l' or 'pykook -L' shows recipes and properties.
*** (or set 'kookbook.default="XXX"' in your kookbook.)
"""[1:]
        soutput, eoutput, status = _main_command("pykook")
        ok (soutput) == ""
        ok (eoutput) == expected
        ok (status) == 1

    def test_help(self): # -h
        expected = r"""
pykook - build tool like Make, Rake, Ant, or Cook
  -h                  : help
  -V                  : version
  -D[N]               : debug level (default: 1)
  -q                  : quiet
  -f file             : kookbook
  -F                  : run forcedly (ignore timestamps)
  -n                  : not execute (dry run)
  -l                  : list public recipes
  -L                  : list all recipes
  -R                  : search parent directory recursively for Kookbook
  --name=value        : property name and value
  --name              : property name and value(=True)
"""[1:]
        ## -h
        soutput, eoutput, status = _main_command("pykook -h")
        ok (soutput) == expected
        ok (eoutput) == ""
        ok (status) == 0
        ## --help
        soutput, eoutput, status = _main_command("pykook --help")
        ok (soutput) == expected
        ok (eoutput) == ""
        ok (status) == 0

    def test_version(self): # -V
        soutput, eoutput, status = _main_command("pykook -V")
        ok (soutput).matches(r'^\d+\.\d+\.\d+$')
        ok (eoutput) == ""
        ok (status) == 0

    def test_debug(self): # -D[N]
        input = r"""
@recipe
@ingreds('echo')
def all(c):
  pass

@recipe
def task_echo(c):
  echo('YES')
"""[1:]
        _write(input)
        ## without -D
        expected = r"""
### * echo (recipe=task_echo)
$ echo YES
YES
"""[1:]
        soutput, eoutput, status = _main_command("pykook echo")
        ok (soutput) == expected
        ok (eoutput) == ""
        ## with -D
        expected = r"""
*** debug: + begin echo
*** debug: + perform echo (recipe=task_echo)
### * echo (recipe=task_echo)
$ echo YES
YES
*** debug: + end echo (content changed)
"""[1:]
        try:
            ok (config.debug_level) == 0
            soutput, eoutput, status = _main_command("pykook -D echo")
            ok (config.debug_level) == 1
            ok (soutput) == expected
            ok (eoutput) == ""
        finally:
            config.debug_level = 0
        ## with -D
        expected = r"""
*** debug: specific task recipes: [<Recipe:'all':all>, <Recipe:'echo':task_echo>]
*** debug: generic  task recipes: []
*** debug: specific file recipes: []
*** debug: generic  file recipes: []
*** debug: Cookbook#find_recipe(): target='echo', func=task_echo, product='echo'
*** debug: start_cooking(): root.product='echo', root.ingreds=()
*** debug: + begin echo
*** debug: + cannot skip: task recipe should be invoked in any case.
*** debug: + perform echo (recipe=task_echo)
### * echo (recipe=task_echo)
$ echo YES
YES
*** debug: + end echo (content changed)
"""[1:]
        try:
            ok (config.debug_level) == 0
            soutput, eoutput, status = _main_command("pykook -D2 echo")
            ok (config.debug_level) == 2
            ok (soutput) == expected
            ok (eoutput) == ""
        finally:
            config.debug_level = 0

    def test_quiet(self): # -q
        input = r"""
@recipe
@ingreds('echo')
def all(c):
  pass

@recipe
def task_echo(c):
  echo('YES')
"""[1:]
        _write(input)
        ## without '-q'
        soutput, eoutput, status = _main_command("pykook echo")
        expected = r"""
### * echo (recipe=task_echo)
$ echo YES
YES
"""[1:]
        ok (soutput) == expected
        ok (eoutput) == ""
        ## with '-q'
        expected = r"""
YES
"""[1:]
        try:
            ok (config.quiet) == False
            soutput, eoutput, status = _main_command("pykook -q echo")
            ok (config.quiet) == True
            ok (soutput) == expected
            ok (eoutput) == ""
        finally:
            config.quiet = False

    def test_file(self): # -f file
        input = r"""
@recipe
def task_print(c):
  echo('No')
"""[1:]
        _write(input)
        input = r"""
@recipe
def task_print(c):
  echo('Yes')
"""[1:]
        _write(input, 'Kookbook2.py')
        ## without -f
        expected = r"""
### * print (recipe=task_print)
$ echo No
No
"""[1:]
        soutput, eoutput, status = _main_command("pykook print")
        ok (soutput) == expected
        ok (eoutput) == ""
        ## with -f
        expected = r"""
### * print (recipe=task_print)
$ echo Yes
Yes
"""[1:]
        soutput, eoutput, status = _main_command("pykook -f Kookbook2.py print")
        ok (soutput) == expected
        ok (eoutput) == ""
        ## if not found
        soutput, eoutput, status = _main_command("pykook -f Kookbook3.py print")
        ok (soutput) == ""
        ok (eoutput) == "pykook: -f Kookbook3.py: not found.\n"

    def test_forced(self): # -F
        input = r"""
@recipe
@product('*.html')
@ingreds('$(1).txt')
def file_html(c):
  cp(c.ingred, c.product)
"""[1:]
        _write(input)
        write_file("index.html", "xxx")
        write_file("index.txt", "foobar")
        ## recipe should not be invoked because product is newer
        soutput, eoutput, status = _main_command("pykook index.html")
        ok (soutput) == ""
        ok (eoutput) == ""
        ## recipe should be invoked when -F specified
        expected = r"""
### * index.html (recipe=file_html)
$ cp index.txt index.html
"""[1:]
        try:
            ok (config.forced) == False
            soutput, eoutput, status = _main_command("pykook -F index.html")
            ok (config.forced) == True
            ok (soutput) == expected
            ok (eoutput) == ""
        finally:
            config.forced = False

    def test_noexec(self): # -n
        input = r"""
@recipe
@product('*.xhtml')
@ingreds('$(1).html')
def file_xhtml(c):
  cp(c.ingred, c.product)

@recipe
@product('*.html')
@ingreds('$(1).txt')
def file_html(c):
  cp(c.ingred, c.product)
"""[1:]
        _write(input)
        write_file("index.txt", "xxx")
        ## products should not be created!
        try:
            soutput, eoutput, status = _main_command("pykook -n index.xhtml")
            ok (config.noexec) == True
        finally:
            config.noexec = False
        not_ok ('indent.html').is_file()
        not_ok ('indent.xhtml').is_file()
        expected = r"""
### ** index.html (recipe=file_html)
$ cp index.txt index.html
### * index.xhtml (recipe=file_xhtml)
$ cp index.html index.xhtml
"""[1:]
        ok (soutput) == expected
        ok (eoutput) == ""

    def test_list(self): # -l, -L
        input = r"""
CC = prop('CC', 'gcc')
kookbook.default = 'all'

@recipe
@ingreds('hello')
def task_all(c):           # well-known recipe
  pass

@recipe
@spices('-h: help', '-f file: filename', '-x:', '-y: ', '-z', '[files...]')
def install(c, *args, **kwargs):        # with spices
  pass

@recipe
@product('hello')
def file_hello(c):         # public recipe
  '''build hello command'''
  system(c%'$(CC) -o $(produt) *.o')

@recipe
@product('*.o')
@ingreds('*.c', '*.h')
def file_o(c):             # private recipe
  system(c%'($CC) -c $(1).c')
"""[1:]
        _write(input)
        expected = r"""
Properties:
  CC                  : 'gcc'

Task recipes:
  all                 : cook all products
  install [files...]  : install product
    -h                    help
    -f file               filename

File recipes:
  hello               : build hello command
  *.o                 : 

kookbook.default: all

(Tips: you can override properties with '--propname=propvalue'.)
"""[1:]
        expected = re.sub(r'\n\(Tips:.*\n', '\n', expected)
        ## -l
        soutput, eoutput, status = _main_command("pykook -l")
        soutput  = re.sub(r'\n\(Tips:.*\n', '\n', soutput)
        ok (soutput) == re.sub(r'\n  \*\.o.*\n', '\n', expected)
        ok (eoutput) == ""
        ## -L
        soutput, eoutput, status = _main_command("pykook -L")
        soutput  = re.sub(r'\n\(Tips:.*\n', '\n', soutput)
        expected = re.sub(r'\n\(Tips:.*\n', '\n', expected)
        ok (soutput) == expected
        ok (eoutput) == ""

    def test_properties(self): # --name=value
        input = r"""
VERBOSE = prop('verbose', False)
CC = prop('CC', 'gcc')
@recipe
def task_echo(c):
  echo(c%'CC=$(CC), VERBOSE=$(VERBOSE)')
"""[1:]
        _write(input)
        expected = r"""
### * echo (recipe=task_echo)
$ echo CC=tcc, VERBOSE=True
CC=tcc, VERBOSE=True
"""[1:]
        ## '--CC=tcc' overrides property value, '--verbose' is regards as '--verbose=True'
        soutput, eoutput, status = _main_command("pykook --CC=tcc --verbose echo")
        ok (soutput) == expected
        ok (eoutput) == ""

    def test_property_file(self):  # Properties.py
        input = r"""
VERBOSE = prop('VERBOSE', True)
CC = prop('CC', 'gcc')
@recipe
def task_echo(c):
  echo(c%'CC=$(CC)')
  echo(c%'VERBOSE=$(VERBOSE)')
"""[1:]
        _write(input)
        input = r"""
VERBOSE = False
CC = 'tcc'
"""[1:]
        filename = "Properties.py"
        write_file(filename, input)
        ## Properties.py overrides property value
        expected = r"""
### * echo (recipe=task_echo)
$ echo CC=tcc
CC=tcc
$ echo VERBOSE=False
VERBOSE=False
"""[1:]
        soutput, eoutput, status = _main_command("pykook echo")
        ok (soutput) == expected
        ok (eoutput) == ""
        ## Properties.py is reflected to output of '-l' or '-L'
        expected = r"""
Properties:
  VERBOSE             : False
  CC                  : 'tcc'

Task recipes:
  echo                : 

File recipes:

(Tips: you can set 'kookbook.default="XXX"' variable in your kookbook.)
"""[1:]
        soutput, eoutput, status = _main_command("pykook -L")
        soutput  = re.sub(r'\n\(Tips:.*\n', '\n', soutput)
        expected = re.sub(r'\n\(Tips:.*\n', '\n', expected)
        ok (soutput) == expected
        ok (eoutput) == ""
        ## command-line option is prior than Properties.py
        expected = r"""
### * echo (recipe=task_echo)
$ echo CC=g++
CC=g++
$ echo VERBOSE=32
VERBOSE=32
"""[1:]
        soutput, eoutput, status = _main_command("pykook --CC=g++ --VERBOSE=32 echo")
        ok (soutput) == expected
        ok (eoutput) == ""

    def test_spices(self):  # @spices
        input = r"""
@recipe
@spices('-h: help', '-v: verbose', '-f file: file name', '-i[N]: indent')
def task_cmd(c, *args, **kwargs):
  echo('args=%s' % repr(args))
  echo('kwargs=%s' % repr(kwargs))
"""[1:]
        _write(input)
        ## specify options
        soutput, eoutput, status = _main_command("pykook cmd -vhf file.txt -i2 foo bar")
        expected = r"""
### * cmd (recipe=task_cmd)
$ echo args=('foo', 'bar')
args=('foo', 'bar')
$ echo kwargs={'i': 2, 'h': True, 'v': True, 'f': 'file.txt'}
kwargs={'i': 2, 'h': True, 'v': True, 'f': 'file.txt'}
"""[1:]
        ok (soutput) == expected
        ok (eoutput) == ""
        ## -L shows spices (command options)
        expected = r"""
Properties:

Task recipes:
  cmd                 : 
    -h                    help
    -v                    verbose
    -f file               file name
    -i[N]                 indent

File recipes:

(Tips: '@ingreds("$(1).c", if_exists("$(1).h"))' is a friend of C programmer.)
"""[1:]
        soutput, eoutput, status = _main_command("pykook -L")
        soutput  = re.sub(r'\n\(Tips:.*\n', '\n', soutput)
        expected = re.sub(r'\n\(Tips:.*\n', '\n', expected)
        ok (soutput) == expected
        ok (eoutput) == ""

    def ktest_search_recursively(self):
        curr_dir = os.getcwd()
        tmp_root = str(random.random())
        tmp_dir  = os.path.join(tmp_root, "foo", "bar")
        book_content = r"""
@recipe
def cwd(c):
    import os
    echo("cwd=" + os.getcwd())
"""
        try:
            os.makedirs(tmp_dir)
            bookpath = os.path.join(tmp_root, "Kookbook.py")
            write_file(bookpath, book_content)
            os.chdir(tmp_dir)
            #
            soutput, eoutput, status = _main_command("pykook cwd")
            ok (soutput) == ""
            ok (eoutput) == "pykook: Kookbook.py: not found.\n"
            #
            expected = r'''
### * cwd (recipe=cwd)
$ echo cwd=/Users/kwatch/src/kook2/python/%s
cwd=/Users/kwatch/src/kook2/python/%s
'''[1:] % (tmp_root, tmp_root)
            soutput, eoutput, status = _main_command("pykook -R cwd")
            ok (soutput) == expected
            ok (eoutput) == ""
            #
        finally:
            os.chdir(curr_dir)
            shutil.rmtree(tmp_root)


SCRIPT = r"""
kook_desc = "helper script"
CC = prop('CC', 'gcc')
CFLAGS = prop('CFLAGS', '-g -Wall')

@recipe
@spices("-d dir: install dir", "--prefix=path: install path")
def setup(c, *args, **kwargs):
    "setup configuration"
    echo("setup(): args=%s, kwargs=%s" % (args, kwargs))

@recipe
@spices("--cflags=opts: compiler options")
def build(c, *args, **kwargs):
    "compile files"
    echo("build(): args=%s, kwargs=%s" % (args, kwargs))

@recipe
def install(c, *args):
    "install files"
    echo("build(): args=%s" % args)

@recipe
def debug(c):
    echo("CC=%s, CFLAGS=%s" % (CC, CFLAGS))

#@recipe
#def model(c, *args, **kwargs):
#    if not args:
#        from kook.utils import CommandOptionError
#        raise CommandOptionError("model: model name is required.")
#    for arg in args:
#        echo("creating %s class ... done." % arg)
"""[1:]

APPNAME = 'hello'


class KookMainApplicationTest(object):

    @classmethod
    def before_all(self):
        write_file(APPNAME, SCRIPT)
        from stat import S_IXUSR, S_IRUSR, S_IWUSR
        os.chmod(APPNAME, S_IXUSR | S_IRUSR | S_IWUSR)

    @classmethod
    def after_all(self):
        if os.path.isfile(APPNAME): os.unlink(APPNAME)

    def before(self):
        #_setup_stdio()
        pass

    def after(self):
        #_teardown_stdio()
        if hasattr(self, 'byprods'):
            for x in self.byprods:
                os.unlink(x)


    def test_init(self):
        argv = ["pykook", "-X", APPNAME, "-h"]
        app = MainApplication(argv)
        ok (app.command) == None
        ok (app.args) == argv[1:]

    def test_help_all(self): # -h
        expected = r"""
hello - helper script

sub-commands:
  setup           : setup configuration
  build           : compile files
  install         : install files

(Type 'hello -h subcommand' to show options of sub-commands.)
"""[1:]
        soutput, eoutput, status = _main_app("pykook -X %s -h" % APPNAME)
        ok (soutput) == expected
        ok (eoutput) == ""

    def test_help_subcommand(self): # -h command
        #
        expected = r"""
hello setup - setup configuration
  -d dir               : install dir
  --prefix=path        : install path
"""[1:]
        soutput, eoutput, status = _main_app("pykook -X %s -h setup" % APPNAME)
        ok (soutput) == expected
        ok (eoutput) == ""
        #
        expected = r"""
hello build - compile files
  --cflags=opts        : compiler options
"""[1:]
        soutput, eoutput, status = _main_app("pykook -X %s -h build" % APPNAME)
        ok (soutput) == expected
        ok (eoutput) == ""
        #
        expected = r"""
hello install - install files
"""[1:]
        soutput, eoutput, status = _main_app("pykook -X %s -h install" % APPNAME)
        ok (soutput) == expected
        ok (eoutput) == ""

    def test_no_subommand(self): #
        expected = "%s: sub-command is required (try '-h' to show all sub-commands).\n" % APPNAME
        soutput, eoutput, status = _main_app("pykook -X %s" % APPNAME)
        ok (soutput) == ""
        ok (eoutput) == expected

    def test_subcommand(self):
        command = "pykook -X %s setup" % APPNAME
        expected = "setup(): args=(), kwargs={}\n"
        soutput, eoutput, status = _main_app(command)
        ok (soutput) == expected
        ok (eoutput) == ""
        #
        command = "pykook -X %s setup aaa bbb" % APPNAME
        expected = "setup(): args=('aaa', 'bbb'), kwargs={}\n"
        soutput, eoutput, status = _main_app(command)
        ok (soutput) == expected
        ok (eoutput) == ""
        #
        command = "pykook -X %s setup -d/tmp --prefix=/usr/local aaa bbb" % APPNAME
        expected = "setup(): args=('aaa', 'bbb'), kwargs={'prefix': '/usr/local', 'd': '/tmp'}\n"
        soutput, eoutput, status = _main_app(command)
        ok (soutput) == expected
        ok (eoutput) == ""

    def test_unknown_subcommand_option(self):
        command = "pykook -X %s setup -j" % APPNAME
        expected = "%s: setup(): -j: unknown command option.\n" % APPNAME
        soutput, eoutput, status = _main_app(command)
        ok (soutput) == ""
        ok (eoutput) == expected

    def test_unknown_global_option(self):
        command = "pykook -j %s setup" % APPNAME
        expected = "-j: unknown command option.\n"
        soutput, eoutput, status = _main_app(command)
        ok (soutput) == ""
        ok (eoutput) == expected



if __name__ == '__main__':
    oktest.main()
