# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
from oktest.dummy import dummy_file, dummy_io
import sys, os, re
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from kook import KookRecipeError
from kook.cookbook import Cookbook, Recipe
from kook.kitchen import Kitchen
from kook.utils import write_file
from kook import config



class dummy_sio(object):

    def __init__(self, content=None):
        self.stdin_content = content

    def __enter__(self):
        self.stdout, config.stdout = config.stdout, StringIO()
        self.stderr, config.stderr = config.stderr, StringIO()
        self.stdin,  sys.stdin     = sys.stdin,     StringIO(self.stdin_content or "")
        return self

    def __exit__(self, *args):
        #sout, serr = config.stdout.getvalue(), config.stderr.getvalue()
        config.stdout, self.stdout = self.stdout, config.stdout.getvalue()
        config.stderr, self.stderr = self.stderr, config.stderr.getvalue()
        sys.stdin,     self.stdin  = self.stdin,  self.stdin_content

    def run(self, func, *args, **kwargs):
        try:
            self.__enter__()
            func(*args, **kwargs)
            return self
        finally:
            self.__exit__(*sys.exc_info())

    def __call__(self, func):
        return self.run(func)



class KookTasksTest(object):


    def test_tasks_clean(self):

        if "loaded then defines 'clean' task.":
            fname = "__Kookbook1.py"
            fcont = r"""
kookbook.load('@kook/books/clean.py')
r = kookbook['clean']
assert r
assert r.__class__.__name__ == 'Recipe'
assert 'CLEAN' in globals()
assert CLEAN == []
#kookbook['clean'].add('*.hogeratta', '*.geriatta')
#assert CLEAN == ['*.hogeratta', '*.geriatta']
CLEAN.extend(['*.hogeratta', '*.geriatta'])
"""[1:]
            def fn1():
                book = Cookbook().load_file(fname)
                ok (book.find_recipe('clean')).is_a(Recipe)
                kitchen = Kitchen(book)
                kitchen.start_cooking('clean')
            def fn2():
                dummy_file(fname, fcont).run(fn1)
            d_io = dummy_sio("").run(fn2)
            ok (d_io.stdout) == ("### * clean (recipe=clean)\n"
                                 "$ rm -rf *.hogeratta *.geriatta\n")
            ok (d_io.stderr) == ""

        if "loaded then defines 'sweep' task.":
            fname = "__Kookbook2.py"
            fcont = r"""
kookbook.load('@kook/books/clean.py')
r = kookbook['sweep']
assert r
assert r.__class__.__name__ == 'Recipe'
assert 'SWEEP' in globals()
assert SWEEP == []
#kookbook['sweep'].add('*.hogeratta2', '*.geriatta2')
#assert SWEEP == ['*.hogeratta2', '*.geriatta2']
#kookbook['clean'].add('*.hogeratta')
SWEEP.extend(['*.hogeratta2', '*.geriatta2'])
CLEAN.append('*.hogeratta')
"""[1:]
            def fn():
                book = Cookbook().load_file(fname)
                ok (book.find_recipe('sweep')).is_a(Recipe)
                kitchen = Kitchen(book)
                kitchen.start_cooking('sweep')
            def fn2():
                dummy_file(fname, fcont).run(fn)
            d_io = dummy_sio("").run(fn2)
            ok (d_io.stdout) == ("### * sweep (recipe=sweep)\n"
                                 "$ rm -rf *.hogeratta\n"
                                 "$ rm -rf *.hogeratta2 *.geriatta2\n")
            ok (d_io.stderr) == ""

        if "called several times then loaded only one time.":
            input = r"""
kookbook.load('@kook/books/clean.py')
CLEAN.append('*.foo')
kookbook.load('@kook/books/clean.py')
CLEAN.append('*.bar')
expected = ['*.foo', '*.bar']
assert CLEAN == expected, "%r != %r" % (CLEAN, expected)
"""[1:]
            def fn():
                book = Cookbook()
                book.load(input)
            ok (fn).not_raise()


    def test_tasks_all(self):

        if "loaded then defines 'all' task.":
            fname = "__Kookbook1.py"
            fcont = r"""
kookbook.load('@kook/books/all.py')
r = kookbook['all']
assert r
assert r.__class__.__name__ == 'Recipe'
assert 'ALL' in globals()
assert ALL == []

kookbook['all'].add('hello', 'haruhi.sos')
expected = ['hello', 'haruhi.sos']
assert ALL == expected, "%r != %r" % (ALL, expected)

@recipe
def hello(c):
    from kook import config
    config.stdout.write("Hello!\n")

@recipe('*.sos')
def file_html(c):
    f = open(c.product, 'w')
    f.write("SOS")
    f.close()
"""[1:]
            try:
                def fn1():
                    def fn2():
                        book = Cookbook().load_file(fname)
                        r = book.find_recipe('all')
                        ok (r).is_a(Recipe)
                        ok (r.ingreds) == ['hello', 'haruhi.sos']
                        kitchen = Kitchen(book)
                        kitchen.start_cooking('all')
                    dummy_file(fname, fcont).run(fn2)
                d_io = dummy_sio("").run(fn1)
                ok (d_io.stdout) == r"""
### ** hello (recipe=hello)
Hello!
### ** haruhi.sos (recipe=file_html)
### * all (recipe=task_all)
"""[1:]
                ok (d_io.stderr) == ""
            finally:
                fname = 'haruhi.sos'
                if os.path.exists(fname): os.unlink(fname)



if __name__ == '__main__':
    run()
