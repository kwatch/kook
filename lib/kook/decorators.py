# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import sys
from types import FunctionType
from kook import KookRecipeError
#from kook.kitchen import IfExists
from kook.utils import flatten, _is_str, ArgumentError, get_funcname
#from kook.cookbook import Recipe
Recipe = None         # lazy import to avoid mutual import
Remote = None         # lazy import

__all__ = ('RecipeDecorator', )


class RecipeDecorator(object):

    def __init__(self, kookbook=None):
        self.kookbook = kookbook

    def to_dict(self):
        return { "recipe":  self.recipe,  "product":  self.product,
                 "ingreds": self.ingreds, "byprods":  self.byprods,
                 "coprods": self.coprods, "priority": self.priority,
                 "spices":  self.spices,  "remotes":  self.remotes,
                 "cmdopts":  self.cmdopts, }

    def recipe(self, product=None, ingreds=None, remotes=None):
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
            global Recipe
            if not Recipe: from kook.cookbook import Recipe
            func._kook_recipe = Recipe.new(func_name, func)
            if self.kookbook: self.kookbook.register(func._kook_recipe )
            return func
        ## ex:
        ##   @recipe('*.o', ['$(1).c', '$(1).h'])
        ##   def file_o(c): ...
        if isinstance(ingreds, (tuple, list)):
            ingreds = flatten(ingreds)
        elif not ingreds:
            ingreds = []
        elif _is_str(ingreds):
            ingreds = [ingreds]
        else:
            raise ArgumentError("%r: recipe ingredients should be a list or tuple." % (ingreds, ))
        def deco(f):
            if product:  f._kook_product = product
            if ingreds:  f._kook_ingreds = ingreds
            if remotes:  f._kook_remotes = list(remotes)
            self.recipe(f)
            return f
        return deco


    def product(self, name):
        def deco(f):
            f._kook_product = name
            return f
        return deco


    def ingreds(self, *names):
        def deco(f):
            f._kook_ingreds = flatten(names)
            return f
        return deco


    def byprods(self, *names):
        def deco(f):
            f._kook_byprods = flatten(names)
            return f
        return deco


    def coprods(self, *names):
        def deco(f):
            f._kook_coprods = flatten(names)
            return f
        return deco


    def priority(self, level):     # not used yet
        if not isinstance(level, int):
            import kook
            raise kook.KookRecipeError("priority requires integer.")  # TODO: change backtrace
        def deco(f):
            f._kook_priority = level
            return f
        return deco


    def spices(self, *names):
        def deco(f):
            f._kook_spices = flatten(names)
            return f
        return deco


    def remotes(self, *remote_objects):
        global Remote
        if not Remote: from kook.remote import Remote
        remote_objects = flatten(remote_objects)
        for obj in remote_objects:
            if not isinstance(obj, Remote):
                raise TypeError("@remotes(): Remote object expected but got %r." % (obj,))
        def deco(f):
            f._kook_remotes = flatten(remote_objects)
            return f
        return deco


    def cmdopts(self, *names):
        import sys
        sys.stderr.write("[pykook] ERROR: '@cmdopts()' is obsolete. Use '@spices()' instead.\n")
        sys.stderr.write("[pykook]        See http://www.kuwata-lab.com/kook/pykook-CHANGES.txt for details.\n")
        sys.exit(1)
