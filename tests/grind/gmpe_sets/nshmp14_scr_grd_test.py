#!/usr/bin/env python
import os.path
import sys


homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..', '..'))
sys.path.insert(0, shakedir)

from shakelib.grind.gmpe_sets import nshmp14_scr_grd


def test_nshmp14_scr_grd():
    gmpes, wts, wts_large_dist, dist_cutoff, site_gmpes = \
        nshmp14_scr_grd.get_weights()

    assert gmpes == \
        ['FrankelEtAl1996MwNSHMP2008()',
         'ToroEtAl1997MwNSHMP2008()',
         'SilvaEtAl2002MwNSHMP2008()',
         'Campbell2003MwNSHMP2008()',
         'TavakoliPezeshk2005MwNSHMP2008()',
         'AtkinsonBoore2006Modified2011()',
         'PezeshkEtAl2011()',
         'Atkinson2008prime()',
         'SomervilleEtAl2001NSHMP2008()']

    assert wts == [0.06, 0.13, 0.06, 0.13, 0.13, 0.25, 0.16, 0.08, 0.0]

    assert wts_large_dist == [0.16, 0.0, 0.0, 0.17, 0.17, 0.3, 0.2, 0.0, 0.0]

    assert dist_cutoff == 500

    assert site_gmpes == ['AtkinsonBoore2006Modified2011()']


if __name__ == '__main__':
    test_nshmp14_scr_grd()
