###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re, time

from kook.decorators import *


class KookDecoratorsTest(object):

    def test_decorator(self):
        @recipe
        def f(c):
            pass
        ok(hasattr(f, '_kook_recipe'), '==', True)
        ok(f._kook_recipe, '==', True)

    def test_product(self):
        @product('hello')
        def f(c):
            pass
        ok(hasattr(f, '_kook_product'), '==', True)
        ok(f._kook_product, '==', 'hello')
        #ok(hasattr(f, '_kook_recipe'), '==', True)
        #ok(f._kook_recipe, '==', True)

    def test_ingreds(self):
        @ingreds('foo', 'bar', 'baz')
        def f(c):
            pass
        ok(hasattr(f, '_kook_ingreds'), '==', True)
        ok(f._kook_ingreds, '==', ('foo', 'bar', 'baz'))

    def test_byrpods(self):
        @byprods('foo', 'bar', 'baz')
        def f(c):
            pass
        ok(hasattr(f, '_kook_byprods'), '==', True)
        ok(f._kook_byprods, '==', ('foo', 'bar', 'baz'))

    def test_coprods(self):
        @coprods('foo', 'bar', 'baz')
        def f(c):
            pass
        ok(hasattr(f, '_kook_coprods'), '==', True)
        ok(f._kook_coprods, '==', ('foo', 'bar', 'baz'))

    def test_priority(self):
        @priority(123)
        def f(c):
            pass
        ok(hasattr(f, '_kook_priority'), '==', True)
        ok(f._kook_priority, '==', 123)
        def func():
            @priority('123')
            def f(c):
                pass
        import kook
        ok(func, 'raises', kook.KookRecipeError, "priority requires integer.")

    def test_spcies(self):
        @spices('-h: help', '-v: verbose')
        def f(c):
            pass
        ok(hasattr(f, '_kook_spices'), '==', True)
        ok(f._kook_spices, '==', ('-h: help', '-v: verbose'))

    def test_cmdopts(self):
        pass


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
