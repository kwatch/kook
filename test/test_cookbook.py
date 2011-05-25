###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
from oktest.dummy import dummy_file
import sys, os, re
import shutil

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
        book = Cookbook()
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
        book = Cookbook()
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
        book = Cookbook()
        book.load(input, '<kookbook>')
        recipes = book.specific_task_recipes
        ok (recipes).is_a(list)
        ok (len(recipes)) == 3
        expected = r"""
#<Recipe
  byprods=[],
  desc=None,
  ingreds=[],
  kind='task',
  method=<function build>,
  name='build',
  pattern=None,
  product='build',
  spices=[]>
"""[1:-1]
        ok (recipes[0]._inspect()) == expected
        expected = r"""
#<Recipe
  byprods=[],
  desc=None,
  ingreds=[],
  kind='task',
  method=<function task_build>,
  name='task_build',
  pattern=None,
  product='build',
  spices=[]>
"""[1:-1]
        ok (recipes[1]._inspect()) == expected
        expected = r"""
#<Recipe
  byprods=[],
  desc=None,
  ingreds=[],
  kind='task',
  method=<function task_build_files>,
  name='task_build_files',
  pattern=None,
  product='build',
  spices=[]>
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
        book = Cookbook().load(input)
        # generic recipe
        ok (book.generic_file_recipes).is_a(list)
        ok (len(book.generic_file_recipes)) == 1
        expected = r"""
#<Recipe
  byprods=[],
  desc=None,
  ingreds=[],
  kind='file',
  method=<function file_ext_html>,
  name='file_ext_html',
  pattern='^(.*?)\\.html$',
  product='*.html',
  spices=[]>
"""[1:-1]
        ok (book.generic_file_recipes[0]._inspect()) == expected
        # specific recipe
        ok (book.specific_file_recipes).is_a(list)
        ok (len(book.specific_file_recipes)) == 1
        expected = r"""
#<Recipe
  byprods=[],
  desc=None,
  ingreds=[],
  kind='file',
  method=<function file_html>,
  name='file_html',
  pattern=None,
  product='html',
  spices=[]>
"""[1:-1]
        ok (book.specific_file_recipes[0]._inspect()) == expected

    def test_load__error_if_no_prefix_with_product(self):
        input = r"""
@recipe
@product('*.html')
def ext_html(c):
  pass
"""[1:]
        book = Cookbook()
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
        book = Cookbook().load(input)
        recipe = book.generic_file_recipes[0]
        ok (recipe.pattern).is_a(type(re.compile('dummy')))
        ok (recipe.pattern.pattern) == r'.*\.html'

    def test_load__materials(self):
        input = r"""
kook_materials = ('index.html', )
"""[1:]
        book = Cookbook().load(input)
        ok (book.materials) == ('index.html', )
        ## kook_materials should be tuple or list
        input = r"""
#kook_materials = ('index.html')
kookbook.materials = ('index.html')
"""[1:]
        book = Cookbook()
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
        book = Cookbook().load(input)
        recipes = book.specific_task_recipes
        ok (len(recipes)) == 2
        ok (recipes[0].product) == 'stash:save'
        ok (recipes[1].product) == 'stash:pop'
        ok (recipes[0].category).is_a(type)
        ok (recipes[0].category.__name__) == 'stash'
        ok (recipes[1].category).is_a(type)
        ok (recipes[1].category.__name__) == 'stash'

    def test_load__category_recursively(self):
        input = r"""
class db(Category):
  class schema(Category):
    @recipe
    def default(c):
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
        book = Cookbook().load(input)
        recipes = book.specific_task_recipes[:]
        ok (len(recipes)) == 4
        #recipes.sort(key=lambda r: r.product)
        ok (recipes[0].product) == 'db:schema'
        ok (recipes[1].product) == 'db:schema:migration:up'
        ok (recipes[2].product) == 'db:schema:migration:down'
        ok (recipes[3].product) == 'db:backup'
        ok (recipes[0].category).is_a(type)
        ok (recipes[1].category).is_a(type)
        ok (recipes[2].category).is_a(type)
        ok (recipes[3].category).is_a(type)
        ok (recipes[0].category.__name__) == "schema"
        ok (recipes[1].category.__name__) == "migration"
        ok (recipes[2].category.__name__) == "migration"
        ok (recipes[3].category.__name__) == "db"

    def test_material_p(self):
        input = r"""
kook_materials = ('index.html', )
"""[1:]
        book = Cookbook().load(input)
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
        book = Cookbook().load(input)
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
        book = Cookbook().load(input)
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
        book = Cookbook().load(input)
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
    def default(c):
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
        book = Cookbook().load(input)
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

        if "called then returns matched recipe, converting generic into specific":
            input = r"""
@recipe("*.html", ["$(1).txt"])
def file_html(c):
  cp(c.ingred, c.product)

r = kookbook.find_recipe("foo.html")
assert r.__class__.__name__ == "Recipe"
assert r.is_generic() == False
assert r.product == "foo.html"
assert r.ingreds == ["foo.txt"]
"""[1:]
            book = Cookbook().load(input)
            r = book.find_recipe("foo.html")
            ok (r.is_generic()) == True
            ok (r.product) == "*.html"

        if "generic recipe is converted into specific then desc is cleared.":
            input = r"""
@recipe("*.html", ["$(1).txt"])
def file_html(c):
  '''create html file from text file'''
  cp(c.ingred, c.product)

r = kookbook["foo.html"]
assert r.product == "foo.html"
assert r.desc    == None
assert r.method.__doc__ == 'create html file from text file'
"""[1:]
            book = Cookbook().load(input)
            r = book.find_recipe("foo.html")
            ok (r.desc) == None

        if "2nd argumetn is True then register found recipe automatically.":
            input = r"""
@recipe("*.html", ["$(1).txt"])
def file_html(c):
  cp(c.ingred, c.product)

r = kookbook.find_recipe("foo.html", True)
r.ingreds = ["foo.txt", "sidebar.html"]
def file_foo_html(c):
    "create foo.html"
    kookbook.get_recipe('*.html').method(c)
r.method = file_foo_html
"""[1:]
            book = Cookbook().load(input)
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
            book = Cookbook()
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
            book = Cookbook()
            def fn(): book.load(input)
            ok (fn).raises(ValueError, "find_recipe('*.html'): not allowed meta characters.")

    def test_get_recipe(self):

        if "called then returns recipe, without pattern matching.":
            input = r"""
@recipe("*.html", ["$(1).txt"])
def file_html(c):
  cp(c.ingred, c.product)

#r = kookbook.find_recipe("*.html")   # ValueError
r = kookbook.get_recipe("*.html")
assert r is not None
assert r is file_html._kook_recipe
"""[1:]
            book = Cookbook()
            def fn(): book.load(input)
            ok (fn).not_raise()

    def test_load(self):

        if "called then load recipes in other book.":
            input = r"""
@recipe
def hello(c):
    '''print hello'''
    print("Hello!")

@recipe("*.html", ["$(1).txt"])
def file_html(c):
    '''create *.html from *.txt'''
    cp(c.ingred, c.product)
"""[1:]
            bookname = "_load_test.py"
            input2 = r"""
kookbook.load('""" + bookname + """')
"""
            def func():
                book = Cookbook()
                def fn(): book.load(input2)
                ok (fn).not_raise()
                ## recipes are loaded
                r = book.find_recipe('hello')
                ok (r).is_a(Recipe)
                ok (r.desc) == "print hello"
                r = book.find_recipe('hello.html')
                ok (r).is_a(Recipe)
                ok (r.ingreds) == ["$(1).txt"]
            dummy_file(bookname, input).run(func)

        if "1st character of filepath is '@' then regarded as file's location.":
            input = r"""
@recipe
def hello99(c):
    '''print hello'''
    print("Hello!")
"""[1:]
            input2 = r"""
kookbook.load('@/f1.py')
"""
            try:
                os.mkdir('t.d1')
                os.mkdir('t.d1/d2')
                fname1 = 't.d1/d2/f1.py'
                f = open(fname1, 'w'); f.write(input); f.close()
                fname2 = 't.d1/d2/f2.py'
                f = open(fname2, 'w'); f.write(input2); f.close()
                book = Cookbook.new(fname2)
                r = book.find_recipe('hello99')
                ok (r).is_a(Recipe)
            finally:
                try:
                    shutil.rmtree('t.d1')
                except Exception:
                    pass

        if "filepath starts with '@*/' then search file in parent directly recursively.":
            input = r"""
@recipe
def hello99(c):
    '''print hello'''
    print("Hello!")
"""[1:]
            input2 = r"""
kookbook.load('@*/f1.py')
"""
            try:
                os.mkdir('t.d1')
                os.mkdir('t.d1/d2')
                fname1 = 'f1.py'
                f = open(fname1, 'w'); f.write(input); f.close()
                fname2 = 't.d1/d2/f2.py'
                f = open(fname2, 'w'); f.write(input2); f.close()
                #
                assert os.path.exists('./f1.py')
                assert os.path.exists('t.d1/d2/f2.py')
                #
                book = Cookbook.new(fname2)
                r = book.find_recipe('hello99')
                ok (r).is_a(Recipe)
            finally:
                try:
                    shutil.rmtree('t.d1')
                except Exception:
                    pass

        if "filepath starts with '@@/' then search file in 2-level above directly.":
            input = r"""
@recipe
def hello96(c):
    '''print hello'''
    print("Hello!")
"""[1:]
            input2 = r"""
kookbook.load('@@@/f1.py')
"""
            try:
                os.mkdir('t.d1')
                os.mkdir('t.d1/d2')
                fname1 = 'f1.py'
                f = open(fname1, 'w'); f.write(input); f.close()
                fname2 = 't.d1/d2/f2.py'
                f = open(fname2, 'w'); f.write(input2); f.close()
                #
                assert os.path.exists('./f1.py')
                assert os.path.exists('t.d1/d2/f2.py')
                #
                book = Cookbook.new(fname2)
                r = book.find_recipe('hello96')
                ok (r).is_a(Recipe)
            finally:
                try:
                    shutil.rmtree('t.d1')
                except Exception:
                    pass

        if "kook_default_product and kook_materials are found then copy it into current context.":
            input = r"""
kookbook.default = "foo.html"
kookbook.materials = ['index.html']
"""[1:]
            bookname = "_load_test2.py"
            input2 = r"""
ret = kookbook.load('""" + bookname + """')
assert kookbook.default == "foo.html"
assert kookbook.materials == ['index.html']
"""
            def func():
                book = Cookbook()
                def fn(): book.load(input2)
                ok (fn).not_raise()
            dummy_file(bookname, input).run(func)

        if "property is specified then propagets values.":
            input = r"""
p1 = prop('p1', 10)
p2 = prop('p2', 20)
p3 = prop('p3', 30)
assert p1 == 11      # != 10, because it is set before loading
assert p2 == 25      # != 25, because it is provided by book.load()
assert p3 == 30
"""[1:]
            bookname = "_load_test3.py"
            input2 = r"""
p1 = prop('p1', 11)  # set before loading
assert p1 == 11
p2 = prop('p2', 21)  # set before loading
assert p2 == 25      # != 21, because p2 is specified by book.load()
kookbook.load('""" + bookname + """')
p3 = prop('p3', 31)  # set after loading
assert p3 == 30      # != 31, because it is set after loading
"""
            def func():
                #book = Cookbook.new(None)
                book = Cookbook()
                def fn(): book.load(input2, properties={"p2": 25})   # set property
                ok (fn).not_raise()
            dummy_file(bookname, input).run(func)

        if "__export__ is provided then copy values into current context.":
            input = r"""
__export__ = ('foo', 'bar')
foo = 123
bar = ["AAA"]
"""[1:]
            bookname = "_load_test4.py"
            input2 = r"""
ret = kookbook.load('""" + bookname + """')
assert foo == 123
assert bar == ["AAA"]
"""
            def func():
                book = Cookbook()
                def fn(): book.load(input2)
                #ok (fn).not_raise()
                fn()
            dummy_file(bookname, input).run(func)

        if "loaded successfully then returns context dict of new book.":
            input = r"""
@recipe
def hello1(c):
    print("Hello!")

foo = "AAA"
"""[1:]
            bookname = "_load_test5.py"
            input2 = r"""
ret = kookbook.load('""" + bookname + """')
assert isinstance(ret, dict)
assert 'hello1' in ret
assert 'foo' in ret
assert ret['foo'] == "AAA"
"""
            def func():
                book = Cookbook()
                def fn(): book.load(input2)
                ok (fn).not_raise()
            dummy_file(bookname, input).run(func)

        if "file is arealy loaded then skip to load it.":
            input = r"""
__export__ = ('randval')
import random
randval = random.randint(0, 1000)
"""[1:]
            bookname = "_load_test6.py"
            input3 = r"""
d = kookbook.load('""" + bookname + """')
assert 'randval' in d
randval = d['randval']
d = kookbook.load('""" + bookname + """')
assert randval == d['randval'], "randval=%r, d['randval']=%r" % (randval, d['randval'])
"""
            def func():
                book = Cookbook()
                def fn(): book.load(input3)
                fn()
                ok (fn).not_raise()
            dummy_file(bookname, input).run(func)


    def test_default(self):

        if "accessed then gets or sets 'kook_default_product'.":
            input = r"""
kookbook.default = 'foo.html'
"""[1:]
            book = Cookbook().load(input)
            ok (book.context).contains('kook_default_product')
            ok (book.default_product()) == 'foo.html'
            input = r"""
kook_default_product = 'bar.html'
assert kookbook.default == 'bar.html'
"""[1:]
            book = Cookbook()
            def fn(): book.load(input)
            ok (fn).not_raise()

    def test_materials(self):

        if "accessed then gets or sets 'kook_materials'.":
            input = r"""
kookbook.materials = ['foo.html']
"""[1:]
            book = Cookbook().load(input)
            ok (book.context).contains('kook_materials')
            ok (book._get_kook_materials(book.context)) == ['foo.html']
            input = r"""
kook_materials = ['bar.html']
assert kookbook.materials == ['bar.html']
"""[1:]
            book = Cookbook()
            def fn(): book.load(input)
            ok (fn).not_raise()



if __name__ == '__main__':
    oktest.run('.*Test$')
