###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import oktest
from oktest import *

import kook.misc
from kook.misc import *
from kook.decorators import RecipeDecorator
_d = RecipeDecorator().to_dict()
recipe  = _d['recipe']

import _testhelper


class KookMiscTest(object):

    def test_if_exists(self):
        ret = if_exists('foo.h', '*.h')
        ok (ret).is_a(list)
        ok (len(ret)) == 2
        ok (ret[0]).is_a(kook.misc.IfExists)
        ok (ret[1]).is_a(kook.misc.IfExists)
        ok (ret[0].filename) == 'foo.h'
        ok (ret[1].filename) == '*.h'


class _git(Category):

    @recipe
    def status(c, *args, **kwargs):
        pass
    def stash(c, *args, **kwargs):
        pass

    class branch(Category):
        @recipe
        def new(c):
            pass
        def rm(c):
            pass


class KookCategoryTest(object):

    @test("converts all instance methods into staticmethods.")
    def _(self):
        ok (_git.__dict__['status']).is_a(staticmethod)   # recipe
        ok (_git.__dict__['stash']).is_a(staticmethod)    # not recipe
        ok (_git.branch.__dict__['new']).is_a(staticmethod)   # recipe
        ok (_git.branch.__dict__['rm']).is_a(staticmethod)    # not recipe
        from types import FunctionType
        ok (_git.status).is_a(FunctionType)   # recipe
        ok (_git.stash).is_a(FunctionType)    # not recipe
        ok (_git.branch.new).is_a(FunctionType)   # recipe
        ok (_git.branch.rm).is_a(FunctionType)    # not recipe

    @test("add category name into recipe's product name as prefix.")
    def _(self):
        ok (_git.status._kook_recipe.product) == "_git:status"
        ok (_git.branch.new._kook_recipe.product) == "_git:branch:new"


if __name__ == '__main__':
    oktest.main()
