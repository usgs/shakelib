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
from shakelib.grind.rupture import read_rupture_file,PointRupture
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
        """Instantiate an InputContainer from an open h5py File Object.

        :param hdfobj:
          Open h5py File Object.
        """
        self._hdfobj = hdfobj
    
    @classmethod
    def loadFromHDF(cls,hdf_file):
        """Instantiate an InputContainer from an HDF5 file.

        :param hdf_file:
          Valid path to HDF5 file.
        :returns:
          Instance of InputContainer.
        """
        hdfobj = h5py.File(hdf_file, "r+")
        #probably should do some validating to make sure relevant data exists
        return cls(hdfobj)

    def getFileName(self):
        return self._hdfobj.filename
    
    @classmethod
    def loadFromInput(cls,filename,config,eventfile,rupturefile=None,datafiles=None):
        """Instantiate an InputContainer from ShakeMap input data.

        :param filename:
          Path to HDF5 file that will be created to encapsulate all input data.
        :param config:
          Dictionary containing all configuration information necessary for ShakeMap 
          ground motion and other calculations.
        :param eventfile:
          Path to ShakeMap event.xml file.
        :param rupturefile:
          Path to ShakeMap rupture text or JSON file.
        :param datafiles:
          List of ShakeMap data (DYFI, strong motion) files.
        :returns:
          Instance of InputContainer.
        """
        #open the file for writing, nuke if already exists
        hdfobj = h5py.File(filename, "w")

        this = cls(hdfobj)


        #The config and event info are mandatory
        #write the config dictionary to a config group
        config_group = this._hdfobj.create_group('config')
        this._saveDict(config_group,config)

        #stash the event.xml in a group
        try:
            event_string = open(eventfile,'rt').read()
        except TypeError:
            event_string = eventfile.getvalue()
        event_group = this._hdfobj.create_group('event')
        event_group.attrs['event_string'] = event_string

        #The rupture and data files are optional
        #write the rupture file data to a rupture group
        if rupturefile is not None:
            rupturedata = open(rupturefile,'rt').read()
            rupture_group = this._hdfobj.create_group('rupture')
            rupture_group.attrs['rupture_string'] = rupturedata

        #create the stationlist object, then dump its database as a big string
        #into the hdf
        if datafiles is not None:
            station = StationList.loadFromXML(datafiles,":memory:")
            this.stashStationList(station)

        return this

    def getConfig(self):
        """Return the config dictionary that was passed in via input files.

        :returns:
          Dictionary of configuration information.
        """
        config = self._loadDict('config')
        return config
    
    def getRupture(self):
        """Return a Rupture object (PointRupture if no rupture file was specified.)

        :returns:
          Rupture (Point, Edge or Quad Rupture).
        """
        origin = self.getOrigin()
        if 'rupture' not in self._hdfobj:
            return PointRupture(origin)
        
        ruptext = self._hdfobj['rupture'].attrs['rupture_string']
        rupio = io.StringIO(ruptext)
        rupture = read_rupture_file(origin,rupio)
        return rupture
        
    def getStationList(self):
        """Return a StationList object if data files were supplied, or None.

        :returns:
          StationList object if data files were supplied, or None.
        """
        if 'station_string' not in self._hdfobj:
            return None
        station_string = self._hdfobj['station'].attrs['station_string']
        return StationList.loadFromSQL(station_string)

    def getOrigin(self):
        """Return an Origin object for this earthquake.

        :returns:
          Origin object.
        """
        origin_file = io.StringIO(self._hdfobj['event'].attrs['event_string'])
        origin = Origin.fromFile(origin_file)
        return origin
        
    def addData(self,datafiles):
        """Append new data to the internal StationList object.
        
        :param datafiles:
          List of paths to XML datafiles.
        """
        stationlist = self.getStationList()
        stationlist.addData(datafiles)
        self.stashStationList(stationlist)

    def stashStationList(self,station):
        """Insert a new StationList object into the data file.

        :param station:
          StationList object.
        """
        station_group = self._hdfobj.create_group('station')
        station_group.attrs['station_string'] = station.dumpToSQL()
        
    def changeConfig(self):
        pass
            
        
    def __del__(self):
        if self._hdfobj:
            self._hdfobj.close()

    def close(self):
        """Close the HDF5 file.

        """
        if self._hdfobj:
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
                raise TypeError('Unsupported metadata value type "%s"' % tvalue)

#            print("key: ", key, " value ", value, " type ", tvalue)
            if isinstance(value,dict):
                subgroup = group.create_group(key)
                self._saveDict(subgroup,value)
                continue
            elif isinstance(value,datetime):
                value = time.mktime(value.timetuple())
            elif isinstance(value, list):
                for i, val in enumerate(value):
#                    print("key: ", key, " value ", val, " type ", type(val))
                    if isinstance(val, str):
                        value[i] = val.encode('utf8')
            else:
                pass
            group.attrs[key] = value

class OutputContainer(object):
    def __init__(self,hdfobj):
        self._hdfobj = hdfobj
    
    @classmethod
    def loadFromHDF(cls,hdffile):
        hdfobj = h5py.File(hdffile, "r+")
        #probably should do some validating to make sure relevant data exists
        return cls(hdfobj)

    
        
