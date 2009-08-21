# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 75;

use Kook::Cookbook;
use Kook::Kitchen;
use Kook::Utils ('write_file', 'ob_start', 'ob_get_clean');
use Kook::Config;


###
### before_all()
###
mkdir "_sandbox" unless -d "_sandbox";
chdir "_sandbox"  or die $!;


###
### helpers
###
sub _create_kitchen {
    my ($kookbook_content) = @_;
    my $bookname = '_Kookbook.pl';
    write_file($bookname, $kookbook_content);
    my $cookbook = Kook::Cookbook->new($bookname);
    my $kitchen = Kook::Kitchen->new($cookbook);
    unlink $bookname;
    return $kitchen;
}



###
### Kook::Kitchen  # tree, not looped
###
if ("recipes are not looped") {

    ### before all
    my $HELLO_C = <<'END';
	#include <stdio.h>
	#include "hello.h"
	int main(int argc, char *argv[]) {
	        printf("%s: argc=%d\n", command, argc);
	        return 0;
	}
END
    ;
    my $HELLO_H = <<'END';
	char *command = "hello";
END
    ;
    write_file('hello.c', $HELLO_C);
    write_file('hello.h', $HELLO_H);


    ### Kookbook.pl  # not looped
    my $input = <<'END';
	recipe "build", {
	    desc => "build all files",
	    ingreds => ["a.out"],
	};
	
	recipe "a.out", {
	    #ingreds => ["foo.o", "bar.o"],
	    ingreds => ["hello.o"],
	    method => sub {
	        my ($c) = @_;
	        sys "gcc *.o";
	    }
	};
	
	recipe "*.o", {
	    ingreds => ['$(1).c', '$(1).h'],
	    method => sub {
	        my ($c) = @_;
	        sys "gcc -c $c->{ingred}";
	    }
	};
END
    ;

    my $kitchen = _create_kitchen($input);

    ### create_cooking_tree()  # not looped
    my $root = $kitchen->create_cooking_tree("build");
    ok($root);
    ok($root->isa('Kook::Cooking'));
    ok($root->{product} eq "build");
    ok(@{$root->{children}} == 1);
    #
    my $cooking = $root->{children}->[0];
    ok($cooking->isa('Kook::Cooking'));
    ok($cooking->{product} eq "a.out");
    ok(@{$cooking->{children}} == 1);
    #
    $cooking = $cooking->{children}->[0];
    ok($cooking->isa('Kook::Cooking'));
    ok($cooking->{product} eq "hello.o");
    ok(@{$cooking->{children}} == 2);
    #
    my $hello_c = $cooking->{children}->[0];
    ok($hello_c->isa('Kook::Material'));
    ok($hello_c->{product} eq "hello.c");
    ok(! $hello_c->{children});
    my $hello_h = $cooking->{children}->[1];
    ok($hello_h->isa('Kook::Material'));
    ok($hello_h->{product} eq "hello.h");
    ok(! $hello_h->{children});

    ### check_cooking_tree()      # not looped
    eval {
        $kitchen->check_cooking_tree($root);
    };
    ok($@ eq "");

    ### start_cooking()
    if ("------------------- 1st\n") {
        ok(! -f "hello.o");
        ok(! -f "a.out");
        ob_start();
        $kitchen->start_cooking("build");
        my $output = ob_get_clean();
        ok(-f "hello.o");
        ok(-f "a.out");
        #
        my $expected = <<'END';
### *** hello.o (recipe=*.o)
$ gcc -c hello.c
### ** a.out (recipe=a.out)
$ gcc *.o
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }

    if ("------------------- 2nd (sleep 1 sec)\n") {
        sleep 1;
        my $ts_hello_o = (stat "hello.o")[9];
        my $ts_a_out   = (stat "a.out")[9];
        ob_start();
        $kitchen->start_cooking("build");
        my $output = ob_get_clean();
        ok((stat "hello.o")[9] == $ts_hello_o);
        ok((stat "a.out")[9] == $ts_a_out);
        #
        my $expected = <<'END';
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }

    if ("------------------- 3rd (touch hello.h)\n") {
        my $now = time();
        utime $now, $now, "hello.h";
        my $ts_hello_o = (stat "hello.o")[9];
        my $ts_a_out   = (stat "a.out")[9];
        ob_start();
        $kitchen->start_cooking("build");
        my $output = ob_get_clean();
        ok((stat "hello.o")[9] > $ts_hello_o);
        ok((stat "a.out")[9] > $ts_a_out);
        #
        my $expected = <<'END';
### *** hello.o (recipe=*.o)
$ gcc -c hello.c
### ** a.out recipe=a.out
$ touch a.out   # skipped
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }

    if ("------------------- 4th (edit hello.h)\n") {
        sleep 1;
        my $ts_hello_o = (stat "hello.o")[9];
        my $ts_a_out   = (stat "a.out")[9];
        write_file("hello.h", "char *command = \"HELLO\";\n");
        ob_start();
        $kitchen->start_cooking("build");
        my $output = ob_get_clean();
        ok((stat "hello.o")[9] > $ts_hello_o);
        ok((stat "a.out")[9] > $ts_a_out);
        #
        my $expected = <<'END';
### *** hello.o (recipe=*.o)
$ gcc -c hello.c
### ** a.out (recipe=a.out)
$ gcc *.o
### * build (recipe=build)
END
        ;
        ok($output eq $expected);
    }

    ### after all
    unlink(glob('hello*'));
    unlink('a.out') if -f 'a.out';
}



###
### Kook::Kitchen  # DAG, not looped
###
if ("recipe tree is DAG") {
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

    ### Kookbook.pl
    my $input = <<'END';
	recipe "build", {
	    desc => "build all files",
	    ingreds => ["hello"],
	};
	
	recipe "hello", {
	    #ingreds => ["foo.o", "bar.o"],
	    ingreds => ["hello1.o", "hello2.o"],
	    kind => "file",
	    method => sub {
	        my ($c) = @_;
	        my $s = join " ", @{$c->{ingreds}};
	        sys "gcc -o $c->{product} $s";
	    }
	};
	
	recipe "*.o", {
	    ingreds => ['$(1).c', 'hello.h'],
	    method => sub {
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
END
    ;

    my $kitchen = _create_kitchen($input);

    ### create_cooking_tree()  # DAG
    my $root = undef;
    my $root = $kitchen->create_cooking_tree("hello");
    ok($root);
    ok($root->isa('Kook::Cooking'));
    ok($root->{product} eq "hello");
    ok(@{$root->{children}} == 2);
    #
    my $hello1_o = $root->{children}->[0];
    ok($hello1_o->{product} eq "hello1.o");
    ok(Dumper($hello1_o->{ingreds}) eq Dumper(["hello1.c", "hello.h"]));
    ok($hello1_o->{recipe}->{product} eq "*.o");
    ok(@{$hello1_o->{children}} == 2);
    #
    my $hello2_o = $root->{children}->[1];
    ok($hello2_o->{product} eq "hello2.o");
    ok(Dumper($hello2_o->{ingreds}) eq Dumper(["hello2.c", "hello.h"]));
    ok($hello2_o->{recipe}->{product} eq "*.o");
    ok(@{$hello2_o->{children}} == 2);
    #
    my $hello1_c = $hello1_o->{children}->[0];
    ok($hello1_c->{product} eq "hello1.c");
    my $hello1_h = $hello1_o->{children}->[1];
    ok($hello1_h->{product} eq "hello.h");
    #
    my $hello2_c = $hello2_o->{children}->[0];
    ok($hello2_c->{product} eq "hello2.c");
    my $hello2_h = $hello2_o->{children}->[1];
    ok($hello2_h->{product} eq "hello.h");
    #
    ok($hello1_h == $hello2_h);   # DAG
    ok($hello1_h->{children}->[0]->{product} eq "hello.h.txt");
    ok($hello2_h->{children}->[0]->{product} eq "hello.h.txt");

    ### check_cooking_tree()      # DAG
    eval {
        $kitchen->check_cooking_tree($root);
    };
    ok($@ eq "");

    ### start_cooking()   # DAG
    if ("------------------- 1st\n") {
        ok(! -f "hello");
        ok(! -f "hello1.o");
        ok(! -f "hello2.o");
        ok(! -f "hello.h");
        ob_start();
        $kitchen->start_cooking("hello");
        my $output = ob_get_clean();
        ok( -f "hello");
        ok( -f "hello1.o");
        ok( -f "hello2.o");
        ok( -f "hello.h");
        #
        my $expected = <<'END'
### *** hello.h (recipe=hello.h)
$ cp hello.h.txt hello.h
### ** hello1.o (recipe=*.o)
$ gcc -c hello1.c
### ** hello2.o (recipe=*.o)
$ gcc -c hello2.c
### * hello (recipe=hello)
$ gcc -o hello hello1.o hello2.o
END
        ;
        ok($output eq $expected);
    }

    if ("------------------- 2nd (sleep 1 sec, all recipes should be skipped)\n") {
        sleep 1;
        my $ts_hello    = (stat "hello")[9];
        my $ts_hello1_o = (stat "hello1.o")[9];
        my $ts_hello2_o = (stat "hello2.o")[9];
        my $ts_hello_h  = (stat "hello.h")[9];
        ob_start();
        $kitchen->start_cooking("hello");
        my $output = ob_get_clean();
        ok((stat "hello")[9]    == $ts_hello);
        ok((stat "hello1.o")[9] == $ts_hello1_o);
        ok((stat "hello2.o")[9] == $ts_hello2_o);
        ok((stat "hello.h")[9]  == $ts_hello_h);
        #
        my $expected = "";
        ok($output eq $expected);
    }
    #
    if ("------------------- 3rd (touch hello.h, hello should be skipped)\n") {
        #$Kook::Config::DEBUG_LEVEL = 2;
        my $now = time();
        utime $now, $now, "hello.h";
        my $ts_hello    = (stat "hello")[9];
        my $ts_hello1_o = (stat "hello1.o")[9];
        my $ts_hello2_o = (stat "hello2.o")[9];
        ob_start();
        $kitchen->start_cooking("hello");
        my $output = ob_get_clean();
        ok((stat "hello.h.txt")[9] < $now);
        ok((stat "hello")[9]    > $ts_hello);
        ok((stat "hello1.o")[9] > $ts_hello1_o);
        ok((stat "hello2.o")[9] > $ts_hello2_o);
        #
        my $expected = <<'END';
### ** hello1.o (recipe=*.o)
$ gcc -c hello1.c
### ** hello2.o (recipe=*.o)
$ gcc -c hello2.c
### * hello recipe=hello
$ touch hello   # skipped
END
        ;
        ok($output eq $expected);
    }
    #
    if ("------------------- 4th (edit hello.h.txt, hello should not be skipped)\n") {
        sleep 1;
        my $ts_hello    = (stat "hello")[9];
        my $ts_hello1_o = (stat "hello1.o")[9];
        my $ts_hello2_o = (stat "hello2.o")[9];
        my $s = $HELLO_H_TXT;
        $s =~ s/hello/HELLO/;
        write_file("hello.h.txt", $s);
        ob_start();
        $kitchen->start_cooking("hello");
        my $output = ob_get_clean();
        ok((stat "hello")[9] > $ts_hello);
        ok((stat "hello1.o")[9] > $ts_hello1_o);
        ok((stat "hello2.o")[9] > $ts_hello2_o);
        #
        my $expected = <<'END';
### *** hello.h (recipe=hello.h)
$ cp hello.h.txt hello.h
### ** hello1.o (recipe=*.o)
$ gcc -c hello1.c
### ** hello2.o (recipe=*.o)
$ gcc -c hello2.c
### * hello (recipe=hello)
$ gcc -o hello hello1.o hello2.o
END
        ok($output eq $expected);
    }

    ### after all
    unlink(glob('hello*'));

}


###
### Kook::Kitchen  # LOOPED
###
if ("recipes are looped") {

    my $HELLO_H_TXT = <<'END';
	extern char *command;
END
    ;
    my $HELLO_C = <<'END';
	#inclue <stdio.h>
	#include "hello.h"
	int main(int argc, char *argv[]) {
	    printf("command=%s\n", command);
	    return 0;
	}
END
    ;

    write_file("hello.h.txt", $HELLO_H_TXT);
    write_file("hello.c", $HELLO_C);

    ### Kookbook.pl
    my $input = <<'END';
	recipe "build", {
	    desc => "build all files",
	    ingreds => ["hello"],
	};
	
	recipe "hello", {
	    ingreds => ["hello.o"],
	    kind => "file",
	    method => sub {
	        my ($c) = @_;
	        sys "gcc -o $c->{product} $c->{ingred}";
	    }
	};
	
	recipe "*.o", {
	    ingreds => ['$(1).c', 'hello.h'],
	    method => sub {
	        my ($c) = @_;
	        sys "gcc -c $c->{ingred}";
	    }
	};
	
	recipe "*.h", {
	    ingreds => ['$(1).h.txt'],
	    method => sub {
	        my ($c) = @_;
	        sys "cp $c->{ingred} $c->{product}";
	    }
	};
	
	recipe '*.h.txt', {
	    ingreds => ['$(1).o'],
	    method => sub {
	        my ($c) = @_;
	    }
	};
END
    ;

    my $kitchen = _create_kitchen($input);

    ### create_cooking_tree()     # LOOPED
    my $root = $kitchen->create_cooking_tree("build");

    ### check_cooking_tree()      # LOOPED
    eval {
        $kitchen->check_cooking_tree($root);
    };
    my $expected = "build: recipe is looped (hello.o->hello.h->hello.h.txt->hello.o).\n";
    ok($@ eq $expected);
}


###
### after_all()
###
#unlink glob('hello*');
chdir ".."  or die $!;
my @a = glob("_sandbox/*");
unlink @a if @a;
rmdir "_sandbox"  or die $!;
