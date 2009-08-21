
$Kook::default_product = "test";

recipe "test", {
    method  => sub {
        #for (glob('test/test_*.pl')) {
        #    print "sh> perl $_\n";
        #    system "perl $_";
        #}
        sys("prove test/test_*.pl");
    }
}


#$x = 1;
#print '*** ', Dumper($x);
