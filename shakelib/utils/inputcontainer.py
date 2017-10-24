#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import collections
import time
import io
import os.path
import json

# third party imports
import h5py
import numpy as np
from mapio.grid2d import Grid2D
from mapio.geodict import GeoDict
from mapio.gridcontainer import GridHDFContainer

# local imports
from shakelib.rupture.factory import get_rupture,text_to_json,json_to_rupture
from shakelib.rupture.point_rupture import PointRupture
from shakelib.rupture.origin import Origin,read_event_file
from shakelib.station import StationList

# list of allowed data types in dictionaries
ALLOWED = [str, int, float, bool, bytes,
           type(None),
           list, tuple, np.ndarray,
           np.float64, np.bool_, np.int64,
           dict, datetime,
           collections.OrderedDict]

class InputContainer():

    def __init__(self,container):
        

    @classmethod
    def loadFromInput(cls, filename, config, eventfile, rupturefile=None,
                      datafiles=None, version_history=None):
        """
        Instantiate an InputContainer from ShakeMap input data.

        Args:
            filename: Path to HDF5 file that will be created to encapsulate all
                input data.
            config: Dictionary containing all configuration information
                necessary for ShakeMap ground motion and other calculations.
            eventfile: Path to ShakeMap event.xml file.
            rupturefile: Path to ShakeMap rupture text or JSON file.
            datafiles: List of ShakeMap data (DYFI, strong motion) files.

        Returns:
            Instance of InputContainer.
        """
        container = cls.create(filename)
        container.setConfig(config)
        container.setEvent(eventfile)
        if rupturefile is not None:
            container.setRupture(rupturefile)
        if datafiles is not None:
            container.setStationData(datafiles)
        if version_history is not None:
            container.setVersionHistory(version_history)
        return container
    
    def setConfig(self,config):
        """
        Add the config as a dictionary to the HDF file.

        Args:
          config (dict-like): Dict-like object with configuration information.
        """
        self.setDictionary('config',config)

    def setEvent(self,event_file):
        """
        Store the information found in an event.xml file as a dictionary.

        Note:  addEvent will attempt to extract productcode as an attribute of the
        event.xml file earthquake tag.  If this fails, productcode will be extracted from the
        directory tree, which should look something like this:
        ~/ShakeMap/[PROFILE]/data/[PRODUCTCODE]/current/event.xml

        where [PROFILE] is the current ShakeMap profile, and [PRODUCTCODE] is something 
        like "us2017abcd".

        Args:
          event_file (str): String path to an event.xml file.
        """
        event_dict = read_event_file(event_file)
        productcode = None
        if 'productcode' not in event_dict:
            epath,efile = os.path.split(event_file)
            path_parts = epath.split(os.sep)
            productcode = path_parts[-2]
        if productcode is not None and 'productcode' in event_dict and productcode != event_dict['productcode']:
            msg = 'productcode %s found in %s does not match data directory %s.'
            raise KeyError(msg % (event_dict['productcode'],event_file,productcode))
        self.setDictionary('event',event_dict)

    def setRupture(self,rupture_file):
        """
        Store data found in either JSON or text format rupture file.

        Args:
          rupture_file (str): File containing either JSON formatted rupture data or 
          older style fault.txt format.
        """
        try:
            rupture_data = json.load(open(rupture_file,'r'))
        except json.decoder.JSONDecodeError:
            rupture_data = text_to_json(rupture_file)

        rupture_data_string = json.dumps(rupture_data)
        self.setString('rupture',rupture_data_string)

    def setStationData(self,datafiles):
        """
        Insert observed ground motion data into the container.

        Args:
          datafiles (str): Path to an XML-formatted file containing ground motion observations,
          (macroseismic or instrumented).

        """
        station = StationList.loadFromXML(datafiles)
        station_sql = station.dumpToSQL()
        self.setString('station_data',station_sql)

    def addStationData(self,datafiles):
        """
        Add observed ground motion data into the container.

        Args:
          datafiles (str): Path to an XML-formatted file containing ground motion observations,
          (macroseismic or instrumented).

        """
        station_sql = self.getString('station_data')
        station = StationList.loadFromSQL(station_sql)
        station.addData(datafiles)
        station_sql = station.dumpToSQL()
        self.setString('station_data',station_sql)

    def setVersionHistory(self,history_dict):
        """
        Store a dictionary containing version history in the container.

        Args:
          history_dict (dict): Dictionary containing version history. ??
        """
        self.setDictionary('version_history',history_dict)

    def getConfig(self):
        """
        Return the configuration information as a dictionary.

        Returns:
          (dict) Dictionary of configuration information.
        """
        config = None
        if 'config' in self.getDictionaryNames():
            config = self.getDictionary('config')
        return config

    def getRupture(self):
        """
        Get rupture object from data stored in container.

        Returns:
          (Rupture) An instance of a sub-class of a Rupture object

        """
        rupture_obj = None
        if 'rupture' in self.getStringNames():
            rupture_data_string = self.getString('rupture')
            rupture_data = json.loads(rupture_data_string)
            origin = self.getOrigin()
            rupture_obj = json_to_rupture(rupture_data,origin)
        else:
            origin = self.getOrigin()
            rupture_obj = PointRupture(origin)
        return rupture_obj

    def getStationList(self):
        """
        Return the StationList object stored in this container.

        Returns:
          StationList object.
        """
        station = None
        if 'station_data' in self.getStringNames():
            station_sql = self.getString('station_data')
            station = StationList.loadFromSQL(station_sql)
        return station

    def getVersionHistory(self):
        """
        Return the dictionary containing version history.

        Returns:
          (dict): Dictionary containing version history. ??
        """
        version_dict = None
        if 'version_history' in self.getDictionaryNames():
            version_dict = self.getDictionary('version_history')
        return version_dict

    def getOrigin(self):
        """
        Extract an Origin object from the event dictionary stored in container.

        Returns:
          (Origin) Origin object.
          
        """
        event_dict = self.getDictionary('event')
        origin = Origin(event_dict)
        return origin
    
    

