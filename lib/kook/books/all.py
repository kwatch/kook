# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###


###
### 'all' task recipe to generate all products.
###
### example::
###
###    ## load cookbook
###    ## ('@kook' is equivarent to 'os.path.dirname(kook.__file__)')
###    kookbook.load('@kook/books/all.py')
###    ## add product names you want to produce
###    ALL.extend(['product1', 'product2'])
###


import types
from kook.utils import flatten


__export__ = ('ALL',)


@recipe
def task_all(c):
    """create all products"""
    pass

ALL = kookbook['all'].ingreds

#def add(self, *products):
#    kookbook['all'].ingreds.extend(flatten(products))
#    return self
#
#r = kookbook['all']
#r.add = types.MethodType(add, r)
#
#del r, add
