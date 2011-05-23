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
kookbook.load_book('@kook/books/clean.py')
r = kookbook['clean']
assert r
assert r.__class__.__name__ == 'Recipe'
assert 'kook_clean_files' in globals()
assert kook_clean_files == []
kookbook['clean'].add('*.hogeratta', '*.geriatta')
assert kook_clean_files == ['*.hogeratta', '*.geriatta']
"""[1:]
            def fn1():
                book = Cookbook.new(fname)
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
kookbook.load_book('@kook/books/clean.py')
r = kookbook['sweep']
assert r
assert r.__class__.__name__ == 'Recipe'
assert 'kook_sweep_files' in globals()
assert kook_sweep_files == []
kookbook['sweep'].add('*.hogeratta2', '*.geriatta2')
assert kook_sweep_files == ['*.hogeratta2', '*.geriatta2']
kookbook['clean'].add('*.hogeratta')
"""[1:]
            def fn():
                book = Cookbook.new(fname)
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
kookbook.load_book('@kook/books/clean.py')
kook_clean_files.append('*.foo')
kookbook.load_book('@kook/books/clean.py')
kook_clean_files.append('*.bar')
expected = ['*.foo', '*.bar']
assert kook_clean_files == expected, "%r != %r" % (kook_clean_files, expected)
"""[1:]
            def fn():
                book = Cookbook.new(None)
                book.load(input)
            ok (fn).not_raise()


if __name__ == '__main__':
    run()
