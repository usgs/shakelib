#!/usr/bin/env python

import os.path
import sys

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..', '..'))
sys.path.insert(0, shakedir)

from shakelib.grind.gmpe_sets import nshmp14_acr


def test_nshmp14_acr():
    gmpes, wts, wts_large_dist, dist_cutoff, site_gmpes = \
        nshmp14_acr.get_weights()

    assert gmpes == \
        ['AbrahamsonEtAl2014()',
         'BooreEtAl2014()',
         'CampbellBozorgnia2014()',
         'ChiouYoungs2014()']

    assert wts == [0.25, 0.25, 0.25, 0.25]

    assert wts_large_dist is None

    assert dist_cutoff is None

    assert site_gmpes is None


if __name__ == '__main__':
    test_nshmp14_acr()
