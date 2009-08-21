###
### $Release:$
### $Copyright$
### $License$
###


package Kook::Commands;
use strict;
use Exporter 'import';
our @EXPORT_OK = ('sys', 'sys_f');
use Kook::Config;


sub _msg {
    my ($msg) = @_;
    return $Kook::Config::MESSAGE_PROMPT . $msg . "\n";
}

sub _pr {
    my ($command) = @_;
    #print _msg($command);
    print $Kook::Config::COMMAND_PROMPT, $command, "\n";
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


1;
