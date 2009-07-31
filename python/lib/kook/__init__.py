# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

__RELEASE__ = "$Release: 0.0.0 $".split(' ')[1]
__all__ = (
    'KookError', 'KookRecipeError', 'KookCommandError',
    #'product', 'ingreds', 'byprods', 'coprods', 'priority', 'spices', 'if_exists',
    #'Recipe', 'TaskRecipe', 'FileRecipe',
    #'Cookbook', 'Kitchen', # 'Cookable', 'Material', 'Cooking', 'create_context',
)

import sys, os, re, types
from kook.utils import *
import kook.config as config


class KookError(Exception):  # StandardError is not available in Python 3.0
    pass


class KookRecipeError(KookError):
    pass


class KookCommandError(KookError):
    pass


def _debug(msg, level=1, depth=0):
    if config.debug_level >= level:
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
