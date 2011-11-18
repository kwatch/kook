# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###


###
### 'clean' and 'clean:all' recipes.
###
### * 'clean' task is intended to remove by-products, such as *.o or *.class.
### * 'clean:all' task is intended to remove products and by-products,
###   for example *.war, *.egg, and so on.
### * 'sweep' task is available for backward compatibility, but not recommended.
###
### example::
###
###    ## load cookbook
###    ## ('@kook' is equivarent to 'os.path.dirname(kook.__file__)')
###    kookbook.load("@kook/books/clean.py")
###    ## add file patterns to remove
###    CLEAN.extend(["**/*.o", "**/*.class"])   # by-products
###    CLEAN_FULL.extend(["*.egg", "*.war"])    # products
###


import types
from kook.utils import flatten


__export__ = ('CLEAN', 'CLEAN_FULL', 'SWEEP')


CLEAN = []
CLEAN_ALL = []
SWEEP = CLEAN_ALL        # for compatibility


class clean(Category):

    @recipe
    def default(c):
        """remove by-products"""
        rm_rf(CLEAN)

    @recipe
    def all(c):
        """remove products and by-products"""
        rm_rf(CLEAN)
        rm_rf(CLEAN_ALL)


@recipe
def sweep(c):
    """same as clean:all (for backward compatibility)"""
    rm_rf(CLEAN)
    rm_rf(SWEEP)
