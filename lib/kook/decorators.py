# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

from types import FunctionType
from kook import KookRecipeError
#from kook.kitchen import IfExists
from kook.utils import flatten, _is_str, ArgumentError, get_funcname
#from kook.cookbook import Recipe
Recipe = None         # lazy import to avoid mutual import

__all__ = ('recipe', 'product', 'ingreds', 'byprods', 'coprods', 'priority', 'spices', 'cmdopts', )


#def recipe(func):
#    func._kook_recipe = True
#    return func

def recipe(product=None, ingreds=None):
    """decorator to mark function as a recipe.
    ex1.
       @recipe
       def clean(c):
         rm_rf('**/*.py')
    ex2.
       @recipe('*.o', ['$(1).c', '($1).h'])
       def file_o(c):
         system(c%'gcc -c $(product)')
    """
    ## ex:
    ##   @recipe
    ##   def clean(c): ...
    if isinstance(product, FunctionType):
        func = product
        func_name = get_funcname(func)
        if getattr(func, '_kook_product', None):
            if not func_name.startswith('task_') and not func_name.startswith('file_'):
                raise KookRecipeError("%s(): prefix ('file_' or 'task_') required when product is specified." % func_name)
        global Recipe
        if not Recipe: from kook.cookbook import Recipe
        func._kook_recipe = Recipe.new(func_name, func)
        return func
    ## ex:
    ##   @recipe('*.o', ['$(1).c', '$(1).h'])
    ##   def file_o(c): ...
    if   product is None:   pass
    elif _is_str(product):  pass
    else:
        raise ArgumentError("%s: recipe product should be a string." % repr(product))
    #
    if   ingreds is None:            pass
    elif isinstance(ingreds, tuple): pass
    elif isinstance(ingreds, list):  ingreds = tuple(ingreds)
    elif _is_str(ingreds):           ingreds = (ingreds, )
    else:
        raise ArgumentError("%s: recipe ingredients should be a list or tuple." % repr(ingreds))
    #
    #if kind in (None, 'file', 'task'):  pass
    #else:
    #    raise TypeError("%s: recipe kind should be 'file' or 'task'." % repr(ingreds))
    #
    def deco(f):
        if product:  f._kook_product = product
        if ingreds:  f._kook_ingreds = ingreds
        return recipe(f)
    return deco


def product(name):
    def deco(f):
        f._kook_product = name
        return f
    return deco


def ingreds(*names):
    def deco(f):
        f._kook_ingreds = tuple(flatten(names))
        return f
    return deco


def byprods(*names):
    def deco(f):
        f._kook_byprods = tuple(flatten(names))
        return f
    return deco


def coprods(*names):
    def deco(f):
        f._kook_coprods = tuple(flatten(names))
        return f
    return deco


def priority(level):     # not used yet
    if not isinstance(level, int):
        import kook
        raise kook.KookRecipeError("priority requires integer.")  # TODO: change backtrace
    def deco(f):
        f._kook_priority = level
        return f
    return deco


def spices(*names):
    def deco(f):
        f._kook_spices = tuple(flatten(names))
        return f
    return deco


def cmdopts(*names):
    import sys
    sys.stderr.write("[pykook] ERROR: '@cmdopts()' is obsolete. Use '@spices()' instead.\n")
    sys.stderr.write("[pykook]        See http://www.kuwata-lab.com/kook/pykook-CHANGES.txt for details.\n")
    sys.exit(1)
