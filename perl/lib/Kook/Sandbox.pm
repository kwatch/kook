# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###


package Kook::Sandbox;
use strict;
use Data::Dumper;

use Kook ('recipe');
use Kook::Commands qw(sys sys_f echo echo_n cp cp_p cp_r cp_pr mkdir mkdir_p rm rm_r rm_f rm_rf rmdir mv store store_p cd edit);
use Kook::Utils ('repr');

our %_properties     = ();
our %_property_descs = ();

sub prop {
    my ($name, $default_value, $desc) = @_;
    $_property_descs{$name} = $desc if $desc;
    return exists($_properties{$name}) ? $_properties{$name} : $default_value;
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
    %_properties     = ();
    %_property_descs = ();
    if ($_context) {
        $_properties{$_} = $_context->{$_} for (keys %$_context);
    }
    eval "# line 1 \"$_filename\"\n".$_script;
}

1;
