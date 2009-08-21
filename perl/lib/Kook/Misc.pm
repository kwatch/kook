# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

package Kook::Misc;
use strict;
use Data::Dumper;
use Exporter 'import';
our @EXPORT_OK = qw(_debug _trace _report_msg _report_cmd);

use Kook::Config;


sub _debug {
    my ($msg, $depth, $level) = @_;
    $level = 1 if ! $level;
    if ($Kook::Config::DEBUG_LEVEL >= $level) {
        print $Kook::Config::DEBUG_PROMPT;
        print '+' x $depth, ' ' if $depth;
        print $msg;
        print "\n" unless substr($msg, -1) eq "\n";
    }
}

sub _trace {
    my ($msg, $depth) = @_;
    _debug($msg, $depth, 2);
}

sub _report_msg {
    my ($msg, $level) = @_;
    if ($Kook::Config::VERBOSE) {
        print $Kook::Config::MESSAGE_PROMPT;
        print '*' x $level, ' ' if $level;
        print $msg;
        print "\n" unless substr($msg, -1) eq "\n";
    }
}

sub _report_cmd {
    my ($cmd) = @_;
    if ($Kook::Config::VERBOSE) {
        print $Kook::Config::COMMAND_PROMPT;
        print $cmd;
        print "\n" unless substr($cmd, -1) eq "\n";
    }
}
