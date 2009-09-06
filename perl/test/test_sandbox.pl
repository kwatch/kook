# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 5;

use Kook::Sandbox;
use Kook::Utils ('ob_start', 'ob_get_clean', 'repr');


##
if ('property is given, it\'s value is used instead of default value') {
    my $str = <<'END';
      my $val1 = prop('val1', "default1", "description1");
      print Dumper($val1);
END
    ob_start();
    Kook::Sandbox::_eval $str, "Kookbook.pl", { val1 => "OVERWRITE" };
    my $output = ob_get_clean();
    ok($output eq "\$VAR1 = 'OVERWRITE';\n");
}


##
if ('property is not given, default value is used') {
    my $str = <<'END';
      my $val2 = prop('val2', "default2", "description2");
      print Dumper($val2);
END
    ob_start();
    Kook::Sandbox::_eval $str, "Kookbook.pl", { val1 => "OVERWRITE" };
    my $output = ob_get_clean();
    ok($output eq "\$VAR1 = 'default2';\n");
}


##
if ('properties hash table is cleared when Kook::Sandbox::_eval() called') {
    my $str = <<'END';
      print Dumper(\%prperties);
END
    ob_start();
    Kook::Sandbox::_eval $str, "Kookbook.pl", { val1 => "OVERWRITE" };
    my $output = ob_get_clean();
    ok($output eq "");
}


###
if ('Sandbok::_eval() is called then properties name and value are kept in @Kook::Sandbox::_property_tuples in declared order') {
    my $str = <<'END';
      my $A = prop('A', 10);
      my $B = prop('B', 20);
      my $C = prop('C', 30);
      my $D = prop('D', 40);
END
    ob_start();
    Kook::Sandbox::_eval $str, "Kookbook.pl", { A=>11, B=>21 };
    my $output = ob_get_clean();
    my $expected = '[["A",11,undef],["B",21,undef],["C",30,undef],["D",40,undef]]';
    ok(repr(\@Kook::Sandbox::_property_tuples) eq $expected);
}


##
if ('property is not scalar nor ref') {
    my $str = <<'END';
      my $prop1 = prop('prop1', 12345);
      my $prop2 = prop('prop2', ['a', 'b', 'c']);
      my $prop3 = prop('prop3', {x=>10});
      my $prop4 = prop('prop4', qw(foo bar baz));    # only "foo" is used
END
    ob_start();
    Kook::Sandbox::_eval $str, "Kookbook.pl";
    my $output = ob_get_clean();
    my $expected = '[["prop1",12345,undef],["prop2",["a","b","c"],undef],["prop3",{"x" => 10},undef],["prop4","foo","bar"]]';
    ok(repr(\@Kook::Sandbox::_property_tuples) eq $expected);
}
