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
        ok (ret).is_a(list)
        ok (len(ret)) == 2
        ok (ret[0]).is_a(kook.misc.IfExists)
        ok (ret[1]).is_a(kook.misc.IfExists)
        ok (ret[0].filename) == 'foo.h'
        ok (ret[1].filename) == '*.h'


if __name__ == '__main__':
    oktest.run('.*Test$')
