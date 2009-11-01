###
### $Release: 0.0.5 $
### copyright(c) 2008-2009 kuwata-lab.com all rights reserved.
### MIT License
###


import sys, re, os
arg1 = len(sys.argv) > 1 and sys.argv[1] or None
if arg1 == 'egg_info':
    #from ez_setup import use_setuptools
    #use_setuptools()
    pass
elif arg1 == 'bdist_egg':
    from setuptools import setup
else:
    from distutils.core import setup


name     = 'Kook'
version  = '0.0.5'
author   = 'makoto kuwata'
email    = 'kwa@kuwata-lab.com'
maintainer = author
maintainer_email = email
url      = 'http://www.kuwata-lab.com/kook/'
desc     = 'a smart build tool for Python, similar to Make, Rake, Ant, or Cook'
detail   = (
           'pyKook is a very useful tool to control your task such as compile, install or clean.\n'
           'pyKook is similar to Make, Rake, Ant, or Cook.\n'
           'Kookbook.py, which is a task definition file for pyKook, is written in Python.\n'
           )
license  = 'MIT License'
platforms = 'any'
download = 'http://pypi.python.org/packages/source/K/%s/%s-%s.tar.gz' % (name, name, version)
#download = 'http://downloads.sourceforge.net/kook/%s-%s.tar.gz' % (name, version)
#download = 'http://downloads.sourceforge.net/kook/%s-%s.tar.gz' % (name, version)
#download = 'http://jaist.dl.sourceforge.net/sourceforge/kook/%s-%s.tar.gz' % (name, version)
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
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.0',
    'Topic :: Software Development :: Libraries :: Python Modules',
]


setup(
    name=name,
    version=version,
    author=author,  author_email=email,
    maintainer=maintainer, maintainer_email=maintainer_email,
    description=desc,  long_description=detail,
    url=url,  download_url=download,  classifiers=classifiers,
    license=license,
    #platforms=platforms,
    #
    py_modules=['kook'],
    package_dir={'': 'lib'},
    scripts=['bin/pykook', 'bin/kk'],
    packages=['kook'],
    #zip_safe = False,
)
