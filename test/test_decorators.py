###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re, time

from kook.decorators import *
from kook.cookbook import Recipe
from kook.utils import ArgumentError


class KookDecoratorsTest(object):

    def test_recipe(self):
        if "@recipe decorator used without arguments":
            @recipe
            def f(c):
                pass
            ok (hasattr(f, '_kook_recipe')) == True
            ok (f._kook_recipe).is_a(Recipe)
            #ok (hasattr(f, '_kook_kind')) == False
        ##
        if "@recipe decorator passed product and ingredients":
            @recipe('*.o', ['$(1).c', '$(1).h'])
            def file_o(c): pass
            ok (file_o._kook_recipe).is_a(Recipe)
            ok (file_o._kook_product) == '*.o'
            ok (file_o._kook_ingreds) == ('$(1).c', '$(1).h', )
        ##
        if "ingredient is a tuple then it is used as is":
            @recipe('*.html', ('$(1).txt', ))
            def file_html(c): pass
            ok (file_html._kook_recipe).is_a(Recipe)
            ok (file_html._kook_product) == '*.html'
            ok (file_html._kook_ingreds) == ('$(1).txt', )
        ##
        if "ingredient is a string then it will be converted into tuple":
            @recipe('*.class', '$(1).java')
            def file_class(c): pass
            ok (file_class._kook_recipe).is_a(Recipe)
            ok (file_class._kook_product) == '*.class'
            ok (file_class._kook_ingreds) == ('$(1).java', )
        ##
        if "product is not a string then TypeError raises":
            def tmp():
                @recipe(False, '$(1).java')
                def file_java(c): pass
            ok (tmp).raises(ArgumentError, 'False: recipe product should be a string.')
        ##
        if "ingredient is not a list nor tuple then TypeError raises":
            def tmp():
                @recipe('*.o', {'ingreds': ['*.c']})
                def file_o(c): pass
            ok (tmp).raises(ArgumentError, "{'ingreds': ['*.c']}: recipe ingredients should be a list or tuple.")
        ##
        #@recipe(kind='task')
        #def f(c):
        #    pass
        #ok (hasattr(f, '_kook_recipe')) == True
        #ok (f._kook_recipe).is_a(Recipe)
        #ok (hasattr(f, '_kook_kind')) == True
        #ok (f._kook_kind) == 'task'
        ##
        #@recipe(kind='file')
        #def f(c):
        #    pass
        #ok (hasattr(f, '_kook_recipe')) == True
        #ok (f._kook_recipe).is_a(Recipe)
        #ok (hasattr(f, '_kook_kind')) == True
        #ok (f._kook_kind) == 'file'
        ##
        #@recipe()
        #def f(c):
        #    pass
        #ok (hasattr(f, '_kook_recipe')) == True
        #ok (f._kook_recipe).is_a(Recipe)
        #ok (hasattr(f, '_kook_kind')) == False


    def test_product(self):
        @product('hello')
        def f(c):
            pass
        ok (hasattr(f, '_kook_product')) == True
        ok (f._kook_product) == 'hello'
        #ok (hasattr(f, '_kook_recipe')) == True
        #ok (f._kook_recipe).is_a(Recipe)

    def test_ingreds(self):
        @ingreds('foo', 'bar', 'baz')
        def f(c):
            pass
        ok (hasattr(f, '_kook_ingreds')) == True
        ok (f._kook_ingreds) == ('foo', 'bar', 'baz')

    def test_byrpods(self):
        @byprods('foo', 'bar', 'baz')
        def f(c):
            pass
        ok (hasattr(f, '_kook_byprods')) == True
        ok (f._kook_byprods) == ('foo', 'bar', 'baz')

    def test_coprods(self):
        @coprods('foo', 'bar', 'baz')
        def f(c):
            pass
        ok (hasattr(f, '_kook_coprods')) == True
        ok (f._kook_coprods) == ('foo', 'bar', 'baz')

    def test_priority(self):
        @priority(123)
        def f(c):
            pass
        ok (hasattr(f, '_kook_priority')) == True
        ok (f._kook_priority) == 123
        def func():
            @priority('123')
            def f(c):
                pass
        import kook
        ok (func).raises(kook.KookRecipeError, "priority requires integer.")

    def test_spices(self):
        @spices('-h: help', '-v: verbose')
        def f(c):
            pass
        ok (hasattr(f, '_kook_spices')) == True
        ok (f._kook_spices) == ('-h: help', '-v: verbose')

    def test_cmdopts(self):
        pass


if __name__ == '__main__':
    oktest.run('.*Test$')
