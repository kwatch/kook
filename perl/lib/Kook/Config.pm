###
### $Release:$
### $Copyright$
### $License$
###


package Kook::Config;
use strict;


our $VERBOSE             = 1;
our $FORCED              = 0;
our $NOEXEC              = 0;
our $DEBUG_LEVEL         = 0;
our $COMMAND_PROMPT      = '$ ';
our $MESSAGE_PROMPT      = '### ';
our $WARNING_PROMPT      = '*** WARNING: ';
our $DEBUG_PROMPT        = '*** debug: ';
our $COMPARE_CONTENTS    = 1;
our $CMDOPT_PARSER_CLASS = 'Kook::Utils::CommandOptionParser';
our $PROPERTIES_FILENAME = 'Properties.pl';
our $COOKBOOK_FILENAME   = 'Kookbook.pl';
#our $STDOUT              = STDOUT;
#our $STDERR              = STDERR;


1;
