# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import os
from kook.utils import flatten

__all__ = ('if_exists', )


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
