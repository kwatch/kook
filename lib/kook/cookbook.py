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
from kook.utils import _is_str, ArgumentError, has_metachars
import kook.config as config
from kook.misc import ConditionalFile

__all__ = ('Cookbook', 'Recipe', )


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
        self.specific_task_recipes = []
        self.generic_task_recipes  = []
        self.specific_file_recipes = []
        self.generic_file_recipes  = []

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

    def load(self, content, bookname='(kook)', properties={}):
        context = self._new_context(properties)
        self.context = context
        self.bookname = bookname
        self._eval_content(content, bookname, context)
        self.materials = self._get_kook_materials(context)
        _trace("specific task recipes: %s" % repr(self.specific_task_recipes))
        _trace("generic  task recipes: %s" % repr(self.generic_task_recipes))
        _trace("specific file recipes: %s" % repr(self.specific_file_recipes))
        _trace("generic  file recipes: %s" % repr(self.generic_file_recipes))

    def _new_context(self, properties):
        context = create_context()
        if properties:
            context.update(properties)
        context['prop'] = self.prop
        context['kookbook'] = KookbookProxy(self)
        return context

    def _eval_content(self, content, bookname, context):
        code_obj = compile(content, bookname, 'exec')
        #exec code_obj in context, context
        exec(code_obj, context, context)

    def _get_kook_materials(self, context):
        name = 'kook_materials'
        if name in context:
            arr = context.get(name)
            if not isinstance(arr, (tuple, list)):
                raise KookRecipeError("%s: kook_materials should be tuple or list." % repr(arr))
            return arr
        else:
            return ()

    def material_p(self, target):
        return target in self.materials    ## TODO: use dict

    def register(self, recipe):
        generic = recipe.is_generic()
        if recipe.kind == 'task':
            if generic: self.generic_task_recipes.append(recipe)
            else:       self.specific_task_recipes.append(recipe)
        elif recipe.kind == 'file':
            if generic: self.generic_file_recipes.append(recipe)
            else:       self.specific_file_recipes.append(recipe)
        else:
            assert False, "recipe.kind=%r" % (recipe.kind,)

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


class KookbookProxy(object):

    def __init__(self, cookbook):
        self._book = cookbook

    def register(self, recipe):
        self._book.register(recipe)

    def find_recipe(self, product, register=True):
        if not _is_str(product):
            raise TypeError("find_recipe(%r): string expected." % (product,))
        if has_metachars(product):
            raise ValueError("find_recipe(%r): not allowed meta characters." % (product,))
        book = self._book
        recipe = book.find_recipe(product)
        if recipe and recipe.is_generic():
            recipe = recipe._to_specific(product)
            if register:
                book.register(recipe)
        return recipe

    def get_recipe(self, product):
        book = self._book
        def _find(recipes, prod=product):
            for r in recipes:
                if r.product == prod:
                    return r
            return None
        return _find(book.specific_task_recipes) or \
               _find(book.specific_file_recipes) or \
               _find(book.generic_task_recipes)  or \
               _find(book.generic_file_recipes)

    def __get_default(self):
        return self._book.context['kook_default_product']

    def __set_default(self, product):
        self._book.context['kook_default_product'] = product

    default = property(__get_default, __set_default)


    def __get_materials(self):
        return self._book.context['kook_materials']

    def __set_materials(self, materials):
        self._book.context['kook_materials'] = materials

    materials = property(__get_materials, __set_materials)



class Recipe(object):

    __category = None

    def __init__(self, kind=None, product=None, ingreds=(), byprods=(), method=None, desc=None, spices=None):
        self.kind    = kind
        self.product = product
        self.ingreds = ingreds
        self.byprods = byprods
        self.method  = method
        self.desc    = desc
        self.spices  = spices

    def __get_kind(self):
        return self.__kind
    def __set_kind(self, kind):
        if kind != 'task' and kind != 'file':
            raise ValueError("%s: kind should be 'task' or 'file'." % (kind, ))
        self.__kind = kind
    kind = property(__get_kind, __set_kind)

    def __get_product(self):
        return self.__product
    def __set_product(self, product):
        self.__product = product
        if not product:
            self.__pattern = None
        elif type(product) is _re_pattern_type:
            self.__pattern = product
        elif kook.utils.has_metachars(product):
            self.__pattern = kook.utils.meta2rexp(product)
        else:
            self.__pattern = None
    product = property(__get_product, __set_product)

    def __get_ingreds(self):
        return self.__ingreds
    def __set_ingreds(self, ingreds):
        self.__ingreds = ingreds
    ingreds = property(__get_ingreds, __set_ingreds)

    def __get_byprods(self):
        return self.__byprods
    def __set_byprods(self, byprods):
        self.__byprods = byprods
    byprods = property(__get_byprods, __set_byprods)

    def __get_method(self):
        return self.__method
    def __set_method(self, method):
        self.__method = method
        self.__name = method and kook.utils.get_funcname(method) or None
        if method.__doc__:
            self.desc = method.__doc__
    method = property(__get_method, __set_method)

    def __get_desc(self):
        return self.__desc
    def __set_desc(self, desc):
        self.__desc = desc
    desc = property(__get_desc, __set_desc)

    def __get_spices(self):
        return self.__spices
    def __set_spices(self, spices):
        self.__spices = spices
    spices = property(__get_spices, __set_spices)

    def __get_pattern(self):
        return self.__pattern
    pattern = property(__get_pattern)

    def __get_name(self):
        return self.__name
    name = property(__get_name)

    def __get_category(self):
        return self.__category
    category = property(__get_category)

    def set_category(self, category_class):
        self.__category = category_class
        if self.kind == 'task':
            names = []
            while category_class:
                names.append(category_class.__name__)
                category_class = category_class._outer
            names.reverse()
            if self.product != '__index__':
                names.append(self.product)
            self.product = ':'.join(names)

    @classmethod
    def new(cls, func_name, method, kind=None):
        if kind: pass
        elif func_name.startswith('task_'):  kind = 'task'
        elif func_name.startswith('file_'):  kind = 'file'
        else:                                kind = 'task'
        prefix  = kind + '_'
        product = getattr(method, '_kook_product', None)
        if product is not None:
            if not func_name.startswith('task_') and not func_name.startswith('file_'):
                raise KookRecipeError("%s(): prefix ('file_' or 'task_') required when product is specified." % func_name)
            if _is_str(product): pass
            elif isinstance(product, _re_pattern_type): pass
            else:
                raise ArgumentError("%r: recipe product should be a string." % (product,))
        else:
            product = (func_name.startswith(prefix) and func_name[len(prefix):] or func_name)
        ingreds = getattr(method, '_kook_ingreds', ())
        if ingreds is not None:
            if   isinstance(ingreds, tuple): pass
            elif isinstance(ingreds, list):  ingreds = tuple(ingreds)
            elif _is_str(ingreds):           ingreds = (ingreds, )
            else:
                raise ArgumentError("%r: recipe ingredients should be a list or tuple." % (ingreds,))
        byprods = getattr(method, '_kook_byprods', ())
        spices  = getattr(method, '_kook_spices', None)
        desc    = method.__doc__  ## can be empty string
        if desc is None: desc = _default_descs.get(product)
        return cls(kind=kind, product=product, ingreds=ingreds, byprods=byprods, method=method, desc=desc, spices=spices)

    def is_generic(self):
        return self.__pattern is not None

    def match(self, target):
        if self.is_generic():
            return re.match(self.pattern, target)
        else:
            return self.product == target

    def _to_specific(self, product):
        if not self.is_generic():
            return self
        if kook.utils.has_metachars(product):
            raise ValueError("_to_specific_recipe(%r): product contains metacharacter." % (product, ))
        matched = re.match(self.pattern, product)
        if not matched:
            return None
        pat = r'\$\((\d+)\)'   # replace '$(1)', '$(2)', ...
        repl = lambda m1: matched.group(int(m1.group(1)))
        def convert(items, _pat=pat, _repl=repl):
            arr = []
            for item in items:
                if isinstance(item, ConditionalFile):
                    filename = re.sub(_pat, _repl, item.filename)
                    filename = item.__call__(filename)
                    if filename: arr.append(filename)
                else:
                    arr.append(re.sub(_pat, _repl, item))
            return tuple(arr)
        ingreds, byprods = self.ingreds, self.byprods
        if ingreds:  ingreds = convert(ingreds)
        if byprods:  byprods = convert(byprods)
        cls = self.__class__
        recipe = cls(product=product, ingreds=ingreds, byprods=byprods,
                     kind=self.kind, method=self.method, desc=self.desc, spices=self.spices)
        recipe._original = self
        recipe._matched = matched
        recipe._m = (matched.group(), ) + matched.groups()   # tuple
        return recipe

    def __repr__(self):
        #return "<%s product=%s method=%s>" % (self.__class__.__name__, repr(self.product), self.name)
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
            key = key.replace('_Recipe__', '')
            if isinstance(val, types.FunctionType):
                buf.append("%s=<function %s>" % (key, kook.utils.get_funcname(val)))
            else:
                buf.append("%s=%s" % (key, repr(val)))
            buf.append(",\n")
        if buf[-1] == ",\n": buf.pop()
        buf.append(">")
        return "".join(buf)


## TODO: define SpecificRecipe and GenericRecipe?


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
