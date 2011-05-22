###
### $Release: $
### $Copyright: copyright(c) 2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

import sys, os, re, time
from glob import glob
import shutil

from oktest import ok, run


def read_file(fname):
    f = open(fname, "rb")
    s = f.read()
    f.close()
    return s

def write_file(fname, content):
    f = open(fname, "wb")
    f.write(content)
    f.close()


class UsersGuide_TC(object):

    pwd = os.getcwd()
    datadir = os.path.dirname(__file__) + "data/users_guide"

    buf = []
    for x in glob(datadir + "/*/*.result"):
        base = x[len(datadir)+1:].replace('.result', '')
        name = re.sub('[^\w]', '_', base)
        buf.append("def test_%s(self): self.do_test('%s')\n\n" % (name, base))
    buf.sort()
    exec("".join(buf))

    try:
        os.chdir(datadir)
        os.popen("gcc -c optparse.c")
    finally:
        os.chdir(pwd)

    def do_test(self, name):
        dir, base = os.path.split(name)
        os.chdir(self.datadir + "/" + dir)
        try:
            ## check file exists or not
            if dir != "topic-framework":
                ok ("Kookbook.py").exists()
            result_file = base + '.result'
            ok (result_file).exists()
            ## copy necessary files
            shutil.copy('../hello.c', '.')
            shutil.copy('../hello.h', '.')
            shutil.copy('../optparse.o', '.')
            if os.path.exists(base + '.properties'):
                shutil.copy(base + '.properties', 'Properties.py')
            if os.path.exists('hello.o'):
                os.unlink('hello.o')
            ## parse result file
            content = read_file(result_file)
            rexp = re.compile(r'^sh> ', re.M)
            for item in rexp.split(content):
                if not item: continue
                ## get command and expected
                m = re.search(r'^(.*?)\n', item)
                command = m.group(1)
                expected = item[len(m.group(0)):]
                ## skip certain commands
                if re.search(r'\./appsvr (start|stop)', command):
                    print("*** skipped: command=%r" % command)
                    continue
                ## modify expected
                if base.endswith('_dc'):
                    expected = re.compile(r'^ +##.*\n', re.M).sub('', expected)
                    expected = re.sub(r' +##.*', '', expected)
                    if re.match(r'^\s+$', expected):
                        expected = ''
                if base.endswith('_dc2'):
                    expected = re.compile(r'^###.*\n', re.M).sub('', expected)
                    if re.match(r'^\s+$', expected):
                        expected = ''
                if re.search(r'\n\n$', expected):
                    expected = expected[:-1]
                ## command-specific preparation
                if command.find('touch ') >= 0:
                    time.sleep(1)
                bkup = {}
                if command.find('ls ') >= 0:
                    for fname in glob('*.result'):
                        bkup[fname] = read_file(fname)
                        os.unlink(fname)
                ## do command
                f = os.popen(command)
                output = f.read()
                status = f.close()
                ## modify output
                #rexp = re.compile(r"^\(Tips: you can set 'kookbook\.default=", re.M)
                rexp = re.compile(r"^\(Tips: .*\)$", re.M)
                m = rexp.search(expected)
                if m:
                    s = m.group(0)
                    output = re.compile(r"^\(Tips: .*\)$", re.M).sub(s, output)
                ## assertion
                ok (output) == expected
                ##
                if bkup:
                    for fname in bkup:
                        write_file(fname, bkup[fname])
        finally:
            os.chdir(self.pwd)


if __name__ == '__main__':
    run()
