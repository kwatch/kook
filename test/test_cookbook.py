###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re

from kook import KookRecipeError
from kook.cookbook import Cookbook, Recipe
from kook.utils import write_file


bookname = 'Kookbook.py'

class KookCookbookTest(object):

    def setup(self, input):
        write_file(bookname, input)

    def after_each(self):
        if os.path.exists(bookname):
            os.unlink(bookname)


    def test_new(self):
        input = r"""
@recipe
def file_html(c):
  pass
"""[1:]
        self.setup(input)
        ## if bookname is not specified, Kookbook is not loaded
        book = Cookbook.new(None)
        ok (book).is_a(Cookbook)
        ok (book.bookname) == None
        ok (book.specific_file_recipes) == []
        ## if bookname is specified, Kookbook is loaded automatically
        book = Cookbook.new(bookname)
        ok (book).is_a(Cookbook)
        ok (book.bookname) == bookname
        recipes = book.specific_file_recipes
        ok (recipes).is_a(list)
        ok (len(recipes)) == 1
        ok (recipes[0].kind) == 'file'

    def test_load_file(self):
        book = Cookbook.new(None)
        ok (book.bookname) == None
        ok (book.specific_file_recipes) == []
        input = r"""
@recipe
def file_html(c):
    pass
"""[1:]
        self.setup(input)
        ## load Kookbook
        book.load_file(bookname)
        ok (book.bookname) == bookname
        recipes = book.specific_file_recipes
        ok (recipes).is_a(list)
        ok (recipes[0].kind) == 'file'

    def test_load__set_self_bookname(self):
        "set self.bookname"
        input = r"""
@recipe
def compile(c):
  pass
"""[1:]
        ## before loading, bookname is None
        book = Cookbook.new(None)
        ok (book.bookname) == None
        ## after loaded, bookname is specified
        book.load(input, '<kookbook>')
        ok (book.bookname) == '<kookbook>'

    def test_load__task_recipes(self):
        input = r"""
@recipe      # without @product nor prefix
def build(c):
  pass

@recipe      # with 'task_' prefix
def task_build(c):
  pass

@recipe      # with @product
@product('build')
def task_build_files(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input, '<kookbook>')
        recipes = book.specific_task_recipes
        ok (recipes).is_a(list)
        ok (len(recipes)) == 3
        expected = r"""
#<Recipe
  byprods=(),
  desc=None,
  func=<function build>,
  ingreds=(),
  kind='task',
  name='build',
  pattern=None,
  product='build',
  spices=None>
"""[1:-1]
        ok (recipes[0]._inspect()) == expected
        expected = r"""
#<Recipe
  byprods=(),
  desc=None,
  func=<function task_build>,
  ingreds=(),
  kind='task',
  name='task_build',
  pattern=None,
  product='build',
  spices=None>
"""[1:-1]
        ok (recipes[1]._inspect()) == expected
        expected = r"""
#<Recipe
  byprods=(),
  desc=None,
  func=<function task_build_files>,
  ingreds=(),
  kind='task',
  name='task_build_files',
  pattern=None,
  product='build',
  spices=None>
"""[1:-1]
        ok (recipes[2]._inspect()) == expected

    def test_load__file_recipes(self):
        input = r"""
@recipe      # with @product and 'file_' prefix
@product('*.html')
def file_ext_html(c):
  pass

@recipe      # without @product
def file_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        # generic recipe
        ok (book.generic_file_recipes).is_a(list)
        ok (len(book.generic_file_recipes)) == 1
        expected = r"""
#<Recipe
  byprods=(),
  desc=None,
  func=<function file_ext_html>,
  ingreds=(),
  kind='file',
  name='file_ext_html',
  pattern='^(.*?)\\.html$',
  product='*.html',
  spices=None>
"""[1:-1]
        ok (book.generic_file_recipes[0]._inspect()) == expected
        # specific recipe
        ok (book.specific_file_recipes).is_a(list)
        ok (len(book.specific_file_recipes)) == 1
        expected = r"""
#<Recipe
  byprods=(),
  desc=None,
  func=<function file_html>,
  ingreds=(),
  kind='file',
  name='file_html',
  pattern=None,
  product='html',
  spices=None>
"""[1:-1]
        ok (book.specific_file_recipes[0]._inspect()) == expected

    def test_load__error_if_no_prefix_with_product(self):
        input = r"""
@recipe
@product('*.html')
def ext_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        def f():
            book.load(input)
        ok (f).raises(KookRecipeError, "ext_html(): prefix ('file_' or 'task_') required when product is specified.")

    def test_load__re_pattern(self):
        input = r"""
import re
@recipe
@product(re.compile(r'.*\.html'))   # pass rexp
def file_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        recipe = book.generic_file_recipes[0]
        ok (recipe.pattern).is_a(type(re.compile('dummy')))
        ok (recipe.pattern.pattern) == r'.*\.html'

    def test_load__materials(self):
        input = r"""
kook_materials = ('index.html', )
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ok (book.materials) == ('index.html', )
        ## kook_materials should be tuple or list
        input = r"""
kook_materials = ('index.html')
"""[1:]
        book = Cookbook.new(None)
        def f():
            book.load(input)
        errmsg = "'index.html': kook_materials should be tuple or list."
        ok (f).raises(KookRecipeError, errmsg)

    def test_load__category(self):
        input = r"""
class stash(Category):
  @recipe
  def save(c, *args, **kwargs):
    print('save to stash')
  @recipe
  def pop(c):
    print('pop from stash')
  def abort(c):
    print('abort top on stash')
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        recipes = book.specific_task_recipes
        ok (len(recipes)) == 2
        ok (recipes[0].product) == 'stash:save'
        ok (recipes[1].product) == 'stash:pop'

    def test_load__category_recursively(self):
        input = r"""
class db(Category):
  class schema(Category):
    @recipe
    def __index__(c):
      pass
    class migration(Category):
      @recipe
      def up(c):
        pass
      @recipe
      def down(c):
        pass
      def reset(c):
        pass
  @recipe
  def backup(c):
    pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        recipes = book.specific_task_recipes[:]
        ok (len(recipes)) == 4
        recipes.sort(key=lambda r: r.product)
        ok (recipes[0].product) == 'db:backup'
        ok (recipes[1].product) == 'db:schema'
        ok (recipes[2].product) == 'db:schema:migration:down'
        ok (recipes[3].product) == 'db:schema:migration:up'

    def test_material_p(self):
        input = r"""
kook_materials = ('index.html', )
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ok (book.material_p('index.html')) == True
        ok (book.material_p('index.txt')) == False

    def test_find_recipe(self):
        ## for file recipes
        input = r"""
@recipe
@product('*.html')
def file_html(c):
  pass

@recipe
@product('index.html')
def file_index_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ## generic file recipe
        recipe = book.find_recipe('foo.html')
        ok (recipe.kind) == 'file'
        ok (recipe.name) == 'file_html'
        ## specific file recipe
        recipe = book.find_recipe('index.html')
        ok (recipe.kind) == 'file'
        ok (recipe.name) == 'file_index_html'
        ## for task recipe
        input = r"""
@recipe
@product('package_*')
def task_package(c):
  pass

@recipe
def package_123(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ## generic task recipe
        recipe = book.find_recipe('package_100')
        ok (recipe.kind) == 'task'
        ok (recipe.name) == 'task_package'
        ## specific task recipe
        recipe = book.find_recipe('package_123')
        ok (recipe.kind) == 'task'
        ok (recipe.name) == 'package_123'
        ## return None if not found
        ok (book.find_recipe('package123')).is_(None)

    def test_find_recipe__category(self):
        input = r"""
class stash(Category):
  @recipe
  def save(c, *args, **kwargs):
    print('save to stash')
  @recipe
  def pop(c):
    print('pop from stash')
  def abort(c):
    print('abort top on stash')
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        recipe = book.find_recipe('stash:save')
        ok (recipe.kind) == 'task'
        ok (recipe.product) == 'stash:save'
        ok (recipe.name) == 'save'
        recipe = book.find_recipe('stash:pop')
        ok (recipe.kind) == 'task'
        ok (recipe.product) == 'stash:pop'
        ok (recipe.name) == 'pop'
        recipe = book.find_recipe('stash:abort')
        ok (recipe).is_(None)

    def test_find_recipe__category_recursively(self):
        input = r"""
class db(Category):
  class schema(Category):
    @recipe
    def __index__(c):
      pass
    class migration(Category):
      @recipe
      def up(c):
        pass
      @recipe
      def down(c):
        pass
      def reset(c):
        pass
  @recipe
  def backup(c):
    pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        #
        recipe = book.find_recipe('db:schema:migration:down')
        ok (recipe.kind) == 'task'
        ok (recipe.product) == 'db:schema:migration:down'
        #
        recipe = book.find_recipe('db:backup')
        ok (recipe.kind) == 'task'
        ok (recipe.product) == 'db:backup'
        #
        recipe = book.find_recipe('db:schema:migration:reset')
        ok (recipe).is_(None)
        #
        recipe = book.find_recipe('db:schema')
        ok (recipe.kind) == 'task'
        ok (recipe.product) == 'db:schema'


class KookbookProxyTest(object):

    def test_find_recipe(self):

        input = r"""
@recipe("*.html", ["$(1).txt"])
def file_html(c):
  cp(c.ingred, c.product)

r = kookbook.find_recipe("foo.html")
r.ingreds = ["foo.txt", "sidebar.html"]
def file_foo_html(c):
    "create foo.html"
    kookbook.find_recipe('*.html').func(c)
r.func = file_foo_html
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        r = book.find_recipe("foo.html")
        ok (r.ingreds) == ["foo.txt", "sidebar.html"]
        ok (r.desc) == "create foo.html"

        if "product is not a string then raises TypeError.":
            input = r"""
@recipe("*.html", ["$(1).txt"])
def file_html(c):
  cp(c.ingred, c.product)
import re
r = kookbook.find_recipe(re.compile('foo.html'))
"""[1:]
            book = Cookbook.new(None)
            def fn(): book.load(input)
            ok (fn).raises(TypeError)
            ok (str(fn.exception)).matches(r"find_recipe\(.*\): string expected.")

        if "product contains meta character then raises ValueError.":
            input = r"""
@recipe("*.html", ["$(1).txt"])
def file_html(c):
  cp(c.ingred, c.product)
r = kookbook.find_recipe("*.html")
"""[1:]
            book = Cookbook.new(None)
            def fn(): book.load(input)
            ok (fn).raises(ValueError, "find_recipe('*.html'): not allowed meta characters.")


if __name__ == '__main__':
    oktest.run('.*Test$')
