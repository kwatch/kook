# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import sys, os, re

import kook
from kook.cookbook import Cookbook
from kook import KookError, KookRecipeError, _debug, _report_cmd, _report_msg
from kook.utils import *
import kook.config as config

__all__ = ('Kitchen', 'IfExists', )


class IfExists(object):
    """represents conditional dependency."""
    def __init__(self, material_filename):
        self.filename = material_filename


class Kitchen(object):

    def __init__(self, cookbook=None, **properties):
        self.cookbook = cookbook
        self.properties = properties

    @classmethod
    def new(cls, cookbook, **properties):
        if kook.utils._is_str(cookbook):
            cookbook = Cookbook.new(cookbook)
        return cls(cookbook, **properties)

    def _create_cooking_tree(self, target_product, cookables=None):
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
                for ingred in cookable.ingreds:
                    if isinstance(ingred, IfExists):
                        if not exists(ingred.filename): continue
                    child_cookable = _create(ingred)
                    cookable.children.append(child_cookable)
            return cookable
        _create(target_product)
        root = cookables[target_product]
        return root   # cookable object

    def _create_cooking_trees(self, target_products):
        roots = []
        cookables = {}
        for target in target_products:
            root = self._create_cooking_tree(target, cookables)
            self._check_cooking_tree(root)
            roots.append(root)
        return roots

    def _check_cooking_tree(self, root):
        def _traverse(cooking, route, visited):
            route.append(cooking.product)
            visited[cooking.product] = True
            for child in cooking.children:
                if child.product in visited:
                    pos = route.index(child.product)
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

    def start_cooking(self, *argv):
        #roots = self._create_cooking_trees(targets)
        #for root in roots:
        #    _debug("start_cooking(): root.product=%s, root.ingreds=%s" % (repr(root.product), repr(root.ingreds), ), 2)
        #    assert isinstance(root, Cooking)
        #    root.start()
        ## target
        if argv:
            target = argv[0]
            argv = argv[1:]
        else:
            target = self.cookbook.context.get('kook_default_product')
            target = ':default'
        ##
        roots = self._create_cooking_trees([target])
        root = roots[0]
        assert isinstance(root, Cookable)
        assert root.product == target
        _debug("start_cooking(): root.product=%s, root.ingreds=%s" % (repr(root.product), repr(root.ingreds), ), 2)
        if isinstance(root, Material):
            raise KookError("%s: is a material (= a file to which no recipe matches)." % target)
        #if config.compare_contents:
        #    root.start2(argv=argv, depth=1)
        #else:
        #    root.start(argv=argv, depth=1)
        root.start2(argv=argv, depth=1)


class Cookable(object):

    product = None
    ingreds = ()

    def start(self, depth=1, argv=()):
        raise NotImplementedError("%s.start(): not implemented yet." % self.__class__.__name__)

    def start2(self, depth=1, argv=(), product_timestamp=0):
        raise NotImplementedError("%s.start2(): not implemented yet." % self.__class__.__name__)


CONTENT_CHANGED = 3
MTIME_UPDATED   = 2
NOT_INVOKED     = 1


class Material(Cookable):

    func = None
    ingreds = ()
    byprods = ()
    children = ()
    cooked = None
    is_material = True
    was_file_recipe = True

    def __init__(self, filename):
        self.product = filename

    @classmethod
    def new(cls, filename):
        return cls(filename)

    def start(self, depth=1, argv=()):
        _debug("material %s" % self.product, 1, depth)
        return True

    def start2(self, depth=1, argv=(), parent_mtime=0):
        assert os.path.exists(self.product)
        if   parent_mtime == 0:
            ret, msg = NOT_INVOKED, "material %s"
        elif parent_mtime < os.path.getmtime(self.product):
            ret, msg = CONTENT_CHANGED, "material %s (newer than product)"
        else:
            ret, msg = NOT_INVOKED, "material %s (not newer than product)"
        _debug(msg % self.product, 1, depth)
        self.cooked = ret
        return ret


class Cooking(Cookable):

    is_material = False
    was_file_recipe = None

    def __init__(self, product, func, ingreds=(), byprods=(), spices=()):
        self.product = product
        self.func    = func
        self.ingreds = ingreds
        self.byprods = byprods
        self.ingred  = ingreds and ingreds[0] or None
        self.byprod  = byprods and byprods[0] or None
        self.children = []       # child cookables
        self.spices  = spices
        self.cooked  = None
        self.argv = ()

    @classmethod
    def new(cls, target, recipe):
        ## TODO: generic recipe support
        product = target
        func    = recipe.func
        ingreds = recipe.ingreds or ()
        byprods = recipe.byprods or ()
        spices  = recipe.spices  or ()
        if recipe.pattern:
            ## replace '$(1)', '$(2)', ..., and remove IfExists object which don't exist
            matched = re.match(recipe.pattern, target)
            assert matched is not None
            pat = r'\$\((\d+)\)'
            repl = lambda m: matched.group(int(m.group(1)))
            def convert(items):
                arr = []
                for item in items:
                    if isinstance(item, IfExists):
                        filename = re.sub(pat, repl, item.filename)
                        if os.path.exists(filename):
                            arr.append(filename)
                    else:
                        arr.append(re.sub(pat, repl, item))
                return tuple(arr)
            if ingreds:  ingreds = convert(ingreds)
            if byprods:  byprods = convert(byprods)
            m = (matched.group(), ) + matched.groups()   # tuple
        else:
            matched = None
            m = None
        self = cls(product, func=func, ingreds=ingreds, byprods=byprods, spices=spices)
        self.was_file_recipe = recipe.kind == 'file'
        self.matched = matched
        self.m = m
        return self

    def get_func_name(self):
        return kook.utils._get_codeobj(self.func).co_name

    def _call_func_with(self, argv):
        if self.spices:
            opts, rests = self.parse_cmdopts(argv)
            self.func(self, *rests, **opts)
        else:
            self.func(self, *argv)

    def start(self, depth=1, argv=()):
        if self.cooked:
            _debug("pass %s (already cooked)" % self.product, 1, depth)
            return
        ## exec recipes of ingredients
        _debug("begin %s" % self.product, 1, depth)
        if self.children:
            for child in self.children:
                child.start(depth+1)
        ## skip if product is newer than ingredients
        if self._can_skip():
            _debug("skip %s (func=%s)" % (self.product, self.get_func_name()), 1, depth)
            return
        ## exec recipe function
        assert self.func is not None
        s = self.was_file_recipe and 'create' or 'perform'
        _debug("%s %s (func=%s)" % (s, self.product, self.get_func_name()), 1, depth)
        _report_msg("%s (func=%s)" % (self.product, self.get_func_name()), depth)
        #self.func(self, *argv)
        self._call_func_with(argv)
        if self.was_file_recipe and not os.path.exists(self.product):
            raise KookRecipeError("%s: product not created (in %s())." % (self.product, self.get_func_name(), ))
        self.cooked = True
        _debug("end %s" % self.product, 1, depth)

    def _can_skip(self):
        if config.forced:             return False
        if not self.was_file_recipe:  return False
        if not self.children:         return False
        if not os.path.exists(self.product): return False
        getmtime = os.path.getmtime
        mtime = getmtime(self.product)
        for child in self.children:
            if not child.was_file_recipe:       return False
            assert os.path.exists(child.product)
            if mtime < getmtime(child.product): return False
        return True

    ##
    ## invoke recipe function.
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
    def start2(self, depth=1, argv=(), parent_mtime=0):
        ## return if already cooked
        if self.cooked:
            _debug("pass %s (already cooked)" % self.product, 1, depth)
            return self.cooked
        ## get mtime of product file if it exists
        _debug("begin %s" % self.product, 1, depth)
        if self.was_file_recipe and os.path.exists(self.product):
            product_mtime = os.path.getmtime(self.product)  # exist
        else:
            product_mtime = 0    # product doesn't exist
        ## invoke ingredients' recipes
        child_status = NOT_INVOKED
        if self.children:
            for child in self.children:
                ret = child.start2(depth+1, (), product_mtime)
                assert ret is not None
                if ret > child_status:  child_status = ret
        assert child_status in (CONTENT_CHANGED, MTIME_UPDATED, NOT_INVOKED)
        ## there are some cases to skip recipe invocation (ex. product is newer than ingredients)
        if self._can_skip2():
            if child_status == MTIME_UPDATED:
                assert os.path.exists(self.product)
                _report_msg("%s (func=%s)" % (self.product, self.get_func_name()), depth)
                _debug("touch and skip %s (func=%s)" % (self.product, self.get_func_name()), 1, depth)
                _report_cmd("touch %s   # skipped" % self.product)
                os.utime(self.product, None)    # update mtime of product file to current timestamp
                self.cooked = MTIME_UPDATED
                return MTIME_UPDATED    # skip recipe invocation
            elif child_status == NOT_INVOKED:
                _debug("skip %s (func=%s)" % (self.product, self.get_func_name()), 1, depth)
                self.cooked = NOT_INVOKED
                return NOT_INVOKED          # skip recipe invocation
            else:
                assert child_status == CONTENT_CHANGED
                pass    # don't skip recipe invocation
        ## invoke recipe function
        assert self.func is not None
        try:
            try:
                ## if product file exists, rename it to temporary filename
                if product_mtime:
                    tmp_basename = ".kook.%s.kook" % os.path.basename(self.product)
                    tmp_filename = os.path.join(os.path.dirname(self.product), tmp_basename)
                    os.rename(self.product, tmp_filename)
                ## invoke recipe
                s = self.was_file_recipe and 'create' or 'perform'
                _debug("%s %s (func=%s)" % (s, self.product, self.get_func_name()), 1, depth)
                _report_msg("%s (func=%s)" % (self.product, self.get_func_name()), depth)
                self._call_func_with(argv)
                ## check whether product file created or not
                if self.was_file_recipe and not os.path.exists(self.product):
                    raise KookRecipeError("%s: product not created (in %s())." % (self.product, self.get_func_name(), ))
                ## if new product file is same as old, return MTIME_UPDATED, else return CONTENT_CHANGED
                if config.compare_contents and product_mtime and kook.utils.has_same_content(self.product, tmp_filename):
                    ret, msg = MTIME_UPDATED,   "end %s (content not changed, mtime updated)"
                else:
                    ret, msg = CONTENT_CHANGED, "end %s (content changed)"
                _debug(msg % self.product, 1, depth)
                return ret
            except Exception:
                ex = sys.exc_info()[1]
                ## if product file exists, remove it when error raised
                if product_mtime:
                    _report_msg("(remove %s because unexpected error raised (func=%s))" % (self.product, self.get_func_name()), depth)
                    if os.path.isfile(self.product): os.unlink(self.product)
                raise
        finally:
            if product_mtime: os.unlink(tmp_filename)

    def _can_skip2(self):
        if config.forced:             return False
        if not self.was_file_recipe:  return False
        if not self.children:         return False
        if not os.path.exists(self.product): return False
        #getmtime = os.path.getmtime
        #mtime = getmtime(self.product)
        #for child in self.children:
        #    if not child.was_file_recipe:       return False
        #    assert os.path.exists(child.product)
        #    if mtime < getmtime(child.product): return False
        #        return False
        return True

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
                if name == 'ingreds':  return ' '.join(self.ingreds)
                if name == 'coprods':  return ' '.join(self.coprods)
                if name in frame.f_locals:  return str(frame.f_locals[name])
                if name in frame.f_globals: return str(frame.f_globals[name])
                raise NameError("$(%s): unknown name. (func=%s)" % (name, self.get_func_name(), ))
        return re.sub(r'\$\((\w+)(?:\[(\d+)\])?\)', repl, string)

    ## utility method for convenience
    def parse_cmdopts(self, argv):
        parser = CommandOptionParser.new(self.spices)
        _debug("parse_cmdopts() (func=%s): spices=%s" % (self.get_func_name(), repr(parser.spices)), 2)
        try:
            opts, rests = parser.parse(argv)
            _debug("parse_cmdopts() (func=%s): opts=%s, rests=%s" % (self.get_func_name(), repr(opts), repr(rests)), 2)
            return opts, rests
        except CommandOptionError:
            ex = sys.exc_info()[1]
            raise CommandOptionError("%s(): %s" % (self.get_func_name(), str(ex), ))
