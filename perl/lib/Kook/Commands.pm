###
### $Release:$
### $Copyright$
### $License$
###


package Kook::Commands;
use strict;
use Exporter 'import';
our @EXPORT_OK = qw(sys sys_f echo echo_n cp cp_p cp_r cp_pr);
use Data::Dumper;
use File::Basename;

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

sub _touch {
    my ($src, $dst) = @_;
    my $mtime = (stat $src)[9];
    utime $mtime, $mtime, $dst;
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


sub cp {
    _cp('cp',    'cp',     0, 0, @_);
}

sub cp_p {
    _cp('cp_p',  'cp -p',  1, 0, @_);
}

sub cp_r {
    _cp('cp_r',  'cp -r',  0, 1, @_);
}

sub cp_pr {
    _cp('cp_pr', 'cp -pr', 1, 1, @_);
}

sub _cp {
    my ($func, $cmd, $p, $r, @filenames) = @_;
    @filenames = _prepare $cmd, @filenames;
    return if $Kook::Config::NOEXEC;
    my $n = @filenames;
    $n >= 2  or die "func: at least two file or directory names are required.";
    my $dst = pop @filenames;
    #if ($n == 2) {
    #    -e $src  or "$func: $src: no such file or directory.";
    #    if (-d $src) {
    #        $r  or "$func: $src: no such file or directory.";
    #        _copy_dir_to_dir($src, $dst, $func, $cmd, $p);
    #    }
    #    elsif (-d $dst) {
    #        _copy_file_to_dir($src, $dst, $func, $cmd, $p);
    #    }
    #    else {
    #        _copy_file_to_file($src, $dst, $func, $cmd, $p);
    #    }
    #}
    #else {    # $n > 2
    #    -e $dst  or "$func: $dst: directory not found.";
    #    -d $dst  or "$func: $dst: not a directory.";
    #    for my $src (@filenames) {
    #        -e $src  or die "$func: $src: no such file or directory.";
    #        if (-d $src) {
    #            $r  or die "$func: $src: cannot copy directory (use 'cp_r' instead).";
    #            _copy_dir_to_dir($src, $dst, $func, $cmd, $p);
    #        }
    #        else {
    #            _copy_file_to_dir($src, $dst, $func, $cmd, $p);
    #        }
    #    }
    #}
    if ($n == 2) {
        my $src = $filenames[0];
        ! (-d $src && -f $dst)  or die "$func: $src: cannot copy directory to file.\n";
    }
    else {   # $n > 2
        -e $dst  or die "$func: $dst: directory not found.\n";
        -d $dst  or die "$func: $dst: not a directory.\n";
    }
    my $to_dir = -d $dst;
    for my $src (@filenames) {
        -e $src  or die "$func: $src: no such file or directory.\n";
        if (-d $src) {
            $r  or die "$func: $src: cannot copy directory (use 'cp_r' instead).\n";
            _copy_dir_to_dir($src, $dst, $func, $p);
        }
        elsif ($to_dir) {
            _copy_file_to_dir($src, $dst, $func, $p);
        }
        else {
            _copy_file_to_file($src, $dst, $func, $p);
        }
    }
}

sub _copy_file_to_file {
    my ($src, $dst, $func, $p) = @_;
    open IN,  $src     or die "$func: $src: $!";
    open OUT, ">$dst"  or die "$func: $dst: $!";
    my ($buf, $size) = (undef, 2*1024*1024);
    print OUT $buf while (read IN, $buf, $size);
    close IN;
    close OUT;
    _touch $src, $dst if $p;
}

sub _copy_file_to_dir {
    my ($src, $dst, $func, $p) = @_;
    _copy_file_to_file($src, $dst . '/' . basename($src), $func, $p);
}

sub _copy_dir_to_dir {
    my ($src, $dst, $func, $p) = @_;
    $dst = $dst . '/' . basename($src) if -d $dst;
    ! -e $dst  or die "$func: $dst: already exists.\n";
    mkdir $dst  or die "$func: $dst: $!";
    opendir DIR, $src  or "$func: $src: $!";
    my @entries = readdir DIR;
    closedir DIR;
    for my $e (@entries) {
        next if $e eq '.' || $e eq '..';
        my $fpath = "$src/$e";
        -d $fpath ? _copy_dir_to_dir($fpath, $dst, $func, $p)
                  : _copy_file_to_dir($fpath, $dst, $func, $p);
    }
    _touch $src, $dst if $p;
}


1;
