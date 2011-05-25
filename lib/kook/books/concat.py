# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###


###
### 'concat' recipe which concatenates cookbook and pyKook libraries into a file.
###
### Using 'concat' recipe, your cookbook can be a stand-alone script
### and user doesn't need to install pyKook.
###
### Example (Kookbook.py)::
###
###    ## load cookbook
###    ## ('@kook' is equivarent to 'os.path.dirname(kook.__file__)')
###    kookbook.load("@kook/books/concat.py")
###
### Example (command-line)::
###
###    bash> kk concat -o script.rb Kookbook.py
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

kook_modules = [
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


@recipe
@spices("-o outfile: output filename",
        "[bookname..]")
def concat(c, *args, **kwargs):
    """concatenate cookbook and pyKook libraries into a file"""
    pairs = [ (mod.__name__, mod.__file__.replace('.pyc', '.py'))
               for mod in kook_modules ]
    buf = []; add = buf.append
    add("#!/usr/bin/env python\n")
    add("\n")
    add("###\n")
    add("### concatenated pykook\n")
    add("###\n")
    add("\n")
    if args:
        add("_BOOK_CONTENT = r'''")
        for fname in args:
            s = read_file(fname)
            t = "'''"
            s = s.replace("'''", '%s + "%s" + r%s' % (t, t, t))
            add(s)
            add("\n")
        add("'''\n")
        add("\n")
        add("\n")
    add("import sys\n")
    add("\n")
    for name, fpath in pairs:
        source = read_file(fpath)
        add("#" * 20 + " " + fpath + "\n")
        add("\n")
        add("%s = type(sys)('%s')\n" % (name, name))
        add("exec(compile(r'''");
        add(source);
        add("''', '%s', 'exec'), %s.__dict__, %s.__dict__)\n" % (name, name, name))
        add("sys.modules['%s'] = %s\n" % (name, name))
        add("\n")
    add("#" * 70 + "\n")
    add("\n")
    if args:
        add("\n")
        add("kook._BOOK_CONTENT = _BOOK_CONTENT\n")
        add("\n")
    add("status = kook.main.MainCommand(sys.argv).main()\n")
    add("sys.exit(status)\n")
    s = "".join(buf)
    if kwargs.get('o'):
        write_file(kwargs.get('o'), s)
    else:
        sys.stdout.write(s)
