# -*- coding: utf-8 -*-

###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

import sys, os, re

import kook
from kook.cookbook import *
from kook.cookbook import FileRecipe
#from kook.cookbook import Cookbook, FileRecipe
from kook import KookError, KookRecipeError, _debug, _report_cmd, _report_msg
from kook.utils import *

__all__ = ('Kitchen', 'IfExists', )


class IfExists(object):
    """represents conditional dependency."""
    def __init__(self, material_filename):
        self.filename = material_filename


class Kitchen(object):

    def __init__(self, cookbook=None, **properties):
        if kook.utils._is_str(cookbook):
            cookbook = Cookbook.new(cookbook)
        self.cookbook = cookbook
        self.properties = properties

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
                cooking = self._create_material_from(_target)
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
        if self.properties.get('compare-content') is False:
            root.start(args=args, depth=1)
        else:
            root.start2(args=args, depth=1)


class Cookable(object):

    product = None
    ingreds = ()

    def start(self, depth=1, args=()):
        raise NotImplementedError("%s.start(): not implemented yet." % self.__class__.__name__)


CONTENT_CHANGED = 2
MTIME_UPDATED   = 1
NOTHING         = 0


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

    def start2(self, depth=1, args=(), parent_mtime=0):
        assert os.path.exists(self.product)
        if parent_mtime == 0:
            msg = "material %s"
            ret = -999
        else:
            mtime = os.path.getmtime(self.product)
            if mtime > parent_mtime:
                msg = "material %s (newer than product)"
                ret = CONTENT_CHANGED
            else:
                msg = "material %s (not newer)"
                ret = NOTHING
        _debug(msg % self.product, 1, depth)
        return ret


class Cooking(Cookable):

    is_material = False
    was_file_recipe = None

    def __init__(self, product, func, ingreds=(), byprods=(), cmdopts=()):
        self.product = product
        self.func    = func
        self.ingreds = ingreds
        self.byprods = byprods
        self.ingred  = ingreds and ingreds[0] or None
        self.byprod  = byprods and byprods[0] or None
        self.children = []       # child cookables
        self.cmdopts = cmdopts
        self.cooked  = None
        self.args = ()

    @classmethod
    def new(cls, target, recipe):
        ## TODO: generic recipe support
        product = target
        func    = recipe.func
        ingreds = recipe.ingreds or ()
        byprods = recipe.byprods or ()
        cmdopts = recipe.cmdopts or ()
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
        self = cls(product, func=func, ingreds=ingreds, byprods=byprods, cmdopts=cmdopts)
        self.was_file_recipe = isinstance(recipe, FileRecipe)
        self.matched = matched
        self.m = m
        return self

    def get_func_name(self):
        return kook.utils._get_codeobj(self.func).co_name

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

    def can_skip2(self, status):
        if kook._forced:
            return False
        if not self.was_file_recipe:
            return False
        if not self.children:
            return False
        if not os.path.exists(self.product):
            return False
        #for child in self.children:
        #    if not child.was_file_recipe:
        #        return False
        #mtime =  os.path.getmtime(self.product)
        #for child in self.children:
        #    assert os.path.exists(child.product)
        #    if mtime < os.path.getmtime(child.product)
        #        return False
        if status == CONTENT_CHANGED:
            return False
        assert status <= MTIME_UPDATED
        return True

    def start2(self, depth=1, args=(), parent_mtime=0):
        if self.cooked:
            _debug("pass %s (already cooked)" % self.product, 1, depth)
            return
        ## exec recipes of ingredients
        _debug("begin %s" % self.product, 1, depth)
        if self.was_file_recipe and os.path.exists(self.product):
            product_mtime = os.path.getmtime(self.product)
        else:
            product_mtime = 0
        status = 0
        if self.children:
            for child in self.children:
                ret = child.start2(depth+1, (), product_mtime)
                if ret is not None and ret > status:  status = ret
        ## skip if product is newer than ingredients
        if self.can_skip2(status):
            if status == MTIME_UPDATED:
                assert os.path.exists(self.product)
                _report_msg("%s (func=%s)" % (self.product, self.get_func_name()), depth)
                _debug("touch and skip %s (func=%s)" % (self.product, self.get_func_name()), 1, depth)
                _report_cmd("touch %s   # skipped" % self.product)
                os.utime(self.product, None)
                return MTIME_UPDATED
            else:
                _debug("skip %s (func=%s)" % (self.product, self.get_func_name()), 1, depth)
                return NOTHING
        ## exec recipe function
        assert self.func is not None
        try:
            try:
                if product_mtime:
                    tmp_basename = ".kook.%s.kook" % os.path.basename(self.product)
                    tmp_filename = os.path.join(os.path.dirname(self.product), tmp_basename)
                    os.rename(self.product, tmp_filename)             # rename old product
                s = self.was_file_recipe and 'create' or 'perform'
                _debug("%s %s (func=%s)" % (s, self.product, self.get_func_name()), 1, depth)
                _report_msg("%s (func=%s)" % (self.product, self.get_func_name()), depth)
                self.func(self, *args)
                if self.was_file_recipe and not os.path.exists(self.product):
                    raise KookRecipeError("%s: product not created (in %s())." % (self.product, self.get_func_name(), ))
                self.cooked = True
                if product_mtime and self._has_same_content(self.product, tmp_filename):
                    ret = MTIME_UPDATED
                    msg = "end %s (content not changed, mtime updated)"
                else:
                    ret = CONTENT_CHANGED
                    msg = "end %s (content changed)"
                _debug(msg % self.product, 1, depth)
            except Exception:
                ex = sys.exc_info()[1]
                if product_mtime:
                    _report_msg("(remove %s because unexpected error raised (func=%s))" % (self.product, self.get_func_name()), depth)
                    #_debug("(remove %s because unexpected error raised (func=%s))" % (self.product, self.get_func_name()), 1, depth)
                    if os.path.isfile(self.product):
                        os.unlink(self.product)
                raise
        finally:
            if product_mtime:
                os.unlink(tmp_filename)                           # remove old product
        return ret

    def _has_same_content(self, filename1, filename2):
        assert os.path.exists(filename1)
        assert os.path.exists(filename2)
        if os.path.getsize(filename1) != os.path.getsize(filename2):
            return False
        return read_file(filename1) == read_file(filename2)    ## TODO: tuning memory size

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
                if name in frame.f_locals:  return frame.f_locals[name]
                if name in frame.f_globals: return frame.f_globals[name]
                raise NameError("$(%s): unknown name. (func=%s)" % (name, self.get_func_name(), ))
        return re.sub(r'\$\((\w+)(?:\[(\d+)\])?\)', repl, string)

    ## utility method for convenience
    def parse_cmdopts(self, args):
        parser = CommandOptionParser.new(self.cmdopts)
        _debug("parse_cmdopts() (func=%s): optdefs=%s" % (self.get_func_name(), repr(parser.optdefs)), 2)
        try:
            opts, rests = parser.parse(args)
            _debug("parse_cmdopts() (func=%s): opts=%s, rests=%s" % (self.get_func_name(), repr(opts), repr(rests)), 2)
            return opts, rests
        except CommandOptionError:
            ex = sys.exc_info()[1]
            raise CommandOptionError("%s(): %s" % (self.get_func_name(), str(ex), ))
