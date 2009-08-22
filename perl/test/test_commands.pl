###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 212;
use File::Path;
use File::Basename;

use Kook::Commands qw(sys sys_f echo echo_n cp cp_p cp_r cp_pr mkdir mkdir_p);
use Kook::Utils qw(read_file write_file ob_start ob_get_clean repr has_metachar mtime);


sub _test_p {
    my ($test_name) = @_;
    return ! $ENV{'TEST'} || $ENV{'TEST'} eq $test_name;
}


my $HELLO_C = <<'END';
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
before_each();
if (_test_p("sys")) {
    ok(! -e 'hello2.c');
    ob_start();
    sys "cat -n hello.c > hello2.c";
    my $output = ob_get_clean();
    ok(-e 'hello2.c');
    #
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
    #
    ok(! $@);
    ob_start();
    eval {
        sys "cat -n hello999.c 2>/dev/null";
    };
    $output = ob_get_clean();
    ok($@);
    ok($@ eq "*** command failed (status=256).\n");
    $@ = undef;
}
after_each();


###
### sys_f
###
before_each();
if (_test_p("sys_f")) {
    ok(! -e 'hello2.c');
    ob_start();
    sys_f "cat -n hello.c > hello2.c";
    my $output = ob_get_clean();
    ok(-e 'hello2.c');
    #
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
    #
    ok(! $@);
    ob_start();
    eval {
        sys_f "cat -n hello999.c 2>/dev/null";
    };
    $output = ob_get_clean();
    ok(! $@);
}
after_each();


###
### echo, echo_n
###
before_each();
if (_test_p("echo")) {
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
}
after_each();
#
before_each();
if (_test_p("echo_n")) {
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
}
after_each();


###
### cp, cp_p
###
sub _test_cp {
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
}

before_each();
if (_test_p("cp")) {
    _test_cp("cp", "cp");
}
after_each();

before_each();
if (_test_p("cp_p")) {
    _test_cp("cp_p", "cp -p");
}
after_each();


###
### cp_r, cp_pr
###
sub _test_cp_r {
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
}

before_each();
if (_test_p("cp_r")) {
    _test_cp_r("cp_r", "cp -r");
}
after_each();

before_each();
if (_test_p("cp_pr")) {
    _test_cp_r("cp_pr", "cp -pr");
}
after_each();


###
### mkdir, mkdir_p
###
before_each();
if (_test_p('mkdir')) {
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
        eval { &mkdir($path); };
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
        eval { &mkdir($path); };
        my $output = ob_get_clean();
        #die $@ if $@;
        #
        ok($output eq "\$ mkdir $path\n");
        ok($@ eq "mkdir: hello.d/tmp3/test: No such file or directory\n");
        $@ = undef;
    }
}
after_each();
#
before_each();
if (_test_p('mkdir_p')) {
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
        eval { &mkdir_p($path); };
        my $output = ob_get_clean();
        #die $@ if $@;
        #
        ok($output eq "\$ mkdir -p $path\n");
        ok($@ eq "mkdir_p: $path: already exists.\n");
        $@ = undef;
    }
}
after_each();



###
### after_all()
###
chdir ".."  or die $!;
rmtree("_sandbox")  or die $!;
