from __future__ import with_statement

import os, sys, re
#from glob import glob
from kook.utils import read_file, write_file, glob2


package = prop('package', 'Kook')
#package = prop('package', 'pyKook')

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
    system('python setup.py sdist')
    #system('python setup.py sdist --keep-temp')
    #
    with chdir('dist') as d:
        #pkgs = kook.utils.glob2(c%"$(package)-$(release).tar.gz");
        #pkg = pkgs[0]
        pkg = c%"$(package)-$(release).tar.gz"
        echo(c%"pkg=$(pkg)")
        #tar_xzf(pkg)
        system(c%"tar xzf $(pkg)")
        dir = c%"$(package)-$(release)"
        #echo("*** debug: pkg=%s, dir=%s" % (pkg, dir))
        edit(c%"$(dir)/**/*", by=repl)
        #with chdir(dir) as d2:
        #    system("python setup.py egg_info --egg-base .")
        #    rm("*.pyc")
        mv(pkg, c%"$(pkg).bkup")
        #tar_czf(c%"$(dir).tar.gz", dir)
        system(c%"tar -cf $(dir).tar $(dir)")
        system(c%"gzip -f9 $(dir).tar")
        ## create *.egg file
        #for python in ['python2.5', 'python2.6']:
        for python in ['python']:
            rm_rf(dir)
            system(c%"tar xzf $(dir).tar.gz")
            with chdir(dir):
                system(c%"$(python) setup.py bdist_egg")
                mv("dist/*.egg", "..")
                #rm_rf("build", "dist")
        rm_rf(dir)
        system(c%"tar -xzf $(dir).tar.gz")


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


@recipe
@spices('-v version: version of python')
def test(c, *args, **kwargs):
    from glob import glob
    ver = kwargs.get('v')
    python_bin = ver and ('/usr/local/python/%s/bin/python' % ver) or 'python'
    targets = [ 'test_%s.py' % arg for arg in args ]
    with chdir('test') as d:
        #system("python test_all.py 2>&1 >  test.log")
        for fname in targets or glob('test_*.py'):
            system(c%"$(python_bin) $(fname)")


@recipe
def clean(c):
    rm_rf('**/*.pyc', 'dist', 'doc/users-guide.toc.html')


kook_default_product = 'test'


#@recipe
#@ingreds('package')
#def default(c):
#    pass
#    #rm_rf("dist")
#    #system("python setup.py sdist")
#    #with chdir("dist"):
#    #    system(c%"tar xzf $(package)-$(release).tar.gz")
#    #    system(c%"ls $(package)-$(release)/")


@recipe(None, ['doc/users-guide.html', 'doc/docstyle.css', 'retrieve'])
#@ingreds('doc/users-guide.html', 'doc/docstyle.css')
def doc(c):
    """make document"""
    pass

@recipe('doc/users-guide.html', ['doc/users-guide.txt'])
#@product('doc/users-guide.html')
#@ingreds('doc/users-guide.txt')
#@byprods('doc/users-guide.toc.html')
@byprods('doc/users-guide.toc.html')
def file_users_guide_html(c):
    u = 'users-guide'
    with chdir("doc"):
        #system(c%"kwaser -t html-css -T $(ingred) > $(byprod)")
        #system(c%"kwaser -t html-css    $(ingred) | tidy -q -i -wrap 9999 > $(product)")
        #system(c%"kwaser -t html-css    $(ingred) > $(product).tmp")
        #system_f(c%"tidy -q -i -wrap 9999 $(product).tmp > $(product)")
        #rm(c.product + '.tmp')
        system(c%"kwaser -t html-css -T $(u).txt > $(u).toc.html")
        system(c%"kwaser -t html-css    $(u).txt > $(u).tmp")
        system_f(c%"tidy -q -i -wrap 9999 $(u).tmp > $(u).html")
        rm(c%'$(u).tmp')
        #mv(c.byprod, "doc")
    rm(c.byprod)

@recipe('doc/users-guide.txt', ['../common/doc/users-guide.eruby'])
#@product('doc/users-guide.txt')
#@ingreds('../common/doc/users-guide.eruby')
def file_users_guide_txt(c):
    os.path.isdir('doc') or mkdir('doc')
    system(c%"erubis -E PercentLine -p '\\[% %\\]' $(ingred) > $(product)")

@recipe('doc/docstyle.css', ['../common/doc/docstyle.css'])
#@product('doc/docstyle.css')
#@ingreds('../common/doc/docstyle.css')
def file_users_guide_css(c):
    os.path.isdir('doc') or mkdir('doc')
    cp(c.ingred, c.product)


@recipe(None, ['doc/users-guide.txt'])
def retrieve(c):
    """retrieve from 'doc/users-guide.txt'"""
    path = 'doc/data/users_guide'
    rm_rf(path)
    mkdir_p(path)
    system(c%"retrieve -Fd $(path) $(ingred)")

@recipe(None, ['retrieve'])
def doctest(c):
    """do test of users guide"""
    with chdir("doc"):
        system("python users_guide_test.py")


@recipe('test/oktest.py', ['../../oktest/python/lib/oktest.py'])
#@product('test/oktest.py')
#@ingreds('../../oktest/python/lib/oktest.py')
def file_test_oktest_py(c):
    rm_f(c.product)
    system(c%'ln $(ingred) $(product)')

@recipe(None, ['test/oktest.py'])
#@ingreds('test/oktest.py')
def update_oktest(c):
    """update 'test/oktest.py'"""
    pass
