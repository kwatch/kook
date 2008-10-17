# -*- coding: utf-8 -*-

###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###


__all__ = ['Main']


import sys, os, re, random
import kook
from kook import *
from kook import _debug
from kook.cookbook import *
from kook.kitchen import *
from kook.util import *


class Main(object):

    def __init__(self, argv=None):
        if argv is None: argv = sys.argv
        self.command = os.path.basename(argv[0])
        self.args = argv[1:]
        self.stdin  = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    optchars = "hVD?vqcQFf:"

    optdef_strs = (
        "-h:      help",
        #"--help: help",
        "-V:      version",
        "-D[N]:   debug level (default: 1)",
        "-q:      quiet",
        "-f file: kookbook",
        "-F:      forcedly",
        "-l:      list public recipes",
        "-L:      list all recipes",
        "-n:      not invoke (dry run)",
        "--name=value: property name and value",
        "--name:       property name and value(=True)",
    )

    def invoke(self):
        ## parse command-line options
        optparser = CommandOptionParser.new(self.optdef_strs)
        opts, longopts, rests = optparser.parse2(self.args, command=self.command)
        #print "*** debug: command option: opts=%s, longopts=%s, rests=%s" % (repr(opts), repr(longopts), repr(rests))
        ## handle options
        if opts.get('h') or longopts.get('help') is True:
            self.stdout.write("pykook - build tool like Make, Rake, Ant, or Cook\n")
            self.stdout.write(optparser.help())
            return 0
        if opts.get('V'):
            self.stdout.write(geekjob.__RELEASE__ + "\n")
            return 0
        if opts.get('q'):  kook._quiet   = True
        if opts.get('F'):  kook._forced  = True
        if opts.get('D'):
            v = str2int(opts['D'])    # notice that int(True) is 1
            if v is None:
                raise CommandOptionError('-D%s: integer is required.' % opts['D'])
            kook._debug_level = v
        if opts.get('f'):
            arg = opts['f']
            if os.path.isdir(arg):
                raise CommandOptionError("-f %s: not a file." % arg)
            if not os.path.isfile(arg):
                raise CommandOptionError("-f %s: not found." % arg)
        ## cookbook
        bookname = opts.get('f', 'Kookbook.py')
        if not os.path.isfile(bookname):
            raise CommandOptionError("%s: not found." % bookname)
        properties = longopts
        cookbook = Cookbook.new(bookname, properties)
        ## list recipes
        if opts.get('l') or opts.get('L'):
            self._list_recipes(cookbook, opts)
            return 0
        ## start cooking
        kitchen = Kitchen.new(cookbook)
        if not rests:
            default_product = cookbook.default_product()
            if not default_product:
                write = self.stderr.write
                write("*** %s: target is not given\n" % self.command)
                write("*** '%s -l' or '%s -L' show recipes and properties.\n" % (self.command, self.command))
                write("*** (or set 'kook_default_product' in your kookbook.)\n")
                return 1
            rests = [default_product]
        kitchen.start_cooking(*rests)
        ##
        return 0

    def _list_recipes(self, cookbook, opts):
        show_all = opts.get('L')
        format  = "  %-20s: %s\n"
        #format2 = "    %-18s:   %s\n"
        format2 = "    %-20s  %s\n"
        write = self.stdout.write
        ## properties
        write("Properties:\n")
        for prop_name, prop_value in cookbook.all_properties():
            write(format % (prop_name, repr(prop_value)))
        write("\n")
        ## task and file recipes
        tuples = (
            ("Task recipes",
             cookbook.specific_task_recipes + cookbook.generic_task_recipes),
            ("File recipes",
             cookbook.specific_file_recipes + cookbook.generic_file_recipes),
        )
        for title, recipes in tuples:
            write(title + ":\n")
            for recipe in recipes:
                if show_all or recipe.desc:
                    write(format % (recipe.product, recipe.desc or ''))
                    if kook._quiet or not recipe.options: continue
                    optparser = CommandOptionParser.new(recipe.options)
                    for opt, desc in optparser.helps:
                        write(format2 % (opt, desc))
            write("\n")
        ## default product
        default_product = cookbook.context.get('kook_default_product')
        if default_product:
            write("kook_default_product: %s\n" % default_product)
            write("\n")
        ## tips
        if not opts.get('q'):
            tip = self.get_tip(default_product)
            write("(Tips: %s)\n" % tip)
        return 0

    TIPS = (
        "you can set 'kook_default_product' variable in your kookbook.",
        "you can override properties with '--propname=propvalue'.",
        "'@ingreds(\"$(1).c\", if_exists(\"$(1).h\"))' is a friend of C programmer.",
        "'c%\"gcc $(ingreds[0])\"' is more natural than '\"gcc %s\" % c.ingreds[0]'.",
    )

    def get_tip(self, default_product):
        from random import random
        TIPS = self.__class__.TIPS
        index = int(random() * len(TIPS))
        assert index < len(TIPS)
        if default_product:       # if default product is specified,
            if index == 0:        # escape tips about it.
                index = int(random() * len(TIPS)) or 1
        else:                     # if default product is not specified,
            if random() < 0.5:    # show tips about it frequently.
                index = 0
        return TIPS[index]


    def main(self):
        try:
            status = self.invoke()
            sys.exit(status)
        except Exception, ex:
            ## show errors
            ex_classes = (CommandOptionError, )   # or (CommandOptionError, KookError)
            if isinstance(ex, ex_classes):
                self.stderr.write(self.command + ": " + str(ex) + "\n")
            ## kick emacsclient when $E defined
            if os.environ.get('E'):
                import traceback
                s = traceback.format_exc()
                pat = re.compile(r'^  File "(.*)", line (\d+),', re.M)
                tuples = [ (m.group(1), m.group(2)) for m in pat.finditer(s) ]
                tuples.reverse()
                for filename, linenum in tuples:
                    if os.access(filename, os.W_OK):
                        break
                else:
                    filename = linenum = None
                if filename and linenum:
                    kicker_command = "emacsclient -n +%s %s" % (linenum, filename)
                    os.system(kicker_command)
            ## re-raise exception when debug mode
            if not isinstance(ex, ex_classes) or kook._debug_level > 0:
                raise
            sys.exit(1)
