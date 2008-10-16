# -*- coding: utf-8 -*-

###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

__RELEASE__ = "$Release: 0.0.0 $".split(' ')[1]
__all__ = (
    'KookError', 'KookRecipeError', 'KookCommandError',
    'product', 'ingreds', 'byprods', 'coprods', 'priority', 'options', 'if_exists',
    'Recipe', 'TaskRecipe', 'FileRecipe',
    'Cookbook', 'Kitchen', # 'Cookable', 'Material', 'Cooking', 'create_context',
)

import sys, os, re, types
from kook.util import *


class KookError(StandardError):
    pass


class KookRecipeError(KookError):
    pass


class KookCommandError(KookError):
    pass


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
        raise KookRecipeError("priority requires integer.")  # TODO: change backtrace
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


class IfExists(object):
    """represents conditional dependency."""
    def __init__(self, material_filename):
        self.filename = material_filename


def if_exists(*args):
    """helper function to create IfExists object."""
    #return IfExists(*args)
    return [ IfExists(arg) for arg in flatten(args) ]


_quiet      = False
_forced     = False
_debug_level = 0
_cmd_prompt = '$ '
_msg_prompt = '### '
_dbg_prompt = '*** debug: '
_stdout = sys.stdout
_stderr = sys.stderr


def _debug(msg, level=1, depth=0):
    if _debug_level >= level:
        write = _stderr.write
        write(_dbg_prompt)
        if depth: write('+' * depth + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_msg(msg, level=None):
    if not _quiet:
        write = _stderr.write
        write(_msg_prompt)
        if level: write('*' * level + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_cmd(cmd):
    if not _quiet:
        write = _stderr.write
        write(_cmd_prompt)
        write(cmd)
        if cmd[-1] != "\n": write("\n")


_re_pattern_type = type(re.compile('x'))


import kook.commands    ## don't move from here!

_default_context = dict( (x, getattr(kook.commands, x)) for x in kook.commands.__all__ )
_default_context.update({
    'product': product,
    'ingreds': ingreds,
    'byprods': byprods,
    'coprods': coprods,
    'options': options,
    'if_exists': if_exists,
})


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


class Recipe(object):

    kind = None

    def __init__(self, product=None, ingreds=(), byprods=(), func=None, desc=None, options=None):
        self.product = product
        self.ingreds = ingreds
        self.byprods = byprods
        self.func    = func
        self.desc    = desc
        self.options = options
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
        options = getattr(func, '_kook_options', None)
        func    = func
        desc    = func.__doc__  ## can be empty string
        if desc is None: desc = _default_descs.get(product)
        return _cls(product=product, ingreds=ingreds, byprods=byprods, func=func, desc=desc, options=options)

    def __repr__(self):
        #return "<%s product=%s func=%s>" % (self.__class__.__name__, repr(self.product), self.get_func_name())
        return "<%s:%s:%s>" % (self.__class__.__name__, repr(self.product), self.get_func_name())


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


## TODO: define SpecificRecipe and GenericRecipe instead of TaskRecipe and FileRecipe?


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
            if name == 'materials':
                array = obj
                self.materials = array
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
                    _debug("find_recipe(): target=%s, func=%s, product=%s" % \
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


class Kitchen(object):

    def __init__(self, cookbook=None):
        if isinstance(cookbook, (str, unicode)):
            cookbook = Cookbook.new(cookbook)
        self.cookbook = cookbook

    @classmethod
    def new(cls, cookbook):
        return cls(cookbook)

    def _create_cooking_from(self, target, recipe):
        return Cooking.new(target, recipe)

    def _create_material_from(self, target):
        return Material(target)

    def _create_cooking_tree(self, target, cookings=None):
        if cookings is None: cookings = {}  # key: product name, value: cooking object
        cookbook = self.cookbook
        def _create(_target):
            if _target in cookings:
                return cookings[_target]
            cooking = None
            if cookbook.material_p(_target):
                if not os.path.exists(_target):
                    raise KookRecipeError("%s: material not found." % _target)
                cooking = self._create_material_from(target)
            else:
                recipe = cookbook.find_recipe(_target)
                if recipe:
                    cooking = self._create_cooking_from(_target, recipe)
                elif os.path.exists(_target):
                    cooking = self._create_material_from(_target)
                else:
                    raise KookRecipeError("%s: can't find any recipe to produce." % _target)
            assert cooking is not None
            cookings[_target] = cooking
            if cooking.ingreds:
                for ingred in cooking.ingreds:
                    if isinstance(ingred, IfExists):
                        if not os.path.exists(ingred.filename): continue
                    child_cooking = _create(ingred)
                    cooking.children.append(child_cooking)
            return cooking
        _create(target)
        root = cookings[target]
        return root   # cooking object

    def _create_cooking_trees(self, targets):
        roots = []
        cookings = {}
        for target in targets:
            root = self._create_cooking_tree(target, cookings)
            self._check_cooking_tree(root)
            roots.append(root)
        return roots

    def _check_cooking_tree(self, root):
        def _traverse(cooking, route, visited):
            route.append(cooking.product)
            visited[cooking.product] = True
            for child in cooking.children:
                if child.product in visited:
                    pos = route.find(child.product)
                    loop = "->".join( prod for prod in route[pos:] + [child.product] )
                    raise KookRecipeError("%s: recipe is looped (%s)." % (child.product, loop))
                elif child.children:
                    _traverse(child, route, visited)
            assert len(route) > 0
            prod = route.pop()
            assert prod == cooking.product
            assert prod in visited
            visited.pop(prod)
        #
        if not root.children:
            return
        route = []
        visited = {}
        _traverse(root, route, visited)
        assert len(route) == 0
        assert len(visited) == 0

    def start_cooking(self, *args):
        #roots = self._create_cooking_trees(targets)
        #for root in roots:
        #    _debug("start_cooking(): root.product=%s, root.ingreds=%s" % (repr(root.product), repr(root.ingreds), ), 2)
        #    assert isinstance(root, Cooking)
        #    root.start()
        ## target
        if args:
            target = args[0]
            args = args[1:]
        else:
            target = self.cookbook.context.get('kook_default_product')
            target = ':default'
        ##
        roots = self._create_cooking_trees([target])
        root = roots[0]
        assert isinstance(root, (Cooking, Material))
        assert root.product == target
        _debug("start_cooking(): root.product=%s, root.ingreds=%s" % (repr(root.product), repr(root.ingreds), ), 2)
        if isinstance(root, Material):
            raise KookError("%s: is a material (= a file to which no recipe matches)." % target)
        root.start(args=args, depth=1)


class Cookable(object):

    product = None
    ingreds = ()

    def start(self, depth=1, args=()):
        raise NotImplementedError("%s.start(): not implemented yet." % self.__class__.__name__)


class Material(Cookable):

    func = None
    ingreds = ()
    byprods = ()
    children = ()
    cooked = True
    is_material = True
    was_file_recipe = True

    def __init__(self, filename):
        self.product = filename

    @classmethod
    def new(cls, filename):
        return cls(filename)

    def start(self, depth=1, args=()):
        _debug("material %s" % self.product, 1, depth)
        return True


class Cooking(Cookable):

    is_material = False
    was_file_recipe = None

    def __init__(self, product, func, ingreds=(), byprods=(), options=()):
        self.product = product
        self.func    = func
        self.ingreds = ingreds
        self.byprods = byprods
        self.ingred  = ingreds and ingreds[0] or None
        self.byprod  = byprods and byprods[0] or None
        self.children = []       # child cookables
        self.options = options
        self.cooked  = None
        self.args = ()

    @classmethod
    def new(cls, target, recipe):
        ## TODO: generic recipe support
        product = target
        func    = recipe.func
        ingreds = recipe.ingreds or ()
        byprods = recipe.byprods or ()
        options = recipe.options or ()
        if recipe.pattern:
            matched = re.match(recipe.pattern, target)
            assert matched is not None
            pat = r'\$\((\d+)\)'
            repl = lambda m: matched.group(int(m.group(1)))
            def convert(items):
                arr = []
                for item in items:
                    if isinstance(item, IfExists):
                        item = re.sub(pat, repl, item.filename)
                        if not os.path.exists(item): continue
                    arr.append(re.sub(pat, repl, item))
                return tuple(arr)
            if ingreds:  ingreds = convert(ingreds)
            if byprods:  byprods = convert(byprods)
            m = (matched.group(), ) + matched.groups()   # tuple
        else:
            matched = None
            m = None
        self = cls(product, func=func, ingreds=ingreds, byprods=byprods, options=options)
        self.was_file_recipe = isinstance(recipe, FileRecipe)
        self.matched = matched
        self.m = m
        return self

    def get_func_name(self):
        return self.func.func_code.co_name

    def can_skip(self):
        if _forced:
            return False
        if not self.was_file_recipe:
            return False
        if not self.children:
            return False
        if not os.path.exists(self.product):
            return False
        for child in self.children:
            if not child.was_file_recipe:
                return False
        mtime =  os.stat(self.product)[os.path.stat.ST_MTIME]
        for child in self.children:
            assert os.path.exists(child.product)
            if mtime < os.stat(child.product)[os.path.stat.ST_MTIME]:
                return False
        return True

    def start(self, depth=1, args=()):
        if self.cooked:
            _debug("pass %s (already cooked)" % self.product, 1, depth)
            return
        ## exec recipes of ingredients
        _debug("begin %s" % self.product, 1, depth)
        if self.children:
            for child in self.children:
                child.start(depth+1)
        ## skip if product is newer than ingredients
        if self.can_skip():
            _debug("skip %s (func=%s)" % (self.product, self.get_func_name()), 1, depth)
            return
        ## exec recipe function
        assert self.func is not None
        s = self.was_file_recipe and 'create' or 'perform'
        _debug("%s %s (func=%s)" % (s, self.product, self.get_func_name()), 1, depth)
        _report_msg("%s (func=%s)" % (self.product, self.get_func_name()), depth)
        self.func(self, *args)
        if self.was_file_recipe and not os.path.exists(self.product):
            raise KookRecipeError("%s: product not created (in %s())." % (self.product, self.get_func_name(), ))
        self.cooked = True
        _debug("end %s" % self.product, 1, depth)

    ## utility method for convenience
    def __mod__(self, string):
        frame = sys._getframe(1)
        def repl(m):
            name  = m.group(1)
            index = m.group(2)
            if index:
                index = int(index)
                if name == 'ingreds':  return self.ingreds[index]
                if name == 'byprods':  return self.byprods[index]
                if name == 'product':  return self.product[index]
                if name in frame.f_locals:  return frame.f_locals[name]
                if name in frame.f_globals: return frame.f_globals[name]
                raise NameError("$(%s[%d]): unknown name. (func=%s)" % (name, index, self.get_func_name(), ))
            else:
                if re.match(r'^\d+$', name):
                    if self.matched is None:
                        raise KookRecipeError("$(%s) is specified but %s() is not a generic recipe." % (name, self.get_func_name(), ))
                    return self.matched.group(int(name))
                #elif name in ('product', 'ingreds', 'coprods') : return getattr(self, name)
                #elif name in ('ingred', 'byprod') : return getattr(self, name+'s')[0]
                if name == 'product':  return self.product
                if name == 'ingred':   return self.ingreds[0]
                if name == 'byprod':   return self.byprods[0]
                if name == 'ingreds':  return self.ingreds
                if name == 'coprods':  return self.coprods
                if name in frame.f_locals:  return frame.f_locals[name]
                if name in frame.f_globals: return frame.f_globals[name]
                raise NameError("$(%s): unknown name. (func=%s)" % (name, self.get_func_name(), ))
        return re.sub(r'\$\((\w+)(?:\[(\d+)\])?\)', repl, string)

    ## utility method for convenience
    def parse_args(self, args):
        parser = CommandOptionParser.new(self.options)
        _debug("parse_args() (func=%s): optdefs=%s" % (self.get_func_name(), repr(parser.optdefs)), 2)
        try:
            opts, rests = parser.parse(args)
            _debug("parse_args() (func=%s): opts=%s, rests=%s" % (self.get_func_name(), repr(opts), repr(rests)), 2)
            return opts, rests
        except CommandOptionError, ex:
            raise CommandOptionError("%s(): %s" % (self.get_func_name(), ex.message, ))
