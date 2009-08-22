# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 39;

use Kook::Utils ('read_file', 'write_file', 'ob_start', 'ob_get_clean', 'has_metachar', 'meta2rexp', 'repr');


###
### before_all()
###
mkdir "_sandbox" unless -d "_sandbox";
chdir "_sandbox"  or die;



###
### read_file() and write_file()
###
if (1) {
    my $input = "foo\nbar\nbaz\n";
    my $filename = "_test.tmp";
    write_file($filename, $input);
    ok(-f $filename);
    ok((-s $filename) == length($input));
    #
    ok(read_file($filename) eq $input);
    unlink $filename;
}


###
### ob_start(), ob_get_clean()
###
if (1) {
    ob_start();
    print "YES";
    my $output = ob_get_clean();
    ok($output eq "YES");
    #
    ob_start();   # 2nd time
    print "NO";
    my $output = ob_get_clean();
    ok($output eq "NO");
}


###
### has_metachar()
###
if (1) {
    ok(has_metachar("*.html") == 1);
    ok(has_metachar("index.htm?") == 1);
    ok(has_metachar("index.{txt,htm}") == 1);
    ok(has_metachar("index.html") eq "");
    ok(has_metachar("\\*.html") eq "");
    ok(has_metachar("index.htm\\?") eq "");
    ok(has_metachar("index.\\{txt,html}") eq "");
}


###
### meta2rexp()
###
if (1) {
    ok(meta2rexp("*.html") eq '^(.*?)\.html$');
    ok(meta2rexp("index.htm?") eq '^index\\.htm(.)$');
    ok(meta2rexp("index.{txt,html,xml}") eq '^index\\.(txt|html|xml)$');
    ok(meta2rexp("index.{a.b,c-d}") eq '^index\\.(a\\.b|c\\-d)$');
    ok(meta2rexp("*-???.{txt,html,xml}") eq '^(.*?)\\-(...)\\.(txt|html|xml)$');
}


###
### repr()
###
if (1) {
    ok(repr(["foo\n", 123, undef]) eq '["foo\n",123,undef]');
    my $s = repr({'x'=>10, 'y'=>20});
    ok($s eq '{"x" => 10,"y" => 20}' || $s eq '{"y" => 20,"x" => 10}');
}


###
### Kook::Utils::CommandOptionParser
###

if (1) {
    ### new()
    my $parser;
    my $optdef_strs;
    $parser = Kook::Utils::CommandOptionParser->new();
    ok(%{$parser->{optdefs}} == ());
    ok(@{$parser->{helps}} == ());

    ### short opts
    my $short_optdef_strs = [
        "-h: help",
        "-f file: filename",
        "-n N: number",
        "-P[pass]: password",
        "-i[N]: indent",
    ];
    my $short_optdefs_expected = {
        'h' => 1,
        'f' => 'file',
        'n' => 'N',
        'P' => '[pass]',
        'i' => '[N]',
    };
    my $short_helps_expected = [
        ['-h',       'help'],
        ['-f file',  'filename'],
        ['-n N',     'number'],
        ['-P[pass]', 'password'],
        ['-i[N]',    'indent'],
    ];
    if ("short options are defiend") {
        #my ($optdefs, $helps) = $parser->parse_optdefs($short_optdef_strs);
        #ok(Dumper($optdefs) eq Dumper($short_optdefs_expected));
        #ok(Dumper($helps)   eq Dumper($short_helps_expected));
        my $parser2 = Kook::Utils::CommandOptionParser->new($short_optdef_strs);
        ok(Dumper($parser2->{optdefs}) eq Dumper($short_optdefs_expected));
        ok(Dumper($parser2->{helps})   eq Dumper($short_helps_expected));
    }

    ### long opts
    my $long_optdef_strs = [
        "--help: Help",
        "--file=path: Filename",
        "--number=N: Number",
        "--password[=pass]: Password",
        "--indent[=N]: Indent",
    ];
    my $long_optdefs_expected = {
        "help"     => 1,
        "file"     => "path",
        "number"   => "N",
        "password" => "[pass]",
        "indent"   => "[N]",
    };
    my $long_helps_expected = [
        ["--help", "Help"],
        ["--file=path", "Filename"],
        ["--number=N", "Number"],
        ["--password[=pass]", "Password"],
        ["--indent[=N]", "Indent"],
    ];
    if ("long options are defined") {
        #my ($optdefs, $helps) = $parser->parse_optdefs($long_optdef_strs);
        #ok(Dumper($optdefs) eq Dumper($long_optdefs_expected));
        #ok(Dumper($helps)   eq Dumper($long_helps_expected));
        my $parser2 = Kook::Utils::CommandOptionParser->new($long_optdef_strs);
        ok(Dumper($parser2->{optdefs}) eq Dumper($long_optdefs_expected));
        ok(Dumper($parser2->{helps})   eq Dumper($long_helps_expected));
    }

    ### parse short opts
    if ("short opts are parsed") {
        my $parser = Kook::Utils::CommandOptionParser->new($short_optdef_strs);
        my ($opts, $rests) = $parser->parse(["-hffile.txt", "-n", "123", "-Pass", "-i2", "AAA", "BBB"]);
        ok(Dumper($opts) eq Dumper({"h"=>1, "f"=>"file.txt", "n"=>'123', "P"=>"ass", "i"=>'2'}));  # or "i"=>2
        ok(Dumper($rests) eq Dumper(["AAA", "BBB"]));
        my ($opts, $rests) = $parser->parse(["-hP", "-i", "CCC", "DDD"]);
        ok(Dumper($opts) eq Dumper({"h"=>1, "P"=>1, "i"=>1}));
        ok(Dumper($rests) eq Dumper(["CCC", "DDD"]));
    }

    ### parse long opts
    if ("long ops are parsed") {
        my $parser = Kook::Utils::CommandOptionParser->new($long_optdef_strs);
        my ($opts, $rests) = $parser->parse(["--help", "--file=foo.txt", "--number=123", "--password=pass", "--indent=2", "AAA", "BBB"]);
        ok(Dumper($opts) eq Dumper({"help"=>1, "file"=>"foo.txt", "number"=>'123', "password"=>"pass", "indent"=>'2'}));
        ok(Dumper($rests) eq Dumper(["AAA", "BBB"]));
        my ($opts, $rests) = $parser->parse(["--password", "--indent", "CCC", "DDD"]);
        ok(Dumper($opts) eq Dumper({"password"=>1, "indent"=>1}));
        ok(Dumper($rests) eq Dumper(["CCC", "DDD"]));
    }

    ### skip if "--" exists
    if ("'--' specified then rests are not parsed") {
        my $parser = Kook::Utils::CommandOptionParser->new($short_optdef_strs);
        my ($opts, $rests) = $parser->parse(["-hf", "file.txt", "--", "-n", "123"]);
        ok(Dumper($opts) eq Dumper({"h"=>1, "f"=>"file.txt"}));
        ok(Dumper($rests) eq Dumper(["-n", "123"]));
    }

    ### help()
    if ("help() method is called") {
        my @optdefs = ();
        push @optdefs, @$short_optdef_strs, @$long_optdef_strs;
        my $parser = Kook::Utils::CommandOptionParser->new(\@optdefs);
        my $help_expected = <<'END';
  -h                  : help
  -f file             : filename
  -n N                : number
  -P[pass]            : password
  -i[N]               : indent
  --help              : Help
  --file=path         : Filename
  --number=N          : Number
  --password[=pass]   : Password
  --indent[=N]        : Indent
END
        ;
        ok($parser->help()  eq  $help_expected);
    }

    ### parse2()
    if ("parse2() called") {
        my $parser = Kook::Utils::CommandOptionParser->new($short_optdef_strs);
        my ($opts, $longopts, $rests) = $parser->parse2(["-hf", "file.txt", "--name=value", "--flag", "-i", "AAA", "BBB"]);
        ok(Dumper($opts) eq Dumper({"h"=>1, "f"=>"file.txt", "i"=>1}));
        ok(Dumper($longopts) eq Dumper({"name"=>"value", "flag"=>1}));
        ok(Dumper($rests) eq Dumper(["AAA", "BBB"]));
    }
}



###
### after_all()
###
chdir ".."  or die $!;
my @a = glob("_sandbox/*");
unlink @a if @a;
rmdir "_sandbox"  or die $!;
