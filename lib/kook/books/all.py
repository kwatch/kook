# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###


###
### 'all' task recipe to generate all products.
###
### example::
###
###    ## load cookbook
###    ## ('@kook' is equivarent to 'os.path.dirname(kook.__file__)')
###    kookbook.load('@kook/books/all.py')
###    ## specify products you want to produce
###    kook_all_products.extend(['product1', 'product2'])
###    ## or
###    kookbook['all'].add('product1', 'product2')
###    ## or
###    kookbook['all'].ingreds.extend(['product1', 'product2'])
###


import types
from kook.utils import flatten


__export__ = ('kook_all_products',)


@recipe
def task_all(c):
    """create all products"""
    pass

def add(self, *products):
    kookbook['all'].ingreds.extend(flatten(products))
    return self

r = kookbook['all']
r.add = types.MethodType(add, r)

del r, add

kook_all_products = kookbook['all'].ingreds
