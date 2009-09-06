# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

use strict;
use Data::Dumper;
use Test::Simple tests => 3;

use Kook::Sandbox;
use Kook::Utils ('ob_start', 'ob_get_clean');


### if property is given, it's value is used instead of default value
my $str = <<'END';
  my $val1 = prop('val1', "default1", "description1");
  print Dumper($val1);
END
ob_start();
Kook::Sandbox::_eval $str, "Kookbook.pl", { val1 => "OVERWRITE" };
my $output = ob_get_clean();
ok($output eq "\$VAR1 = 'OVERWRITE';\n");


### if property is not given, default value is used
my $str = <<'END';
  my $val2 = prop('val2', "default2", "description2");
  print Dumper($val2);
END
ob_start();
Kook::Sandbox::_eval $str, "Kookbook.pl", { val1 => "OVERWRITE" };
my $output = ob_get_clean();
ok($output eq "\$VAR1 = 'default2';\n");


### properties hash table is cleared when Kook::Sandbox::_eval() called
my $str = <<'END';
  print Dumper(\%prperties);
END
ob_start();
Kook::Sandbox::_eval $str, "Kookbook.pl", { val1 => "OVERWRITE" };
my $output = ob_get_clean();
ok($output eq "");
