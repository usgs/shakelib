#!/usr/bin/env python

# stdlib imports
import os.path
import sys
import io

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)

from shakelib.grind.container import InputContainer


def test_container():
    config = {'alliance': 'chaotic neutral',
              'race': 'Elf',
              'armor': 5,
              'class': 'Warrior',
              'intelligence': 10}
    datafile = os.path.join(os.path.expanduser('~'), 'test.hdf')
    rupturefile = os.path.join(shakedir, 'test/data/Barkaetal02_fault.txt')
    event_text = """<?xml version="1.0" encoding="US-ASCII" standalone="yes"?>
<earthquake id="2008ryan" lat="30.9858" lon="103.3639" mag="7.9" year="2008" 
month="05" day="12" hour="06" minute="28" second="01" timezone="GMT" depth="19.0" 
locstring="EASTERN SICHUAN, CHINA" created="1211173621" otime="1210573681" type="" />"""
    eventfile = io.StringIO(event_text)
    datafiles = [os.path.join(
        shakedir, 'test/data/eventdata/northridge/northridge_stations_dat.xml')]
    container = InputContainer.loadFromInput(datafile, config, eventfile,
                                             datafiles=datafiles,
                                             rupturefile=rupturefile)
    station = container.getStationList()
    origin = container.getOrigin()
    rupture = container.getRupture()
    del container

    container2 = InputContainer.loadFromHDF(datafile)
    station = container2.getStationList()
    origin = container2.getOrigin()
    rupture = container2.getRupture()


if __name__ == '__main__':
    test_container()
