
my $project   = prop('project', "plkook");
my $release   = prop('release', "0.0.1");
my $copyright = "copyright(c) 2009 kuwata-lab.com all rights reserved.";
my $license   = prop('license', "MIT License");

$Kook::default_product = "test";

recipe "test", {
    method  => sub {
        #for (glob('test/test_*.pl')) {
        #    print "sh> perl $_\n";
        #    system "perl $_";
        #}
        sys("prove test/test_*.pl");
    }
};

recipe "package", {
    desc   => "create package",
    method => sub {
        rm_rf "dist";
        my $dir = "dist/$project-$release";
        mkdir_p $dir;
        store "bin/*", "lib/**/*.pm", "test/**/*.pl", $dir;
        edit {
            s/\$Release\$/$release/g;
            s/\$Release:.*?\$/\$Release: $release \$/g;
            s/\$Copyright\$/$copyright/g;
            s/\$License\$/$license/g;
            $_;
        } "$dir/**/*";
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
}


#$x = 1;
#print '*** ', Dumper($x);
