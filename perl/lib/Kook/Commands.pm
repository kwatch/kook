###
### $Release:$
### $Copyright$
### $License$
###


package Kook::Commands;
use strict;
use Exporter 'import';
our @EXPORT_OK = qw(sys sys_f echo echo_n);
use Data::Dumper;

use Kook::Config;
use Kook::Misc ('_report_cmd');
use Kook::Utils ('has_metachar', 'flatten');


sub _msg {
    my ($msg) = @_;
    return $Kook::Config::MESSAGE_PROMPT . $msg . "\n";
}

sub _pr {
    my ($command) = @_;
    #print _msg($command);
    print $Kook::Config::COMMAND_PROMPT, $command, "\n";
}

sub _prepare {
    my ($cmd, @filenames) = @_;
    _report_cmd("$cmd " . join(' ', @filenames)) if $cmd;
    my @arr;
    #my @fnames = map { has_metachar($_) ? ((@arr = glob($_)) ? @arr : $_) : $_ } @filenames;
    my @fnames = map { (@arr = glob($_)) ? @arr : $_ } flatten(@filenames);
    return @fnames;
}


sub sys {
    my $command = shift @_;
    _pr($command) if $Kook::Config::VERBOSE;
    return 0      if $Kook::Config::NOEXEC;
    my $status = system($command);
    $status == 0  or die "*** command failed (status=$status).\n";
    return $status;
}

sub sys_f {
    my $command = shift @_;
    _pr($command) if $Kook::Config::VERBOSE;
    return 0      if $Kook::Config::NOEXEC;
    return system($command);
}


sub echo {
    _echo("echo", "echo", 0, @_);
}

sub echo_n {
    _echo("echo", "echo", 1, @_);
}

sub _echo {
    my ($func, $cmd, $n, @filenames) = @_;
    @filenames = _prepare $cmd, @filenames;
    return if $Kook::Config::NOEXEC;
    my $i = 0;
    for (@filenames) {
        print " " if ($i++);
        print $_;
    }
    print "\n" unless $n;
}


1;
