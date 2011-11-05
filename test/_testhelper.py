###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2008-2011 kuwata-lab.com all rights reserved. $
### $License: MIT License $
###

import sys, os, glob, shutil
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import oktest
try:
    _MainApp = oktest.mainapp.MainApp
except AttributeError:
    _MainApp = oktest.main.MainApp
    def main(*args, **kwargs):
        if sys.argv[0] != oktest.__file__:
            sys.argv.insert(0, oktest.__file__)
        _MainApp.main(*args, **kwargs)
    oktest.main = main
    del main


def mkdir_p(path):
    d = None
    mkdir = os.mkdir
    for item in os.path.split(path):
        if d is None:
            os.mkdir(item)
            d = item
        else:
            d = d + '/' + item
            os.mkdir(d)


def rm_rf(path):
    if os.path.exists(path):
        shutil.rmtree(path)


@classmethod
def _before_all(cls):
    cls._back_to = os.getcwd()
    if not os.path.exists('_test_tmp.d'):
        os.mkdir('_test_tmp.d')
    os.chdir('_test_tmp.d')


@classmethod
def _after_all(cls):
    os.chdir(cls._back_to)
    rm_rf('_test_tmp.d')


def _setup_stdio():
    import kook.config
    kook.config.stdout = StringIO()
    kook.config.stderr = StringIO()


def _teardown_stdio():
    import kook.config
    kook.config.stdout = sys.stdout
    kook.config.stderr = sys.stderr


class dummy_sio(object):

    def __init__(self, content=None):
        self.stdin_content = content

    def __enter__(self):
        import kook.config as config
        self.stdout, config.stdout = config.stdout, StringIO()
        self.stderr, config.stderr = config.stderr, StringIO()
        self.stdin,  sys.stdin     = sys.stdin,     StringIO(self.stdin_content or "")
        return self

    def __exit__(self, *args):
        import kook.config as config
        #sout, serr = config.stdout.getvalue(), config.stderr.getvalue()
        config.stdout, self.stdout = self.stdout, config.stdout.getvalue()
        config.stderr, self.stderr = self.stderr, config.stderr.getvalue()
        sys.stdin,     self.stdin  = self.stdin,  self.stdin_content

    def run(self, func, *args, **kwargs):
        try:
            self.__enter__()
            func(*args, **kwargs)
            return self
        finally:
            self.__exit__(*sys.exc_info())

    def __call__(self, func):
        return self.run(func)


def _invoke_kookbook(input, start_task='remote_test', stdin=''):
    import kook.config
    from kook.cookbook import Cookbook
    from kook.kitchen import Kitchen
    from oktest.dummy import dummy_io
    _sout, _serr = kook.config.stdout, kook.config.stderr
    try:
        #with dummy_io(stdin) as dio:
        dio = dummy_io(stdin)
        dio.__enter__()
        try:
            kook.config.stdout = sys.stdout
            kook.config.stderr = sys.stderr
            kookbook = Cookbook().load(input)
            kitchen = Kitchen(kookbook)
            kitchen.start_cooking(start_task)
        finally:
            dio.__exit__(*sys.exc_info())
        return dio
    finally:
        kook.config.stdout, kook.config.stderr = _sout, _serr
