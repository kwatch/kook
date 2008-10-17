============
pyKook REAMD
============

Release::  $Release$


About
-----

pyKook is a took to controll your tasks such as install, build, or clean.
pyKook is similar to Make, Ant, Rake, or SCons.
Kookbook.py, which is a task definition file for pyKook, is written in Python.
You can write any Python code in Kookbook.py.


Install
-------

    $ git clone git@github.com:kwatch/kook.git
    $ cd kook/python
    $ sudo python setup.py install


Example
-------

Kookbook.py::

    from __future__ import with_statement
    
    kook_default_product = 'all'

    release = prop('release', '1.0.0')

    ## file recipe
    @product('hello')                 # product
    @ingreds('hello.o')               # ingredients
    def file_hello(c):
        """build hello command"""
        system(c%"gcc -o $(product) $(ingred)")

    ## file recipe
    @product('*.o')                   # product
    @ingreds('$(1).c', '$(1).h')      # ingredients
    def file_ext_o(c):
        """build hello command"""
        system(c%"gcc -c $(ingreds[0])")

    ## task recipe
    @ingreds('hello')                 # ingredients
    def task_package(c):              # product name is 'package'
        """create package"""
        base = "hello-" + release
        pkgdir  = "build/" + base
        rm_rf(pkgdir)
	mkdir_p(pkgdir)
        cp('README.txt', 'hello', pkgdir)
        with chdir("build"):
            system(c%"tar czf $(base).tar.gz $(base)")

    ## task recipe
    @ingreds('package')               # ingredients
    def task_all(c):                  # task name is 'all'
        """build all"""
        pass
    
    ## task recipe
    def task_clean(c):
        """remove *.o"""
        rm_f("*.o")


Command-line example::

    bash> pykook -l
    Properties:
      release             : '1.0.0'
    
    Task recipes:
      package             : create package
      all                 : build all
      clean               : remove *.o
    
    File recipes:
      *.o                 : build hello command
    
    kook_default_product: all
    
    (Tips: you can override properties with '--propname=propvalue'.)

    bash> pykook
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

    bash> pykook clean
    ### * clean (func=task_clean)
    $ rm -f *.o


Trouble Shooting
----------------


Q: I got the "*.c: can't find any recipe to produce." error.
A: You may use "*.c" instead of "$(1).c" as @ingreds() argument.

::
    ## Use "$(1).c" instead of "*.c"
    @product("*.o")
    @ingreds("*.c")  #=> KookRecipeError: *.c: can't find any recipe to produce.
    def file_ext_o(c):
        system(c%"gcc -c $(ingred)")


Q: I got the "sh: line 1: ingred: command not found" error.
A: You may forget to add "c%" at the beginning of string.

::
    ## Don't forget to add "c%" if you want to use "$()".
    @product("*.o")
    @ingreds("$(1).c")
    def file_ext_o(c):
        system("gcc -c $(ingred)")
	    #=> KookCommandError: sh: line 1: ingred: command not found" error.



License
-------

$License$


Author
------

makoto kuwata

copyright(c) 2008 kuwata-lab.com all rights reserved.
