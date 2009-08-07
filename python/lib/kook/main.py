# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###


__all__ = ('MainObject', 'MainCommand', 'MainApplication')


import sys, os, re
from kook import KookCommandError, KookRecipeError, __RELEASE__
from kook.cookbook import Cookbook
from kook.kitchen import Kitchen
import kook.config as config
from kook.utils import CommandOptionParser, CommandOptionError, read_file, str2int


class MainObject(object):

    def __init__(self, argv=None):
        if argv is None: argv = sys.argv
        self.command = os.path.basename(argv[0])
        self.args = argv[1:]

    def invoke():
        raise NotImplementedError("%s#invoke(): not implemented yet." % self.__class__.__name__)

    def main():
        raise NotImplementedError("%s#main(): not implemented yet." % self.__class__.__name__)

    def _load_property_file(self, filename=None):
        if filename is None:
            filename = config.properties_filename
        props = {}
        if os.path.isfile(filename):
            content = read_file(config.properties_filename)
            #exec content in props, props
            exec(content, props, props)
            for name in list(props.keys()):
                if not re.match(r'[a-zA-Z]', name):
                    del props[name]
        return props


class MainCommand(MainObject):

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
        #"-n:      not invoke (dry run)",
        "--name=value: property name and value",
        "--name:       property name and value(=True)",
    )

    def invoke(self):
        ## parse command-line options
        optparser = CommandOptionParser(self.optdef_strs)
        opts, longopts, rests = optparser.parse2(self.args, command=self.command)
        #print "*** debug: command option: opts=%s, longopts=%s, rests=%s" % (repr(opts), repr(longopts), repr(rests))
        ## handle options
        if opts.get('h') or longopts.get('help') is True:
            config.stdout.write("%s - build tool like Make, Rake, Ant, or Cook\n" % self.command)
            config.stdout.write(optparser.help())
            return 0
        if opts.get('V'):
            config.stdout.write(__RELEASE__ + "\n")
            return 0
        if opts.get('q'):  config.quiet  = True
        if opts.get('F'):  config.forced = True
        if opts.get('D'):
            v = str2int(opts['D'])    # notice that int(True) is 1
            if v is None:
                raise CommandOptionError('-D%s: integer is required.' % opts['D'])
            config.debug_level = v
        if opts.get('f'):
            arg = opts['f']
            if os.path.isdir(arg):
                raise CommandOptionError("-f %s: not a file." % arg)
            if not os.path.isfile(arg):
                raise CommandOptionError("-f %s: not found." % arg)
        ## property file
        props = self._load_property_file()
        if longopts:
            props.update(longopts)
        ## create cookbook
        bookname = opts.get('f', config.cookbook_filename)
        if not os.path.isfile(bookname):
            raise CommandOptionError("%s: not found." % bookname)
        cookbook = Cookbook.new(bookname, props)
        ## list recipes
        if opts.get('l') or opts.get('L'):
            self._list_recipes(cookbook, opts)
            return 0
        ## get default product if no argument
        if not rests:
            default_product = cookbook.default_product()
            if not default_product:
                write = config.stderr.write
                write("*** %s: target is not given\n" % self.command)
                write("*** '%s -l' or '%s -L' show recipes and properties.\n" % (self.command, self.command))
                write("*** (or set 'kook_default_product' in your kookbook.)\n")
                return 1
            rests = [default_product]
        ## start cooking
        kitchen = Kitchen.new(cookbook)
        kitchen.start_cooking(*rests)
        ##
        return 0

    def _list_recipes(self, cookbook, opts):
        show_all = opts.get('L')
        format  = "  %-20s: %s\n"
        #format2 = "    %-18s:   %s\n"
        format2 = "    %-20s  %s\n"
        write = config.stdout.write
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
                    if config.quiet or not recipe.spices: continue
                    optparser = CommandOptionParser(recipe.spices)
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
        "it is able to separate properties into 'Properties.py' file.",
        "try 'kk' command which is shortcat for 'pykook' command.",
        "'@ingreds(\"$(1).c\", if_exists(\"$(1).h\"))' is a friend of C programmer.",
        "'c%\"gcc $(ingred)\"' is more natural than '\"gcc %s\" % c.ingreds[0]'.",
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
            return status
        except Exception:
            ex = sys.exc_info()[1]
            ## show command option error
            ex_classes = (CommandOptionError, KookCommandError, KookRecipeError)   # or (CommandOptionError, KookError)
            if isinstance(ex, ex_classes):
                if not isinstance(ex, CommandOptionError):
                    config.stderr.write("*** ERROR\n")
                config.stderr.write(self.command + ": " + str(ex) + "\n")
            ## system() failed
            if isinstance(ex, KookCommandError):
                #config.stderr.write(self.command + ": " + str(ex) + "\n")
                traceback_obj = sys.exc_info()[2]
                import traceback
                found = False
                bookname = config.cookbook_filename
                for tupl in reversed(traceback.extract_tb(traceback_obj)):
                    filename, linenum, func_name, message = tupl
                    if filename.endswith(bookname):
                        found = True
                        break
                if found:
                    config.stderr.write("%s:%s: %s\n" % (filename, linenum, message))
                else:
                    traceback.print_tb(traceback_obj, file=sys.stderr)
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
            if not isinstance(ex, ex_classes) or config.debug_level > 0:
                raise
            status = 1
            return status


class MainApplication(MainObject):

    def __init__(self, argv=None):
        if argv is None: argv = sys.argv
        #self.command = os.path.basename(argv[0])
        self.command = None
        self.args = argv[1:]

    optdef_strs = (
        "-h:      help",
        #"--help: help",
        #"-V:      version",
        "-D[N]:   debug level (default: 1)",
        #"-q:      quiet",
        #"-f file: kookbook",
        "-F:      forcedly",
        #"-l:      list public recipes",
        #"-L:      list all recipes",
        #"-n:      not invoke (dry run)",
        "-X file:",
        "--name=value: property name and value",
        "--name:       property name and value(=True)",
    )

    def invoke(self):
        quiet = config.quiet
        config.quiet = True
        try:
            self._invoke()
        finally:
            config.quiet = quiet

    def _invoke(self):
        ## parse command-line options
        optparser = CommandOptionParser(self.optdef_strs)
        opts, longopts, rests = optparser.parse2(self.args, command=self.command)
        #print "*** debug: command option: opts=%s, longopts=%s, rests=%s" % (repr(opts), repr(longopts), repr(rests))
        ## handle options
        bookname = opts.get('X')
        if not bookname:
            raise CommandOptionError("-X: script filename required.")
        self.command = os.path.basename(bookname)
        ## property file
        props = self._load_property_file()
        if longopts:
            props.update(longopts)
        ## help
        if opts.get('h') or longopts.get('help') is True:
            target = rests and rests[0] or None
            self._show_help(bookname, props, target=target, optparser=optparser)
            return 0
        ## other options
        #if opts.get('V'):
        #    config.stdout.write(__RELEASE__ + "\n")
        #    return 0
        #if opts.get('q'):  config.quiet  = True
        if opts.get('F'):  config.forced = True
        if opts.get('D'):
            v = str2int(opts['D'])    # notice that int(True) is 1
            if v is None:
                raise CommandOptionError('-D%s: integer is required.' % opts['D'])
            config.debug_level = v
        ## create cookbook
        cookbook = Cookbook.new(bookname, props)
        if not rests:
            default_product = cookbook.default_product()
            if not default_product:
                raise CommandOptionError("sub-command is required (try '-h' to show all sub-commands).")
            rests = [default_product]
        ## start cooking
        kitchen = Kitchen.new(cookbook)
        kitchen.start_cooking(*rests)
        ##
        return 0

    def _show_help(self, bookname, props={}, target=None, optparser=None):
        cookbook = Cookbook.new(bookname, props)
        if target:
            self._show_help_for(cookbook, target)
        else:
            self._show_help_all(cookbook, optparser)

    def _show_help_for(self, cookbook, target):
        recipes = cookbook.specific_task_recipes
        write = config.stdout.write
        lst = [ recipe for recipe in recipes if recipe.product == target ]
        if not lst:
            raise CommandOptionError("%s: sub command not found." % target)
        recipe = lst[0]
        write("%s %s - %s\n" % (self.command, recipe.product, recipe.desc or ''))
        if recipe.spices:
            optparser = CommandOptionParser(recipe.spices)
            for opt, desc in optparser.helps:
                write("  %-20s : %s\n" % (opt, desc))

    def _show_help_all(self, cookbook, optparser):
        recipes = cookbook.specific_task_recipes
        write = config.stdout.write
        desc = cookbook.context.get('kook_desc') or ''
        write("%s - %s\n" % (self.command, desc))
        if False:
            write("\n")
            write("global-options:\n")
            write(optparser.help())
        write("\n")
        write("sub-commands:\n")
        for recipe in recipes:
            if recipe.desc:
                write("  %-15s : %s\n" % (recipe.product, recipe.desc))
        write("\n")
        write("(Type '%s -h subcommand' to show options of sub-commands.)\n" % self.command)

    def main(self):
        try:
            status = self.invoke()
        except CommandOptionError:
            ex = sys.exc_info()[1]
            config.stderr.write(self.command + ": " + str(ex) + "\n")
            status = 1
        return status
