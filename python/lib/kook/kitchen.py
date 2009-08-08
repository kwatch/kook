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
from kook.misc import ConditionalFile, _debug, _report_cmd, _report_msg

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
        def _create(target):
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
                else: raise KookRecipeError("%s: can't find any recipe to produce." % target)
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
                    child_cookable = _create(ingred)
                    cookable.children.append(child_cookable)
            return cookable
        _create(target_product)
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
        _debug("start_cooking(): root.product=%s, root.ingreds=%s" % (repr(root.product), repr(root.ingreds), ), 2)
        if isinstance(root, Material):
            raise KookError("%s: is a material (= a file to which no recipe matched)." % target)
        ## start cooking
        root.cook(argv=argv, depth=1)


class Cookable(object):
    """abstract class for Cooking and Material."""

    product = None
    ingreds = ()
    children = ()

    def cook(self, depth=1, argv=(), parent_mtime=0):
        raise NotImplementedError("%s.cook(): not implemented yet." % self.__class__.__name__)


CONTENT_CHANGED = 3     # recipe is invoked, and product content is changed when recipe is FileRecipe
MTIME_UPDATED   = 2     # file content of product is not changed (recipe may be invoked or not)
NOT_INVOKED     = 1     # recipe is not invoked (= skipped), for example product is newer than all ingredients


class Material(Cookable):
    """represents material file."""

    def __init__(self, filename):
        self.product = filename

    @classmethod
    def new(cls, filename):
        return cls(filename)

    def cook(self, depth=1, argv=(), parent_mtime=0):
        assert os.path.exists(self.product)
        if   parent_mtime == 0:
            ret, msg = NOT_INVOKED, "material %s"
        elif parent_mtime < os.path.getmtime(self.product):
            ret, msg = CONTENT_CHANGED, "material %s (newer than product)"
        else:
            ret, msg = NOT_INVOKED, "material %s (not newer than product)"
        _debug(msg % self.product, 1, depth)
        #self.cooked = ret
        return ret


class Cooking(Cookable):
    """represens recipe invocation. in other words, Recipe is 'definition', Cooking is 'execution'."""

    def __init__(self, recipe, product=None, ingreds=None, byprods=None, spices=None):
        if product is None: product = recipe.product
        if ingreds is None: ingreds = recipe.ingreds
        if byprods is None: byprods = recipe.byprods
        if spices  is None: spices  = recipe.spices
        self.recipe  = recipe
        self.product = product
        self.ingreds = ingreds
        self.byprods = byprods
        self.ingred  = ingreds and ingreds[0] or None
        self.byprod  = byprods and byprods[0] or None
        self.children = []       # child cookables
        self.spices  = spices
        self.cooked  = None
        self.argv = ()
        self._r = 'recipe=%s' % recipe.name

    @classmethod
    def new(cls, target, recipe):
        product = target
        ingreds = recipe.ingreds or ()
        byprods = recipe.byprods or ()
        spices  = recipe.spices  or ()
        if recipe.pattern:
            ## convert generic recipe into specific values
            matched = re.match(recipe.pattern, target)
            assert matched is not None
            pat = r'\$\((\d+)\)'   # replace '$(1)', '$(2)', ...
            repl = lambda m: matched.group(int(m.group(1)))
            def convert(items):
                arr = []
                for item in items:
                    if isinstance(item, ConditionalFile):
                        filename = re.sub(pat, repl, item.filename)
                        filename = item.__call__(filename)
                        if filename: arr.append(filename)
                    else:
                        arr.append(re.sub(pat, repl, item))
                return tuple(arr)
            if ingreds:  ingreds = convert(ingreds)
            if byprods:  byprods = convert(byprods)
            m = (matched.group(), ) + matched.groups()   # tuple
        else:
            matched = None
            m = None
        self = cls(recipe, product=product, ingreds=ingreds, byprods=byprods, spices=spices)
        self.matched = matched
        self.m = m
        return self

    ##
    ## pseudo-code:
    ##
    ##   if CONENT_CHANGED in self.children:
    ##     invoke recipe
    ##     if new content is same as old:
    ##       return MTIME_UPDATED
    ##     else:
    ##       return CONTENT_CHANGED
    ##   elif MTIME_UPDATED in self.children:
    ##     # not invoke recipe function
    ##     touch product file
    ##     return MTIME_UPDATED
    ##   else:
    ##     # not invoke recipe function
    ##     return NOT_INVOKED
    ##
    def cook(self, depth=1, argv=(), parent_mtime=0):
        """invoke recipe function."""
        is_file_recipe = self.recipe.kind == 'file'
        ## return if already cooked
        if self.cooked:
            _debug("pass %s (already cooked)" % self.product, 1, depth)
            return self.cooked
        ## get mtime of product file if it exists
        _debug("begin %s" % self.product, 1, depth)
        if is_file_recipe and os.path.exists(self.product):
            product_mtime = os.path.getmtime(self.product)  # exist
        else:
            product_mtime = 0    # product doesn't exist
        ## invoke ingredients' recipes
        child_status = NOT_INVOKED
        if self.children:
            for child in self.children:
                ret = child.cook(depth+1, (), product_mtime)
                assert ret is not None
                if ret > child_status:  child_status = ret
        assert child_status in (CONTENT_CHANGED, MTIME_UPDATED, NOT_INVOKED)
        ## there are some cases to skip recipe invocation (ex. product is newer than ingredients)
        if self._can_skip(child_status, depth):
            if child_status == MTIME_UPDATED:
                assert os.path.exists(self.product)
                _report_msg("%s (%s)" % (self.product, self._r), depth)
                _debug("touch and skip %s (%s)" % (self.product, self._r), 1, depth)
                _report_cmd("touch %s   # skipped" % self.product)
                os.utime(self.product, None)    # update mtime of product file to current timestamp
                self.cooked = MTIME_UPDATED
                return MTIME_UPDATED    # skip recipe invocation
            elif child_status == NOT_INVOKED:
                _debug("skip %s (%s)" % (self.product, self._r), 1, depth)
                self.cooked = NOT_INVOKED
                return NOT_INVOKED          # skip recipe invocation
            else:
                assert child_status == CONTENT_CHANGED
                pass    # don't skip recipe invocation
        ## invoke recipe function
        assert self.recipe.func is not None
        try:
            try:
                ## if product file exists, rename it to temporary filename
                if product_mtime:
                    tmp_basename = ".kook.%s.kook" % os.path.basename(self.product)
                    tmp_filename = os.path.join(os.path.dirname(self.product), tmp_basename)
                    os.rename(self.product, tmp_filename)
                ## invoke recipe
                s = is_file_recipe and 'create' or 'perform'
                _debug("%s %s (%s)" % (s, self.product, self._r), 1, depth)
                _report_msg("%s (%s)" % (self.product, self._r), depth)
                self._invoke_recipe_with(argv)
                ## check whether product file created or not
                if is_file_recipe and not os.path.exists(self.product):
                    raise KookRecipeError("%s: product not created (in %s())." % (self.product, self.recipe.name, ))
                ## if new product file is same as old, return MTIME_UPDATED, else return CONTENT_CHANGED
                if config.compare_contents and product_mtime and kook.utils.has_same_content(self.product, tmp_filename):
                    ret, msg = MTIME_UPDATED,   "end %s (content not changed, mtime updated)"
                else:
                    ret, msg = CONTENT_CHANGED, "end %s (content changed)"
                _debug(msg % self.product, 1, depth)
                return ret
            except Exception:
                ## if product file exists, remove it when error raised
                if product_mtime:
                    _report_msg("(remove %s because unexpected error raised (%s))" % (self.product, self._r), depth)
                    if os.path.isfile(self.product): os.unlink(self.product)
                raise
        finally:
            if product_mtime: os.unlink(tmp_filename)

    def _can_skip(self, child_status, depth):
        if config.forced:
            #_debug("cannot skip: invoked forcedly.", 2, depth)
            return False
        if self.recipe.kind == 'task':
            _debug("cannot skip: task recipe should be invoked in any case.", 2, depth)
            return False
        if not self.children:
            _debug("cannot skip: no children for product '%s'." % self.product, 2, depth)
            return False
        if not os.path.exists(self.product):
            _debug("cannot skip: product '%s' not found." % self.product, 2, depth)
            return False
        #
        if child_status == CONTENT_CHANGED:
            _debug("cannot skip: there is newer file in children than product '%s'." % self.product, 2, depth)
            return False
        if child_status == NOT_INVOKED:
            timestamp = os.path.getmtime(self.product)
            for child in self.children:
                child_has_product_file = isinstance(self, Material) or self.recipe.kind == 'file'
                if child_has_product_file and os.path.getmtime(child.product) > timestamp:
                    _debug("cannot skip: child '%s' is newer than product '%s'." % (child.product, self.product), 2, depth)
                    return False
        #
        return True

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
        _debug("parse_cmdopts() (%s): spices=%s" % (self._r, repr(parser.spices)), 2)
        try:
            opts, rests = parser.parse(argv)
            _debug("parse_cmdopts() (%s): opts=%s, rests=%s" % (self._r, repr(opts), repr(rests)), 2)
            return opts, rests
        except kook.utils.CommandOptionError:
            ex = sys.exc_info()[1]
            raise kook.utils.CommandOptionError("%s(): %s" % (self.recipe.name, str(ex), ))
