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

our @_recipes         = ();     # out
our %_properties      = ();     # in
our @_property_tuples = ();     # out
our $kook_default     = undef;  # out

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

sub _eval {
    my ($_script, $_filename, $_context) = @_;
    #my @_list = ();
    #for my $_k (keys %$_context) {
    #    push @_list, "my \$$_k=%\$_context->{$_k};";
    #}
    #my $_code = join "", @_list;
    #undef @_list;
    #eval $_code;  #, $_context;
    #undef $_code;
    @_recipes         = ();
    %_properties      = $_context ? %$_context : ();
    @_property_tuples = ();
    $kook_default     = undef;
    eval "# line 1 \"$_filename\"\n".$_script;
}

1;
