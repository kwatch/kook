###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 17;
use File::Path;

use Kook::Commands qw(sys sys_f echo echo_n);
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
mkdir "_sandbox" unless -d "_sandbox";
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
    mkdir('hello.d');
    mkdir('hello.d/src');
    mkdir('hello.d/src/lib');
    mkdir('hello.d/src/include');
    write_file('hello.d/src/lib/hello.c', $HELLO_C);
    write_file('hello.d/src/include/hello.h',  $HELLO_H);
    write_file('hello.d/src/include/hello2.h', $HELLO_H);
    utime $t, $t, 'hello.d/src/lib/hello.c';
    utime $t, $t, 'hello.d/src/include/hello.h';
    utime $t, $t, 'hello.d/src/include/hello2.h';
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
### after_all()
###
chdir ".."  or die $!;
rmtree("_sandbox")  or die $!;
