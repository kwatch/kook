============
pyKook REAMD
============

Release::  $Release$


About
-----

pyKook is a smart build tool similar to Make, Rake, And, SCons, or Cook.
Kookbook.py, which is a task definition file for pyKook, is written in Python.
You can write any Python code in Kookbook.py.


*NOTICE* pyKook is under alpha release. Specs and features are subject to
change without notice.


Installation
------------

If you have install easy_install command:

    $ easy_install Kook

Or:
    $ tar xzf Kook-$Release$.tar.gz
    $ cd Kook-$Release$/
    $ sudo python setup.py install


Example
-------

Kookbook.py::

    from __future__ import with_statement

    ## default task
    kookbook.default = 'all'

    ## properties
    release = prop('release', '1.0.0')
    CC      = prop('CC, 'gcc')

    ## file recipe
    @recipe('hello', ['hello.o'])   # product, [ingedients, ...]
    def file_hello(c):
        """build hello command"""
        system(c%"$(CC) -o $(product) $(ingred)")

    ## file recipe
    @recipe('*.o', ['$(1).c', '$(1).h'])  # product, [ingredients, ...]
    def file_ext_o(c):
        """build hello command"""
        system(c%"$(CC) -c $(ingreds[0])")

    ## task recipe
    @recipe                         # or @recipe(None, ['hello'])
    @ingreds('hello')
    def package(c):                 # or task_package(c)
        """create package"""
        base   = "hello-" + release
        pkgdir = "build/" + base
        rm_rf(pkgdir)
	mkdir_p(pkgdir)
        cp('README.txt', 'hello', pkgdir)
        with chdir("build"):
            system(c%"tar czf $(base).tar.gz $(base)")

    ## task recipe
    @recipe                         # or @recipe(None, ['package'])
    @ingreds('package')
    def task_all(c):                # or all(c)
        """build all"""
        pass
    
    ## load 'clean' and 'sweep' recipes
    kookbook.load('@kook/books/clean.py')
    kook_clean_files.append("**/*.o")


Command-line example::

    bash> pykook -l
    Properties:
      release             : '1.0.0'
      CC                  : 'gcc'
    
    Task recipes:
      package             : create package
      all                 : build all
      clean               : remove byproducts
      sweep               : remove products and by-products
    
    File recipes:
      *.o                 : build hello command
    
    kookbook.default: all
    
    (Tips: you can override properties with '--propname=propvalue'.)

    bash> pykook         # or kk
    ### **** hello.o (func=file_ext_o)
    $ gcc -c hello.c
    ### *** hello (func=file_hello)
    $ gcc -o hello hello.o
    ### ** package (func=task_package)
    $ rm -rf build/hello-1.0.0
    $ mkdir -p build/hello-1.0.0
    $ cp README.txt hello build/hello-1.0.0
    $ chdir build
    $ tar czf hello-1.0.0.tar.gz hello-1.0.0
    $ chdir -   # /Users/kwatch/src/kook2/python/tmp/readme
    ### * all (func=task_all)

    bash> pykook clean   # or kk clean
    ### * clean (func=task_clean)
    $ rm -f **/*.o


See 'doc/users-guide.html' for details.


License
-------

$License$


Author
------

makoto kuwata <kwa.atmark.kuwata-lab.com>

$Copyright$
