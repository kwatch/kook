# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import sys, os, re, types
from types import FunctionType
from kook import KookRecipeError
from kook.decorators import RecipeDecorator
from kook.misc import Category, _debug, _trace
import kook.utils
from kook.utils import _is_str, to_list, read_file, resolve_filepath, ArgumentError, has_metachars
import kook.config as config
from kook.misc import ConditionalFile, Category

__all__ = ('Cookbook', 'Recipe', )



#class BookObject(object):
#
#    def __init__(self, content, context, filepath=None):
#        code_obj = compile(content, filepath or "(kook)", "exec")
#        exec(code_obj, context, context)
#        self.__dict__ = context
#        self.__file__ = filepath
#
#    def __getitem__(self, key):
#        return self.__dict__[key]
#
#    def get(self, key, default=None):
#        return self.__dict__.get(key, default)



class ICookbook(object):

    ## for Kitchen

    def find_recipe(self, target):
        pass

    def material_p(self, target):
        pass

    def deault(self):
        pass

    ## for user
    @classmethod
    def new(cls, bookname, properties=None):
        pass

    def load_file(self, filename, properties=None):
        pass

    def load(self, context, bookname='(kook)', properties=None):
        pass

    def register(self, recipe):
        pass

    ## for main
    def default_product(self):
        pass

    def all_properties(self):
        pass



class Cookbook(ICookbook):

    def __init__(self, properties=None):
        if properties is None: properties = {}
        self.bookname = None
        self.properties = properties
        self._propnames_list = []
        self._propnames_dict = {}
        self._loaded_books = {}
        self._decorators = RecipeDecorator(self).to_dict()
        self.specific_task_recipes = []
        self.specific_file_recipes = []
        self.generic_task_recipes  = []
        self.generic_file_recipes  = []
        self._recipes_list = [
            self.specific_task_recipes,
            self.specific_file_recipes,
            self.generic_task_recipes,
            self.generic_file_recipes,
        ]
        self._kookbook_proxy = KookbookProxy(self)
        self.context = self._new_context()

    def register(self, recipe):
        index = 0
        index += recipe.kind == 'file' and 1 or 0
        index += recipe.is_generic()   and 2 or 0
        self._recipes_list[index].append(recipe)

    @classmethod
    def new(cls, bookname, properties={}):
        obj = cls(properties)
        if bookname:
            obj.load_book(bookname)
        return obj

    def prop(self, name, value):
        if name not in self._propnames_dict:
            self._propnames_dict[name] = True
            self._propnames_list.append(name)
        return self.properties.setdefault(name, value)

    def all_properties(self):
        return [ (pname, self.properties.get(pname)) for pname in self._propnames_list ]

    def default_product(self):
        return self.default

    def _get_kook_materials(self, _unused=None):
        return self.materials

    def material_p(self, target):
        return target in self.materials    ## TODO: use dict

    def find_recipe(self, target):
        for recipes in self._recipes_list:      ## TODO: use dict for specific recipes
            for r in recipes:
                if r.match(target):
                    _trace("Cookbook#find_recipe(): target=%r, func=%s, product=%r" % (target, r.name, r.product, ))
                    return r
        return None

    def get_recipe(self, product):
        for recipes in self._recipes_list:
            for r in recipes:
                if r.product == product:
                    return r
        return None

    def _new_context(self):
        context = create_context()        # dict containing commands ('cp', 'rm', 'mkdir', ...)
        context['prop'] = self.prop       # properties are shared with all books
        context.update(self._decorators)  # decorators ('recipe', 'ingreds', ...) are shared
        context['kookbook'] = self._kookbook_proxy
        return context

    def __setup(self, bookname, properties):
        if self.bookname is None:
            self.bookname = bookname
        if properties:
            self.properties.update(properties)

    def load(self, content, bookname='(kook)', properties=None):
        self.__setup(bookname, properties)
        self._load(content, None, True)
        return self

    def load_file(self, filename, properties=None):
        self.__setup(filename, properties)
        filepath = resolve_filepath(filename, 1)
        self.load_book(filepath, True)
        return self

    def load_book(self, filename, content_shared=False):
        if self.bookname is None: self.bookname = filename
        filepath = resolve_filepath(filename, 1)
        return self._load_book(filepath, content_shared)

    def _load_book(self, filepath, content_shared=False):
        if not os.path.isfile(filepath):
            raise kook.utils.ArgumentError("%s: not found." % filepath)
        abspath = os.path.abspath(filepath)
        content = read_file(abspath)
        return self._load_content_with_check(content, filepath, abspath, content_shared)

    def _load_content_with_check(self, content, filepath, key, content_shared):
        book = self._loaded_books.get(key)
        if not book:
            #_debug("load_book(): filepath=%r, abspath=%r" % (filepath, key))
            if key: self._loaded_books[key] = True
            book = self._load(content, filepath, True)
            if key: self._loaded_books[key] = book
        elif book is True:
            _debug("load_book(): filepath=%r: loading recursively." % (filepath, ))
            raise RuntimeError("load_book(): %s: loading recursively." % (filepath, ))
        else:
            #_debug("load_book(): filepath=%r: already loaded." % (filepath, ))
            pass
        return book

    def _load(self, content, filepath, context_shared):
        #
        if not self.context:
            context = self.context = self._new_context()
        elif context_shared:
            context = self.context
        else:
            context = self._new_context(properties)
        context['__file__'] = filepath
        #
        code_obj = compile(content, filepath or "(kook)", "exec")
        exec(code_obj, context, context)
        #
        self._hook_context(context)
        #
        _trace("specific task recipes: %s" % repr(self.specific_task_recipes))
        _trace("generic  task recipes: %s" % repr(self.generic_task_recipes))
        _trace("specific file recipes: %s" % repr(self.specific_file_recipes))
        _trace("generic  file recipes: %s" % repr(self.generic_file_recipes))
        return context

    def _hook_context(self, context):
        ## copy exported values
        if context is not self.context:
            #context['__file__'] = filepath
            if '__export__' in context:
                for k in context['__export__']:
                    self.context[k] = context[k]

    def __get_default(self):
        return self.context.get('kook_default_product')

    def __set_default(self, product):
        self.context['kook_default_product'] = product

    default = property(__get_default, __set_default)


    def __get_materials(self):
        return self.context.setdefault('kook_materials', [])

    def __set_materials(self, materials):
        if not isinstance(materials, (tuple, list)):
            raise KookRecipeError("%r: kook_materials should be tuple or list." % (materials, ))
        self.context['kook_materials'] = materials

    materials = property(__get_materials, __set_materials)



class KookbookProxy(object):

    def __init__(self, cookbook):
        self._book = cookbook

    def __getitem__(self, name):
        return self.find_recipe(name, True)

    def find_recipe(self, product, register=False):
        if not _is_str(product):
            raise TypeError("find_recipe(%r): string expected." % (product,))
        if has_metachars(product):
            raise ValueError("find_recipe(%r): not allowed meta characters." % (product,))
        r = self._book.find_recipe(product)
        if r and r.is_generic():
            r = r._to_specific(product)
            r.desc = None    # clear desc not to show when '-l' or '-L' specified
            if register:
                self._book.register(r)
        return r

    def get_recipe(self, product):
        for recipes in self._book._recipes_list:
            for r in recipes:
                if r.product == product:
                    return r
        return None

    def load(self, filename, context_shared=False):
        filepath = resolve_filepath(filename, 2)
        return self._book.load_book(filepath, context_shared)

    def __get_default(self):
        return self._book.default

    def __set_default(self, product):
        self._book.default = product

    default = property(__get_default, __set_default)


    def __get_materials(self):
        return self._book.materials

    def __set_materials(self, materials):
        self._book.materials = materials

    materials = property(__get_materials, __set_materials)



class Recipe(object):

    __category = None

    def __init__(self, kind=None, product=None, ingreds=None, byprods=None, method=None, desc=None, spices=None):
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
        self.__ingreds = to_list(ingreds)
    ingreds = property(__get_ingreds, __set_ingreds)

    def __get_byprods(self):
        return self.__byprods
    def __set_byprods(self, byprods):
        self.__byprods = to_list(byprods)
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
        self.__spices = to_list(spices)
    spices = property(__get_spices, __set_spices)

    def __get_pattern(self):
        return self.__pattern
    pattern = property(__get_pattern)

    def __get_name(self):
        return self.__name
    name = property(__get_name)

    def __get_category(self):
        return self.__category
    def __set_category(self, category_class):
        self.__category = category_class
    category = property(__get_category, __set_category)

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
        ingreds = getattr(method, '_kook_ingreds', [])
        if ingreds is not None:
            if   isinstance(ingreds, tuple): ingreds = list(ingreds)
            elif isinstance(ingreds, list):  pass
            elif _is_str(ingreds):           ingreds = [ingreds]
            else:
                raise ArgumentError("%r: recipe ingredients should be a list or tuple." % (ingreds,))
        byprods = getattr(method, '_kook_byprods', [])
        spices  = getattr(method, '_kook_spices', [])
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
            return arr
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


_re_pattern_type = type(re.compile('dummy'))


## TODO: define SpecificRecipe and GenericRecipe?


import kook.commands    ## don't move from here!
import kook.misc

_default_context = dict( [ (x, getattr(kook.commands,   x)) for x in kook.commands.__all__ ] +
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
