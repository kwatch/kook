###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *

import kook.misc
from kook.misc import *


class KookMiscTest(object):

    def test_if_exists(self):
        ret = if_exists('foo.h', '*.h')
        ok(ret, 'is a', list)
        ok(len(ret), '==', 2)
        ok(ret[0], 'is a', kook.misc.IfExists)
        ok(ret[1], 'is a', kook.misc.IfExists)
        ok(ret[0].filename, '==', 'foo.h')
        ok(ret[1].filename, '==', '*.h')

