# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import types
from kook.utils import flatten


__export__ = ('kook_clean_files', 'kook_sweep_files')


kook_clean_files = []

@recipe
def clean(c):
    """remove by-products"""
    rm_rf(kook_clean_files)

def add(self, *file_patterns):
    kook_clean_files.extend(flatten(file_patterns))
    return self

r = kookbook['clean']
r.add = types.MethodType(add, r)

del r, add


kook_sweep_files = []

@recipe
def sweep(c):
    """remove products and by-products"""
    rm_rf(kook_clean_files)
    rm_rf(kook_sweep_files)

def add(self, *file_patterns):
    kook_sweep_files.extend(flatten(file_patterns))
    return self

r = kookbook['sweep']
r.add = types.MethodType(add, r)

del r, add
