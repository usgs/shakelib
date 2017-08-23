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

from shakelib.utils.container import InputContainer, OutputContainer
from shakelib.rupture.point_rupture import PointRupture

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)


def dict_equal(d1, d2):
    s1 = sorted(set(d1.keys()))
    s2 = sorted(set(d2.keys()))
    return s1 == s2


def test_container():
    config = {'alliance': 'chaotic neutral',
              'race': 'Elf',
              'armor': 5,
              'class': 'Warrior',
              'intelligence': 10}
    datafile = os.path.join(os.path.expanduser('~'), 'test.hdf')
    rupturefile = os.path.join(homedir, 'container_data', 
                               'Barkaetal02_fault.txt')
    event_text = """<?xml version="1.0" encoding="US-ASCII" standalone="yes"?>
<earthquake id="2008ryan" lat="30.9858" lon="103.3639" mag="7.9" year="2008"
month="05" day="12" hour="06" minute="28" second="01" timezone="GMT"
depth="19.0" locstring="EASTERN SICHUAN, CHINA" created="1211173621"
otime="1210573681" type="" />"""
    eventfile = io.StringIO(event_text)
    datafiles = [os.path.join(
        homedir, 'container_data/northridge_stations_dat.xml')]

    timestamp = datetime.datetime.utcnow().strftime('%FT%TZ')
    originator = 'us'
    version = 1
    history = {'history': [[timestamp, originator, version]]}

    container = InputContainer.loadFromInput(datafile, config, eventfile,
                                             datafiles=datafiles,
                                             rupturefile=rupturefile,
                                             version_history=history)
    cfile = container.getFileName()
    assert datafile == cfile
    config = container.getConfig()
    station = container.getStationList()
    origin = container.getOrigin()
    rupture = container.getRupture()
    history = container.getHistory()
    del container

    container2 = InputContainer.loadFromHDF(datafile)
    config2 = container2.getConfig()
    station2 = container2.getStationList()  # noqa
    origin2 = container2.getOrigin()  # noqa
    rupture2 = container2.getRupture()  # noqa
    history2 = container2.getHistory()  # noqa

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

    container2.updateConfig(config)
    container2.updateRupture(rupturefile)
    container2.updateEvent(eventfile)
    container2.addData(datafiles)
    container2.updateHistory(history)
    container2.close()

    container3 = InputContainer.loadFromInput(datafile, config, eventfile)
    station = container3.getStationList()
    origin = container3.getOrigin()  # noqa
    rupture = container3.getRupture()
    history = container3.getHistory()
    assert station is None
    assert history is None
    assert isinstance(rupture, PointRupture)

    container3.addData(datafiles)


def test_output_container():
    test_file = os.path.join(homedir, 'container_data', 'test.hdf')
    oc = OutputContainer.createEmpty(test_file)
    test_dict = {'float': 2.5,
                 'int': 3,
                 'string': 'This is a test',
                 'list': [1, 2, 3],
                 'dict': {'name': 'Joe', 'age': 20},
                 'nparray': np.array([1., 2., 3.]),
                 'datetime': dt.datetime.utcnow()}
    test_string = 'This is a string.'
    test_json = json.dumps({'thing': 'some json', 'stuff': [1, 2, 3]})
    test_array = np.array([[1., 2., 3.], [4., 5., 6.]])
    test_dset_metadata = {'nx': 100,
                          'ny': 200,
                          'an_array': np.array([1, 2, 3])}

    oc.addMetadata(test_dict)
    oc.addData(test_string, 'test_string')
    oc.addData(test_json, 'test_json')
    oc.addData(test_array, 'test_array', metadata=test_dset_metadata)
    oc.close()

    del oc

    oc = OutputContainer.loadFromHDF(test_file)
    td = oc.getMetadata()
    ts, tsmd = oc.getData('test_string')
    tj, tjmd = oc.getData('test_json')
    ta, tamd = oc.getData('test_array')

    oc.close()
    os.remove(test_file)

    assert set(td.keys()) == set(test_dict.keys())
    assert td['datetime'] == \
        dt.datetime.fromtimestamp(time.mktime(
            test_dict['datetime'].timetuple()))
    assert ts == test_string
    assert tj == test_json
    assert np.all(ta == test_array)
    assert set(tamd.keys()) == set(test_dset_metadata.keys())

    #
    # Get a real data file
    #
    hdf_file = os.path.join(homedir, 'container_data', 
                            'shake_result.hdf')
    oc = OutputContainer.loadFromHDF(hdf_file)
    imtlist = oc.getIMTlist()
    assert 'MMI' in imtlist
    assert 'PGA' in imtlist
    assert 'PGV' in imtlist

if __name__ == '__main__':
    test_container()
    test_output_container()
