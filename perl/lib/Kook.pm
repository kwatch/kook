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
our $desc;


sub recipe {
    my $recipe_obj = Kook::Recipe->new(@_);
    push @$all_recipes, $recipe_obj;
    return $recipe_obj;
}


1;
