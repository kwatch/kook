# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import os, re, types
from kook import KookRecipeError
from kook.misc import Category, _debug, _trace
import kook.utils
import kook.config as config

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

    @classmethod
    def new(cls, bookname, properties={}):
        self = cls(bookname)
        if bookname:
            self.load_file(bookname, properties)
        return self

    def prop(self, name, value):
        if name not in self._property_names_dict:
            self._property_names_dict[name] = True
            self.property_names.append(name)
        if name in self.context:
            value = self.context[name]
        else:
            self.context[name] = value
        return value

    def all_properties(self):
        return [ (pname, self.context.get(pname)) for pname in self.property_names ]

    def default_product(self):
        return self.context.get('kook_default_product')

    def load_file(self, filename, properties={}):
        ## read file
        self.bookname = filename
        if not os.path.isfile(filename):
            raise kook.utils.ArgumentError("%s: not found." % filename)
        content = kook.utils.read_file(filename)
        self.load(content, filename, properties)

    def load(self, content, bookname='(kook)', properties={}):  ## TODO: refactoring
        ## eval content
        self.bookname = bookname
        code_obj = compile(content, bookname, 'exec')
        context = create_context()
        if properties: context.update(properties)
        context['prop'] = self.prop
        self.context = context
        exec(code_obj, context, context)
        ## kook_materials
        name = 'kook_materials'
        if name in context:
            obj = context.get(name)
            if not isinstance(obj, (tuple, list)):
                raise KookRecipeError("%s: kook_materials should be tuple or list." % repr(obj))
            self.materials = obj
        ## collect recipe functions
        tuples = []
        for name in context:         # dict.iteritems() is not available in Python 3.0
            obj = context.get(name)
            if Recipe.is_recipe_func(obj):
                func = obj
                tuples.append((name, func, None))
            elif type(obj) is type and issubclass(obj, Category):
                klass = obj
                tuples.extend([ (k, v, klass) for k, v in klass.__dict__.items()
                                              if Recipe.is_recipe_func(v) ])
        ## masks
        TASK     = 0x0
        FILE     = 0x1
        SPECIFIC = 0x0
        GENERIC  = 0x2
        ## create recipes
        recipes = (
            [],    # SPECIFIC | TASK
            [],    # SPECIFIC | FILE
            [],    # GENERIC  | TASK
            [],    # GNERIC   | FILE
        )
        for name, func, category_class in tuples:
            ## detect recipe type
            if   name.startswith('file_'):  flag = FILE
            elif name.startswith('task_'):  flag = TASK
            else:
                #flag = getattr(func, '_kook_product', None) and FILE or TASK
                if getattr(func, '_kook_product', None):
                    raise KookRecipeError("%s(): prefix ('file_' or 'task_') required when @product() specified." % name)
                flag = TASK   # regard as task recipe when prefix is not specified
            ## create recipe object
            klass = flag == FILE and FileRecipe or TaskRecipe
            recipe = klass.new(name, func)
            if category_class:
                recipe.set_category(category_class)
            flag = flag | (recipe.pattern and GENERIC or SPECIFIC)
            recipes[flag].append(recipe)
        #lambda1 = lambda recipe: kook.utils.get_funclineno(recipe.func)
          #=> SyntaxError: unqualified exec is not allowed in function 'load' it contains a nested function with free variables
        def lambda1(recipe, get_funclineno=kook.utils.get_funclineno):
            return get_funclineno(recipe.func)
        for lst in recipes:
            lst.sort(key=lambda1)
        self.specific_task_recipes = recipes[SPECIFIC | TASK]   ## TODO: use dict
        self.specific_file_recipes = recipes[SPECIFIC | FILE]   ## TODO: use dict
        self.generic_task_recipes  = recipes[GENERIC  | TASK]   ## TODO: support priority
        self.generic_file_recipes  = recipes[GENERIC  | FILE]   ## TODO: support priority
        _trace("specific task recipes: %s" % repr(self.specific_task_recipes))
        _trace("generic  task recipes: %s" % repr(self.generic_task_recipes))
        _trace("specific file recipes: %s" % repr(self.specific_file_recipes))
        _trace("generic  file recipes: %s" % repr(self.generic_file_recipes))

    def material_p(self, target):
        return target in self.materials    ## TODO: use dict

    def find_recipe(self, target):
        recipes_tuple = (self.specific_task_recipes, self.specific_file_recipes,
                         self.generic_task_recipes,  self.generic_file_recipes, )
        for recipes in recipes_tuple:      ## TODO: use dict for specific recipes
            for recipe in recipes:
                if recipe.match(target):
                    _trace("Cookbook#find_recipe(): target=%s, func=%s, product=%s" % \
                               (repr(target), recipe.name, repr(recipe.product), ))
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
        #        _trace("find_recipe(): target=%s, func=%s, product=%s" % \
        #                   (repr(target), recipe.name, repr(recipe.product), ))
        #        return recipe
        #for recipe in generic_recipes:
        #    if recipe.match(target):
        #        _trace("find_recipe(): target=%s, func=%s, product=%s" % \
        #                   (repr(target), recipe.name, repr(recipe.product), ))
        #        return recipe
        #return None


_re_pattern_type = type(re.compile('dummy'))


class Recipe(object):

    kind = None
    prefix = ''
    name = None
    category = None

    def __init__(self, product=None, ingreds=(), byprods=(), func=None, desc=None, spices=None):
        self.product = product
        self.ingreds = ingreds
        self.byprods = byprods
        self.func    = func
        self.desc    = desc
        self.spices  = spices
        self.name    = func and kook.utils.get_funcname(self.func) or None
        if not product:
            self.pattern = None
        elif type(product) is _re_pattern_type:
            self.pattern = product
        elif kook.utils.has_metachars(product):
            self.pattern = kook.utils.meta2rexp(product)
        else:
            self.pattern = None

    @classmethod
    def new(cls, func_name, func, _cls=None):
        if _cls: cls = _cls
        prefix  = cls.prefix
        product = getattr(func, '_kook_product', None) or \
                  (func_name.startswith(prefix) and func_name[len(prefix):] or func_name)
        ingreds = getattr(func, '_kook_ingreds', ())
        byprods = getattr(func, '_kook_byprods', ())
        spices  = getattr(func, '_kook_spices', None)
        desc    = func.__doc__  ## can be empty string
        if desc is None: desc = _default_descs.get(product)
        return cls(product=product, ingreds=ingreds, byprods=byprods, func=func, desc=desc, spices=spices)

    @staticmethod
    def is_recipe_func(obj):
        return kook.utils.is_func_or_method(obj) and hasattr(obj, '_kook_recipe')

    def is_generic(self):
        return self.pattern is not None

    def set_category(self, category_class):
        self.category = category_class

    def match(self, target):
        if self.pattern:
            return re.match(self.pattern, target)
        else:
            return self.product == target

    def __repr__(self):
        #return "<%s product=%s func=%s>" % (self.__class__.__name__, repr(self.product), self.name)
        return "<%s:%s:%s>" % (self.__class__.__name__, repr(self.product), self.name)

    def _inspect(self, depth=1):
        buf = []
        buf.extend(("#<", self.__class__.__name__, "\n"))
        keys = list(self.__dict__.keys())
        keys.sort()
        space = '  ' * depth
        for key in keys:
            buf.append(space)
            val = self.__dict__[key]
            if isinstance(val, types.FunctionType):
                buf.append("%s=<function %s>" % (key, kook.utils.get_funcname(val)))
            else:
                buf.append("%s=%s" % (key, repr(val)))
            buf.append(",\n")
        if buf[-1] == ",\n": buf.pop()
        buf.append(">")
        return "".join(buf)


## TODO: define SpecificRecipe and GenericRecipe instead of TaskRecipe and FileRecipe?


class TaskRecipe(Recipe):

    kind   = 'task'
    prefix = 'task_'

    def set_category(self, category_class):
        Recipe.set_category(self, category_class)
        ## use category class name as product prefix
        self.product = category_class.__name__ + ':' + self.product


class FileRecipe(Recipe):

    kind   = 'file'
    prefix = 'file_'


import kook.commands    ## don't move from here!
import kook.decorators
import kook.misc

_default_context = dict( [ (x, getattr(kook.commands,   x)) for x in kook.commands.__all__ ] +
                         [ (x, getattr(kook.decorators, x)) for x in kook.decorators.__all__ ] +
                         [ (x, getattr(kook.misc,       x)) for x in kook.misc.__all__ ] )


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
