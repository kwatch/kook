# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###

import sys as _sys
import kook.utils as _utils

quiet            = False
forced           = False
debug_level      = 0
command_prompt   = '$ '
message_prompt   = '### '
debug_prompt     = '*** debug: '
compare_contents = True
cmdopt_parser_class = _utils.CommandOptionParser
stdout           = _sys.stdout
stderr           = _sys.stderr
