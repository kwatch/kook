# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Cwd;
use Test::Simple tests => 42;

use Kook::Main;
use Kook::Utils ('write_file');

use IPC::Open3;
use Symbol;

sub _system {
    my ($command) = @_;
    my ($IN, $OUT, $ERR) = (gensym, gensym, gensym);
    open3($IN, $OUT, $ERR, $command);
    my @output = <$OUT>;
    my @error  = <$ERR>;
    close $IN;
    close $OUT;
    close $ERR;
    return join("", @output), join("", @error);
}


###
### before all
###
mkdir "_sandbox" unless -d "_sandbox";
chdir "_sandbox"  or die;


###
### hello1.c, hello2.c, hello.h
###
my $HELLO_H_TXT = <<'END';
/*extern char *command;*/
#define COMMAND "hello"
void print_args(int argc, char *argv[]);
END
    ;
my $HELLO1_C = <<'END';
#include "hello.h"
/*char *command = "hello";*/
int main(int argc, char *argv[]) {
    print_args(argc, argv);
    return 0;
}
END
    ;
my $HELLO2_C = <<'END';
#include <stdio.h>
#include "hello.h"
void print_args(int argc, char *argv[]) {
    int i;
    printf("%s: argc=%d\n", COMMAND, argc);
    for (i = 0; i < argc; i++) {
        printf("%s: argv[%d]: %s\n", COMMAND, i, argv[i]);
    }
}
END
    ;

write_file("hello.h.txt", $HELLO_H_TXT);
write_file("hello1.c", $HELLO1_C);
write_file("hello2.c", $HELLO2_C);

###
### Kookbook.pl
###
my $KOOKBOOK = <<'END';
recipe "build", {
    desc => "build all files",
    ingreds => ["hello"],
};

recipe "hello", {
    #ingreds => ["foo.o", "bar.o"],
    desc    => "build hello command",
    kind    => "file",
    ingreds => ["hello1.o", "hello2.o"],
    method  => sub {
        my ($c) = @_;
        my $s = join " ", @{$c->{ingreds}};
        sys "gcc -o $c->{product} $s";
    }
};

recipe "*.o", {
    ingreds => ['$(1).c', 'hello.h'],
    desc    => "compile *.c",
    method  => sub {
        my ($c) = @_;
        sys "gcc -c $c->{ingred}";
    }
};

recipe "hello.h", {
    ingreds => ["hello.h.txt"],
    method => sub {
        my ($c) = @_;
        sys "cp $c->{ingred} $c->{product}";
    }
};

recipe "test1", {
    desc   => "test of spices",
    spices => ["-v: verbose", "-f file: file", "-i[N]: indent", "-D:", "--name=str: name string"],
    method => sub {
        my ($c, $opts, $rest) = @_;
        #my @arr = map { repr($_).'=>'.repr($opts->{$_}) } sort keys %$opts;
        #print "opts={", join(", ", @arr), "}\n";
        my $s = join ", ", map { repr($_).'=>'.repr($opts->{$_}) } sort keys %$opts;
        print "opts={", $s, "}\n";
        print "rest=", repr($rest), "\n";
    }
};
END
    ;

write_file("Kookbook.pl", $KOOKBOOK);



###
### before_each(), after_each()
###
sub before_each {
    #for (qw(hello hello1.o hello2.o hello.h)) { unlink $_ if -f $_; }
}
sub after_each {
    #unlink(glob("hello*"));
    for (qw(hello hello1.o hello2.o hello.h)) { unlink $_ if -f $_; }
}


###
### do test
###


###
### invoke recipe
###
before_each();
if ("recipe is invoked") {
    ## 1st
    if ("recipe is invoked then hello should be created") {
        my $output = `plkook build`;
        my $expected = <<'END';
### **** hello.h (recipe=hello.h)
$ cp hello.h.txt hello.h
### *** hello1.o (recipe=*.o)
$ gcc -c hello1.c
### *** hello2.o (recipe=*.o)
$ gcc -c hello2.c
### ** hello (recipe=hello)
$ gcc -o hello hello1.o hello2.o
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }
    ## 2nd
    if ("invoked again then all recipes should be skipped)") {
        sleep 1;
        my $output = `plkook build`;
        my $expected = <<'END';
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }
    ## 3rd
    if ("only hello.h is touched then hello recipe should be skipped because content of *.o is not changed") {
        my $now = time();
        utime $now, $now, "hello.h";
        my $output = `plkook build`;
        my $expected = <<'END';
### *** hello1.o (recipe=*.o)
$ gcc -c hello1.c
### *** hello2.o (recipe=*.o)
$ gcc -c hello2.c
### ** hello recipe=hello
$ touch hello   # skipped
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }
    ## 4th
    if ("hello.h.txt is updated then all recipes should not be skipped)") {
        sleep 1;
        my $s = $HELLO_H_TXT;
        $s =~ s/hello/HELLO/;
        write_file("hello.h.txt", $s);
        my $output = `plkook build`;
        my $expected = <<'END';
### **** hello.h (recipe=hello.h)
$ cp hello.h.txt hello.h
### *** hello1.o (recipe=*.o)
$ gcc -c hello1.c
### *** hello2.o (recipe=*.o)
$ gcc -c hello2.c
### ** hello (recipe=hello)
$ gcc -o hello hello1.o hello2.o
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }
}
after_each();


###
### -h
###
before_each();
if ("option -h specified") {
    my $output = `plkook -hlL`;
    #my $main = Kook::MainCommand->new(["-hlL"], "plkook");
    #$main->invoke();
    my $expected = <<'END';
plkook - build tool like Make, Rake, Ant, or Cook
  -h                  : help
  -V                  : version
  -D[N]               : debug level (default: 1)
  -q                  : quiet
  -f file             : kookbook
  -F                  : forcedly
  -n                  : not execute (dry run)
  -l                  : list public recipes
  -L                  : list all recipes
  --name=value        : property name and value
  --name              : property name and value(=True)
END
    ;
    ok($output eq $expected);
}
after_each();


###
### -V
###
before_each();
if ("option -V specified") {
    my $output = `plkook -V`;
    my $expected = "".$Kook::RELEASE."\n";
    ok($output eq $expected);
    ok(length($output) > 5);     # not empty
}
after_each();


###
### -l
###
before_each();
if ("option -l specified") {
    my $output = `plkook -l`;
    my $expected = <<'END';
Properties:

Task recipes
  build                : build all files
  test1                : test of spices
    -v                     verbose
    -f file                file
    -i[N]                  indent
    --name=str             name string

File recipes
  hello                : build hello command
  *.o                  : compile *.c

(Tips: it is able to separate properties into 'Properties.pl' file.)
END
    ;
    $output   =~ s/^\(Tips:.*\n//m;
    $expected =~ s/^\(Tips:.*\n//m;
    ok($output eq $expected);
}
after_each();


###
### -D
###
before_each();
if ("option -D specified") {
    my $output = `plkook -D build`;
    my $expected = <<'END';
*** debug: ++ Cookbook#find_recipe(): target=build, func=, product=build
*** debug: ++ Cookbook#find_recipe(): target=hello, func=, product=hello
*** debug: ++ Cookbook#find_recipe(): target=hello1.o, func=, product=*.o
*** debug: ++ Cookbook#find_recipe(): target=hello.h, func=, product=hello.h
*** debug: ++ Cookbook#find_recipe(): target=hello2.o, func=, product=*.o
*** debug: + begin build
*** debug: ++ begin hello
*** debug: +++ begin hello1.o
*** debug: ++++ material \'hello1.c\'
*** debug: ++++ begin hello.h
*** debug: +++++ material \'hello.h.txt\'
*** debug: ++++ create hello.h (recipe=hello.h)
### **** hello.h (recipe=hello.h)
$ cp hello.h.txt hello.h
*** debug: ++++ end hello.h (content changed)
*** debug: +++ create hello1.o (recipe=*.o)
### *** hello1.o (recipe=*.o)
$ gcc -c hello1.c
*** debug: +++ end hello1.o (content changed)
*** debug: +++ begin hello2.o
*** debug: ++++ material \'hello2.c\'
*** debug: ++++ begin hello.h
*** debug: +++++ material \'hello.h.txt\'
*** debug: ++++ skip hello.h (recipe=hello.h)
*** debug: +++ create hello2.o (recipe=*.o)
### *** hello2.o (recipe=*.o)
$ gcc -c hello2.c
*** debug: +++ end hello2.o (content changed)
*** debug: ++ create hello (recipe=hello)
### ** hello (recipe=hello)
$ gcc -o hello hello1.o hello2.o
*** debug: ++ end hello (content changed)
*** debug: + perform build (recipe=build)
### * build (recipe=build)
*** debug: + end build (content changed)
END
    ;
}
after_each();


###
### -D2
###
before_each();
if ("option -D2 specified") {
    my $output = `plkook -D2 build`;
    my $expected = <<'END';
*** debug: specific task recipes: ["build","test1"]
*** debug: specific file recipes: ["hello","hello.h"]
*** debug: generic  task recipes: []
*** debug: generic  file recipes: ["*.o"]
*** debug: ++ Cookbook#find_recipe(): target=build, func=, product=build
*** debug: ++ Cookbook#find_recipe(): target=hello, func=, product=hello
*** debug: ++ Cookbook#find_recipe(): target=hello1.o, func=, product=*.o
*** debug: ++ Cookbook#find_recipe(): target=hello.h, func=, product=hello.h
*** debug: ++ Cookbook#find_recipe(): target=hello2.o, func=, product=*.o
*** debug: + begin build
*** debug: ++ begin hello
*** debug: +++ begin hello1.o
*** debug: ++++ material 'hello1.c'
*** debug: ++++ begin hello.h
*** debug: +++++ material 'hello.h.txt'
*** debug: ++++ cannot skip: product 'hello.h' not found.
*** debug: ++++ create hello.h (recipe=hello.h)
### **** hello.h (recipe=hello.h)
$ cp hello.h.txt hello.h
*** debug: ++++ end hello.h (content changed)
*** debug: +++ cannot skip: product 'hello1.o' not found.
*** debug: +++ create hello1.o (recipe=*.o)
### *** hello1.o (recipe=*.o)
$ gcc -c hello1.c
*** debug: +++ end hello1.o (content changed)
*** debug: +++ begin hello2.o
*** debug: ++++ material 'hello2.c'
*** debug: ++++ pass hello.h (already cooked)
*** debug: +++ cannot skip: product 'hello2.o' not found.
*** debug: +++ create hello2.o (recipe=*.o)
### *** hello2.o (recipe=*.o)
$ gcc -c hello2.c
*** debug: +++ end hello2.o (content changed)
*** debug: ++ cannot skip: product 'hello' not found.
*** debug: ++ create hello (recipe=hello)
### ** hello (recipe=hello)
$ gcc -o hello hello1.o hello2.o
*** debug: ++ end hello (content changed)
*** debug: + cannot skip: task recipe should be invoked in any case.
*** debug: + perform build (recipe=build)
### * build (recipe=build)
*** debug: + end build (content changed)
END
    ;
    ok($output eq $expected);
    #
    sleep 1;
    my $now = time();
    utime $now, $now, "hello.h";
    $output = `plkook -D2 build`;
    $expected = <<'END';
*** debug: specific task recipes: ["build","test1"]
*** debug: specific file recipes: ["hello","hello.h"]
*** debug: generic  task recipes: []
*** debug: generic  file recipes: ["*.o"]
*** debug: ++ Cookbook#find_recipe(): target=build, func=, product=build
*** debug: ++ Cookbook#find_recipe(): target=hello, func=, product=hello
*** debug: ++ Cookbook#find_recipe(): target=hello1.o, func=, product=*.o
*** debug: ++ Cookbook#find_recipe(): target=hello.h, func=, product=hello.h
*** debug: ++ Cookbook#find_recipe(): target=hello2.o, func=, product=*.o
*** debug: + begin build
*** debug: ++ begin hello
*** debug: +++ begin hello1.o
*** debug: ++++ material 'hello1.c'
*** debug: ++++ begin hello.h
*** debug: +++++ material 'hello.h.txt'
*** debug: ++++ recipe for 'hello.h' can be skipped.
*** debug: ++++ skip hello.h (recipe=hello.h)
*** debug: +++ child file 'hello.h' is newer than product 'hello1.o'.
*** debug: +++ cannot skip: there is newer file in children than product 'hello1.o'.
*** debug: product 'hello1.o' is renamed to '/var/folders/FD/FDjI6Ce4H7eSxs5w+QNj+k+++TI/-Tmp-/5UHUs_n8qN'
*** debug: +++ create hello1.o (recipe=*.o)
### *** hello1.o (recipe=*.o)
$ gcc -c hello1.c
*** debug: +++ end hello1.o (content not changed, mtime updated)
*** debug: temporary file '/var/folders/FD/FDjI6Ce4H7eSxs5w+QNj+k+++TI/-Tmp-/5UHUs_n8qN' is removed.
*** debug: +++ begin hello2.o
*** debug: ++++ material 'hello2.c'
*** debug: ++++ pass hello.h (already cooked)
*** debug: +++ child file 'hello.h' is newer than product 'hello2.o'.
*** debug: +++ cannot skip: there is newer file in children than product 'hello2.o'.
*** debug: product 'hello2.o' is renamed to '/var/folders/FD/FDjI6Ce4H7eSxs5w+QNj+k+++TI/-Tmp-/lQlyRgrTBk'
*** debug: +++ create hello2.o (recipe=*.o)
### *** hello2.o (recipe=*.o)
$ gcc -c hello2.c
*** debug: +++ end hello2.o (content not changed, mtime updated)
*** debug: temporary file '/var/folders/FD/FDjI6Ce4H7eSxs5w+QNj+k+++TI/-Tmp-/lQlyRgrTBk' is removed.
*** debug: ++ recipe for 'hello' can be skipped.
### ** hello recipe=hello
*** debug: ++ touch and skip hello (recipe=hello)
$ touch hello   # skipped
*** debug: + cannot skip: task recipe should be invoked in any case.
*** debug: + perform build (recipe=build)
### * build (recipe=build)
*** debug: + end build (content changed)
END
    ;
    $output   =~ s/temporary file '.*' is removed/temporary file '...' is removed/g;
    $output   =~ s/is renamed to '.*'/is renamed to '...'/g;
    $expected =~ s/temporary file '.*' is removed/temporary file '...' is removed/g;
    $expected =~ s/is renamed to '.*'/is renamed to '...'/g;
    ok($output eq $expected);
}
after_each();


###
### -q
###
before_each();
if ("option -q specified") {
    ok(! -f "hello");
    my $output = `plkook -q build`;
    ok($output eq "");
    ok(-f "hello");
}
after_each();


###
### -f file
###
before_each();
if ("option -f specified") {
    rename "Kookbook.pl", "_Kookbook.xxx";
    #
    ok(! -f "hello");
    ok(! -f "hello1.o");
    my $output = `plkook -f _Kookbook.xxx hello1.o`;
    ok(! -f "hello");
    ok(-f "hello1.o");
    #
    rename "_Kookbook.xxx", "Kookbook.pl";
}
after_each();


###
### -F
###
before_each();
if ("option -F specified") {
    my $output = `plkook build`;
    my $expected = $output;
    #
    $output = `plkook build`;
    ok($output eq "### * build (recipe=build)\n");
    #
    $output = `plkook -F build`;
    ok($output eq $expected);
}
after_each();


###
### -n
###
before_each();
if ("option -n specified") {
    ok(! -f "hello.h");
    ok(! -f "hello");
    my $output = `plkook -n build`;
    ok(! -f "hello.h");
    ok(! -f "hello");
    my $expected = <<'END';
### **** hello.h (recipe=hello.h)
$ cp hello.h.txt hello.h
### *** hello1.o (recipe=*.o)
$ gcc -c hello1.c
### *** hello2.o (recipe=*.o)
$ gcc -c hello2.c
### ** hello (recipe=hello)
$ gcc -o hello hello1.o hello2.o
### * build (recipe=build)
END
    ;
    ok($output eq $expected);
}
after_each();


###
### spices
###
before_each();
if ("spices") {
    if ("spices specified") {
        my ($output, $errmsg) = _system 'plkook test1 -vDf file1.txt -i AAA BBB';
        my $expected = <<'END';
	### * test1 (recipe=test1)
	opts={"D"=>1, "f"=>"file1.txt", "i"=>1, "v"=>1}
	rest=["AAA","BBB"]
END
        $expected =~ s/^\t//gm;
        ok($output eq $expected);
        ok($errmsg eq "");
    }
    if ("invalid option (-ifoo) specified") {
        my ($output, $errmsg) = _system 'plkook test1 -ifoo AAA BBB';
        ok($output eq "### * test1 (recipe=test1)\n");
        ok($errmsg eq "-ifoo: integer required.\n");
    }
    if ("argument is not passed to '-f'") {
        my ($output, $errmsg) = _system 'plkook test1 -f';
        ok($output eq "### * test1 (recipe=test1)\n");
        ok($errmsg eq "-f: file required.\n");
    }
}
after_each();


###
### error: invalid options
###
before_each();
if ("invalid options specified") {
    if ("not-an-integer specified for -D") {
        my ($output, $errmsg) = _system 'plkook -Dh build';
        ok($output eq "");
        ok($errmsg eq "-Dh: integer required.\n");
    }
    if ("argument is not passed for -f") {
        my ($output, $errmsg) = _system 'plkook -f';
        ok($output eq "");
        ok($errmsg eq "-f: file required.\n");
    }
    if ("argument file of -f is not found") {
        my ($output, $errmsg) = _system 'plkook -foobar';
        ok($output eq "");
        ok($errmsg eq "-f oobar: file not found.\n");
    }
    if ("argument of -f is directory") {
        my ($output, $errmsg) = _system 'plkook -f..';
        ok($output eq "");
        ok($errmsg eq "-f ..: not a file.\n");
    }
}
after_each();


###
### error: no recipe or material
###
before_each();
if ("there is no recipes which matches to specified target") {
    my ($output, $errmsg) = _system 'plkook foobar';
    ok($output eq "");
    ok($errmsg eq "foobar: no such recipe or material.\n");
    #
    ($output, $errmsg) = _system 'plkook hello3.o';
    ok($output eq "");
    ok($errmsg eq "hello3.c: no such recipe or material (required for 'hello3.o').\n");
}
after_each();


###
### after_all
###
chdir "..";
unlink glob("_sandbox/*");
rmdir "_sandbox"  or die;

