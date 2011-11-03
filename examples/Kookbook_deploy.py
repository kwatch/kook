##
## Kookbook to deploy application.
##
## (requires: pycrypto, paramiko)
##
## Usage:
##   $ kk [--production] deploy [-t tag]
##   $ kk [--production] deploy:checkout [-t tag]
##   $ kk [--production] deploy:info
##

from __future__ import with_statement
from kook.remote import Remote, Password

## repository url
repository_url = "git@bitbucket.org:yourname/myapp1.git"

## production or staging servers
production = prop('production', False)
if production:
    hosts = ['www.example.com']     ## production server
else:
    hosts = ['dev.example.com']     ## staging server

app_server = Remote(
    hosts = hosts,
    port  = 22,
    user  = 'user1',
    password = Password(),
)

## default recipe
kookbook.default = 'deploy:info'

## recipe definitions
class deploy(Category):

    @recipe
    @app_server
    def info(c):
        ssh = c.ssh
        ssh.run("hostname")
        ssh.run("whoami")
        #ssh.sudo("whoami")

    @recipe
    @app_server
    @spices("-t tag: tag name to checkout")
    def default(c, *args, **kwargs):
        """deploy to remote server"""
        tagname = kwargs.get('t')
        ssh = c.ssh
        if "repo" not in ssh.listdir_f("app"):
            ssh.run("mkdir -p app/repo")
        ## call other recipe to check-out source code
        deploy.checkout(c, *args, **kwargs)
        ## deploy
        target = tagname or 'master'
        ssh.run(c%"mkdir -p app/releases/$(target)")
        with ssh.cd(c%"app/releases/$(target)"):
            ## copy source files
            ssh.run("cp -pr ../../repo/* .")
            ## migrate database by 'migrate'
            #ssh.run("python db_repository/manage.py upgrade")
        ## recreate symbolic link
        with ssh.cd("app/releases"):
            ssh.run(c%"rm -f current")
            ssh.run(c%"ln -s $(tagname) current")

    @recipe
    @app_server
    @spices("-t tag: tag name to checkout")
    def checkout(c, *args, **kwargs):
        """checkout source code from git repository"""
        tagname = kwargs.get('t')
        ssh = c.ssh
        if "repo" not in ssh.listdir_f("app"):
            ssh.run("mkdir -p app/repo")
        ## checkout git repository
        with ssh.cd("app/repo"):
            files = ssh.listdir(".")
            if '.git' not in files:
                ssh.run(c%"git clone $(repository_url) .")
            else:
                ssh.run(c%"git fetch")
            if tagname:
                ssh.run(c%"git checkout -q refs/tags/$(tagname)")
            else:
                ssh.run(c%"git checkout master")
