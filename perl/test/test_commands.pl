###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 351;
use File::Path;
use File::Basename;
use Cwd;

use Kook::Commands qw(sys sys_f echo echo_n cp cp_p cp_r cp_pr mkdir mkdir_p rm rm_r rm_f rm_rf rmdir mv store store_p cd edit);
use Kook::Utils qw(read_file write_file ob_start ob_get_clean repr has_metachar mtime);


sub _test_p {
    my ($test_name) = @_;
    return ! $ENV{'TEST'} || $ENV{'TEST'} eq $test_name;
}


my $HELLO_C = <<'END';
/* $COPYRIGHT$ */
#include <stdio.h>
int main(int argc, char *argv[]) {
    int i;
    for (i = 0; i < argc; i++) {
        printf("argv[%d]: %s\n", i, argv[i]);
    }
    return 0;
}
END
    ;

my $HELLO_H = <<'END';
/* $COPYRIGHT$ */
char *command = "hello";
char *release = "$_RELEASE_$";
END
    ;   #"


###
### before_all()
###
CORE::mkdir "_sandbox" unless -d "_sandbox";
chdir "_sandbox"  or die $!;


###
### before_each()/after_each()
###
sub before_each {
    write_file('hello.c', $HELLO_C);
    write_file('hello.h', $HELLO_H);
    my $t = time() - 99;
    utime $t, $t, 'hello.c';
    utime $t, $t, 'hello.h';
    #
    CORE::mkdir 'hello.d';
    CORE::mkdir 'hello.d/src';
    CORE::mkdir 'hello.d/src/lib';
    CORE::mkdir 'hello.d/src/include';
    CORE::mkdir 'hello.d/tmp';
    write_file('hello.d/src/lib/hello.c', $HELLO_C);
    write_file('hello.d/src/include/hello.h',  $HELLO_H);
    write_file('hello.d/src/include/hello2.h', $HELLO_H);
    utime $t, $t, 'hello.d/src/lib/hello.c';
    utime $t, $t, 'hello.d/src/include/hello.h';
    utime $t, $t, 'hello.d/src/include/hello2.h';
    #
    $@ = undef;
}

sub after_each {
    for (glob("hello*")) {
        -d $_ ? rmtree $_ : unlink $_;
    }
}


###
### test target
###
my $T = $ENV{'TEST'};


###
### sys
###
if (_test_p("sys")) {
    before_each();
    if ("os command specified") {
        ok(! -e 'hello2.c');
        ob_start();
        sys "cat -n hello.c > hello2.c";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(-e 'hello2.c');
        ok($output eq "\$ cat -n hello.c > hello2.c\n");
        #
        open FH, 'hello.c'  or die $!;
        my @lines = <FH>;
        close FH;
        my $i = 0;
        my @buf = ();
        my $i = 0;
        my $expected = join "", map { sprintf("%6d\t%s", ++$i, $_) } @lines;
        ok(read_file('hello2.c') eq $expected);
    }
    if ("os cmmand failed then report error") {
        ok(! $@);
        ob_start();
        eval { sys "cat -n hello999.c 2>/dev/null"; };
        my $output = ob_get_clean();
        #
        ok($@ eq "*** command failed (status=256).\n");
        $@ = undef;
    }
    after_each();
}


###
### sys_f
###
if (_test_p("sys_f")) {
    before_each();
    if ("os command specified") {
        ok(! -e 'hello2.c');
        ob_start();
        sys_f "cat -n hello.c > hello2.c";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(-e 'hello2.c');
        ok($output eq "\$ cat -n hello.c > hello2.c\n");
        #
        open FH, 'hello.c'  or die $!;
        my @lines = <FH>;
        close FH;
        my $i = 0;
        my @buf = ();
        my $i = 0;
        my $expected = join "", map { sprintf("%6d\t%s", ++$i, $_) } @lines;
        ok(read_file('hello2.c') eq $expected);
    }
    if ("os cmmand failed then error is not reported") {
        ob_start();
        eval { sys_f "cat -n hello999.c 2>/dev/null"; };
        my $output = ob_get_clean();
        #
        ok(! $@);
    }
    after_each();
}


###
### echo, echo_n
###
if (_test_p("echo")) {
    before_each();
    if ("argument doesn't contain any meta character") {
        ob_start();
        echo("foo", "bar");
        my $output = ob_get_clean();
        ok($output eq "\$ echo foo bar\nfoo bar\n");
    }
    if ("argument contains meta character") {
        ob_start();
        echo("hello.d/src/*/hello.?");
        my $output = ob_get_clean();
        my $expected = <<'END';
$ echo hello.d/src/*/hello.?
hello.d/src/include/hello.h hello.d/src/lib/hello.c
END
        ;
        ok($output eq $expected);
    }
    after_each();
}
#
if (_test_p("echo_n")) {
    before_each();
    if ("argument doesn't contain any meta character") {
        ob_start();
        echo_n("foo", "bar");
        my $output = ob_get_clean();
        ok($output eq "\$ echo foo bar\nfoo bar");
    }
    if ("argument contains meta character") {
        ob_start();
        echo_n("hello.d/src/*/hello.?");
        my $output = ob_get_clean();
        my $expected = <<'END';
$ echo hello.d/src/*/hello.?
hello.d/src/include/hello.h hello.d/src/lib/hello.c
END
        ;
        chomp $expected;
        ok($output eq $expected);
    }
    after_each();
}


###
### cp, cp_p
###
sub _test_cp {
    before_each();
    my ($func, $cmd) = @_;
    my $op = $func =~ /_pr?$/ ? '==' : '>';
    if ("file to file") {
        ok(! -e "hello2.c");
        ob_start();
        eval "$func('hello.c', 'hello2.c');";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(-f "hello2.c");
        ok($output eq "\$ $cmd hello.c hello2.c\n");
        ok(read_file("hello2.c") eq $HELLO_C);
        ok(eval "mtime('hello2.c') $op mtime('hello.c')");
    }
    if ("file to dir") {
        my $src = "./hello.c";
        my $base = basename($src);
        my $dst = "hello.d/tmp";
        ok(! -e "$dst/$base");
        ob_start();
        eval "$func(\$src, \$dst);";
        my $output = ob_get_clean();
        die $@ if $@;
        ok(-f "$dst/$base");
        #
        ok($output eq "\$ $cmd $src $dst\n");
        ok(read_file("$dst/$base") eq $HELLO_C);
        ok(eval "mtime('$dst/$base') $op mtime('$src')");
    }
    if ("ERROR: dir to dir") {
        my ($src, $dst) = ("hello.d/src", "hello.d/tmp/hoge");
        ok(! $@);
        ob_start();
        eval "$func(\$src, \$dst);";
        my $output = ob_get_clean();
        ok($@ eq "$func: hello.d/src: cannot copy directory (use 'cp_r' instead).\n");
        $@ = undef;
        ok(! -e $dst);
    }
    if ("ERROR: dir to file") {
        my ($src, $dst) = ("hello.d/src", "hello.h");
        ok(-f $dst);
        ok(! $@);
        ob_start();
        eval "$func(\$src, \$dst);";
        my $output = ob_get_clean();
        ok($@ eq "$func: hello.d/src: cannot copy directory to file.\n");
        $@ = undef;
    }
    if ("files into dir") {
        my $src = "hello.d/src";
        my $dst = "hello.d/tmp";
        unlink glob("$dst/*");
        ob_start();
        eval "$func('$src/lib/hello.c', '$src/include/hello.h', '$src/include/hello2.h', \$dst);";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ $cmd $src/lib/hello.c $src/include/hello.h $src/include/hello2.h $dst\n");
        ok(-f "$dst/hello.c");
        ok(-f "$dst/hello.h");
        ok(-f "$dst/hello2.h");
        ok(eval "mtime('$dst/hello.c')  $op  mtime('$src/lib/hello.c')");
        ok(eval "mtime('$dst/hello.h')  $op  mtime('$src/include/hello.h')");
        ok(eval "mtime('$dst/hello2.h') $op  mtime('$src/include/hello2.h')");
    }
    if ("handles metachars") {
        my $src = "hello.d/src";
        my $dst = "hello.d/tmp";
        unlink glob("$dst/*");
        ob_start();
        eval "$func('$src/lib/*.c', '$src/include/*.h', \$dst)";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(eval "mtime('$dst/hello.c')  $op  mtime('$src/lib/hello.c')");
        ok(eval "mtime('$dst/hello.h')  $op  mtime('$src/include/hello.h')");
        ok(eval "mtime('$dst/hello2.h') $op  mtime('$src/include/hello2.h')");
    }
    after_each();
}

if (_test_p("cp")) {
    _test_cp("cp", "cp");
}

if (_test_p("cp_p")) {
    _test_cp("cp_p", "cp -p");
}


###
### cp_r, cp_pr
###
sub _test_cp_r {
    before_each();
    my ($func, $cmd) = @_;
    my $op = $func =~ /_pr?$/ ? '==' : '>';
    if ("dir to dir which exists") {
        ok(-d 'hello.d/tmp');
        ok(! -e 'hello.d/tmp/src');
        ob_start();
        eval "$func('hello.d/src', 'hello.d/tmp');";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ $cmd hello.d/src hello.d/tmp\n");
        ok(-d 'hello.d/tmp/src');
        ok(-d 'hello.d/tmp/src/lib');
        ok(-f 'hello.d/tmp/src/lib/hello.c');
        ok(-d 'hello.d/tmp/src/include');
        ok(-f 'hello.d/tmp/src/include/hello.h');
        ok(-f 'hello.d/tmp/src/include/hello2.h');
        ok(eval "mtime('hello.d/tmp/src/lib/hello.c')      $op mtime('hello.d/src/lib/hello.c')");
        ok(eval "mtime('hello.d/tmp/src/include/hello.h')  $op mtime('hello.d/src/include/hello.h')");
        ok(eval "mtime('hello.d/tmp/src/include/hello2.h') $op mtime('hello.d/src/include/hello2.h')");
        rmtree('hello.d/tmp/src');
    }
    if ("dir to dir which doesn't exist") {
        ok(! -e 'hello.d/tmp/src2');
        ob_start();
        eval "$func('hello.d/src', 'hello.d/tmp/src2');";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ $cmd hello.d/src hello.d/tmp/src2\n");
        ok(-d 'hello.d/tmp/src2');
        ok(-d 'hello.d/tmp/src2/lib');
        ok(-f 'hello.d/tmp/src2/lib/hello.c');
        ok(-d 'hello.d/tmp/src2/include');
        ok(-f 'hello.d/tmp/src2/include/hello.h');
        ok(-f 'hello.d/tmp/src2/include/hello2.h');
        ok(eval "mtime('hello.d/tmp/src2/lib/hello.c')      $op mtime('hello.d/src/lib/hello.c')");
        ok(eval "mtime('hello.d/tmp/src2/include/hello.h')  $op mtime('hello.d/src/include/hello.h')");
        ok(eval "mtime('hello.d/tmp/src2/include/hello2.h') $op mtime('hello.d/src/include/hello2.h')");
        rmtree('hello.d/tmp/src2');
    }
    if ("ERROR: dir to file") {
        my ($src, $dst) = ("hello.d/src", "hello.h");
        ok(-f $dst);
        ok(! $@);
        ob_start();
        eval "$func(\$src, \$dst);";
        my $output = ob_get_clean();
        ok($@ eq "$func: hello.d/src: cannot copy directory to file.\n");
        $@ = undef;
    }
    if ("files and directories into exisiting dir") {
        write_file('hello.d/hello.c', $HELLO_C);
        write_file('hello.d/hello.h', $HELLO_H);
        my $t = time() - 99;
        utime $t, $t, ('hello.d/hello.c', 'hello.d/hello.h');
        #
        ok(! -e 'hello.d/tmp/hello.c');
        ok(! -e 'hello.d/tmp/hello.h');
        ok(! -e 'hello.d/tmp/src');
        ob_start();
        eval "$func('hello.d/hello.c', 'hello.d/hello.h', 'hello.d/src', 'hello.d/tmp')";
        my $output = ob_get_clean();
        die $@ if $@;
        ok($output eq "\$ $cmd hello.d/hello.c hello.d/hello.h hello.d/src hello.d/tmp\n");
        #
        ok(-f 'hello.d/tmp/hello.c');
        ok(-f 'hello.d/tmp/hello.h');
        ok(-d 'hello.d/tmp/src');
        ok(-d 'hello.d/tmp/src/lib');
        ok(-f 'hello.d/tmp/src/lib/hello.c');
        ok(-d 'hello.d/tmp/src/include');
        ok(-f 'hello.d/tmp/src/include/hello.h');
        ok(-f 'hello.d/tmp/src/include/hello2.h');
        ok(eval "mtime('hello.d/tmp/hello.c') $op mtime('hello.d/hello.c')");
        ok(eval "mtime('hello.d/tmp/hello.h') $op mtime('hello.d/hello.h')");
        ok(eval "mtime('hello.d/tmp/src/lib/hello.c') $op mtime('hello.d/src/lib/hello.c')");
        ok(eval "mtime('hello.d/tmp/src/include/hello.h') $op mtime('hello.d/src/include/hello.h')");
        ok(eval "mtime('hello.d/tmp/src/include/hello2.h') $op mtime('hello.d/src/include/hello2.h')");
        rmtree('hello.d/tmp/src');
        unlink glob('hello.d/tmp/*');
    }
    if ("handles meta-chracters") {
        write_file('hello.d/hello.c', $HELLO_C);
        write_file('hello.d/hello.h', $HELLO_H);
        my $t = time() - 99;
        utime $t, $t, ('hello.d/hello.c', 'hello.d/hello.h');
        #
        ok(! -e 'hello.d/tmp/hello.c');
        ok(! -e 'hello.d/tmp/hello.h');
        ok(! -e 'hello.d/tmp/src');
        ob_start();
        eval "$func('hello.d/hello.*', 'hello.d/sr?', 'hello.d/tmp')";
        my $output = ob_get_clean();
        die $@ if $@;
        ok($output eq "\$ $cmd hello.d/hello.* hello.d/sr? hello.d/tmp\n");
        #
        ok(-f 'hello.d/tmp/hello.c');
        ok(-f 'hello.d/tmp/hello.h');
        ok(-d 'hello.d/tmp/src');
        ok(-d 'hello.d/tmp/src/lib');
        ok(-f 'hello.d/tmp/src/lib/hello.c');
        ok(-d 'hello.d/tmp/src/include');
        ok(-f 'hello.d/tmp/src/include/hello.h');
        ok(-f 'hello.d/tmp/src/include/hello2.h');
        ok(eval "mtime('hello.d/tmp/hello.c') $op mtime('hello.d/hello.c')");
        ok(eval "mtime('hello.d/tmp/hello.h') $op mtime('hello.d/hello.h')");
        ok(eval "mtime('hello.d/tmp/src/lib/hello.c') $op mtime('hello.d/src/lib/hello.c')");
        ok(eval "mtime('hello.d/tmp/src/include/hello.h') $op mtime('hello.d/src/include/hello.h')");
        ok(eval "mtime('hello.d/tmp/src/include/hello2.h') $op mtime('hello.d/src/include/hello2.h')");
        rmtree('hello.d/tmp/src');
        unlink glob('hello.d/tmp/*');
    }
    if ("ERROR: files and directories into not-exisiting dir") {
        ok(! -e 'hello.d/tmp2');
        ok(! $@);
        ob_start();
        eval "$func('hello.d/hello.c', 'hello.d/hello.h', 'hello.d/src/lib', 'hello.d/tmp2')";
        my $output = ob_get_clean();
        ok($@ eq "$func: hello.d/tmp2: directory not found.\n");
        $@ = undef;
    }
    after_each();
}

if (_test_p("cp_r")) {
    _test_cp_r("cp_r", "cp -r");
}

if (_test_p("cp_pr")) {
    _test_cp_r("cp_pr", "cp -pr");
}


###
### mkdir, mkdir_p
###
if (_test_p('mkdir')) {
    before_each();
    if ("unexisted path is specified then create directory") {
        my ($path1, $path2) = ('hello.d/foo', 'hello.d/bar');
        ok(! -e $path1 && ! -e $path2);
        ob_start();
        &mkdir($path1, $path2);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ mkdir $path1 $path2\n");
        ok(-d $path1);
        ok(-d $path2);
    }
    if ("existing path is specified then error raises") {
        my $path = "hello.d/tmp";
        ok(-d $path);
        ob_start();
        eval { mkdir($path); };
        my $output = ob_get_clean();
        #die $@ if $@;
        #
        ok($output eq "\$ mkdir $path\n");
        ok($@ eq "mkdir: $path: already exists.\n");
        $@ = undef;
    }
    if ("deep path is specified") {
        my $path = "hello.d/tmp3/test";
        ok(! -e "hello.d/tmp3");
        ob_start();
        eval { mkdir($path); };
        my $output = ob_get_clean();
        #die $@ if $@;
        #
        ok($output eq "\$ mkdir $path\n");
        ok($@ eq "mkdir: hello.d/tmp3/test: No such file or directory\n");
        $@ = undef;
    }
    after_each();
}
#
if (_test_p('mkdir_p')) {
    before_each();
    if ("deep path specified then create it") {
        my ($path1, $path2) = ('hello.d/foo/d1', 'hello.d/bar/d2');
        ok(! -e $path1 && ! -e $path2);
        ob_start();
        mkdir_p($path1, $path2);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ mkdir -p $path1 $path2\n");
        ok(-d $path1);
        ok(-d $path2);
    }
    if ("file is specified then error raises") {
        my $path = "hello.d/src/lib/hello.c";
        ok(-f $path);
        ob_start();
        eval { mkdir_p($path); };
        my $output = ob_get_clean();
        #die $@ if $@;
        #
        ok($output eq "\$ mkdir -p $path\n");
        ok($@ eq "mkdir_p: $path: already exists.\n");
        $@ = undef;
    }
    after_each();
}


###
### rm, rm_f, rm_r, rm_rf
###
if (_test_p('rm')) {
    before_each();
    if ("filenames are specified") {
        my ($path1, $path2) = "hello.d/hello.*", "hello.d/tmp/foo.c";
        write_file("hello.d/hello.c", $HELLO_C);
        write_file("hello.d/hello.h", $HELLO_H);
        write_file("hello.d/tmp/foo.c", $HELLO_C);
        ok(-f "hello.d/hello.c");
        ok(-f "hello.d/hello.h");
        ok(-f "hello.d/tmp/foo.c");
        #
        ob_start();
        rm("hello.d/hello.*", "hello.d/tmp/foo.c");
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e "hello.d/hello.c");
        ok(! -e "hello.d/hello.h");
        ok(! -e "hello.d/tmp/foo.c");
        ok($output eq "\$ rm hello.d/hello.* hello.d/tmp/foo.c\n");
    }
    if ("directory name is specified then report error") {
        my $path = "hello.d/tmp";
        ob_start();
        eval { rm($path); };
        my $output = ob_get_clean();
        #
        ok($@ eq "rm: $path: can't remove directory (try 'rm_r' instead).\n");
        ok($output eq "\$ rm $path\n");
        $@ = undef;
    }
    if ("unexisting filename specified then error is reported") {
        ob_start();
        eval { rm("hello.d/tmp/bar.txt"); };
        my $output = ob_get_clean();
        #
        ok($@ eq "rm: hello.d/tmp/bar.txt: not found.\n");
        $@ = undef;
    }
    after_each();
}
#
if (_test_p("rm_f")) {
    before_each();
    if ("unexisitng filename specified then error is not reported") {
        my $path = "hello.d/tmp/bar.txt";
        ob_start(! -e $path);
        eval { rm_f($path); };
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ rm -f $path\n");
    }
    if ("directory name is specified then report error") {
        my $path = "hello.d/tmp";
        ob_start();
        eval { rm_f($path); };
        my $output = ob_get_clean();
        #
        ok($@ eq "rm_f: $path: can't remove directory (try 'rm_r' instead).\n");
        ok($output eq "\$ rm -f $path\n");
        $@ = undef;
    }
    after_each();
}
#
if (_test_p("rm_r")) {
    before_each();
    if ("directory is specified") {
        write_file("hello.d/hello.c", $HELLO_C);
        ok(-f "hello.d/hello.c" && -d "hello.d/src" && -d "hello.d/tmp");
        #
        ob_start();
        rm_r("hello.d/*");
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e "hello.d/hello.c" && ! -e "hello.d/src" && ! -e "hello.d/tmp");
        ok($output eq "\$ rm -r hello.d/*\n");
    }
    if ("unexisting filename or directory name specified then report error") {
        my $path = "hello.d/tmp3";
        ob_start();
        eval { rm_r($path); };
        my $output = ob_get_clean();
        #
        ok($@ eq "rm_r: $path: not found.\n");
        ok($output eq "\$ rm -r $path\n");
        $@ = undef;
    }
    after_each();
}
#
if (_test_p("rm_rf")) {
    before_each();
    if ("unexisitng file or directory specified") {
        my $path = "hello.d/tmp3";
        ok(! -e $path);
        #
        ob_start();
        eval { rm_rf($path); };
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! $@);
        ok($output eq "\$ rm -rf $path\n");
    }
    if ("file or directory specified") {
        write_file("hello.d/hello.c", $HELLO_C);
        ok(-f "hello.d/hello.c" && -d "hello.d/src" && -d "hello.d/tmp");
        my $path = "hello.d/*";
        #
        ob_start();
        eval { rm_rf($path); };
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e "hello.d/hello.c" && ! -e "hello.d/src" && ! -e "hello.d/tmp");
        ok($output eq "\$ rm -rf $path\n");
    }
    after_each();
}


###
### rmdir
###
if (_test_p('rmdir')) {
    if ("empty directory specified") {
        before_each();
        #
        my $path = "hello.d/tmp";
        ok(-d $path);
        #
        ob_start();
        rmdir $path;
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ rmdir $path\n");
        ok(! -e $path);
        #
        after_each();
    }
    if ("non-existing directory specified then report error") {
        before_each();
        #
        my $path = "hello.d/tmp3";
        ok(! -e $path);
        #
        ob_start();
        eval { rmdir $path; };
        my $output = ob_get_clean();
        #
        ok($output eq "\$ rmdir $path\n");
        ok($@ eq "rmdir: $path: not found.\n");
        #
        after_each();
    }
    if ("not-empty directory specified then report error") {
        before_each();
        #
        my $path = "hello.d/src";
        ok(-d $path);
        #
        ob_start();
        eval { rmdir $path; };
        my $output = ob_get_clean();
        #die $@ if $@;
        #
        ok($output eq "\$ rmdir $path\n");
        ok($@ eq "rmdir: hello.d/src: Directory not empty\n");
        ok(-e $path);
        #
        after_each();
    }
}


###
### mv
###
if (_test_p('mv')) {
    if ("move file to new") {
        before_each();
        #
        my ($path1, $path2) = ("hello.c", "hello.d/tmp/foo.c");
        ok(-f $path1);
        ok(! -e $path2);
        #
        ob_start();
        mv($path1, $path2);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e $path1);
        ok(-f $path2);
        ok($output eq "\$ mv $path1 $path2\n");
        #
        after_each();
    }
    if ("move dir to new") {
        before_each();
        #
        my ($path1, $path2) = ("hello.d/src", "hello.d/src3");
        ok(-d $path1);
        ok(! -e $path2);
        #
        ob_start();
        mv($path1, $path2);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e $path1);
        ok(-d $path2);
        ok($output eq "\$ mv $path1 $path2\n");
        #
        after_each();
    }
    if ("move file to file") {
        before_each();
        #
        my ($path1, $path2) = ("hello.c", "hello.h");
        ok(-f $path1);
        ok(-f $path2);
        #
        ob_start();
        mv($path1, $path2);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e $path1);
        ok(-f $path2);
        ok($output eq "\$ mv $path1 $path2\n");
        #
        after_each();
    }
    if ("move file to dir") {
        before_each();
        #
        my ($path1, $path2) = ("hello.d/src/lib/hello.c", "hello.d/tmp");
        ok(-f $path1);
        ok(-d $path2);
        #
        ob_start();
        mv($path1, $path2);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e $path1);
        ok(-f "$path2/hello.c");
        ok($output eq "\$ mv $path1 $path2\n");
        #
        after_each();
    }
    if ("move dir to dir") {
        before_each();
        #
        my ($path1, $path2) = ("hello.d/src", "hello.d/tmp");
        ok(-d $path1);
        ok(-d $path2);
        #
        ob_start();
        mv($path1, $path2);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! -e $path1);
        ok(-d "$path2/src");
        ok($output eq "\$ mv $path1 $path2\n");
        #
        after_each();
    }
    if ("move dir to file then report error") {
        before_each();
        #
        my ($path1, $path2) = ("hello.d/src", "hello.c");
        ok(-d $path1);
        ok(-f $path2);
        #
        ob_start();
        eval { mv($path1, $path2); };
        my $output = ob_get_clean();
        #
        ok($@ eq "mv: $path2: not a directory.\n");
        ok($output eq "\$ mv $path1 $path2\n");
        #
        after_each();
    }
    if ("move unexisting file then report error") {
        before_each();
        #
        my ($path1, $path2) = ("hello.d/tmp3", "hello.d/tmp");
        ok(! -d $path1);
        #
        ob_start();
        eval { mv($path1, $path2); };
        my $output = ob_get_clean();
        #
        ok($@ eq "mv: $path1: not found.\n");
        ok($output eq "\$ mv $path1 $path2\n");
        #
        after_each();
    }
    #
    if ("move files or directories into a directory") {
        before_each();
        #
        my @src = ("hello.{c,h}", "hello.d/src/*");
        my $dst = "hello.d/tmp";
        ok(-d $dst);
        #ok(-f "hello.c" && -f "hello.h" && -d "hello.d/src/lib" && -d "hello.d/src/include");
        #ok(! -e "$dst/hello.c" && ! -e "$dst/hello.h" && ! -e "$dst/lib" && ! -e "$dst/include");
        ok(-f "hello.c");
        ok(-f "hello.h");
        ok(-d "hello.d/src/lib");
        ok(-d "hello.d/src/include");
        ok(! -e "$dst/hello.c");
        ok(! -e "$dst/hello.h");
        ok(! -e "$dst/lib");
        ok(! -e "$dst/include");
        #
        ob_start();
        mv(@src, $dst);
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ mv ".join(' ', @src)." $dst\n");
        ok(! -e "hello.c");
        ok(! -e "hello.h");
        ok(! -e "hello.d/src/lib");
        ok(! -e "hello.d/src/include");
        ok(-f "$dst/hello.c");
        ok(-f "$dst/hello.h");
        ok(-d "$dst/lib");
        ok(-d "$dst/include");
        #
        after_each();
    }
    if ("move files or directories into non-existing directory then report error") {
        before_each();
        #
        my @src = ("hello.{c,h}", "hello.d/src/*", "hello.txt");
        my $dst = "hello.d/tmp";
        ok(-f "hello.c");
        ok(-f "hello.h");
        ok(! -e "hello.txt");
        #
        ob_start();
        eval { mv(@src, $dst); };
        my $output = ob_get_clean();
        #
        ok($@ eq "mv: hello.txt: not found.\n");
        ok(-f "hello.c");
        ok(-f "hello.h");
        #
        after_each();
    }

}


###
### store, store_p
###
sub _test_store {
    my ($func, $cmd, $op) = @_;
    if ("copy files to dir with keeping file path") {
        before_each();
        #
        my $dst = "hello.d/tmp";
        #
        ob_start();
        eval "$func('*.{c,h}', 'hello.d/src/*/*.{c,h}', '$dst')";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ $cmd *.{c,h} hello.d/src/*/*.{c,h} $dst\n");
        ok(-f "hello.c");
        ok(-f "hello.h");
        ok(-f "hello.d/src/lib/hello.c");
        ok(-f "hello.d/src/include/hello.h");
        ok(-f "hello.d/src/include/hello2.h");
        ok(-f "$dst/hello.c");
        ok(-f "$dst/hello.h");
        ok(-f "$dst/hello.d/src/lib/hello.c");
        ok(-f "$dst/hello.d/src/include/hello.h");
        ok(-f "$dst/hello.d/src/include/hello2.h");
        ok(eval "mtime('$dst/hello.c') $op mtime('hello.c')");
        ok(eval "mtime('$dst/hello.h') $op mtime('hello.h')");
        ok(eval "mtime('$dst/hello.d/src/lib/hello.c') $op mtime('hello.d/src/lib/hello.c')");
        ok(eval "mtime('$dst/hello.d/src/include/hello.h') $op mtime('hello.d/src/include/hello.h')");
        ok(eval "mtime('$dst/hello.d/src/include/hello2.h') $op mtime('hello.d/src/include/hello2.h')");
        #
        after_each();
    }
    if ("only an argument specified then report error") {
        before_each();
        #
        ob_start();
        eval "$func('hello.d/tmp');";
        my $output = ob_get_clean();
        ok($@ eq "$func: at least two file or directory names are required.\n");
        #
        after_each();
    }
    if ("destination directory doesn't exist then report error") {
        before_each();
        #
        ob_start();
        eval "$func('*.foo', 'foo.d');";
        my $output = ob_get_clean();
        ok($@ eq "$func: foo.d: directory not found.\n");
        #
        after_each();
    }
    if ("destination is not a directory then report error") {
        before_each();
        #
        ob_start();
        eval "$func('*.foo', 'hello.c');";
        my $output = ob_get_clean();
        ok($@ eq "$func: hello.c: not a directory.\n");
        #
        after_each();
    }
    if ("source file doesn't exist then report error") {
        before_each();
        #
        ob_start();
        eval "$func('hello.c', '*.foo', 'hello.d/tmp');";
        my $output = ob_get_clean();
        ok($@ eq "$func: *.foo: not found.\n");
        ok(! -e 'hello.d/tmp/hello.c');
        #
        after_each();
    }
}
#
if (_test_p('store')) {
    _test_store('store', 'store', '>');
}
if (_test_p('store_p')) {
    _test_store('store_p', 'store -p', '==');
}


###
### cd
###
if (_test_p("cd")) {
    if ("both dirname and closure are specified") {
        before_each();
        #
        my $cwd = getcwd();
        #
        ob_start();
        cd "hello.d/src/include", sub { echo "*.h"; };
        my $output = ob_get_clean();
        die $@ if $@;
        #
        my $expected = <<END;
\$ cd hello.d/src/include
\$ echo *.h
hello.h hello2.h
\$ cd -  # back to $cwd
END
        ;
        ok($output eq $expected);
        ok(getcwd() eq $cwd);
        #
        after_each();
    }
    if ("only directory name specified") {
        before_each();
        #
        my $cwd = getcwd();
        #
        ob_start();
        cd "hello.d/src/lib";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ cd hello.d/src/lib\n");
        ok(getcwd() eq "$cwd/hello.d/src/lib");
        #
        chdir $cwd;
        #
        after_each();
    }
    if ("unexisting directory specified then report error") {
        before_each();
        #
        my $cwd = getcwd();
        my $path = "hello.d/tmp3";
        ok(! -e $path);
        #
        ob_start();
        eval { cd $path; };
        my $output = ob_get_clean();
        #
        ok($@ eq "cd: $path: directory not found.\n");
        ok(getcwd() eq $cwd);
        #
        after_each();
    }
    if ("file name specified then report error") {
        before_each();
        #
        my $cwd = getcwd();
        my $path = "hello.d/src/lib/hello.c";
        ok(-f $path);
        #
        ob_start();
        eval { cd $path; };
        my $output = ob_get_clean();
        #
        ok($@ eq "cd: $path: not a directory.\n");
        ok(getcwd() eq $cwd);
        #
        after_each();
    }
    if ("directory name is not specified then report error") {
        before_each();
        #
        my $cwd = getcwd();
        #
        ob_start();
        eval { cd; };
        my $output = ob_get_clean();
        #
        ok($@ eq "cd: directory name required.\n");
        ok(getcwd() eq $cwd);
        #
        after_each();
    }
}


###
### edit
###
if (_test_p("edit")) {
    if ("filenames specified with closure") {
        before_each();
        #
        ob_start();
        edit { s/\$COPYRIGHT\$/MIT License/g; $_ } "hello.d/src/*/*.c", "hello.d/src/*/*.h";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok($output eq "\$ edit hello.d/src/*/*.c hello.d/src/*/*.h\n");
        my $expected = $HELLO_C;
        $expected =~ s/\$COPYRIGHT\$/MIT License/g;
        ok($expected ne $HELLO_C);
        ok(read_file("hello.d/src/lib/hello.c") eq $expected);
        my $expected = $HELLO_H;
        $expected =~ s/\$COPYRIGHT\$/MIT License/g;
        ok($expected ne $HELLO_H);
        ok(read_file("hello.d/src/include/hello.h") eq $expected);
        ok(read_file("hello.d/src/include/hello2.h") eq $expected);
    }
    if ("directory names are specified") {
        before_each();
        #
        ob_start();
        edit { s/\$COPYRIGHT\$/MIT License/g; $_ } "hello.d/src";
        my $output = ob_get_clean();
        die $@ if $@;
        #
        ok(! $@);
        #
        after_each();
    }
}


###
### after_all()
###
chdir ".."  or die $!;
rmtree("_sandbox")  or die $!;
