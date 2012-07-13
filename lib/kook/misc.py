# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2012 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import sys, os
from types import FunctionType
from kook.utils import flatten
import kook.config as config

__all__ = ('if_exists', 'Category', )

python3 = sys.version_info[0] == 3


class ConditionalFile(object):

    def __init__(self, filename):
        self.filename = filename

    def __call__(self, filename=None):
        return None


class IfExists(ConditionalFile):

    def __call__(self, filename=None):
        if filename is None: self.filename = filename
        return os.path.exists(filename) and filename or None


def if_exists(*args):
    return [ IfExists(arg) for arg in flatten(args) ]



###

Category = None


class _CategoryMetaClass(type):

    def __new__(cls, name, bases, dct):
        ## convert all instance methods into staticmethods
        for k in dct.keys():
            v = dct[k]
            if isinstance(v, FunctionType):
                dct[k] = staticmethod(v)
        return type.__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        def modify(prefix, outer_cls, d, depth):
            for k in d:
                v = d[k]
                #if isinstance(v, FunctionType):
                if isinstance(v, staticmethod):
                    fn = v.__get__(0)
                    if hasattr(fn, '_kook_recipe'):
                        r = fn._kook_recipe
                        if r.kind == 'task':
                            if r.product == 'default' or r.product == '__index__':
                                r.product = prefix[:-1]
                            else:
                                r.product = prefix + r.product
                        if depth == 0:
                            r.category = outer_cls
                elif isinstance(v, type):
                    if k != '_outer' and Category and issubclass(v, Category):
                        inner_cls = v
                        modify(prefix, inner_cls, inner_cls.__dict__, depth+1)
                        if not inner_cls._outer:
                            inner_cls._outer = outer_cls
        name = dct.get('__name__', name)
        modify(name.split('.')[-1] + ':', cls, dct, 0)


class Category(object):
    """Namespace of recipes"""
    __metaclass__ = _CategoryMetaClass
    _outer = None


if python3:
    exec("""
Category = None
class Category(object, metaclass=_CategoryMetaClass):
    "Namespace of recipes"
    _outer = None
""")


###


def _debug(msg, depth=0):
    if config.debug_level >= 1:
        write = sys.stdout.write
        write(config.debug_prompt)
        if depth: write('+' * depth + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _trace(msg, depth=0):
    if config.debug_level >= 2:
        write = sys.stdout.write
        write(config.debug_prompt)
        if depth: write('+' * depth + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_msg(msg, level=None):
    if not config.quiet:
        write = sys.stdout.write
        write(config.message_prompt)
        if level: write('*' * level + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_cmd(cmd):
    if not config.quiet:
        write = sys.stdout.write
        write(config.command_prompt)
        write(cmd)
        if cmd[-1] != "\n": write("\n")
