# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import sys, os, re

from kook.cookbook import Cookbook
from kook import KookError, KookRecipeError
import kook.utils
import kook.config as config
from kook.misc import ConditionalFile, _debug, _trace, _report_cmd, _report_msg

__all__ = ('Kitchen', )


class Kitchen(object):
    """read recipes from cookbook, create cooking objects for recipes, and invoke them.
    ex.
      cookbook = Cookbook.new('Kookbook.py')
      kitchen = Kitchen.new(cookbook)
      argv = ['hello.o', '-h', '-v']
      kitchen.start_cooking(*argv)    # recipe is invoked and 'hello.o' will be created
    """

    def __init__(self, cookbook=None, **properties):
        self.cookbook = cookbook
        self.properties = properties

    @classmethod
    def new(cls, cookbook, **properties):
        if kook.utils._is_str(cookbook):
            cookbook = Cookbook.new(cookbook)
        return cls(cookbook, **properties)

    def start_cooking(self, *argv):
        ## target
        if argv:
            target = argv[0]
            argv = argv[1:]
        else:
            target = self.cookbook.context.get('kook_default_product')
            if not target:
                raise KookError('Kitchen#start_cooking(): no argv nor no kook_default_product.')
        ## create tree of cooking object
        tree = CookingTree(self.cookbook).build(target)
        tree.verify()
        root = tree.root
        assert tree.root.product == target
        tree.start_cooking(argv)


class CookingTree(object):
    """tree of cooking objects"""

    def __init__(self, cookbook):
        self.cookbook = cookbook
        self.root = None

    def build(self, target_product, cookings=None):
        """create tree of RecipeCooking and MaterialCooking. raises error if recipe or material not found."""
        if cookings is None: cookings = {}  # key: product name, value: cooking object
        cookbook = self.cookbook
        def _create(target, parent_product):
            exists = os.path.exists
            if target in cookings:
                return cookings[target]
            cooking = None
            if cookbook.material_p(target):
                if not exists(target):
                    raise KookRecipeError("%s: material not found." % target)
                cooking = MaterialCooking.new(target)
            else:
                recipe = cookbook.find_recipe(target)
                if   recipe:          cooking = RecipeCooking.new(target, recipe)
                elif exists(target):  cooking = MaterialCooking.new(target)
                else:
                    if parent_product:
                        raise KookRecipeError("%s: no such recipe nor material (required for %s)." % (target, repr(parent_product)))
                    else:
                        raise KookRecipeError("%s: no such recipe nor material." % target)
            assert cooking is not None
            cookings[target] = cooking
            if cooking.ingreds:
                assert isinstance(cooking, RecipeCooking)
                for ingred in cooking.ingreds:
                    if isinstance(ingred, ConditionalFile):
                        filename = ingred()
                        if not filename: continue
                        ingred = filename
                    #if isinstance(ingred, IfExists):
                    #    if not exists(ingred.filename): continue
                    child_cooking = _create(ingred, target)
                    cooking.children.append(child_cooking)
            return cooking
        _create(target_product, None)
        self.root = cookings[target_product]
        assert self.root.product == target_product
        return self

    def verify(self):
        """raise KookRecipeError if tree has a loop."""
        def _traverse(cooking, route, visited):
            route.append(cooking.product)
            visited[cooking.product] = True
            for child in cooking.children:
                # assert isinstance(child, (MaterialCooking, RecipeCooking))
                if child.product in visited:
                    pos = route.index(child.product)
                    loop = "->".join(route[pos:] + [child.product])
                    raise KookRecipeError("%s: recipe is looped (%s)." % (child.product, loop))
                elif child.children:
                    # assert isinstance(child, RecipeCooking)
                    _traverse(child, route, visited)
            assert len(route) > 0
            prod = route.pop()
            assert prod == cooking.product
            assert prod in visited
            visited.pop(prod)
        #
        if not self.root.children:
            return
        route = []
        visited = {}
        _traverse(self.root, route, visited)
        assert len(route) == 0
        assert len(visited) == 0

    def start_cooking(self, argv=()):
        _trace("start_cooking(): root.product=%s, root.ingreds=%s" % (repr(self.root.product), repr(self.root.ingreds), ))
        if isinstance(self.root, MaterialCooking):
            raise KookError("%s: is a material (= a file to which no recipe matched)." % self.root.product)
        self.root.cook(argv=argv, depth=1)


class Cooking(object):
    """abstract class for RecipeCooking and MaterialCooking."""

    product = None
    ingreds = ()
    children = ()

    def cook(self, depth=1, argv=()):
        raise NotImplementedError("%s.cook(): not implemented yet." % self.__class__.__name__)

    def has_product_file(self):
        raise NotImplementedError("%s.has_product_file(): not implemented yet." % self.__class__.__name__)


CHANGED = 3     # recipe is invoked, and product content is changed when recipe is FileRecipe
TOUCHED = 2     # file content of product is not changed (recipe may be invoked or not)
SKIPPED = 1     # recipe is not invoked (= skipped), for example product is newer than all ingredients


class MaterialCooking(Cooking):
    """represents material file."""

    def __init__(self, filename):
        self.product = filename

    @classmethod
    def new(cls, filename):
        return cls(filename)

    def cook(self, depth=1, argv=()):
        assert os.path.exists(self.product)
        _debug("material %s" % self.product, depth)
        return SKIPPED

    def has_product_file(self):
        return True


class RecipeCooking(Cooking):
    """represens recipe invocation. in other words, Recipe is 'definition', RecipeCooking is 'execution'."""

    def __init__(self, recipe, product=None, ingreds=None, byprods=None, spices=None, remotes=None, matched=None, m=None):
        if product is None: product = recipe.product
        if ingreds is None: ingreds = recipe.ingreds or ()
        if byprods is None: byprods = recipe.byprods or ()
        if spices  is None: spices  = recipe.spices  or ()
        if remotes is None: remotes = recipe.remotes or ()
        self.recipe  = recipe
        self.product = product
        self.ingreds = ingreds
        self.byprods = byprods
        self.ingred  = ingreds and ingreds[0] or None
        self.byprod  = byprods and byprods[0] or None
        self.matched = matched
        self.m       = m
        self.children = []       # child cookings
        self.spices  = spices
        self.remotes = remotes
        self.cooked  = None
        self.argv = ()
        self._r = 'recipe=%s' % recipe.name

    @classmethod
    def new(cls, target, recipe):
        product = target
        matched = m = None
        if recipe.is_generic():
            recipe  = recipe._to_specific(product)
            matched = recipe._matched
            m = recipe._m
        ingreds = recipe.ingreds or ()
        byprods = recipe.byprods or ()
        spices  = recipe.spices  or ()
        self = cls(recipe, product=product, matched=matched, m=m)
        return self

    def has_product_file(self):
        return self.recipe.kind == "file"

    ##
    ## pseudo-code:
    ##
    ##   if CONENT_CHANGED in self.children:
    ##     invoke recipe
    ##     if new content is same as old:
    ##       return TOUCHED
    ##     else:
    ##       return CHANGED
    ##   elif TOUCHED in self.children:
    ##     # not invoke recipe function
    ##     touch product file
    ##     return TOUCHED
    ##   else:
    ##     # not invoke recipe function
    ##     return SKIPPED
    ##
    def cook(self, depth=1, argv=()):
        """invoke recipe method."""
        ## return if already cooked
        if self.cooked:
            _debug("pass %s (already cooked)" % self.product, depth)
            return self.cooked
        ##
        if self.recipe.kind == 'task':
            return self._cook_task_recipe(depth, argv)
        else:
            return self._cook_file_recipe(depth, argv)

    def _cook_task_recipe(self, depth, argv):
        product = self.product
        _debug("begin %s" % product, depth)
        ## invoke ingredients' recipes
        if self.children:
            for child in self.children:
                child.cook(depth+1, ())
        ## invoke recipe
        _trace("cannot skip: task recipe should be invoked in any case.", depth)
        assert self.recipe.method is not None
        _debug("perform %s (%s)" % (product, self._r), depth)
        _report_msg("%s (%s)" % (product, self._r), depth)
        self._invoke_recipe_with(argv)
        _debug("end %s (content changed)" % product, depth)
        self.cooked = CHANGED
        return self.cooked

    def _cook_file_recipe(self, depth, argv):
        product = self.product
        _debug("begin %s" % product, depth)
        ## get mtime of product file if it exists
        product_mtime = os.path.exists(product) and os.path.getmtime(product) or 0
        ## invoke ingredients' recipes
        child_status = self._cook_children(product_mtime, depth)
        assert child_status in (CHANGED, TOUCHED, SKIPPED)
        ## there are some cases to skip recipe invocation (ex. product is newer than ingredients)
        if self._can_skip(child_status, depth):
            assert child_status == TOUCHED or child_status == SKIPPED
            self._skip(child_status, depth)
            self.cooked = child_status
            return child_status
        ## invoke recipe function
        assert self.recipe.method is not None
        try:
            try:
                ## if product file exists, rename it to temporary filename
                if product_mtime:
                    tmp_filename = self._tmp_filename(product)
                    os.rename(product, tmp_filename)
                ## invoke recipe
                _debug("create %s (%s)" % (product, self._r), depth)
                _report_msg("%s (%s)" % (product, self._r), depth)
                self._invoke_recipe_with(argv)
                ## check whether product file created or not
                if not config.noexec and not os.path.exists(product):
                    raise KookRecipeError("%s: product not created (in %s())." % (product, self.recipe.name, ))
                ## if new product file is same as old one, return TOUCHED, else return CHANGED
                if product_mtime and self._same_content(product, tmp_filename):
                    _debug("end %s (content not changed, mtime updated)" % product, depth)
                    self.cooked = TOUCHED
                else:
                    _debug("end %s (content changed)" % product, depth)
                    self.cooked = CHANGED
                return self.cooked
            except Exception:
                ## if product file exists, remove it when error raised
                if product_mtime:
                    _report_msg("(remove %s because unexpected error raised (%s))" % (product, self._r), depth)
                    if os.path.isfile(product): os.unlink(product)
                raise
        finally:
            ## remove temporary file
            if product_mtime: os.unlink(tmp_filename)

    def _cook_children(self, product_mtime, depth):
        flag_changed = flag_touched = False
        if self.children:
            for child in self.children:
                status = child.cook(depth+1, ())
                assert status in (CHANGED, TOUCHED, SKIPPED)
                if   status == CHANGED: flag_changed = True
                elif status == TOUCHED: flag_touched = True
                if product_mtime and status == SKIPPED and child.has_product_file():
                    assert os.path.exists(child.product)
                    if os.path.getmtime(child.product) > product_mtime:
                        _trace("child file '%s' is newer than product '%s'." % (child.product, self.product), depth)
                        flag_changed = True
        if flag_changed: return CHANGED
        if flag_touched: return TOUCHED
        return SKIPPED

    def _can_skip(self, child_status, depth):
        product = self.product
        if config.forced:
            #_trace("cannot skip: invoked forcedly.", depth)
            return False
        if not self.children:
            _trace("cannot skip: no children for product '%s'." % product, depth)
            return False
        if not os.path.exists(product):
            _trace("cannot skip: product '%s' not found." % product, depth)
            return False
        ##
        if child_status == CHANGED:
            _trace("cannot skip: there is newer file in children than product '%s'." % product, depth)
            return False
        #if child_status == SKIPPED:
        #    timestamp = os.path.getmtime(product)
        #    for child in self.children:
        #        if child.has_product_file() and os.path.getmtime(child.product) > timestamp:
        #            _trace("cannot skip: child '%s' is newer than product '%s'." % (child.product, product), depth)
        #            return False
        ##
        return True

    def _skip(self, child_status, depth):
        product = self.product
        if child_status == TOUCHED:
            assert os.path.exists(product)
            _report_msg("%s (%s)" % (product, self._r), depth)
            _debug("touch and skip %s (%s)" % (product, self._r), depth)
            _report_cmd("touch %s   # skipped" % product)
            os.utime(product, None)    # update mtime of product file to current timestamp
        elif child_status == SKIPPED:
            _debug("skip %s (%s)" % (product, self._r), depth)
        else:
            assert 'unreachable'

    def _tmp_filename(self, filename):
        tmp_basename = ".kook.%s.kook" % os.path.basename(filename)
        tmp_filename = os.path.join(os.path.dirname(filename), tmp_basename)
        return tmp_filename

    def _invoke_recipe_with(self, argv):
        if self.spices:
            opts, rests = self.parse_cmdopts(argv)
            args, kwargs = rests, opts
        else:
            args, kwargs = argv, {}
        if not self.remotes:
            self.recipe.method(self, *args, **kwargs)
        #elif hasattr(self, 'session'):
        #    self.recipe.method(self, *args, **kwargs)
        else:
            for remote in self.remotes:
                remote._invoke(self.recipe.method, self, args, kwargs)

    def _same_content(self, product, tmp_filename):
        return config.compare_contents and kook.utils.has_same_content(product, tmp_filename)

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
                raise NameError("$(%s[%d]): unknown name. (%s)" % (name, index, self._r, ))
            else:
                if re.match(r'^\d+$', name):
                    if self.matched is None:
                        raise KookRecipeError("$(%s) is specified but %s() is not a generic recipe." % (name, self.recipe.name, ))
                    return self.matched.group(int(name))
                #elif name in ('product', 'ingreds', 'coprods') : return getattr(self, name)
                #elif name in ('ingred', 'byprod') : return getattr(self, name+'s')[0]
                if name == 'product':  return self.product
                if name == 'ingred':   return self.ingreds[0]
                if name == 'byprod':   return self.byprods[0]
                if name == 'ingreds':  return ' '.join(self.ingreds)
                #if name == 'coprods':  return ' '.join(self.coprods)
                if name in frame.f_locals:  return str(frame.f_locals[name])
                if name in frame.f_globals: return str(frame.f_globals[name])
                raise NameError("$(%s): unknown name. (%s)" % (name, self._r, ))
        return re.sub(r'\$\((\w+)(?:\[(\d+)\])?\)', repl, string)

    ## utility method for convenience
    def parse_cmdopts(self, argv):
        parser = config.cmdopt_parser_class(self.spices)
        _trace("parse_cmdopts() (%s): spices=%s" % (self._r, repr(parser.spices)))
        try:
            opts, rests = parser.parse(argv)
            _trace("parse_cmdopts() (%s): opts=%s, rests=%s" % (self._r, repr(opts), repr(rests)))
            return opts, rests
        except kook.utils.CommandOptionError:
            ex = sys.exc_info()[1]
            raise kook.utils.CommandOptionError("%s(): %s" % (self.recipe.name, str(ex), ))
