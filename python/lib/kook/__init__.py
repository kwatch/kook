# -*- coding: utf-8 -*-

###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

__RELEASE__ = "$Release: 0.0.0 $".split(' ')[1]
__all__ = (
    'KookError', 'KookRecipeError', 'KookCommandError',
    #'product', 'ingreds', 'byprods', 'coprods', 'priority', 'cmdopts', 'if_exists',
    #'Recipe', 'TaskRecipe', 'FileRecipe',
    #'Cookbook', 'Kitchen', # 'Cookable', 'Material', 'Cooking', 'create_context',
)

import sys, os, re, types
from kook.utils import *


class KookError(Exception):  # StandardError is not available in Python 3.0
    pass


class KookRecipeError(KookError):
    pass


class KookCommandError(KookError):
    pass


_quiet      = False
_forced     = False
_debug_level = 0
_cmd_prompt = '$ '
_msg_prompt = '### '
_dbg_prompt = '*** debug: '
_stdout = sys.stdout
_stderr = sys.stderr


def _debug(msg, level=1, depth=0):
    if _debug_level >= level:
        write = _stderr.write
        write(_dbg_prompt)
        if depth: write('+' * depth + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_msg(msg, level=None):
    if not _quiet:
        write = _stderr.write
        write(_msg_prompt)
        if level: write('*' * level + ' ')
        write(msg)
        if msg[-1] != "\n": write("\n")


def _report_cmd(cmd):
    if not _quiet:
        write = _stderr.write
        write(_cmd_prompt)
        write(cmd)
        if cmd[-1] != "\n": write("\n")
