# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###


package Kook::Sandbox;
use strict;
use Data::Dumper;

use Kook::Recipe;
use Kook::Commands qw(sys sys_f echo echo_n cp cp_p cp_r cp_pr mkdir mkdir_p rm rm_r rm_f rm_rf rmdir mv store store_p cd edit);
use Kook::Utils ('repr');

our @_recipes;          # out
our %_properties;       # in
our @_property_tuples;  # out
our $kook_default;      # out
our $kook_desc;         # out

sub __init {
   @_recipes         = ();
   %_properties      = ();
   @_property_tuples = ();
   $kook_default     = undef;
   $kook_desc        = undef;
}

sub recipe {
    my $recipe_obj = Kook::Recipe->new(@_);
    push @_recipes, $recipe_obj;
    return $recipe_obj;
}

sub prop {
    my ($name, $default_value, $desc) = @_;
    my $value = exists($_properties{$name}) ? $_properties{$name} : $default_value;
    push @_property_tuples, [$name, $value, $desc];
    return $value;
}

sub private_prop {
    my ($name, $default_value, $desc) = @_;
    return prop($name, $default_value, -1);   # if $desc is -1, that property is regarded as private
}

sub _eval {
    my ($_script, $_filename, $_props) = @_;
    __init();
    %_properties      = %$_props if $_props;
    eval "# line 1 \"$_filename\"\n".$_script;
}

1;
