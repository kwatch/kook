#from __future__ import with_statement

import os, sys, re
#from glob import glob
from kook.utils import read_file, write_file, glob2


package = prop('package', 'Kook')

release         = prop('release', None)
copyright       = prop('copyright', None)
license         = prop('license', None)
script_file     = ["pykook", "kk"]
library_files   = [ "lib/*.py" ]


@recipe
#@ingreds('doc')
def task_package(c):
    """create package"""
    ## remove files
    #pattern = c%"dist/$(package)-$(release)*"
    #if glob2(pattern):
    #    rm_rf(pattern)
    rm_rf('dist')
    ## edit files
    repl = (
        (r'\$Release\$', release),
        (r'\$Release:.*?\$', '$Release: %s $' % release),
        (r'\$Copyright\$', copyright),
        (r'\$Package\$', package),
        (r'\$License\$', license),
    )
    cp('setup.py.txt', 'setup.py')
    edit('setup.py', by=repl)
    ## setup
    #rm_f('MANIFEST')
    run('python setup.py sdist')
    #run('python setup.py sdist --keep-temp')
    #
    @pushd('dist')
    def do(d):
        #pkgs = kook.utils.glob2(c%"$(package)-$(release).tar.gz");
        #pkg = pkgs[0]
        pkg = c%"$(package)-$(release).tar.gz"
        echo(c%"pkg=$(pkg)")
        #tar_xzf(pkg)
        run(c%"tar xzf $(pkg)")
        dir = c%"$(package)-$(release)"
        #echo("*** debug: pkg=%s, dir=%s" % (pkg, dir))
        edit(c%"$(dir)/**/*", exclude="*.png", by=repl)
        #with chdir(dir) as d2:
        #    run("python setup.py egg_info --egg-base .")
        #    rm("*.pyc")
        mv(pkg, c%"$(pkg).bkup")
        #tar_czf(c%"$(dir).tar.gz", dir)
        run(c%"tar -cf $(dir).tar $(dir)")
        run(c%"gzip -f9 $(dir).tar")
        ## create *.egg file
        #for python in ['python2.5', 'python2.6']:
        for python in ['python']:
            rm_rf(dir)
            run(c%"tar xzf $(dir).tar.gz")
            @pushd(dir)
            def do():
                _python = python
                run(c%"$(_python) setup.py bdist_egg")
                mv("dist/*.egg", "..")
                #rm_rf("build", "dist")
        rm_rf(dir)
        run(c%"tar -xzf $(dir).tar.gz")


replacer = (
    (r'\$Release\$', release),
    (r'\$Release:.*?\$', '$Release: %s $' % release),
    (r'\$Copyright\$', copyright),
    (r'\$Package\$', package),
    (r'\$License\$', license),
)


@recipe('setup.py', ['setup.py.txt'])
def file_setup_py(c):
    cp(c.ingred, c.product)
    edit(c.product, by=replacer)

@recipe(None, ['doc'])
def task_dist(c):
    """create package"""
    dir = 'dist-' + release
    rm_rf(dir)
    mkdir_p(dir)
    ## copy files
    text_files = ['README.txt', 'CHANGES.txt', 'MIT-LICENSE', 'MANIFEST.in',
                  'setup.py', 'Kookbook.py', 'Properties.py', ]
    store(text_files, dir)
    store('lib/kook/**/*.py', 'bin/kk', 'bin/pykook', 'test/**/*.py', dir)
    remote_py = dir + '/lib/kook/remote.py'
    os.path.isfile(remote_py) and rm_f(remote_py)
    store('doc/users-guide.html', 'doc/docstyle.css', 'doc/fig001.png', dir)
    cp('setup.py.txt', dir + '/setup.py')    # copy setup.py.txt as setup.py
    ##
    @pushd(dir)
    def do():
        edit("**/*", exclude=["*.png", "oktest.py", "Kookbook.py"], by=replacer)
    ##
    @pushd(dir)
    def do():
        #run('python setup.py sdist --force-manifest')
        run('python setup.py sdist --manifest-only')
        run('python setup.py sdist')
        #run('python setup.py sdist --keep-temp')
    #


@recipe
def uninstall(c):
    site_packages_dir = None
    for path in sys.path:
        if os.path.basename(path) == 'site-packages':
            site_packages_dir = path
            break
    else:
        raise Exception("site-packages directory not found.")
    script_files = ["/usr/local/bin/pykook", "/usr/local/bin/pyk"]
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


vs_path = '/opt/lang/python'
python_versions = [ '2.5.5', '2.6.7', '2.7.2', '3.0.1', '3.1.4', '3.2.1' ]


@recipe
@spices('-v version: version of python',
        '-a: do test for all version of python',
        '-s style: reporting style of oktest.py')
def test(c, *args, **kwargs):
    from glob import glob
    pwd = os.getcwd()
    os.environ['PYTHONPATH'] = "%s:%s/lib" % (pwd, pwd)
    oktest_opt = ''
    if 's' in kwargs:
        oktest_opt = '-s ' + kwargs['s']
    if kwargs.get('a'):
        for ver in python_versions:
            python_bin = vs_path + '/' + ver + '/bin/python'
            print(c%"---------- python $(ver)")
            @pushd('test')
            def do(testdir, python_bin=python_bin, opt=oktest_opt):
                opt = oktest_opt
                #for fname in glob('test_*.py'):
                #    run(c%"$(python_bin) $(fname)")
                run(c%"$(python_bin) -m oktest $(opt) .")
    else:
        ver = kwargs.get('v')
        #python_bin = ver and ('/usr/local/python/%s/bin/python' % ver) or 'python'
        python_bin = ver and ('/opt/local/bin/python%s' % ver) or 'python'
        targets = [ 'test_%s.py' % arg for arg in args ]
        @pushd('test')
        def do(d, python_bin=python_bin, opt=oktest_opt):
            #run("python test_all.py 2>&1 >  test.log")
            #for fname in targets or glob('test_*.py'):
            #    run(c%"$(python_bin) $(fname)")
            run(c%"$(python_bin) -m oktest $(opt) .")


kookbook.load("@kook/books/clean.py")
CLEAN.extend(["**/*.pyc", "**/__pycache__", "dist", "doc/*.toc.html", "lib/Kook.egg-info"])
SWEEP.extend(['dist-*'])

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


@recipe('test/oktest.py', ['../../oktest/python/lib/oktest.py'])
def file_test_oktest_py(c):
    rm_f(c.product)
    run(c%'ln $(ingred) $(product)')
    #cp(c.ingred, c.product)
    #def f(s):
    #    s = re.sub(r'\$Release:.*?\$', '$Release: $', s)
    #    return s
    #edit(c.product, by=f)


@recipe
@ingreds('test/oktest.py')
def update_oktest(c):
    """update 'test/oktest.py'"""
    pass


kookbook.load("@kook/books/concatenate.py")
