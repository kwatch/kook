###
### $Release:$
### $Copyright$
### $License$
###


package Kook;
use strict;
use Exporter 'import';
our @EXPORT_OK = ('recipe');

use Kook::Recipe;
use Kook::Commands;


our $RELEASE = (split ' ', '$Release: 0.0.0 $')[1];
our $default_product;
our $desc;


1;
