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
from shakelib.grind.rupture import read_rupture_file, PointRupture
from shakelib.grind.origin import Origin
from shakelib.grind.station import StationList

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
                      datafiles=None):
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
        #-----------------------------------------------------------------------
        # open the file for writing, nuke if already exists
        #-----------------------------------------------------------------------
        hdfobj = h5py.File(filename, "w")

        this = cls(hdfobj)

        #-----------------------------------------------------------------------
        # The config and event info are mandatory
        # write the config dictionary to a config group
        #-----------------------------------------------------------------------
        config_group = this._hdfobj.create_group('config')
        _dict2h5group(config, config_group)

        # stash the event.xml in a group
        try:
            event_string = open(eventfile, 'rt').read()
        except TypeError:
            event_string = eventfile.getvalue()
        event_group = this._hdfobj.create_group('event')
        event_group.attrs['event_string'] = event_string

        # The rupture and data files are optional
        # write the rupture file data to a rupture group
        if rupturefile is not None:
            rupturedata = open(rupturefile, 'rt').read()
            rupture_group = this._hdfobj.create_group('rupture')
            rupture_group.attrs['rupture_string'] = rupturedata

        #-----------------------------------------------------------------------
        # create the stationlist object, then dump its database as a big string
        # into the hdf
        #-----------------------------------------------------------------------
        if datafiles is not None:
            station = StationList.loadFromXML(datafiles, ":memory:")
            this.stashStationList(station)

        return this

    def getConfig(self):
        """
        Return the config dictionary that was passed in via input files.

        Returns:
            Dictionary of configuration information.
        """
        config = _h5group2dict(self._hdfobj['config'])
        return config

    def getRupture(self):
        """
        Return a Rupture object (PointRupture if no rupture file was specified.)

        Returns:
            Rupture (Point, Edge or Quad Rupture).
        """
        origin = self.getOrigin()
        if 'rupture' not in self._hdfobj:
            return PointRupture(origin)

        ruptext = self._hdfobj['rupture'].attrs['rupture_string']
        rupio = io.StringIO(ruptext)
        rupture = read_rupture_file(origin, rupio)
        return rupture

    def getStationList(self):
        """
        Return a StationList object if data files were supplied, or None.

        Returns:
            StationList object if data files were supplied, or None.
        """
        if 'station_string' not in self._hdfobj['station'].attrs:
            print('No station list in object')
            return None
        station_string = self._hdfobj['station'].attrs['station_string']
        return StationList.loadFromSQL(station_string)

    def getOrigin(self):
        """
        Return an Origin object for this earthquake.

        Returns:
            Origin object.
        """
        origin_file = io.StringIO(self._hdfobj['event'].attrs['event_string'])
        origin = Origin.fromFile(origin_file)
        return origin

    def addData(self, datafiles):
        """
        Append new data to the internal StationList object.

        Args:
            datafiles: List of paths to XML datafiles.
        """
        stationlist = self.getStationList()
        stationlist.addData(datafiles)
        self.stashStationList(stationlist)

    def stashStationList(self, station):
        """
        Insert a new StationList object into the data file.

        Args:
            station: StationList object.
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
        if isinstance(dset, list) or isinstance(dset, np.ndarray):
            data = dset[:]
        else:
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
            for i, val in enumerate(value):
                if isinstance(val, str):
                    value[i] = val.encode('utf8')
        else:
            pass
        group.attrs[key] = value


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
            value = datetime.datetime.utcfromtimestamp(value)
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
