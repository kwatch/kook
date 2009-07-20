# -*- coding: utf-8 -*-

###
### $Rev$
### $Release: $
### $Copyright$
### $License$
###

import sys, os, re
from glob import glob

if sys.version_info[0] == 2:
    python2 = True
    python3 = False
elif sys.version_info[0] == 3:
    python2 = False
    python3 = True


class ArgumentError(Exception):

    def __init__(self, *args):
        Exception.__init__(self, *args)


def str2int(s):
    try:
        return int(s)
    except ValueError:
        return None


if python2:
    def read_file(filename, encoding=None):
        f = content = None
        try:
            if encoding:
                f = open(filename, 'rb+')
                content = f.read().decode(kwargs['encoding'])
            else:
                f = open(filename, 'r+')
                content = f.read()
        finally:
            if f:
                f.close()
        return content

elif python3:
    def read_file(filename, encoding=None):
        f = content = None
        try:
            if encoding:
                f = open(filename, 'r+', encoding=encoding)
                content = f.read()
            else:
                f = open(filename, 'r+', encoding='utf-8')
                #f = open(filename, 'r+')
                content = f.read()
        finally:
            if f:
                f.close()
        return content
 

if python2:
    def write_file(filename, content, encoding=None):
        if encoding and isinstance(content, unicode):
            content = content.encode(encoding)
        f = open(filename, 'w')
        try:
            f.write(content)
        finally:
            f.close()

elif python3:
    def write_file(filename, content, encoding='utf-8'):
        if encoding is None: encoding = 'utf-8'
        f = open(filename, 'w', encoding=encoding)
        try:
            f.write(content)
        finally:
            f.close()


def flatten(items, _arr=None):
    """flatten nested list or tuple."""
    if _arr is None: _arr = []
    for item in items:
        if isinstance(item, (list, tuple)):
            flatten(item, _arr)
        else:
            _arr.append(item)
    return _arr


def has_metachars(string):
    """detect whether string has meta characers ('*', '?', '{') or not."""
    ## TODO: implement correctly
    if string.find('*') < 0 and string.find('?') < 0 and string.find('{') < 0:
        return False
    return True


def meta2rexp(pattern):
    """
    convert shell-like pattern into regular expression.

    ex.
    >>> print meta2rexp('foo.html')
    ^foo\.html$
    >>> print meta2rexp('*.html')
    ^(.*?)\.html$
    >>> print meta2rexp('*_???.{gif,jpg,png}')
    ^(.*?)\_(...)\.(gif|jpg|png)$
    """
    n = len(pattern)
    i = 0
    buf = ['^']
    while i < n:
        ch = pattern[i]
        if ch == '\\':
            i += 1
            if i >= n:
                raise ArgumentError("%s: invalid pattern." % pattern)  # or StandardError
            ch = pattern[i]
            buf.append(ch)
        elif ch == '*':
            buf.append('(.*?)')
        elif ch == '?':
            buf.append('(')
            while i < n and ch == '?':
                buf.append('.')
                i += 1
                ch = pattern[i]
            buf.append(')')
            i -= 1
        elif ch == '{':
            left = i
            right = None
            i += 1
            while i < n:
                ch = pattern[i]
                if ch == '}':
                    right = i
                    break
                i += 1
            if right is None:
                raise ArgumentError("%s: '{' is not closed by '}'." % pattern)  # or StandardError
            words = pattern[left+1:right].split(',')
            buf.extend(('(', '|'.join(words), ')', ))
        else:
            buf.append(re.escape(ch))
        i += 1
    buf.append('$')
    return ''.join(buf)


def _listup(path, kind=None, arr=None):
    if arr is None: arr = []
    if kind == 'f':
        if os.path.isfile(path): arr.append(path)
    elif kind == 'd':
        if os.path.isdir(path): arr.append(path)
    else:
        arr.append(path)
    if os.path.isdir(path):
        dir = os.listdir(path)   # raise error
        for fname in dir:
            if fname[0] == '.': continue
            path2 = os.path.join(path, fname)
            _listup(path2, kind, arr)
    return arr


def glob2(pattern):
    pair = pattern.split(r'**/', 2)
    if len(pair) == 1:
        filenames = glob(pattern)
        return filenames
    dirpat, basepat = pair
    if dirpat and dirpat[-1] == '/':
        dirpat = dirpat[0:-1]
    else:
        dirpat += '*'
    filenames = []
    for path in glob(dirpat):
        dirlist = _listup(path, 'd')
        for dir in dirlist:
            entries = glob2(os.path.join(dir, basepat))
            filenames.extend(entries)
    return filenames


class CommandOptionError(Exception):   # StandardError is not available in Python 3.0
    pass


class CommandOptionParser(object):

    uncheck_longopts = False

    def __init__(self, optdef_strs=()):
        self.parse_optdefs(optdef_strs)

    @classmethod
    def new(cls, optdef_strs=()):
        return cls(optdef_strs)

    def parse_optdefs(self, optdef_strs):
        helps = []
        optdefs = {}
        for optdef_str in optdef_strs:
            opt, desc = optdef_str.split(':', 1)
            if desc: desc = desc.strip()
            opt = opt.strip()
            helps.append((opt, desc))
            m = re.match(r'^-(\w)(?:\s+(.+)|\[(\w+)\])?$', opt)
            if m:
                name, arg1, arg2 = m.group(1), m.group(2), m.group(3)
                #optdefs[name] = arg1 and arg1 or (arg2 and True or False)
                if   arg1:  optdefs[name] = arg1
                elif arg2:  optdefs[name] = arg2 == 'N' and 1 or True
                else:       optdefs[name] = False
                continue
            m = re.match(r'^--([a-zA-Z][-\w]+)(?:=(.+)|\[=(.+)\])?$', opt)
            if m:
                name, arg1, arg2 = m.group(1), m.group(2), m.group(3)
                #optdefs[name] = arg1 and arg1 or (arg2 and True or False)
                if   arg1:  optdefs[name] = arg1
                elif arg2:  optdefs[name] = arg2 == 'N' and 1 or True
                else:       optdefs[name] = False
                continue
            raise ArgumentError("%s: invalid command optin definition." % optdef_str)
        self.optdefs = optdefs
        self.helps = helps
        return optdefs, help

    def parse(self, cmd_args, command=None):
        opts, rests = self._parse(cmd_args, command, check_longopts=True)
        return opts, rests

    def parse2(self, cmd_args, command=None):  ## TODO: rename
        opts, longopts, rests = self._parse(cmd_args, command, check_longopts=False)
        return opts, longopts, rests

    def _parse(self, cmd_args, command=None, check_longopts=True):
        optdefs = self.optdefs
        i = 0
        N = len(cmd_args)
        opts = {}
        if not check_longopts: longopts = {}
        while i < N:
            cmd_arg = cmd_args[i]
            if cmd_arg == '--':
                i += 1
                break
            m = re.match(r'^--([a-zA-Z][-\w]+)(?:=(.*))?$', cmd_arg)
            if m:
                name, arg = m.group(1), m.group(2)
                if not check_longopts:
                    if arg is None: arg = True
                    longopts[name] = arg
                elif name not in optdefs:
                    raise CommandOptionError("%s: unknown command option." % cmd_arg)
                elif optdefs[name] is False:    # --name
                    if arg is not None:
                        raise CommandOptionError("%s: argument is now allowed." % cmd_arg)
                    opts[name] = True
                elif optdefs[name] is True:     # --name[=arg]
                    opts[name] = arg is None and True or arg
                elif optdefs[name] is 1:        # --name[=N]
                    if arg and str2int(arg) is None:
                        raise CommandOptionError("%s: integer required." % cmd_arg)
                    opts[name] = arg is None and True or str2int(arg)
                else:                           # --name=arg
                    assert isinstance(arg, (str, unicode))
                    if arg is None:
                        raise CommandOptionError("%s: argument required." % cmd_arg)
                    if optdefs[name] == 'N':    # --name=N
                        if str2int(arg) is None:
                            raise CommandOptionError("%s: integer required." % cmd_arg)
                        arg = str2int(arg)
                    opts[name] = arg
            elif cmd_arg and cmd_arg[0] == '-':
                optchars = cmd_arg
                j = 1
                n = len(optchars)
                while j < n:
                    ch = optchars[j]
                    if ch not in optdefs:
                        raise CommandOptionError("-%s: unknown command option." % ch)
                    elif optdefs[ch] is False:  # -x
                        opts[ch] = True
                        j += 1
                        continue
                    elif optdefs[ch] is True:   # -x[arg]
                        opts[ch] = optchars[j+1:] or True
                        break
                    elif optdefs[ch] is 1:      # -x[N]
                        arg = optchars[j+1:]
                        if arg and str2int(arg) is None:
                            raise CommandOptionError("-%s%s: integer required." % (ch, arg))
                        opts[ch] = not arg and True or str2int(arg)
                        break
                    else:                       # -x arg
                        assert isinstance(optdefs[ch], (str, unicode))
                        if optchars[j+1:]:
                            arg = optchars[j+1:]
                        else:
                            assert j + 1 == n
                            i += 1      # not j
                            if i == N:
                                raise CommandOptionError("-%s: %s required." % (ch, optdefs[ch], ))
                            arg = cmd_args[i]
                        if optdefs[ch] == 'N':  # -x N
                            if str2int(arg) is None:
                                raise CommandOptionError("-%s %s: integer required." % (ch, arg, ))
                            arg = str2int(arg)
                        opts[ch] = arg
                        break
            else:
                break
            i += 1
        #
        rests = cmd_args[i:]
        return check_longopts and (opts, rests) or (opts, longopts, rests)

    def help(self, command=None, format="  %-20s: %s\n"):
        return "".join( format % (optdef_str, desc) for optdef_str, desc in self.helps if desc )


#def parse_command_options(optchars, args=None, command=None):
#    """
#    parse command line options.
#    optchars is a string such as "hvf:i?" (':' means argument is required and
#    '?' means arugument is optional).
#    """
#    if args is None:
#        command = os.path.basename(sys.argv[0])
#        args = sys.argv[1:]
#    ## parse optchars
#    singles, requireds, optionals = {}, {}, {}
#    iter = reversed(optchars).__iter__()
#    for ch in iter:
#        if   ch == ':':  requireds[iter.next()] = True
#        elif ch == '?':  optionals[iter.next()] = True
#        else:            singles[ch]            = True
#    #print "*** debug: singles:", repr(singles), ", requireds:", repr(requireds), ", optionals:", repr(optionals)
#    ## parse command-line options
#    opts = {}
#    longopts = {}
#    i = 0
#    n = len(args)
#    while i < n:
#        arg = args[i]
#        if arg == '--':              ## stop if '--' specified
#            break
#        elif arg.startswith('--'):   ## long options
#            m = re.match('--(\w[-\w]*)(=(.*))?$', arg)
#            if m is None:
#                raise CommandOptionError("%s: invalid option." % arg)
#            name = m.group(1)
#            value = m.group(3)
#            if value is None: value = True
#            #print "*** debug: name:", repr(name), ", value:", repr(value)
#            longopts[name] = value
#        elif arg.startswith('-'):    ## short options
#            j = 1
#            n_ch = len(arg)
#            while j < n_ch:
#                ch = arg[j]
#                if singles.has_key(ch):
#                    opts[ch] = True
#                elif requireds.has_key(ch):
#                    if j + 1 == n_ch:
#                        i += 1
#                        if i == n:
#                            raise CommandOptionError("-%s: argument required." % ch)
#                        opts[ch] = args[i]
#                    else:
#                        opts[ch] = arg[j+1:]
#                    break
#                elif optionals.has_key(ch):
#                    if j + 1 == n_ch:
#                        opts[ch] = True
#                    else:
#                        opts[ch] = arg[j+1:]
#                    break
#                else:
#                    raise CommandOptionError("-%s: unknown option." % ch)
#                #print "*** debug: ch:", repr(opts[ch])
#                j += 1
#        else:
#            break
#        i += 1
#    rests = args[i:]
#    #print "*** debug: opts:", repr(opts), ", longopts:", repr(longopts), ", rests:", repr(rests)
#    return opts, longopts, rests
#


## compatibility for Python 2.x and 3.0

if python2:
    def _is_str(obj):
        return isinstance(obj, (str, unicode))  # unicode is not defined in Python 3.0
    def _get_codeobj(func):
        return func.func_code
elif python3:
    def _is_str(obj):
        return isinstance(obj, str)
    def _get_codeobj(func):
        return func.__code__


