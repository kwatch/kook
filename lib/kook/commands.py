# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import sys, os, re
import shutil
#from glob import glob as _glob
import kook
from kook import KookCommandError
from kook.utils import glob2, flatten, has_metachars, meta2rexp, ArgumentError
import kook.config as config
from kook.misc import _report_cmd


__all__ = (
    'system_f', 'system',
    'cp', 'cp_r', 'cp_p', 'cp_pr',
    'mkdir', 'mkdir_p',
    'rm', 'rm_r', 'rm_f', 'rm_rf',
    'mv',
    'echo', 'echo_n',
    'store', 'store_p',
    'chdir', 'cd',
    'edit',
)


def system_f(command):
    _report_cmd(command)
    if config.noexec:
        return
    return os.system(command)


def system(command):
    _report_cmd(command)
    if config.noexec:
        return
    status = os.system(command)
    if status != 0:
        #status = status % 255
        raise KookCommandError("command failed (status=%s)." % status)
    return status


def cp(*filenames):
    _cp(filenames, 'cp', 'cp', p=False, r=False)

def cp_p(*filenames):
    _cp(filenames, 'cp_p', 'cp -p', p=True, r=False)

def cp_r(*filenames):
    _cp(filenames, 'cp_r', 'cp -r', p=False, r=True)

def cp_pr(*filenames):
    _cp(filenames, 'cp_pr', 'cp -pr', p=True, r=True)

def _prepare(filenames, cmd=None):
    filenames = flatten(filenames)
    if cmd: _report_cmd("%s %s" % (cmd, " ".join(filenames)))
    fnames = flatten([ not has_metachars(fname) and fname or (glob2(fname) or fname) \
                           for fname in filenames ])
    return fnames

def _cp(filenames, func, cmd, p, r):
    fnames = _prepare(filenames, cmd)
    if config.noexec:
        return
    _copy_file = p and shutil.copy2 or shutil.copy
    n = len(fnames)
    if n < 2:
        raise KookCommandError("%s: at least two file or directory names are required." % func)
    elif n == 2:
        src, dst = fnames
        if not os.path.exists(src):
            raise KookCommandError("%s: %s: no such file or directory." % (func, src))
        if os.path.isdir(src):
            if r: _copy_dir(src, dst, func, cmd, p=p)
            else: raise KookCommandError("%s: %s: cannot copy directory (use 'cp_r' instead)." % (func, src))
        else:
            _copy_file(src, dst)
    else:   # n > 2
        dst = fnames[-1]
        if not os.path.exists(dst):
            raise KookCommandError("%s: %s: directory not found." % (func, dst))
        elif not os.path.isdir(dst):
            raise KookCommandError("%s: %s: not a directory." % (func, dst))
        for src in fnames[0:-1]:
            if os.path.isdir(src):
                if r: _copy_dir(src, dst, func, cmd, p=p)
                else: raise KookCommandError("%s: %s: cannot copy directory (use 'cp_r' instead)." % (func, src))
            else:
                _copy_file(src, dst)

def _copy_dir(srcdir, dstdir, func, cmd, p=False):
    assert os.path.isdir(srcdir)
    #assert os.path.isdir(dstdir)
    _copy_file = p and shutil.copy2 or shutil.copy
    #
    def _copy_r(srcdir, dstdir):
        assert os.path.isdir(srcdir)
        assert not os.path.exists(dstdir)
        os.mkdir(dstdir)
        for fname in os.listdir(srcdir):
            s = os.path.join(srcdir, fname)
            d = os.path.join(dstdir, fname)
            if os.path.isdir(s):     # dir to dir
                _copy_r(s, d)
            else:                    # fie to file
                _copy_file(s, d)
    #
    if os.path.exists(dstdir):
        if not os.path.isdir(dstdir):
            raise KookCommandError("%s: %s: not a directory." % (func, dstdir))
        dstdir = os.path.join(dstdir, os.path.basename(srcdir))
        if os.path.exists(dstdir):
            raise KookCommandError("%s: %s: alread exists." % (func, dstdir))
    assert not os.path.exists(dstdir)
    _copy_r(srcdir, dstdir)


def mkdir(*dirnames):
    _mkdir(dirnames, 'mkdir', 'mkdir', p=False)

def mkdir_p(*dirnames):
    _mkdir(dirnames, 'mkdir_p', 'mkdir -p', p=True)

def _mkdir(dirnames, func, cmd, p):
    dnames = _prepare(dirnames, cmd)
    if config.noexec:
        return
    if not dnames:
        raise KookCommandError("%s: directory name required." % func)
    for dname in dnames:
        if p:
            if os.path.isdir(dname):
                pass
            elif os.path.exists(dname):
                raise KookCommandError("%s: %s: already exists." % (func, dname))
            else:
                _makedir(dname)
        else:
            if os.path.exists(dname):
                raise KookCommandError("%s: %s: already exists." % (func, dname))
            else:
                os.mkdir(dname)

def _makedir(dirpath):
    if (os.path.isdir(dirpath)): return
    parent = os.path.dirname(dirpath)
    if parent:
        _makedir(parent)
    os.mkdir(dirpath)


def rm(*filenames):
    _rm(filenames, 'rm', 'rm', r=False, f=False)

def rm_r(*filenames):
    _rm(filenames, 'rm_r', 'rm -r', r=True, f=False)

def rm_f(*filenames):
    f = True
    _rm(filenames, 'rm_f', 'rm -f', r=False, f=f)

def rm_rf(*filenames):
    _rm(filenames, 'rm_rf', 'rm -rf', r=True, f=True)

def _rm(filenames, func, cmd, r=False, f=False):
    fnames = _prepare(filenames, cmd)
    if config.noexec:
        return
    for fname in fnames:
        if os.path.isdir(fname):
            if r: _remove(fname)
            else: raise KookCommandError("%s: %s: can't remove directry (try 'rm_r' instead)." % (func, fname))
        elif os.path.exists(fname):
            os.unlink(fname)
        else:
            if f: pass
            else: raise KookCommandError("%s: %s: not found." % (func, fname))

def _remove(fname):
    assert os.path.exists(fname)
    if os.path.isdir(fname):
        for child in os.listdir(fname):
            _remove(os.path.join(fname, child))
        os.rmdir(fname)
    else:
        os.unlink(fname)


def mv(*filenames):
    _mv(filenames, 'mv', 'mv')

def _mv(filenames, func, cmd):
    fnames = _prepare(filenames, cmd)
    if config.noexec:
        return
    n = len(fnames)
    if n < 2:
        raise KookCommandError("%s: at least two file or directory names are required." % func)
    elif n == 2:
        src, dst = fnames
        if not os.path.exists(src):
            raise KookCommandError("%s: %s: not found." % (func, src))
        elif not os.path.exists(dst):  # any to new
            #shutil.move(src, dst)
            os.rename(src, dst)
        elif os.path.isdir(dst):       # any to dir
            #shutil.move(src, dst)
            os.rename(src, os.path.join(dst, os.path.basename(src)))
        elif os.path.isdir(src):       # dir to file
            raise KookCommandError("%s: %s: already exists." % (func, dst))
        else:                          # file to file
            os.rename(src, dst)
    else:  # n > 2                     # files and dirs to a dir
        dst = fnames[-1]
        if not os.path.exists(dst):
            raise KookCommandError("%s: %s: directory not found." % (func, dst))
        if not os.path.isdir(dst):
            raise KookCommandError("%s: %s: not a directory." % (func, dst))
        for src in fnames[0:-1]:
            if not os.path.exists(src):
                raise KookCommandError("%s: %s: not found." % (func, src))
        for src in fnames[0:-1]:
            #shutil.move(src, dst)
            os.rename(src, os.path.join(dst, os.path.basename(src)))


def echo(*messages):
    _echo(messages, 'echo', 'echo', n=False)

def echo_n(*messages):
    _echo(messages, 'echo_n', 'echo -n', n=True)

def _echo(messages, func, cmd, n=False):
    msgs = _prepare(messages, cmd)
    if config.noexec:
        return
    write = config.stdout.write
    for i, msg in enumerate(msgs):
        if i > 0: write(' ')
        write(msg)
    if not n: write("\n")
    config.stdout.flush()      # requires for 'echo -n'


def store(*filenames):
    _store(filenames, 'store', 'store', p=False)

def store_p(*filenames):
    _store(filenames, 'store_p', 'store -p', p=True)

def _store(filenames, func, cmd, p=False):
    fnames = _prepare(filenames, cmd)
    if config.noexec:
        return
    n = len(fnames)
    _copy_file = p and shutil.copy2 or shutil.copy
    if n < 2:
        raise KookCommandError("%s: at least two file or directory names are required." % func)
    else:
        basedir = fnames[-1]
        if not os.path.exists(basedir):
            raise KookCommandError("%s: %s: directory not found." % (cmd, basedir))
        elif not os.path.isdir(basedir):
            raise KookCommandError("%s: %s: not a directory." % (cmd, basedir))
        for src in fnames[0:-1]:
            if not os.path.exists(src):
                raise KookCommandError("%s: %s: not found." % (cmd, src))
        for src in fnames[0:-1]:
            dst = os.path.join(basedir, src)
            if os.path.isdir(src):
                _makedir(dst)
            else:
                dirname = os.path.dirname(dst)
                _makedir(dirname)
                _copy_file(src, dst)  # copy file to file


class Chdir(object):

    def __init__(self, dirname, func, cmd):
        self.dirname = dirname
        self.func = func
        self.cmd = cmd
        self.cwd = None

    def __enter__(self):
        func = self.func
        dnames = _prepare([self.dirname], self.cmd)
        n = len(dnames)
        if n < 1:
            raise KookCommandError("%s: directory name required." % func)
        elif n > 1:
            raise KookCommandError("%s: too many directories." % func)
        dname = dnames[0]
        if not os.path.exists(dname):
            raise KookCommandError("%s: %s: directory not found." % (func, dname))
        elif not os.path.isdir(dname):
            raise KookCommandError("%s: %s: not a directory." % (func, dname))
        self.cwd = os.getcwd()
        os.chdir(self.dirname)
        return self

    def __exit__(self, type, value, traceback):   # type and value is not used
        _prepare(['-', '  # back to '+self.cwd], self.cmd)
        os.chdir(self.cwd)


def chdir(dirname, block=None):
    #return _chdir(dirname, 'chdir', 'chdir')
    obj = Chdir(dirname, 'chdir', 'chdir')
    if block:
        ex_type = ex_obj = traceback = None
        try:
            obj.__enter__()
            block.__call__()
        except Exception:
            ex_type, ex_obj, traceback = sys.exc_info();
        finally:
            obj.__exit__(ex_type, ex_obj, traceback)
            if ex_obj:
                raise
    return obj

def cd(dirname):
    return _chdir(dirname, 'cd', 'cd')

def _chdir(dirname, func, cmd):
    dnames = _prepare([dirname], cmd)
    n = len(dnames)
    if n < 1:
        raise KookCommandError("%s: directory name required." % func)
    elif n > 1:
        raise KookCommandError("%s: too many directories." % func)
    dname = dnames[0]
    if not os.path.exists(dname):
        raise KookCommandError("%s: %s: directory not found." % (func, dname))
    elif not os.path.isdir(dname):
        raise KookCommandError("%s: %s: not a directory." % (func, dname))
    cwd = os.getcwd()
    os.chdir(dirname)
    return cwd


def edit(*filenames, **kwargs):
    by       = kwargs.get('by', None)
    encoding = kwargs.get('encoding', None)
    exclude  = kwargs.get('exclude', None)
    if isinstance(exclude, (str, unicode)):
        exclude = [exclude]
    if not by:
        raise ArgumentError("edit: keyword arg 'by' is reqiured.")
    if hasattr(by, '__call__'):
        pass
    elif isinstance(by, (tuple, list)):
        pairs = by
        def by(s):
            for rexp, repl in pairs:
                s = re.sub(rexp, repl, s)
            return s
    else:
        raise ArgumentError("edit: 'by' should be callable or list of tuples.")
    _edit(filenames, 'edit', 'edit', by, encoding, exclude)

def _edit(filenames, func, cmd, by, encoding=None, exclude=None):
    fnames = _prepare(filenames, cmd)
    if config.noexec:
        return
    if exclude:
        exclude_patterns = [ re.compile(meta2rexp(s)) for s in exclude ]
        def ok_p(fname, _patterns=exclude_patterns):
            for pat in _patterns:
                if pat.match(fname):
                    return False
            return True
        fnames = [ fname for fname in fnames if ok_p(fname) ]
    for fname in fnames:
        if not os.path.exists(fname):
            raise KookCommandError("%s: %s: not found." % (func, fname))
        if os.path.isdir(fname):
            #raise KookCommandError("%s: %s: can't edit directory." % (func, fname))
            continue
        content = kook.utils.read_file(fname, encoding)
        content = by(content)
        kook.utils.write_file(fname, content, encoding)
