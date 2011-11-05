###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import sys, os, re, time
import oktest
from oktest import *
from oktest import skip
from oktest.tracer import Tracer

from kook.decorators import RecipeDecorator
from kook.cookbook import Recipe
from kook.utils import ArgumentError
try:
    import kook.remote
    from kook.remote import Remote
    remote_available = True
except ImportError:
    remote_available = False

globals().update(RecipeDecorator().to_dict())

import _testhelper


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
            ok (file_o._kook_ingreds) == ['$(1).c', '$(1).h']
        ##
        if "ingredient is a tuple then it is used as is":
            @recipe('*.html', ('$(1).txt', ))
            def file_html(c): pass
            ok (file_html._kook_recipe).is_a(Recipe)
            ok (file_html._kook_product) == '*.html'
            ok (file_html._kook_ingreds) == ['$(1).txt']
        ##
        if "ingredient is a string then it will be converted into tuple":
            @recipe('*.class', '$(1).java')
            def file_class(c): pass
            ok (file_class._kook_recipe).is_a(Recipe)
            ok (file_class._kook_product) == '*.class'
            ok (file_class._kook_ingreds) == ['$(1).java']
        ##
        if "product is not a string then TypeError raises":
            def tmp():
                @recipe(123, '$(1).java')
                def file_java(c): pass
            ok (tmp).raises(ArgumentError, '123: recipe product should be a string.')
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
        #
        if "kookbook exists in context then register recipe into it.":
            tr = Tracer()
            kookbook = tr.fake_obj(register=True)
            _recipe = RecipeDecorator(kookbook).to_dict()["recipe"]
            @_recipe
            def hello(c):
                print("Hello")
            ok (len(tr)) == 1
            ok (tr[0].args) == (hello._kook_recipe, )
            @_recipe('hi', ['hello'])
            def task_hi(c):
                print("Hi")
            ok (len(tr)) == 2
            ok (tr[1].args) == (task_hi._kook_recipe, )
        ##
        if "'remotes' arugment specified":
            if remote_available:
                r1 = Remote(hosts=['host1'])
                r2 = Remote(hosts=['host2'])
                @recipe('*.o', ['$(1).c', '$(1).h'], remotes=[r1, r2])
                def file_o(c): pass
                ok (file_o._kook_remotes) == [r1, r2]


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
        ok (f._kook_ingreds) == ['foo', 'bar', 'baz']

    def test_byrpods(self):
        @byprods('foo', 'bar', 'baz')
        def f(c):
            pass
        ok (hasattr(f, '_kook_byprods')) == True
        ok (f._kook_byprods) == ['foo', 'bar', 'baz']

    def test_coprods(self):
        @coprods('foo', 'bar', 'baz')
        def f(c):
            pass
        ok (hasattr(f, '_kook_coprods')) == True
        ok (f._kook_coprods) == ['foo', 'bar', 'baz']

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
        ok (f._kook_spices) == ['-h: help', '-v: verbose']

    @test("@remotes(): takes Remote objects.")
    @skip.when(not remote_available, "kook.remote is not available")
    def test_remotes(self):
        r1 = Remote(hosts=['host1'])
        r2 = Remote(hosts=['host2'])
        @remotes(r1, r2)
        def f(c):
            pass
        ok (hasattr(f, '_kook_remotes')) == True
        ok (f._kook_remotes) == [r1, r2]

    @test("@remotes(): raises TypeError when argument is not a Remote object.")
    @skip.when(not remote_available, "kook.remote is not available")
    def test_remotes(self):
        def fn():
            @remotes("remote")
            def f(c):
                pass
        ok (fn).raises(TypeError, "@remotes(): Remote object expected but got 'remote'.")

    def test_cmdopts(self):
        pass


if __name__ == '__main__':
    oktest.main()
