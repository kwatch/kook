###
### $Release: 0.0.5 $
### copyright(c) 2008-2009 kuwata-lab.com all rights reserved.
### MIT License
###


#import sys, re, os
#arg1 = len(sys.argv) > 1 and sys.argv[1] or None
#if arg1 == 'egg_info':
#    #from ez_setup import use_setuptools
#    #use_setuptools()
#    pass
#elif arg1 == 'bdist_egg':
#    from setuptools import setup
#else:
#    from distutils.core import setup
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def _kwargs():
    name             = 'Kook'
    version          = '0.0.5'
    author           = 'makoto kuwata'
    author_email     = 'kwa@kuwata-lab.com'
    maintainer       = author
    maintainer_email = author_email
    url              = 'http://www.kuwata-lab.com/kook/'
    description      = 'a smart build tool for Python, similar to Make, Rake, Ant, or Cook'
    long_description = r"""
pyKook is a very useful tool to control your task such as compile, install or clean.
pyKook is similar to Make, Rake, Ant, or Cook.
Kookbook.py, which is a task definition file for pyKook, is written in Python.
"""[1:]
    license          = 'MIT License'
    platforms        = 'any'
    download         = 'http://pypi.python.org/packages/source/K/%s/%s-%s.tar.gz' % (name, name, version)
    #download        = 'http://downloads.sourceforge.net/kook/%s-%s.tar.gz' % (name, version)
    #download        = 'http://downloads.sourceforge.net/kook/%s-%s.tar.gz' % (name, version)
    #download        = 'http://jaist.dl.sourceforge.net/sourceforge/kook/%s-%s.tar.gz' % (name, version)

    py_modules       = ['kook']
    package_dir      = {'': 'lib'}
    scripts          = ['bin/pykook', 'bin/kk']
    packages         = ['kook']
    #zip_safe        = False

    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
    return locals()


setup(**_kwargs())
