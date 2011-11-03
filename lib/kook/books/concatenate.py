# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###


###
### 'concatenate' recipe which concatenates cookbook and pyKook libraries into a file.
###
### Using 'concatenate' recipe, your cookbook can be a stand-alone script
### and user doesn't need to install pyKook.
###
### Example (Kookbook.py)::
###
###    ## load cookbook
###    ## ('@kook' is equivarent to 'os.path.dirname(kook.__file__)')
###    kookbook.load("@kook/books/concatenate.py")
###    #CONCATENATE_MODULES.append(foo.bar.module)  # if you want
###    #CONCATENATE_BOOKS.append('foo/bar/book.py') # if you want
###
### Example (command-line)::
###
###    bash> kk concatenate -o script.rb Kookbook.py
###    bash> python script.rb -h
###

import kook
import kook.utils
import kook.config
import kook.misc
import kook.commands
import kook.decorators
import kook.cookbook
import kook.kitchen
import kook.main

from kook.utils import resolve_filepath

CONCATENATE_MODULES = [
    kook,
    kook.utils,
    kook.config,
    kook.misc,
    kook.commands,
    kook.decorators,
    kook.cookbook,
    kook.kitchen,
    kook.main,
]

CONCATENATE_BOOKS = [
    'kook/books/clean.py',
    'kook/books/all.py',
    'kook/books/concatenate.py',
]

__export__ = ('CONCATENATE_MODULES', 'CONCATENATE_BOOKS')


def _escape(content):
    s = "'''"
    return content.replace("'''", '%s + "%s" + r%s' % (s, s, s))


@recipe
@spices("-o outfile: output filename",
        "[bookname..]")
def concatenate(c, *args, **kwargs):
    """concatenate cookbook and library files into a file"""
    pairs = [ (mod.__name__, mod.__file__.replace('.pyc', '.py'))
               for mod in CONCATENATE_MODULES ]
    buf = []; add = buf.append
    add(r'''#!/usr/bin/env python

###
### concatenated pykook
###

''')
    if args:
        add("_BOOK_CONTENT = r'''")
        for fname in args:
            s = read_file(fname)
            add(_escape(s))
            add("\n")
        add("'''\n")
        add("\n")
        add("\n")
    add("import sys\n")
    add("\n")
    for name, fpath in pairs:
        s = read_file(fpath)
        add("#" * 20 + " " + fpath + "\n")
        add("\n")
        add("%s = type(sys)('%s')\n" % (name, name))
        add("exec(compile(r'''");
        add(_escape(s));
        add("''', '%s', 'exec'), %s.__dict__, %s.__dict__)\n" % (name, name, name))
        add("sys.modules['%s'] = %s\n" % (name, name))
        add("\n")
    for bookname in CONCATENATE_BOOKS:
        fpath = resolve_filepath(bookname)
        s = read_file(fpath)
        add("#" * 20 + " " + fpath + "\n")
        add("\n")
        add("kook.__dict__.setdefault('_BOOK_LIBRARY', {})\n")
        add("kook._BOOK_LIBRARY['%s'] = r'''" % bookname)
        add(_escape(s))
        add("'''\n")
    add("#" * 70 + "\n")
    if args:
        add("\n")
        add("kook._BOOK_CONTENT = _BOOK_CONTENT\n")
        add("\n")
    add(r'''

## dict to store 'kook/books/{clean,all}.py' in memory
kook.__dict__.setdefault('_BOOK_LIBRARY', {})

if __name__ == '__main__':
    import re

    ## monkey patch to load '@kook/books/{clean,all}.py' from memory
    def load(self, filename, context_shared=False):
        m = re.match(r'^@(\w+)', filename)
        if m:
            content = kook._BOOK_LIBRARY.get(filename[1:])
            if content:
                return self._book._load_content_with_check(content, filename, filename, context_shared)
        #return self._orig_load(filename, context_shared)
        filepath = kook.utils.resolve_filepath(filename, 1)
        return self._book.load_book(filepath, context_shared)

    cls = kook.cookbook.KookbookProxy
    cls._orig_load = cls.load
    cls.load = load

    ## use this filename instead of Kookbook.py
    argv = list(sys.argv)
    if getattr(kook, '_BOOK_CONTENT', None):
        argv[1:1] = ['-f', __file__]

    ## start command
    status = kook.main.MainCommand(argv).main()
    sys.exit(status)
''')
    s = "".join(buf)
    if kwargs.get('o'):
        write_file(kwargs.get('o'), s)
    else:
        sys.stdout.write(s)
