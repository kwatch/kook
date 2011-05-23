# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

###
### Usage (in Kookbook.py):
###
###    kookbook.load_book('@kook/books/all.py')
###    kookbook['all'].add('task1', 'task2')
###    # or
###    # kookbook_all_products.extend(('task1', 'task2'))
###    # or
###    # kookbook['all'].ingreds.extend(('task1', 'task2'))
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
