###
### $Release:$
### $Copyright$
### $License$
###


package Kook::Commands;
use strict;
use Exporter 'import';
our @EXPORT_OK = qw(sys sys_f echo echo_n cp cp_p cp_r cp_pr mkdir mkdir_p rm rm_r rm_f rm_rf mv);
use Data::Dumper;
use File::Basename;     # basename()
use File::Path;         # mkpath(), rmtree()

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


sub mkdir {
    _mkdir('mkdir', 'mkdir', 0, @_);
}

sub mkdir_p {
    _mkdir('mkdir_p', 'mkdir -p', 1, @_);
}

sub _mkdir {
    my ($func, $cmd, $p, @dirnames) = @_;
    @dirnames = _prepare($cmd, @dirnames);
    return if $Kook::Config::NOEXEC;
    @dirnames  or die "$func: directory name required.\n";
    if ($p) {
        for my $dname (@dirnames) {
            -d $dname and next;
            -e $dname and die "$func: $dname: already exists.\n";
            mkpath($dname)  or die "$func: $dname: $!\n";
        }
    }
    else {
        for my $dname (@dirnames) {
            -e $dname and die "$func: $dname: already exists.\n";
            CORE::mkdir $dname  or die "$func: $dname: $!\n";
        }
    }
}


sub rm {
    _rm('rm', 'rm', 0, 0, @_);
}

sub rm_r {
    _rm('rm_r', 'rm -r', 1, 0, @_);
}

sub rm_f {
    _rm('rm_f', 'rm -f', 0, 1, @_);
}

sub rm_rf {
    _rm('rm_rf', 'rm -rf', 1, 1, @_);
}

sub _rm {
    my ($func, $cmd, $r, $f, @filenames) = @_;
    @filenames = _prepare($cmd, @filenames);
    return if $Kook::Config::NOEXEC;
    @filenames  or die "$func: directory name required.\n";
    for my $fname (@filenames) {
        if (-d $fname) {
            $r  or die "$func: $fname: can't remove directory (try 'rm_r' instead).\n";
            rmtree $fname  or die "$func: $fname: $!";
        }
        elsif (-e $fname) {
            unlink $fname  or die "$func: $fname: $!";
        }
        else {
            $f  or die "$func: $fname: not found.\n";
        }
    }
}


sub mv {
    _mv('mv', 'mv', @_);
}

sub _mv {
    my ($func, $cmd, @filenames) = @_;
    @filenames = _prepare($cmd, @filenames);
    return if $Kook::Config::NOEXEC;
    my $n = @filenames;
    if ($n < 2) {
        die "$func: at least two file or directory names are required.\n";
    }
    elsif ($n == 2) {
        my ($src, $dst) = @filenames;
        if    (! -e $src) { die "$func: $src: not found.\n";       }
        elsif (! -e $dst) { rename $src, $dst                     or die "$func: $!"; } # any to new
        elsif (-d $dst)   { rename $src, $dst.'/'.basename($src)  or die "$func: $!"; } # any to dir
        elsif (-d $src)   { die "$func: $dst: not a directory.\n";                    } # dir to file
        else              { rename $src, $dst                     or die "$func: $!"; } # file to file
    }
    else {
        my $dst = pop @filenames;
        -e $dst  or die "$func: $dst: directory not found.\n";
        -d $dst  or die "$func: $dst: not a directory.\n";
        for my $src (@filenames) {
            -e $src  or die "$func: $src: not found.\n";
        }
        for my $src (@filenames) {
            rename($src, $dst.'/'.basename($src))  or die "$func: $!";
        }
    }
}


1;
