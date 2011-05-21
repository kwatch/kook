# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
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

    def create_cooking_tree(self, target_product, cookables=None):
        """create tree of Cooking and Material. raises error if recipe or material not found."""
        if cookables is None: cookables = {}  # key: product name, value: cookable object
        cookbook = self.cookbook
        def _create(target, parent_product):
            exists = os.path.exists
            if target in cookables:
                return cookables[target]
            cookable = None
            if cookbook.material_p(target):
                if not exists(target):
                    raise KookRecipeError("%s: material not found." % target)
                cookable = Material.new(target)
            else:
                recipe = cookbook.find_recipe(target)
                if   recipe:          cookable = Cooking.new(target, recipe)
                elif exists(target):  cookable = Material.new(target)
                else:
                    if parent_product:
                        raise KookRecipeError("%s: no such recipe nor material (required for %s)." % (target, repr(parent_product)))
                    else:
                        raise KookRecipeError("%s: no such recipe nor material." % target)
            assert cookable is not None
            cookables[target] = cookable
            if cookable.ingreds:
                assert isinstance(cookable, Cooking)
                for ingred in cookable.ingreds:
                    if isinstance(ingred, ConditionalFile):
                        filename = ingred()
                        if not filename: continue
                        ingred = filename
                    #if isinstance(ingred, IfExists):
                    #    if not exists(ingred.filename): continue
                    child_cookable = _create(ingred, target)
                    cookable.children.append(child_cookable)
            return cookable
        _create(target_product, None)
        root = cookables[target_product]
        return root   # cookable object

    def check_cooking_tree(self, root):
        """raise KookRecipeError if tree has a loop."""
        def _traverse(cooking, route, visited):
            route.append(cooking.product)
            visited[cooking.product] = True
            for child in cooking.children:
                # assert isinstance(child, (Material, Cooking))
                if child.product in visited:
                    pos = route.index(child.product)
                    loop = "->".join(route[pos:] + [child.product])
                    raise KookRecipeError("%s: recipe is looped (%s)." % (child.product, loop))
                elif child.children:
                    # assert isinstance(child, Cooking)
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

    def start_cooking(self, *argv):
        ## target
        if argv:
            target = argv[0]
            argv = argv[1:]
        else:
            target = self.cookbook.context.get('kook_default_product')
            if not target:
                raise KookError('Kitchen#start_cooking(): no argv nor no kook_default_product.')
        ## create tree of cookable object
        root = self.create_cooking_tree(target)
        self.check_cooking_tree(root)
        assert isinstance(root, Cookable)
        assert root.product == target
        _trace("start_cooking(): root.product=%s, root.ingreds=%s" % (repr(root.product), repr(root.ingreds), ))
        if isinstance(root, Material):
            raise KookError("%s: is a material (= a file to which no recipe matched)." % target)
        ## start cooking
        root.cook(argv=argv, depth=1)


class Cookable(object):
    """abstract class for Cooking and Material."""

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


class Material(Cookable):
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


class Cooking(Cookable):
    """represens recipe invocation. in other words, Recipe is 'definition', Cooking is 'execution'."""

    def __init__(self, recipe, product=None, ingreds=None, byprods=None, spices=None, matched=None, m=None):
        if product is None: product = recipe.product
        if ingreds is None: ingreds = recipe.ingreds or ()
        if byprods is None: byprods = recipe.byprods or ()
        if spices  is None: spices  = recipe.spices  or ()
        self.recipe  = recipe
        self.product = product
        self.ingreds = ingreds
        self.byprods = byprods
        self.ingred  = ingreds and ingreds[0] or None
        self.byprod  = byprods and byprods[0] or None
        self.matched = matched
        self.m       = m
        self.children = []       # child cookables
        self.spices  = spices
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
        """invoke recipe function."""
        is_file_recipe = self.recipe.kind == 'file'
        ## return if already cooked
        if self.cooked:
            _debug("pass %s (already cooked)" % self.product, depth)
            return self.cooked
        ## get mtime of product file if it exists
        _debug("begin %s" % self.product, depth)
        if is_file_recipe and os.path.exists(self.product):
            product_mtime = os.path.getmtime(self.product)  # exist
        else:
            product_mtime = 0    # product doesn't exist
        ## invoke ingredients' recipes
        child_status = SKIPPED
        if self.children:
            for child in self.children:
                ret = child.cook(depth+1, ())
                assert ret is not None
                if ret > child_status:  child_status = ret
                if product_mtime and ret == SKIPPED and child.has_product_file():
                    assert os.path.exists(child.product)
                    if os.path.getmtime(child.product) > product_mtime:
                        _trace("child file '%s' is newer than product '%s'." % (child.product, self.product), depth)
                        child_status = CHANGED
        assert child_status in (CHANGED, TOUCHED, SKIPPED)
        ## there are some cases to skip recipe invocation (ex. product is newer than ingredients)
        if self._can_skip(child_status, depth):
            assert child_status == TOUCHED or child_status == SKIPPED
            self._skip(child_status, depth)
            self.cooked = child_status
            return child_status
        ## invoke recipe function
        assert self.recipe.func is not None
        try:
            try:
                ## if product file exists, rename it to temporary filename
                if product_mtime:
                    tmp_filename = self._tmp_filename(self.product)
                    os.rename(self.product, tmp_filename)
                ## invoke recipe
                s = is_file_recipe and 'create' or 'perform'
                _debug("%s %s (%s)" % (s, self.product, self._r), depth)
                _report_msg("%s (%s)" % (self.product, self._r), depth)
                self._invoke_recipe_with(argv)
                ## check whether product file created or not
                if is_file_recipe and not config.noexec and not os.path.exists(self.product):
                    raise KookRecipeError("%s: product not created (in %s())." % (self.product, self.recipe.name, ))
                ## if new product file is same as old one, return TOUCHED, else return CHANGED
                if config.compare_contents and product_mtime and kook.utils.has_same_content(self.product, tmp_filename):
                    _debug("end %s (content not changed, mtime updated)" % self.product, depth)
                    self.cooked = TOUCHED
                else:
                    _debug("end %s (content changed)" % self.product, depth)
                    self.cooked = CHANGED
                return self.cooked
            except Exception:
                ## if product file exists, remove it when error raised
                if product_mtime:
                    _report_msg("(remove %s because unexpected error raised (%s))" % (self.product, self._r), depth)
                    if os.path.isfile(self.product): os.unlink(self.product)
                raise
        finally:
            ## remove temporary file
            if product_mtime: os.unlink(tmp_filename)

    def _can_skip(self, child_status, depth):
        if config.forced:
            #_trace("cannot skip: invoked forcedly.", depth)
            return False
        if self.recipe.kind == 'task':
            _trace("cannot skip: task recipe should be invoked in any case.", depth)
            return False
        if not self.children:
            _trace("cannot skip: no children for product '%s'." % self.product, depth)
            return False
        if not os.path.exists(self.product):
            _trace("cannot skip: product '%s' not found." % self.product, depth)
            return False
        ##
        if child_status == CHANGED:
            _trace("cannot skip: there is newer file in children than product '%s'." % self.product, depth)
            return False
        #if child_status == SKIPPED:
        #    timestamp = os.path.getmtime(self.product)
        #    for child in self.children:
        #        if child.has_product_file() and os.path.getmtime(child.product) > timestamp:
        #            _trace("cannot skip: child '%s' is newer than product '%s'." % (child.product, self.product), depth)
        #            return False
        ##
        return True

    def _skip(self, child_status, depth):
        if child_status == TOUCHED:
            assert os.path.exists(self.product)
            _report_msg("%s (%s)" % (self.product, self._r), depth)
            _debug("touch and skip %s (%s)" % (self.product, self._r), depth)
            _report_cmd("touch %s   # skipped" % self.product)
            os.utime(self.product, None)    # update mtime of product file to current timestamp
        elif child_status == SKIPPED:
            _debug("skip %s (%s)" % (self.product, self._r), depth)
        else:
            assert 'unreachable'

    def _tmp_filename(self, filename):
        tmp_basename = ".kook.%s.kook" % os.path.basename(filename)
        tmp_filename = os.path.join(os.path.dirname(filename), tmp_basename)
        return tmp_filename

    def _invoke_recipe_with(self, argv):
        if self.spices:
            opts, rests = self.parse_cmdopts(argv)
            self.recipe.func(self, *rests, **opts)
        else:
            self.recipe.func(self, *argv)

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
