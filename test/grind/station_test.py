#!/usr/bin/env python

# stdlib modules
import sys
import os.path
import time as time
import shutil
import glob

# third party modules
import pandas.util.testing as pdt
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)

# local imports
from shakelib.grind.station import StationList
from shakelib.grind.origin import Origin
from shakelib.grind.multigmpe import MultiGMPE
from shakelib.grind.sites import Sites
from shakelib.grind.rupture import read_rupture_file

def test_station():
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.abspath(os.path.join(homedir, '..', 'data', 'eventdata'))
    events = os.listdir(datadir)
    for event in events:
        inputfolder = os.path.join(datadir,event,'input')
        if not os.path.isdir(inputfolder):
            continue
        xmlfiles = glob.glob(os.path.join(inputfolder,'*_dat.xml'))
        stations = StationList.loadFromXML(xmlfiles,':memory:')

        instrumented = stations.getStationDataframe(1, sort=True)
        non_instrumented = stations.getStationDataframe(0, sort=True)

        instrumented_columns = ['id', 'lat', 'lon', 'code', 'network', 'vs30', 'repi', 'rhypo', 'rjb',
                                'rrup', 'rx', 'ry', 'ry0', 'U', 'T', 'SA(0.3)', 'SA(3.0)', 'PGA', 'PGV',
                                'SA(1.0)', 'name']
        noninstrumented_columns = ['id', 'lat', 'lon', 'code', 'network', 'vs30', 'repi', 'rhypo', 'rjb',
                                   'rrup', 'rx', 'ry', 'ry0', 'U', 'T', 'MMI', 'name']
        
        assert sorted(list(instrumented.columns)) == sorted(list(instrumented_columns))
        assert sorted(list(non_instrumented.columns)) == sorted(list(noninstrumented_columns))

if __name__ == '__main__':
    test_station()

