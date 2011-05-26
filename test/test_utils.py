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
from kook.utils import CommandOptionParser, CommandOptionError, ArgumentError


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


    def test_meta2rexp(self):
        from kook.utils import meta2rexp
        ok (meta2rexp('foo.html')) == r'^foo\.html$'
        ok (meta2rexp('*.html')) == r'^(.*?)\.html$'
        ok (meta2rexp('*_???.{gif,jpg,png}')) == r'^(.*?)\_(...)\.(gif|jpg|png)$'
        ok (meta2rexp(r'index[abc][0-9].html')) == r'^index[abc][0-9]\.html$'


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
            ok (glob2("hello.d/**/*.h")) == expected
            #
            expected = [
                "hello.h",
                "hello.d/src/include/hello.h",
                "hello.d/src/include/hello2.h",
            ]
            ok (glob2("**/*.h")) == expected
            #
            expected = [
                "hello.d/src",
                "hello.d/src/include",
                "hello.d/src/lib",
                "hello.d/src/include/hello.h",
                "hello.d/src/include/hello2.h",
                "hello.d/src/lib/hello.c",
            ]
            ok (glob2("hello.d/**/*")) == expected
            #
        finally:
            for f in glob('hello*'):
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.unlink(f)


    def test_is_func_or_method(self):
        from kook.utils import is_func_or_method
        if "function is passed then returns True":
            def f1(c):
                pass
            ok (is_func_or_method(f1)).is_(True)
        if "method is passed then returns True":
            class Foo(object):
                def f2(c):
                    pass
            ok (is_func_or_method(Foo.f2)).is_(True)
        if "other data is passed then returns False":
            ok (is_func_or_method(None)).is_(False)
            ok (is_func_or_method('str')).is_(False)
            class Bar(object):
                pass
            ok (is_func_or_method(Bar)).is_(False)


class CommandOptionParserTest(object):

    def test_parse_spices1(self):
        spices = ('-h: help', '-p port: port', '-i[N]: indent',
                  '--version: version', '--user[=root]: username', '--pass=password: password phrase')
        parser = CommandOptionParser()
        ret = parser.parse_spices(spices)
        ok (type(ret)) == tuple
        ok (len(ret)) == 3
        ok (ret[0]) == {'i': 1, 'h': False, 'p': 'port', 'version': False, 'user': True, 'pass': 'password'}
        ok (ret[1]) == None
        ok (ret[2]) == [('-h', 'help'), ('-p port', 'port'), ('-i[N]', 'indent'), ('--version', 'version'), ('--user[=root]', 'username'), ('--pass=password', 'password phrase')]
        ok (ret[0]).is_(parser.spices)
        ok (ret[1]).is_(parser.arg_desc)
        ok (ret[2]).is_(parser.helps)

    def test_parse_spices2(self):
        spices = ('-p port: port', 'url')
        parser = CommandOptionParser()
        ret = parser.parse_spices(spices)
        ok (parser.spices) == {'p': 'port'}
        ok (parser.arg_desc) == 'url'
        ##
        spices = ('-p port: port', 'url', '-h: help')
        parser = CommandOptionParser()
        def f():
            parser.parse_spices(spices)
        ok (f).raises(ArgumentError, "'url': invalid command option definition.")


if __name__ == '__main__':
    oktest.run('.*Test$')
