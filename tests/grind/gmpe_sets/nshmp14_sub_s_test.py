#!/usr/bin/env python

import os
import sys


homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..', '..'))
sys.path.insert(0, shakedir)

from shakelib.grind.gmpe_sets import nshmp14_sub_s


def test_nshmp14_sub_s():
    gmpes, wts, wts_large_dist, dist_cutoff, site_gmpes = \
        nshmp14_sub_s.get_weights()

    assert gmpes == \
        ['AtkinsonBoore2003SSlab()',
         'AtkinsonBoore2003SSlabCascadia()',
         'ZhaoEtAl2006SSlab()',
         'AbrahamsonEtAl2015SSlab()']

    assert wts == [0.1667, 0.1667, 0.33, 0.33]

    assert wts_large_dist is None

    assert dist_cutoff is None

#    assert site_gmpes ==


if __name__ == '__main__':
    test_nshmp14_sub_s()
