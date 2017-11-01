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
from mapio.gridcontainer import GridHDFContainer,_split_dset_attrs
from impactutils.io.container import _get_type_list

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

class InputContainer(GridHDFContainer):
    @classmethod
    def createFromInput(cls, filename, config, eventfile, rupturefile=None,
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
        if 'config' in self.getDictionaries():
            self.dropDictionary('config')
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

        if 'event' in self.getDictionaries():
            self.dropDictionary('event')
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
        if 'rupture' in self.getStrings():
            self.dropString('rupture')
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
        if 'station_data' in self.getStrings():
            self.dropString('station_data')
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
        if 'station_data' in self.getStrings():
            self.dropString('station_data')
        self.setString('station_data',station_sql)

    def setVersionHistory(self,history_dict):
        """
        Store a dictionary containing version history in the container.

        Args:
          history_dict (dict): Dictionary containing version history. ??
        """
        if 'version_history' in self.getDictionaries():
            self.dropDictionary('version_history')
        self.setDictionary('version_history',history_dict)

    def getConfig(self):
        """
        Return the configuration information as a dictionary.

        Returns:
          (dict) Dictionary of configuration information.
        """
        config = None
        if 'config' in self.getDictionaries():
            config = self.getDictionary('config')
        return config

    def getRupture(self):
        """
        Get rupture object from data stored in container.

        Returns:
          (Rupture) An instance of a sub-class of a Rupture object

        """
        rupture_obj = None
        if 'rupture' in self.getStrings():
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
        if 'station_data' in self.getStrings():
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
        if 'version_history' in self.getDictionaries():
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
    
    
class OutputContainer(GridHDFContainer):
    def setIMT(self,imt_name,imt_mean,mean_metadata,
               imt_std,std_metadata,
               component='maximum',
               compression=True):
        """Store IMT mean and standard deviation objects as datasets.
        
        Args:
          name (str): Name of the IMT (MMI,PGA,etc.) to be stored.
          imt_mean (Grid2D): Grid2D object of IMT mean values to be stored.
          mean_metadata (dict): Dictionary containing metadata for mean IMT grid.
          imt_std (Grid2D): Grid2D object of IMT standard deviation values to be stored.
          std_metadata (dict): Dictionary containing metadata for mean IMT grid.
          component (str): Component type, i.e. 'maximum','rotd50',etc.
          compression (bool): Boolean indicating whether dataset should be compressed
                              using the gzip algorithm.

        Returns:
          HDF Group containing IMT grids and metadata.
        """
        #set up the name of the group holding all the information for the IMT
        group_name = '__imt_%s_%s__' % (imt_name,component)
        imt_group = self._hdfobj.create_group(group_name)

        #create the data set containing the mean IMT data and metadata
        mean_name = '__mean_%s_%s__' % (imt_name,component)
        mean_data = imt_mean.getData()
        mean_set = imt_group.create_dataset(mean_name,data=mean_data,compression=compression)
        if mean_metadata is not None:
            for key,value in mean_metadata.items():
                mean_set.attrs[key] = value
        for key,value in imt_mean.getGeoDict().asDict().items():
            mean_set.attrs[key] = value

        #create the data set containing the std IMT data and metadata
        std_name = '__std_%s_%s__' % (imt_name,component)
        std_data = imt_std.getData()
        std_set = imt_group.create_dataset(std_name,data=std_data,compression=compression)
        if std_metadata is not None:
            for key,value in std_metadata.items():
                std_set.attrs[key] = value
        for key,value in imt_std.getGeoDict().asDict().items():
            std_set.attrs[key] = value

        return imt_group

    def getIMT(self,imt_name,component='maximum'):
        """
        Retrieve a Grid2D object and any associated metadata from the container.

        Args:
            name (str):
                The name of the Grid2D object stored in the container.

        Returns:
            (dict) Dictionary containing 4 items:
                   - mean Grid2D object for IMT mean values.
                   - mean_metadata Dictionary containing any metadata describing mean layer.
                   - std Grid2D object for IMT standard deviation values.
                   - std_metadata Dictionary containing any metadata describing standard deviation layer.
        """
        group_name = '__imt_%s_%s__' % (imt_name,component)
        if group_name not in self._hdfobj:
            raise LookupError('No group called %s in HDF file %s' % (imt_name,self.getFileName()))
        imt_group = self._hdfobj[group_name]

        #get the mean data and metadata
        mean_name = '__mean_%s_%s__' % (imt_name,component)
        mean_dset = imt_group[mean_name]
        mean_data = mean_dset[()]

        array_metadata,mean_metadata = _split_dset_attrs(mean_dset)
        mean_geodict = GeoDict(array_metadata)
        mean_grid = Grid2D(mean_data,mean_geodict)

        #get the std data and metadata
        std_name = '__std_%s_%s__' % (imt_name,component)
        std_dset = imt_group[std_name]
        std_data = std_dset[()]

        array_metadata,std_metadata = _split_dset_attrs(std_dset)
        std_geodict = GeoDict(array_metadata)
        std_grid = Grid2D(std_data,std_geodict)

        #create an output dictionary
        imt_dict = {'mean':mean_grid,
                    'mean_metadata':mean_metadata,
                    'std':std_grid,
                    'std_metadata':std_metadata}
        return imt_dict

    def getIMTs(self,component='maximum'):
        """
        Return list of names of IMTs matching input component type.

        Args:
          component (str): Name of component ('maximum','rotd50',etc.)

        Returns:
          (list) List of names of IMTs matching component stored in container.
        """
        imt_groups = _get_type_list(self._hdfobj,'imt')
        comp_groups = []
        for imt_group in imt_groups:
            if imt_group.find(component) > -1:
                comp_groups.append(imt_group.replace('_'+component,''))
        return comp_groups

    def getComponents(self,imt_name):
        """
        Return list of components for given IMT.

        Args:
          imt_name (str): Name of IMT ('MMI','PGA',etc.)

        Returns:
          (list) List of names of components for given IMT.
        """
        components = _get_type_list(self._hdfobj,'imt_'+imt_name)
        return components

    def dropIMT(self,imt_name):
        """
        Delete IMT datasets from container.

        Args:
          name (str):
                The name of the IMT to be deleted.

        """
        group_name = '__imt_%s_%s__' % (imt_name,component)
        if group_name not in self._hdfobj:
            raise LookupError('No group called %s in HDF file %s' % (imt_name,self.getFileName()))
        del self._hdfobj[group_name]
