# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

#from kook import KookRecipeError
#from kook.kitchen import IfExists
from kook.utils import flatten

__all__ = ('product', 'ingreds', 'byprods', 'coprods', 'priority', 'cmdopts', 'if_exists', )


def product(name):
    def deco(f):
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


def priority(level):
    if not isinstance(leve, int):
        import kook
        raise kook.KookRecipeError("priority requires integer.")  # TODO: change backtrace
    def deco(f):
        f._kook_priority = level
        return f
    return deco


def cmdopts(*names):
    def deco(f):
        f._kook_cmdopts = names
        return f
    return deco


def if_exists(*args):
    import kook
    #return kook.kitchen.IfExists(*args)
    return [ kook.kitchen.IfExists(arg) for arg in flatten(args) ]
