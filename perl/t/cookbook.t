# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 27;

use Kook::Cookbook;
use Kook::Utils ('write_file');


###
### before_all()
###
mkdir "_sandbox" unless -d "_sandbox";
chdir "_sandbox"  or die $!;



###
### Kook::Cookbook
###

### new()
my $input = <<'END';
recipe "ex1", {
    desc => "example #1",
    method => sub {
        my ($c) = @_;
        print "product=$c->{product}\n";
    }
};

recipe "*.html", {
    desc => "generate *.html from *.txt",
    ingreds => ["$(1).txt"],
    method => sub {
        my ($c) = @_;
        print "txt2html $c->{ingred} > $c->{product}";
    }
};

recipe "index.html", ["index.wiki"], {   # short notation
    desc => "generate index.html",
    method => sub {
        my ($c) = @_;
        print "wiki2html index.wiki > index.html";
    }
};
END
    ;
my $bookname = '_Kookbook.pl';
write_file($bookname, $input);
my $cookbook = Kook::Cookbook->new($bookname);
ok($cookbook->{bookname} eq $bookname);
unlink $bookname;
### static task recipe
my $recipes = $cookbook->{specific_task_recipes};
my $len = @$recipes;
ok($len == 1);
my $recipe1 = $recipes->[0];
ok($recipe1->{product} eq "ex1");
ok($recipe1->{kind} eq "task");
ok($recipe1->{desc} eq "example #1");
ok($recipe1->{method});
### generic file recipe
my $recipes = $cookbook->{generic_file_recipes};
my $len = @$recipes;
ok($len == 1);
my $recipe2 = $recipes->[0];
ok($recipe2->{product} eq "*.html");
ok($recipe2->{kind} eq "file");
ok($recipe2->{desc} eq "generate *.html from *.txt");
ok(Dumper($recipe2->{ingreds}) eq Dumper(["$(1).txt"]));
ok($recipe2->{method});
### specific file recipe
my $recipes = $cookbook->{specific_file_recipes};
my $len = @$recipes;
ok($len == 1);
my $recipe3 = $recipes->[0];
ok($recipe3->{product} eq "index.html");
ok($recipe3->{kind} eq "file");
ok($recipe3->{desc} eq "generate index.html");
ok(Dumper($recipe3->{ingreds}) eq Dumper(["index.wiki"]));
ok($recipe3->{method});

### find_recipe()
my $recipe = $cookbook->find_recipe("ex1");
ok($recipe);
ok($recipe->{product} eq "ex1");
ok($recipe->{kind} eq "task");
#
my $recipe = $cookbook->find_recipe("foo.html");
ok($recipe);
ok($recipe->{product} eq "*.html");
ok($recipe->{kind} eq "file");
#
my $recipe = $cookbook->find_recipe("index.html");
ok($recipe);
ok($recipe->{product} eq "index.html");
ok($recipe->{kind} eq "file");



###
### after_all()
###
chdir ".."  or die $!;
my @a = glob("_sandbox/*");
unlink @a if @a;
rmdir "_sandbox"  or die $!;
