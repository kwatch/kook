from __future__ import with_statement

import os, sys, re
#from glob import glob
from kook.utils import read_file, write_file, glob2


package = prop('package', 'Kook')
#package = prop('package', 'pyKook')

release         = prop('release', None)
copyright       = prop('copyright', None)
license         = prop('license', None)
python_basepath = "/usr/local/lib/python2.6"
#site_packages_path = "%s/lib/python2.4/site-packages" % python_basepath
site_packages_path = "%s/site-packages" % python_basepath
script_file     = ["pykook", "pyk"]
library_files   = [ "lib/*.py" ]


@product("package")
def task_package(c):
    """create package"""
    ## remove files
    pattern = c%"dist/$(package)-$(release)*"
    if glob2(pattern):
        rm_rf(pattern)
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
        rm_rf(dir)
        ## create *.egg file
        for python in ['python2.5', 'python2.6']:
            system(c%"tar xzf $(dir).tar.gz")
            with chdir(dir):
                system(c%"$(python) setup.py bdist_egg")
                mv("dist/*.egg", "..")
                #rm_rf("build", "dist")
            rm_rf(dir)
        system(c%"tar -xzf $(dir).tar.gz")


def task_uninstall(c):
    #script_file    = "$python_basepath/bin/" + script_file;
    #library_files  = [ os.path.join(site_packages_path, item) for item in library_files ]
    #compiled_files = [ item + '.c' for item in library_files ]
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


def task_test(c):
    with chdir('test') as d:
        system("python test_all.py 2>&1 >  test.log")


def task_clean(c):
    pass


kook_default_product = 'default'

@product('default')
@ingreds('package')
def task_default(c):
    pass
    #rm_rf("dist")
    #system("python setup.py sdist")
    #with chdir("dist"):
    #    system(c%"tar xzf $(package)-$(release).tar.gz")
    #    system(c%"ls $(package)-$(release)/")


@product('doc')
@ingreds('doc/users-guide.html', 'doc/docstyle.css')
def task_doc(c):
    """make document"""
    pass

@product('doc/users-guide.html')
@ingreds('doc/users-guide.txt')
#@byprods('doc/users-guide.toc.html')
@byprods('users-guide.toc.html')
def file_users_guide_html(c):
    system(c%"kwaser -t html-css -T $(ingred) > $(byprod)")
    #system(c%"kwaser -t html-css    $(ingred) | tidy -q -i -wrap 9999 > $(product)")
    system(c%"kwaser -t html-css    $(ingred) > $(product).tmp")
    system_f(c%"tidy -q -i -wrap 9999 $(product).tmp > $(product)")
    rm(c%"$(product).tmp")
    mv(c.byprod, "doc")

@product('doc/users-guide.txt')
@ingreds('../doc/users-guide.eruby')
def file_users_guide_txt(c):
    os.path.isdir('doc') or mkdir('doc')
    system(c%"erubis -E PercentLine -p '\\[% %\\]' $(ingred) > $(product)")

@product('doc/docstyle.css')
@ingreds('../doc/docstyle.css')
def file_users_guide_css(c):
    os.path.isdir('doc') or mkdir('doc')
    cp(c.ingred, c.product)
