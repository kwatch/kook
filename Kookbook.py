from __future__ import with_statement

import os, sys, re
#from glob import glob
from kook.utils import read_file, write_file, glob2


package = prop('package', 'Kook')

release         = prop('release', None)
copyright       = prop('copyright', None)
license         = prop('license', None)
script_file     = ["pykook", "kk"]
library_files   = [ "lib/*.py" ]


replacer = (
    (r'\$Release\$', release),
    (r'\$Copyright\$', copyright),
    (r'\$Package\$', package),
    (r'\$License\$', license),
    (r'\$Release:.*?\$',   '$Release: %s $' % release),
    (r'\$Copyright:.*?\$', '$Copyright: %s $' % copyright),
    (r'\$License:.*?\$',   '$License: %s $' % license),
)

python = sys.executable

@recipe
@ingreds('dist')
def package(c):
    """create package"""
    ## setup
    dir = c%"dist/Kook-$(release)"
    @pushd(dir)
    def do():
        system(c%'$(python) setup.py sdist')
        #system('python setup.py sdist --keep-temp')
    cp(c%'$(dir)/MANIFEST', '.')

@recipe(None, ['doc'])
def dist(c):
    """create package"""
    ## create base dir
    dir = c%"dist/Kook-$(release)"
    os.path.exists(dir) and rm_rf(dir)
    mkdir_p(dir)
    ## copy files
    text_files = ['README.txt', 'CHANGES.txt', 'MIT-LICENSE',  'MANIFEST.in',
                  'Kookbook.py', 'setup.py', 'Properties.py', ]
    store(text_files, dir)
    store('lib/kook/**/*.py', 'bin/*', 'test/**/*.py', 'examples/*.py', dir)
    store('doc/users-guide.html', 'doc/docstyle.css', 'doc/fig001.png', dir)
    ##
    @pushd(dir)
    def do():
        ## edit files
        edit("**/*", exclude=["*.png", "oktest.py", "Kookbook.py"], by=replacer)

@recipe
def update_headers(c):
    """update headers of lib, test, and bin files"""
    replacer = (
        (r'# \$Release.*?\$',   '# $Release: %s $' % release),
        (r'# \$Copyright.*?\$', '# $Copyright: %s $' % copyright),
        (r'# \$License.*?\$',   '# $License: %s $' % license),
        )
    edit("lib/**/*.py", "test/*.py", "bin/*", by=replacer)

@recipe('setup.py', ['setup.py.txt'])
def file_setup_py(c):
    cp(c.ingred, c.product)
    edit(c.product, by=replacer)

@recipe
def uninstall(c):
    site_packages_dir = None
    for path in sys.path:
        if os.path.basename(path) == 'site-packages':
            site_packages_dir = path
            break
    else:
        raise Exception("site-packages directory not found.")
    basedir = "/usr/local"
    script_files = [basedir + "/bin/pykook", basedir + "/bin/kk"]
    library_files = c%"$(site_packages_dir)/$(package)*"
    rm(script_files, library_files)
    filename = c%"($site_packages_dir)/easy-install.pth"
    if os.path.exists(filename):
        s = read_file(filename)
        pattern = re.compile(c%r'/^\.\/$(package)-.*\n/m', re.S)
        s2 = re.sub(pattern, s)
        if s != s2:
            write_file(filename, s2)
            #repl = ((pattern, ''), )
            #edit(filename, by=repl)


vs_path = '/opt/lang/python/%(version)s/bin/python'
python_versions = [ '2.5.5', '2.6.7', '2.7.2', '3.0.1', '3.1.4', '3.2.1' ]


@recipe
@spices('-v version: version of python',
        '-a: do test for all version of python',
        '-s style: reporting style of oktest.py')
def test(c, *args, **kwargs):
    from glob import glob
    pwd = os.getcwd()
    if os.getenv('PYTHONPATH'):
        os.environ['PYTHONPATH'] = os.environ['PYTHONPATH'] + ":%s/test" % pwd
    else:
        os.environ['PYTHONPATH'] = "%s:%s/lib:%s/test" % (pwd, pwd, pwd)
    oktest_opt = ''
    if 's' in kwargs:
        oktest_opt = '-s ' + kwargs['s']
    extra = os.path.isfile('test_remote.py') and 'test_remote.py' or ''
    cmd = c%" -m oktest $(oktest_opt) -sp test $(extra)"
    if kwargs.get('a'):
        for ver in python_versions:
            python_bin = vs_path % { 'version': ver }
            print(c%"---------- python $(ver)")
            run(python_bin + cmd)
    else:
        ver = kwargs.get('v')
        #python_bin = ver and ('/usr/local/python/%s/bin/python' % ver) or 'python'
        python_bin = ver and ('/opt/local/bin/python%s' % ver) or 'python'
        #targets = [ 'test/%s_test.py' % arg for arg in args ]
        run(python_bin + cmd)


kookbook.load("@kook/books/clean.py")
CLEAN.extend(["**/*.pyc", "**/__pycache__", "dist", "doc/*.toc.html", "lib/Kook.egg-info"])
SWEEP.extend(['dist'])

kookbook.default = 'test'


#@recipe
#@ingreds('package')
#def default(c):
#    pass
#    #rm_rf("dist")
#    #run("python setup.py sdist")
#    #with chdir("dist"):
#    #    run(c%"tar xzf $(package)-$(release).tar.gz")
#    #    run(c%"ls $(package)-$(release)/")


@recipe(None, ['doc/users-guide.html', 'doc/docstyle.css', 'retrieve'])
def doc(c):
    """make document"""
    pass

@recipe('doc/users-guide.html', ['doc/users-guide.txt'])
@byprods('doc/users-guide.toc.html')
def file_users_guide_html(c):
    @pushd("doc")
    def do():
        u = 'users-guide'
        run(c%"kwaser -t html-css -T $(u).txt > $(u).toc.html")
        run(c%"kwaser -t html-css    $(u).txt > $(u).tmp")
        run_f(c%"tidy -q -i -wrap 9999 $(u).tmp > $(u).html")
        replacer = [
            (r'<p>\.\+NOTE:</p>', r'<div class="note"><span class="caption">NOTE:</span>'),
            (r'<p>\.\-NOTE:</p>', r'</div>'),
            (r'<p>\.\+TIPS:</p>', r'<div class="note"><span class="caption">TIPS:</span>'),
            (r'<p>\.\-TIPS:</p>', r'</div>'),
        ]
        edit(c%"$(u).html", by=replacer)
        rm(c%'$(u).tmp', c%'$(u).toc.html')

@recipe('doc/users-guide.txt', ['../common/doc/users-guide.eruby'])
def file_users_guide_txt(c):
    os.path.isdir('doc') or mkdir('doc')
    run(c%"erubis -E PercentLine -p '\\[% %\\]' $(ingred) > $(product)")

@recipe('doc/docstyle.css', ['../common/doc/docstyle.css'])
def file_users_guide_css(c):
    os.path.isdir('doc') or mkdir('doc')
    cp(c.ingred, c.product)


@recipe(None, ['doc/users-guide.txt'])
def retrieve(c):
    """retrieve from 'doc/users-guide.txt'"""
    path = 'doc/data/users_guide'
    rm_rf(path)
    mkdir_p(path)
    run(c%"retrieve -Fd $(path) $(ingred)")

@recipe(None, ['retrieve'])
def doctest(c):
    """do test of users guide"""
    @pushd("doc")
    def do():
        run("python users_guide_test.py")


kookbook.load("@kook/books/concatenate.py")
