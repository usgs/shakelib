#!/usr/bin/env python

# stdlib imports
import os.path
import sys
import io
import json
import numpy as np
import datetime as dt
import time
import datetime
import tempfile

from shakelib.utils.inputcontainer import InputContainer
from shakelib.rupture.point_rupture import PointRupture

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)


def dict_equal(d1, d2):
    s1 = sorted(set(d1.keys()))
    s2 = sorted(set(d2.keys()))
    return s1 == s2


def test_container():
    f,datafile = tempfile.mkstemp()
    os.close(f)
    try:
        config = {'alliance': 'chaotic neutral',
                  'race': 'Elf',
                  'armor': 5,
                  'class': 'Warrior',
                  'intelligence': 10}
        rupturefile = os.path.join(homedir, 'container_data', 
                                   'Barkaetal02_fault.txt')
        event_text = """<?xml version="1.0" encoding="US-ASCII" standalone="yes"?>
    <earthquake id="2008ryan" lat="30.9858" lon="103.3639" mag="7.9" year="2008"
    month="05" day="12" hour="06" minute="28" second="01" timezone="GMT"
    depth="19.0" locstring="EASTERN SICHUAN, CHINA" created="1211173621" productcode="us2008ryan"
    otime="1210573681" type="" />"""
        eventfile = io.StringIO(event_text)
        datafiles = [os.path.join(
            homedir, 'container_data/northridge_stations_dat.xml')]

        timestamp = datetime.datetime.utcnow().strftime('%FT%TZ')
        originator = 'us'
        version = 1
        history = {'history': [[timestamp, originator, version]]}

        container = InputContainer.createFromInput(datafile, config, eventfile,
                                                 datafiles=datafiles,
                                                 rupturefile=rupturefile,
                                                 version_history=history)
        cfile = container.getFileName()
        assert datafile == cfile
        config = container.getConfig()
        station = container.getStationList()
        origin = container.getOrigin()
        rupture = container.getRupture()
        history = container.getVersionHistory()
        container.close()

        container2 = InputContainer.load(datafile)
        config2 = container2.getConfig()
        station2 = container2.getStationList()  # noqa
        origin2 = container2.getOrigin()  # noqa
        rupture2 = container2.getRupture()  # noqa
        history2 = container2.getVersionHistory()  # noqa

        assert dict_equal(config, config2)
        df1 = station.getStationDataframe(0)
        df2 = station.getStationDataframe(0)
        assert dict_equal(df1, df2)
        df1 = station.getStationDataframe(1)
        df2 = station.getStationDataframe(1)
        assert dict_equal(df1, df2)
        assert history['history'][-1][0] == history['history'][-1][0]
        assert history['history'][-1][1] == history['history'][-1][1]
        assert history['history'][-1][2] == history['history'][-1][2]

        container2.close()

        eventfile.seek(0)
        container3 = InputContainer.createFromInput(datafile, config, eventfile)
        station = container3.getStationList()
        origin = container3.getOrigin()  # noqa
        rupture = container3.getRupture()
        history = container3.getVersionHistory()
        assert station is None
        assert history is None
        assert isinstance(rupture, PointRupture)

        container3.setStationData(datafiles)
    except:
        assert 1==2
    finally:
        os.remove(datafile)
if __name__ == '__main__':
    test_container()
    #test_output_container()
