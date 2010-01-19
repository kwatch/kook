# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import os
from kook.utils import flatten
import kook.config as config

__all__ = ('if_exists', 'Category', )


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


class Category(object):
    """Namespace of recipes"""

    _outer = None


###


def _debug(msg, depth=0):
    if config.debug_level >= 1:
        write = config.stdout.write
        write(config.debug_prompt)
        if depth: write('+' * depth + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _trace(msg, depth=0):
    if config.debug_level >= 2:
        write = config.stdout.write
        write(config.debug_prompt)
        if depth: write('+' * depth + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_msg(msg, level=None):
    if not config.quiet:
        write = config.stdout.write
        write(config.message_prompt)
        if level: write('*' * level + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_cmd(cmd):
    if not config.quiet:
        write = config.stdout.write
        write(config.command_prompt)
        write(cmd)
        if cmd[-1] != "\n": write("\n")
