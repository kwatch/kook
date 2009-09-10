
use Kook::Utils ('read_file', 'write_file');

my $project   = prop('project', "plkook");
my $release   = prop('release', "0.0.0");
my $copyright = "copyright(c) 2009 kuwata-lab.com all rights reserved.";
my $license   = prop('license', "MIT License");

$kook_default = "test";

recipe "test", {
    method  => sub {
        sys("prove t/*.t");
    }
};

recipe "package", {
    ingreds => ["dist"],
    desc   => "create package",
    method => sub {
        rm_rf "dist/*"   if -d "dist";
        mkdir "dist" unless -d "dist";
        cd "dist", sub {
            my $base = "Kook-$release";
            mv "../$base.tar.gz", ".";
            sys "tar xzf $base.tar.gz";
            edit "$base/**/*", sub {
                s/\$Release\$/$release/g;
                s/\$Release:.*?\$/\$Release: $release \$/g;
                s/\$Copyright\$/$copyright/g;
                s/\$License\$/$license/g;
                $_;
            };
            mv "$base.tar.gz", "$base.tar.gz.bkup";
            sys "tar czf $base.tar.gz $base";
        };
        rm_rf "Makefile", "MANIFEST", "pm_to_blib", "blib";
    }
};

my $orig_kk = "../python/bin/kk";

recipe "bin/kk", {
    ingreds => [$orig_kk],
    desc  => "copy from '$orig_kk'",
    method => sub {
        my ($c) = @_;
        cp($c->{ingred}, $c->{product});
    }
};


## for documents

recipe "doc", ['doc/users-guide.html', 'doc/docstyle.css'];

recipe "doc/users-guide.html", ['doc/users-guide.txt'], {
    byprods => ['users-guide.toc.html', 'users-guide.tmp'],
    method => sub {
        my ($c) = @_;
        my $tmp = $c->{byprods}->[1];
        sys "kwaser -t html-css -T $c->{ingred} > $c->{byprod}";
        sys "kwaser -t html-css    $c->{ingred} > $tmp";
        sys_f "tidy -q -i -wrap 9999 $tmp > $c->{product}";
        rm_f $c->{byprods};
    }
};

recipe "doc/users-guide.txt", ['../doc/users-guide.eruby'], {
    method => sub {
        my ($c) = @_;
        mkdir "doc" unless -d "doc";
        sys "erubis -E PercentLine -p '\\[% %\\]' $c->{ingred} > $c->{product}";
    }
};

recipe 'doc/docstyle.css', ['../doc/docstyle.css'], {
    method => sub {
        my ($c) = @_;
        mkdir "doc" unless -d "doc";
        cp $c->{ingred}, $c->{product};
    }
};



### for CPAN package

recipe "edit-version", {
    method => sub {
        my $s = read_file("lib/Kook.pm");
        $s =~ m/^our \$VERSION = '(.*)';/m  or die "*** \$VERSION not found in lib/Kook.pm";
        if ($1 ne $release) {
            edit "lib/Kook.pm", sub {
                s/^(our \$VERSION = ).*$/$1'$release';/m;
                $_
            };
        }
    }
};

recipe "MANIFEST", {
    ingreds => ["edit-version", "clean"],
    method => sub {
        my ($c) = @_;
        rm_f $c->{product};
        sys "perl Makefile.PL";
        sys "make";
        sys "make manifest";
    }
};

recipe "clean", {
    method => sub {
        sys "make distclean" if -f "Makefile";
        rm_f "Kook-*.tar.gz";
    }
};

recipe "dist", {
    ingreds => ["clean", "MANIFEST", "Kook-$release.tar.gz"],
};

recipe "Kook-*.tar.gz", {
    method => sub {
        #sys "make distclean";
        #sys "perl Makefile.PL";
        #sys "make";
        #sys "make disttest";
        sys "make dist";
    }
};

