#!/usr/bin/env python

# stdlib imports
from datetime import datetime
import collections
import time
import io

# third party imports
import h5py
import numpy as np

# local imports
from shakelib.rupture.factory import get_rupture
from shakelib.rupture.point_rupture import PointRupture
from shakelib.rupture.origin import Origin
from shakelib.station import StationList

# list of allowed data types in dictionaries
ALLOWED = [str, int, float, bool, bytes,
           type(None),
           list, tuple, np.ndarray,
           np.float64, np.bool_, np.int64,
           dict, datetime,
           collections.OrderedDict]


class InputContainer(object):
    def __init__(self, hdfobj):
        """
        Instantiate an InputContainer from an open h5py File Object.

        Args:
            hdfobj:  Open h5py File Object.
        """
        self._hdfobj = hdfobj

    @classmethod
    def loadFromHDF(cls, hdf_file):
        """
        Instantiate an InputContainer from an HDF5 file.

        Args:
            hdf_file: Valid path to HDF5 file.

        Returns:
            Instance of InputContainer.
        """
        hdfobj = h5py.File(hdf_file, "r+")
        # probably should do some validating to make sure relevant data exists
        return cls(hdfobj)

    def getFileName(self):
        return self._hdfobj.filename

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
        # ----------------------------------------------------------------------
        # open the file for writing, nuke if already exists
        # ----------------------------------------------------------------------
        hdfobj = h5py.File(filename, "w")

        self = cls(hdfobj)

        # ----------------------------------------------------------------------
        # The config and event info are mandatory
        # write the config dictionary to a config group
        # ----------------------------------------------------------------------
        self._storeConfig(config)

        # stash the event.xml in a group
        self._storeEvent(eventfile)

        # The rupture and data files are optional
        if rupturefile:
            self._storeRupture(rupturefile)

        # ----------------------------------------------------------------------
        # create the stationlist object, then dump its database as a big string
        # into the hdf
        # ----------------------------------------------------------------------
        if datafiles:
            station = StationList.loadFromXML(datafiles, ":memory:")
            self.stashStationList(station)

        # ----------------------------------------------------------------------
        # Store the version history.
        # ----------------------------------------------------------------------
        if version_history:
            self._storeHistory(version_history)

        return self

    def getConfig(self):
        """
        Return the config dictionary that was passed in via input files.

        Returns:
            Dictionary of configuration information.
        """
        config = _h5group2dict(self._hdfobj['config'])
        return config

    def _storeConfig(self, config):
        config_group = self._hdfobj.create_group('config')
        _dict2h5group(config, config_group)

    def updateConfig(self, config):
        if 'config' in self._hdfobj:
            del self._hdfobj['config']
        self._storeConfig(config)

    def _storeEvent(self, eventfile):
        try:
            event_string = open(eventfile, 'rt').read()
        except TypeError:
            event_string = eventfile.getvalue()
        event_group = self._hdfobj.create_group('event')
        event_group.attrs['event_string'] = event_string

    def updateEvent(self, eventfile):
        if 'event' in self._hdfobj:
            del self._hdfobj['event']
        self._storeEvent(eventfile)

    def _storeRupture(self, rupturefile):
        rupturedata = open(rupturefile, 'rt').read()
        rupture_group = self._hdfobj.create_group('rupture')
        rupture_group.attrs['rupture_string'] = rupturedata

    def updateRupture(self, rupturefile):
        if 'rupture' in self._hdfobj:
            del self._hdfobj['rupture']
        self._storeRupture(rupturefile)

    def getRupture(self):
        """
        Return a Rupture object (PointRupture if no rupture file was
        specified.)

        Returns:
            Rupture (Point, Edge or Quad Rupture).
        """
        origin = self.getOrigin()
        if 'rupture' not in self._hdfobj:
            return PointRupture(origin)

        ruptext = self._hdfobj['rupture'].attrs['rupture_string']
        rupio = io.StringIO(ruptext)
        rupture = get_rupture(origin, rupio)
        return rupture

    def getStationList(self):
        """
        Return a StationList object if data files were supplied, or None.

        Returns:
            StationList object if data files were supplied, or None.
        """
        if 'station' not in self._hdfobj:
            return None
        station_sql = self._hdfobj['station'][()]
        return StationList.loadFromSQL(station_sql)

    def addData(self, datafiles):
        """
        Append new data to the internal StationList object.

        Args:
            datafiles: List of paths to XML datafiles.
        """
        if 'station' in self._hdfobj:
            stationlist = self.getStationList()
            stationlist.addData(datafiles)
            del self._hdfobj['station']
        else:
            stationlist = StationList.loadFromXML(datafiles, ":memory:")
        self.stashStationList(stationlist)

    def stashStationList(self, station):
        """
        Insert a new StationList object into the data file.

        Args:
            station: StationList object.
        """
        self._hdfobj.create_dataset('station', data=station.dumpToSQL())

    def getHistory(self):
        """
        Return the history dictionary.

        Returns:
            Dictionary holding the history list
        """
        if 'version_history' in self._hdfobj:
            return _h5group2dict(self._hdfobj['version_history'])
        else:
            return None

    def _storeHistory(self, version_history):
        history_group = self._hdfobj.create_group('version_history')
        _dict2h5group(version_history, history_group)

    def updateHistory(self, version_history):
        if 'version_history' in self._hdfobj:
            del self._hdfobj['version_history']
        self._storeHistory(version_history)

    def getOrigin(self):
        """
        Return an Origin object for this earthquake.

        Returns:
            Origin object.
        """
        origin_file = io.StringIO(self._hdfobj['event'].attrs['event_string'])
        origin = Origin.fromFile(origin_file)
        return origin

    def __del__(self):
        if self._hdfobj:
            self._hdfobj.close()

    def close(self):
        """Close the HDF5 file.

        """
        if self._hdfobj:
            self._hdfobj.close()


class OutputContainer(object):
    """
    Generic hdf5 output container to store metadata and data sets (with or
    without associated metadata).
    """

    def __init__(self, hdfobj):
        self._hdfobj = hdfobj

    @classmethod
    def loadFromHDF(cls, hdffile):
        """
        Load an HDF file into the object.

        Args:
            hdffile (str):
                Path to file to be loaded.

        Returns:
            A :class:`OutputContainer` object.
        """
        hdfobj = h5py.File(hdffile, "r+")
        return cls(hdfobj)

    @classmethod
    def createEmpty(cls, filename):
        """
        Create an empty HDF file/object.

        Args:
            filename (str):
                Path to file to be created.

        Returns:
            An empty :class:`OutputContainer` object tied to file
            'filename'.
        """

        hdfobj = h5py.File(filename, "w")
        return cls(hdfobj)

    def addMetadata(self, data, name='metadata'):
        """
        Add a dictionary of metatata as a group.

        Args:
            data (dict):
                Dictionary to be saved as a group.
            name (str)(optional):
                The name of the group holding the metadata. The default is
                'metadata'.

        Returns:
            The h5py group holding the metadata.
        """

        mgroup = self._hdfobj.create_group(name)
        _dict2h5group(data, mgroup)
        return mgroup

    def getMetadata(self, name='metadata'):
        """
        Retrieve a dictionary of metatata from a group.

        Args:
            name (str)(optional):
                The name of the group holding the metadata. The default is
                'metadata'.

        Returns:
            A dictionary holding the metadata.
        """

        return _h5group2dict(self._hdfobj[name])

    def addData(self, data, name, metadata=None):
        """
        Add an array of data (and, optionally, it's metadata) as a dataset.

        Args:
            data (array):
                Array to be saved as a dataset.
            name (str):
                The name of the dataset holding the data.
            metadata (dict)(optional):
                An (optional) dictionary of metadata to be associated with
                the dataset. The dictionary must contain only scalars and
                numpy arrays.

        Returns:
            The h5py dataset holding the data and metadata.
        """

        dset = self._hdfobj.create_dataset(name, data=data)
        if metadata:
            for key, value in metadata.items():
                dset.attrs[key] = value
        return dset

    def getData(self, name):
        """
        Retrieve an array of data and any associated metadata from a dataset.

        Args:
            name (str):
                The name of the dataset holding the data and metadata.

        Returns:
            An array of data and a dictionary of metadata.
        """

        dset = self._hdfobj[name]
        data = dset[()]
        metadata = {}
        for key, value in dset.attrs.items():
            metadata[key] = value
        return data, metadata

    def close(self):
        """
        Close the HDF5 file.

        """
        if self._hdfobj:
            self._hdfobj.close()

    def getIMTlist(self):
        """
        Returns a list of IMT grids in the file.
        """
        imtlist = []
        for key in self._hdfobj.keys():
            if key in ('PGA', 'PGV', 'MMI') or \
               (key.startswith('SA(') and key.endswith(')')):
                imtlist.append(key)
        return imtlist

def _dict2h5group(mydict, group):
    """
    Recursively save dictionaries into groups in an HDF group..

    Args:
        mydict (dict):
            Dictionary of values to save in group or dataset.  Dictionary
            can contain objects of the following types: str, unicode, int,
            float, long, list, tuple, np. ndarray, dict,
            datetime.datetime, collections.OrderedDict
        group:
            HDF group or dataset in which to storedictionary of data.

    Returns
        nothing
    """
    for (key, value) in mydict.items():
        tvalue = type(value)
        if tvalue not in ALLOWED:
            raise TypeError('Unsupported metadata value type "%s"' % tvalue)
        if isinstance(value, dict):
            subgroup = group.create_group(key)
            _dict2h5group(value, subgroup)
            continue
        elif isinstance(value, datetime):
            value = time.mktime(value.timetuple())
        elif isinstance(value, list):
            value = _encode_list(value)
        else:
            pass
        group.attrs[key] = value


def _encode_list(value):
    for i, val in enumerate(value):
        if isinstance(val, list):
            value[i] = _encode_list(val)
        elif isinstance(val, str):
            value[i] = val.encode('utf8')
        else:
            value[i] = val
    return value


def _h5group2dict(group):
    """
    Recursively create dictionaries from groups in an HDF file.

    Args:
        group:
            HDF5 group object.

    Returns:
      Dictionary of metadata (possibly containing other dictionaries).
    """
    tdict = {}
    for (key, value) in group.attrs.items():  # attrs are NOT subgroups
        if key.find('time') > -1:
            value = datetime.fromtimestamp(value)
        tdict[key] = value
    for (key, value) in group.items():  # these are going to be the subgroups
        tdict[key] = _h5group2dict(value)
    return _convert(tdict)


def _convert(data):
    """
    Recursively convert the bytes elements in a dictionary's values, lists,
    and tuples into ascii.

    Args:
        data (dict):
            A dictionary.

    Returns;
        A copy of the dictionary with the byte strings converted to ascii.
    """
    if isinstance(data, bytes):
        return data.decode('ascii')
    if isinstance(data, dict):
        return dict(map(_convert, data.items()))
    if isinstance(data, tuple):
        return tuple(map(_convert, data))
    if type(data) in (np.ndarray, list):
        return list(map(_convert, data))
    return data
