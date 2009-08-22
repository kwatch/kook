# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Cwd;
use Test::Simple tests => 15;

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
### script
###
my $SCRIPT = <<'END';
	#!/usr/bin/env plkook -X
	
	$Kook::desc = 'example of plkook scripting framework feature';
	
	recipe "print", {
	    desc  => "print args",
	    method => sub {
	        my ($c, $opts, $rest) = @_;
	        for (@$rest) {
	            print $_, "\n";
	        }
	    }
	};
	
	recipe "echo", {
	    desc  => "echo arguments",
	    spices => [
	        "-v: version",
	        "-f file: filename",
	        "-D:",
	        "-i[N]: indent",
	        "--keyword=kw1,kw2,...: keyword strings",
	    ],
	    method => sub {
	        my ($c, $opts, $rest) = @_;
	        my @arr = map { repr($_).'=>'.repr($opts->{$_}) } sort keys %$opts;
	        print "opts={", join(', ', @arr), "}\n";
	        print "rest=", repr($rest), "\n";
	    }
	};
END
    ;
$SCRIPT =~ s/^\t//mg;
write_file("peko", $SCRIPT);
chmod 0755, "peko";


###
### before_each(), after_each()
###
sub before_each {
}
sub after_each {
}


###
### -h
###
before_each();
if ("'-h' specified") {
    my ($output, $errmsg) = _system "./peko -h";
    my $expected = <<'END'
	peko - example of plkook scripting framework feature
	
	sub-commands:
	  print           : print args
	  echo            : echo arguments
	
	(Type 'peko -h subcommand' to show options of sub-commands.)
END
    ;
    $expected =~ s/^\t//mg;
    ok($output eq $expected);
    ok($errmsg eq "");
}
after_each();


###
### -h sub-command
###
before_each();
if ("'-h subcommand' specified") {
    my ($output, $errmsg) = _system "./peko -h echo";
    my $expected = <<'END'
	peko echo - echo arguments
	  -v                   : version
	  -f file              : filename
	  -i[N]                : indent
	  --keyword=kw1,kw2,... : keyword strings
END
    ;
    $expected =~ s/^\t//mg;
    ok($output eq $expected);
    ok($errmsg eq "");
}
after_each();


###
### ERROR: -h with unknown sub-command
###
before_each();
if ("'-h unknown' specified") {
    my ($output, $errmsg) = _system "./peko -h foobar";
    ok($output eq "");
    ok($errmsg eq "foobar: sub command not found.\n");
}
after_each();


###
### invoke sub-command
###
before_each();
if ("invoke sub-command") {
    my ($output, $errmsg) = _system "./peko print AAA BBB";
    ok($output eq "AAA\nBBB\n");
}
after_each();


###
### ERROR: unknown sub command sub-command
###
before_each();
if ("sub-command is unknown") {
    my ($output, $errmsg) = _system "./peko hoge";
    ok($output eq "");
    ok($errmsg eq "hoge: sub-command not found.\n");
}
after_each();


###
### invoke sub-command with spices
###
before_each();
if ("invoke sub-command with spices") {
    my ($output, $errmsg) = _system "./peko echo -vDffile.txt -i AAA BBB";
    my $expected = <<'END';
	opts={"D"=>1, "f"=>"file.txt", "i"=>1, "v"=>1}
	rest=["AAA","BBB"]
END
    ;
    $expected =~ s/^\t//mg;
    ok($output eq $expected);
    ok($errmsg eq "");
}
after_each();


###
### ERROR: invoke sub-command with invalid spices
###
before_each();
if ("invoke sub-command with spices") {
    my ($output, $errmsg) = _system "./peko echo -ifoo AAA BBB";
    ok($output eq "");
    ok($errmsg eq "-ifoo: integer required.\n");
}
after_each();
#
before_each();
if ("invoke sub-command with spices") {
    my ($output, $errmsg) = _system "./peko echo -f";
    ok($output eq "");
    ok($errmsg eq "-f: file required.\n");
}
after_each();


###
### after_all
###
chdir "..";
unlink glob("_sandbox/*");
rmdir "_sandbox"  or die;
