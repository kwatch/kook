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


    def _before(self):
        self._cwd = os.getcwd()
        os.mkdir('_test_tmp.d')
        os.chdir('_test_tmp.d')

    def _after(self):
        os.chdir(self._cwd)
        import shutil
        shutil.rmtree('_test_tmp.d')


    def test_meta2rexp(self):
        from kook.utils import meta2rexp
        ok (meta2rexp('foo.html')) == r'^foo\.html$'
        ok (meta2rexp('*.html')) == r'^(.*?)\.html$'
        ok (meta2rexp('*_???.{gif,jpg,png}')) == r'^(.*?)\_(...)\.(gif|jpg|png)$'
        ok (meta2rexp(r'index[abc][0-9].html')) == r'^index[abc][0-9]\.html$'


    def test_glob2(self):
        try:
            self._before()
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
            self._after()


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


    def test_resolve_filepath(self):
        from kook.utils import resolve_filepath
        from os.path import dirname, abspath
        if "filepath starts with './' then expands current directory.":
            expected = dirname(abspath(__file__)) + '/foo.py'
            ok (resolve_filepath('./foo.py')) == expected
        if "filepath starts with '../' then expands parent directory.":
            expected = dirname(dirname(abspath(__file__))) + '/foo.py'
            ok (resolve_filepath('../foo.py')) == expected
        if "filepath starts with '../../' then expands parent's parent directory":
            expected = dirname(dirname(dirname(abspath(__file__)))) + '/foo.py'
            ok (resolve_filepath('../../foo.py')) == expected
        if "filepath starts with '.../' then finds file in parent directory recursively":
            dct = {}
            try:
                os.mkdir('_test_tmp.d');
                os.mkdir('_test_tmp.d/d1');
                os.mkdir('_test_tmp.d/d1/d2');
                code = """
from kook.utils import resolve_filepath
foo_path = resolve_filepath('.../foo.py')
bar_path = resolve_filepath('.../bar.py')
"""
                #write_file('_test_tmp.d/d1/d2/example.py', code);
                write_file('_test_tmp.d/foo.py', '')
                #
                codeobj = compile(code, '_test_tmp.d/d1/d2/example.py', 'exec')
                exec(codeobj, dct, dct);
                #
            finally:
                import shutil
                shutil.rmtree('_test_tmp.d')
            ok (dct['foo_path']) == os.getcwd() + '/_test_tmp.d/foo.py'
            ok (dct['bar_path']) == '.../bar.py'
        if "filepath starts with '~/' then expands to home directory.":
            ok (resolve_filepath('~/foo')) == os.environ.get('HOME') + '/foo'
        if "filepath starts with '~user/' then expands to home directory of user.":
            ok (resolve_filepath('~root/foo')).in_(['/foo', '/root/foo', '/var/root/foo'])
        if "else then returns filepath as it is.":
            ok (resolve_filepath('foo.py')) == 'foo.py'



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
        #
        if "help message is not specified then parsed collectly without error.":
            spices = ('-h: help', '-x:', '-y: ', '-z')
            parser = CommandOptionParser()
            ret = parser.parse_spices(spices)
            ok (ret).is_a(tuple).length(3)
            ok (ret[0]) == {'h': False, 'x': False, 'y': False, 'z': False}
            ok (ret[1]) == None
            ok (ret[2]) == [('-h', 'help'), ('-x', ''), ('-y', ''), ('-z', None)]
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
