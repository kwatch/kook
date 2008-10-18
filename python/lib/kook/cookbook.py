# -*- coding: utf-8 -*-

###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

import os, re, types
from kook import _debug
from util import *

#__all__ = ('Cookbook', 'Recipe', 'TaskRecipe', 'FileRecipe', )
__all__ = ('Cookbook', )


class Cookbook(object):

    bookname = None
    specific_task_recipes = ()
    generic_task_recipes  = ()
    specific_file_recipes = ()
    generic_file_recipes  = ()
    materials = ()
    property_names = ()
    _property_names_dict = None
    context = None

    def __init__(self, bookname=None):
        self.bookname = bookname
        self.property_names = []
        self._property_names_dict = {}
        #if bookname:
        #    self.load_file(bookname)

    def prop(self, name, value):
        if not self._property_names_dict.has_key(name):
            self._property_names_dict[name] = True
            self.property_names.append(name)
        if self.context.has_key(name):
            value = self.context[name]
        else:
            self.context[name] = value
        return value

    def all_properties(self):
        return [ (pname, self.context.get(pname)) for pname in self.property_names ]

    @classmethod
    def new(cls, bookname, properties={}):
        self = cls(bookname)
        if bookname:
            self.load_file(bookname, properties)
        return self

    def default_product(self):
        return self.context.get('kook_default_product')

    def load_file(self, filename, properties={}):
        ## read file
        self.bookname = filename
        if not os.path.isfile(filename):
            raise ArgumentError("%s: not found." % filename)
        content = read_file(filename)
        self.load(content, filename, properties)

    def load(self, content, bookname='(kook)', properties={}):  ## TODO: refactoring
        ## eval content
        code_obj = compile(content, bookname, 'exec')
        context = create_context()
        if properties: context.update(properties)
        context['prop'] = self.prop
        self.context = context
        exec code_obj in context, context
        ## create recipes
        recipes = {
            'task': {'specific': [], 'generic': []},
            'file': {'specific': [], 'generic': []},
        }
        for name, obj in context.iteritems():
            if name == 'kook_materials':
                if not isinstance(obj, (tuple, list)):
                    raise KookRecipeError("kook_materials: tuple or list expected.")
                self.materials = obj
            elif type(obj) == types.FunctionType:
                func = obj
                if name.startswith('task_'):
                    key1 = 'task'
                    recipe = TaskRecipe.new(name, func)
                elif name.startswith('file_'):
                    key1 = 'file'
                    recipe = FileRecipe.new(name, func)
                else:
                    continue
                key2 = recipe.pattern and 'generic' or 'specific'
                recipes[key1][key2].append(recipe)
        lambda1 = lambda recipe: recipe._func_linenum()
        recipes['task']['specific'].sort(key=lambda1)
        recipes['task']['generic'].sort(key=lambda1)
        recipes['file']['specific'].sort(key=lambda1)
        recipes['file']['generic'].sort(key=lambda1)
        self.specific_task_recipes = recipes['task']['specific']   ## TODO: use dict
        self.generic_task_recipes  = recipes['task']['generic']    ## TODO: support priority
        self.specific_file_recipes = recipes['file']['specific']   ## TODO: use dict
        self.generic_file_recipes  = recipes['file']['generic']    ## TODO: support priority
        _debug("specific task recipes: %s" % repr(self.specific_task_recipes), 2)
        _debug("generic  task recipes: %s" % repr(self.generic_task_recipes), 2)
        _debug("specific file recipes: %s" % repr(self.specific_file_recipes), 2)
        _debug("generic  file recipes: %s" % repr(self.generic_file_recipes), 2)

    def material_p(self, target):
        return target in self.materials    ## TODO: use dict

    def find_recipe(self, target):
        recipes_tuple = (self.specific_task_recipes, self.specific_file_recipes,
                         self.generic_task_recipes,  self.generic_file_recipes, )
        for recipes in recipes_tuple:      ## TODO: use dict for specific recipes
            for recipe in recipes:
                if recipe.match(target):
                    _debug("Cookbook#find_recipe(): target=%s, func=%s, product=%s" % \
                               (repr(target), recipe.get_func_name(), repr(recipe.product), ), 2)
                    return recipe
        return None
        #if target.startswith(':'):
        #    specific_recipes = self.specific_task_recipes
        #    generic_recipes  = self.generic_task_recipes
        #else:
        #    specific_recipes = self.specific_file_recipes
        #    generic_recipes  = self.generic_file_recipes
        #for recipe in specific_recipes:    ## TODO: use dict
        #    if recipe.match(target):
        #        _debug("find_recipe(): target=%s, func=%s, product=%s" % \
        #                   (repr(target), recipe.get_func_name(), repr(recipe.product), ), 2)
        #        return recipe
        #for recipe in generic_recipes:
        #    if recipe.match(target):
        #        _debug("find_recipe(): target=%s, func=%s, product=%s" % \
        #                   (repr(target), recipe.get_func_name(), repr(recipe.product), ), 2)
        #        return recipe
        #return None

    def start(self, depth=1, args=()):
        _debug("material %s" % self.product, 1, depth)
        return True

    def start2(self, depth=1, args=(), parent_mtime=0):
        assert os.path.exists(self.product)
        if parent_mtime == 0:
            msg = "material %s"
            ret = -999
        else:
            mtime = os.path.getmtime(self.product)


_re_pattern_type = type(re.compile('x'))


class Recipe(object):

    kind = None

    def __init__(self, product=None, ingreds=(), byprods=(), func=None, desc=None, cmdopts=None):
        self.product = product
        self.ingreds = ingreds
        self.byprods = byprods
        self.func    = func
        self.desc    = desc
        self.cmdopts = cmdopts
        if not product:
            self.pattern = None
        elif type(product) is _re_pattern_type:
            self.pattern = product
        elif has_metachars(product):
            self.pattern = meta2rexp(product)
        else:
            self.pattern = None

    def is_generic(self):
        return self.pattern is not None

    def match(self, target):
        if self.pattern:
            return re.match(self.pattern, target)
        else:
            return self.product == target

    def get_func_name(self):
        return self.func.func_code.co_name

    def _func_linenum(self):
        return self.func.func_code.co_firstlineno

    @classmethod
    def new(cls, func_name, func, prefix, _cls=None):
        if _cls is None: _cls = cls
        product = getattr(func, '_kook_product', func_name[len(prefix):])
        ingreds = getattr(func, '_kook_ingreds', ())
        byprods = getattr(func, '_kook_byprods', ())
        cmdopts = getattr(func, '_kook_cmdopts', None)
        func    = func
        desc    = func.__doc__  ## can be empty string
        if desc is None: desc = _default_descs.get(product)
        return _cls(product=product, ingreds=ingreds, byprods=byprods, func=func, desc=desc, cmdopts=cmdopts)

    def __repr__(self):
        #return "<%s product=%s func=%s>" % (self.__class__.__name__, repr(self.product), self.get_func_name())
        return "<%s:%s:%s>" % (self.__class__.__name__, repr(self.product), self.get_func_name())


## TODO: define SpecificRecipe and GenericRecipe instead of TaskRecipe and FileRecipe?


class TaskRecipe(Recipe):

    kind = 'task'

    @classmethod
    def new(cls, func_name, func):
        recipe = Recipe.new(func_name, func, 'task_', _cls=TaskRecipe)
        #if recipe.product[0] != ':':
        #    recipe.product = ':' + recipe.product
        return recipe


class FileRecipe(Recipe):

    kind = 'file'

    @classmethod
    def new(cls, func_name, func):
        return Recipe.new(func_name, func, 'file_', _cls=FileRecipe)


import kook.commands    ## don't move from here!
import kook.decorators

_default_context = dict( [ (x, getattr(kook.commands,   x)) for x in kook.commands.__all__ ] +
                         [ (x, getattr(kook.decorators, x)) for x in kook.decorators.__all__ ] )


def create_context():
    return _default_context.copy()


_default_descs = {
    "all"       : "cook all products",
    "clean"     : "remove by-products",
    "clear"     : "remove products and by-products",
    "help"      : "show help",
    "install"   : "install product",
    "setup"     : "setup configuration",
    "test"      : "do test",
    "uninstall" : "uninstall product",
}
