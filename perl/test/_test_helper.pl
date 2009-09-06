# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

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

sub _test_p {
    my ($test_name) = @_;
    return ! $ENV{'TEST'} || $ENV{'TEST'} eq $test_name;
}


1;
