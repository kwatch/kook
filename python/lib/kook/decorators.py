# -*- coding: utf-8 -*-

###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

#from kook import KookRecipeError
#from kook.kitchen import IfExists
from kook.util import flatten

__all__ = ('product', 'ingreds', 'byprods', 'coprods', 'priority', 'options', 'if_exists', )


def product(name):
    """decorator for recipe function"""
    def deco(f):
        f._kook_product = name
        return f
    return deco


def ingreds(*names):
    """decorator for recipe function"""
    def deco(f):
        f._kook_ingreds = flatten(names)
        return f
    return deco


def byprods(*names):
    """decorator for recipe function"""
    def deco(f):
        f._kook_byprods = flatten(names)
        return f
    return deco


def coprods(*names):
    """decorator for recipe function"""
    def deco(f):
        f._kook_coprods = flatten(names)
        return f
    return deco


def priority(level):
    """decorator for recipe function"""
    if not isinstance(leve, int):
        import kook
        raise kook.KookRecipeError("priority requires integer.")  # TODO: change backtrace
    def deco(f):
        f._kook_priority = level
        return f
    return deco


def options(*names):
    """decorator for recipe function"""
    def deco(f):
        f._kook_options = names
        return f
    return deco


def if_exists(*args):
    """helper function to create IfExists object."""
    import kook
    #return kook.kitchen.IfExists(*args)
    return [ kook.kitchen.IfExists(arg) for arg in flatten(args) ]
