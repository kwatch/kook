###
### $Release:$
### $Copyright$
### $License$
###


package Kook;
use strict;
use Exporter 'import';
our @EXPORT_OK = ('recipe');

use Kook::Recipe;
use Kook::Commands;


our $RELEASE = (split ' ', '$Release: 0.0.0 $')[1];
our $all_recipes = [];
our $default_product;


sub recipe {
    my $recipe_obj = new Kook::Recipe(@_);
    push @$all_recipes, $recipe_obj;
}


1;
