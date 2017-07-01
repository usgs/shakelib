#!/usr/bin/env python

#stdlib imports
from datetime import datetime
import collections
import time
import sqlite3
import io

#third party imports
import h5py
import numpy as np

#local imports
from shakelib.grind.rupture import read_rupture_file
from shakelib.grind.origin import Origin
from shakelib.grind.station import StationList
from shakelib.grind.sites import Sites

#list of allowed data types in dictionaries
ALLOWED = [str,int,float,
           type(None),
           list,tuple,np.ndarray,
           dict,datetime,
           collections.OrderedDict]

class InputContainer(object):

    def __init__(self,hdfobj):
        self._hdfobj = hdfobj
    
    @classmethod
    def loadFromHDF(cls,hdffile):
        hdfobj = h5py.File(hdffile, "r+")
        #probably should do some validating to make sure relevant data exists
        return cls(hdfobj)

    @classmethod
    def loadFromInput(cls,filename,config,eventfile,vs30file=None,rupturefile=None,datafiles=None):
        #open the file for writing, nuke if already exists
        hdfobj = h5py.File(filename, "w")

        this = cls(hdfobj)
        
        #write the config dictionary to a config group
        config_group = this._hdfobj.create_group('config')
        this._saveDict(config_group,config)

        #write the rupture file data to a rupture group
        rupturedata = open(rupturefile,'rt').read()
        rupture_group = this._hdfobj.create_group('rupture')
        rupture_group.attrs['rupture_string'] = rupturedata

        #create the stationlist object, then dump its database as a big string
        #into the hdf
        station = StationList.loadFromXML(datafiles,":memory:")
        this.stashStationList(station)

        #stash the event.xml in a group
        try:
            event_string = open(eventfile,'rt').read()
        except TypeError:
            event_string = eventfile.getvalue()
        event_group = this._hdfobj.create_group('event')
        event_group.attrs['event_string'] = event_string

        return this

    def getRupture(self):
        origin = self.getOrigin()
        ruptext = self._hdfobj['rupture'].attrs['rupture_string']
        rupio = io.StringIO(ruptext)
        rupture = read_rupture_file(origin,rupio)
        return rupture
        
    def getStationList(self):
        station_string = self._hdfobj['station'].attrs['station_string']
        db = sqlite3.connect(':memory:')
        cursor = db.cursor()
        cursor.executescript(station_string)
        station = StationList(db)
        return station

    def getOrigin(self):
        origin_file = io.StringIO(self._hdfobj['event'].attrs['event_string'])
        origin = Origin.fromFile(origin_file)
        return origin
        
    def addData(self,datafiles):
        stationlist = self.getStationList()
        stationlist.addData(datafiles)
        self.stashStationList(stationlist)

    def stashStationList(self,station):
        station_string = '\n'.join(list(station.db.iterdump()))
        station_group = self._hdfobj.create_group('station')
        station_group.attrs['station_string'] = station_string
        
    def changeConfig(self):
        pass
            
        
    def __del__(self):
        self._hdfobj.close()

    def _loadDict(cls,group):
        """Recursively load dictionaries from groups in an HDF file.
        
        :param group:
          HDF5 group object.
        :returns:
          Dictionary of metadata (possibly containing other dictionaries).
        """
        tdict = {}
        for (key,value) in group.attrs.items(): #attrs are NOT subgroups
            if key.find('time') > -1:
                value = value = datetime.datetime.utcfromtimestamp(value)
            tdict[key] = value
        for (key,value) in group.items(): #these are going to be the subgroups
            tdict[key] = cls._loadDict(value)
        return tdict

    def _saveDict(self,group,mydict):
        """
        Recursively save dictionaries into groups in an HDF file.
        :param group:
          HDF group object to contain a given dictionary of data in HDF file.
        :param mydict:
          Dictionary of values to save in group.  Dictionary can contain objects of the following types:
            - str,unicode,int,float,long,list,tuple,np.ndarray,dict,datetime.datetime,collections.OrderedDict
        """
        for (key,value) in mydict.items():
            tvalue = type(value)
            if tvalue not in ALLOWED:
                raise DataSetException('Unsupported metadata value type "%s"' % tvalue)
            if not isinstance(value,dict):
                if isinstance(value,datetime):
                    value = time.mktime(value.timetuple())
                group.attrs[key] = value
            else:
                subgroup = group.create_group(key)
                self._saveDict(subgroup,value)
