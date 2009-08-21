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
use Kook::Commands ('sys', 'sys_f');


sub _eval {
    my ($_script, $_filename, $_context) = @_;
    my @_list = ();
    for my $_k (keys %$_context) {
        push @_list, "my \$$_k=%\$_context->{$_k};";
    }
    my $_code = join "", @_list;
    undef @_list;
    eval $_code;  #, $_context;
    undef $_code;
    eval "# line 1 \"$_filename\"\n".$_script;
}


1;
