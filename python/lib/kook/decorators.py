# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

#from kook import KookRecipeError
#from kook.kitchen import IfExists
from kook.utils import flatten

__all__ = ('recipe', 'product', 'ingreds', 'byprods', 'coprods', 'priority', 'spices', 'cmdopts', 'if_exists', )


def recipe(f):
    f._kook_recipe = True
    return f


def product(name):
    def deco(f):
        #f._kook_recipe  = True
        f._kook_product = name
        return f
    return deco


def ingreds(*names):
    def deco(f):
        f._kook_ingreds = flatten(names)
        return f
    return deco


def byprods(*names):
    def deco(f):
        f._kook_byprods = flatten(names)
        return f
    return deco


def coprods(*names):
    def deco(f):
        f._kook_coprods = flatten(names)
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
        f._kook_spices = names
        return f
    return deco


def cmdopts(*names):
    import sys
    sys.stderr.write("[pykook] ERROR: '@cmdopts()' is obsolete. Use '@spices()' instead.\n")
    sys.stderr.write("[pykook]        See http://www.kuwata-lab.com/kook/pykook-CHANGES.txt for details.\n")
    sys.exit(1)


def if_exists(*args):
    import kook
    #return kook.kitchen.IfExists(*args)
    return [ kook.kitchen.IfExists(arg) for arg in flatten(args) ]
