# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###


###
### 'clean' and 'sweep' recipes.
###
### * 'clean' task is intended to remove by-products, such as *.o or *.class.
### * 'sweep' task is intended to remove products and by-products,
###   for example *.war, *.egg, and so on.
###
### example::
###
###    ## load cookbook
###    ## ('@kook' is equivarent to 'os.path.dirname(kook.__file__)')
###    kookbook.load("@kook/books/clean.py")
###    ## specify file patterns to remove
###    CLEAN.extend(["**/*.o", "**/*.class"])   # by-products
###    kook_sweep_files.extend(["*.egg", "*.war"])         # products
###    ## or
###    kookbook['clean'].add("**/*.o", "**/*.class")       # by-products
###    kookbook['sweep'].add("*.egg", "*.war")             # products
###    ## or
###    kookbook['clean'].ingreds.extend(["*.o", "*.class"])
###    kookbook['sweep'].ingreds.extend(["*.egg", "*.war"])
###


import types
from kook.utils import flatten


__export__ = ('CLEAN', 'kook_sweep_files')


CLEAN = []

@recipe
def clean(c):
    """remove by-products"""
    rm_rf(CLEAN)

def add(self, *file_patterns):
    CLEAN.extend(flatten(file_patterns))
    return self

r = kookbook['clean']
r.add = types.MethodType(add, r)

del r, add


kook_sweep_files = []

@recipe
def sweep(c):
    """remove products and by-products"""
    rm_rf(CLEAN)
    rm_rf(kook_sweep_files)

def add(self, *file_patterns):
    kook_sweep_files.extend(flatten(file_patterns))
    return self

r = kookbook['sweep']
r.add = types.MethodType(add, r)

del r, add
