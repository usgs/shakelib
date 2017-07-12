# stdlib imports
import sqlite3
import xml.etree.ElementTree as ET
import copy
from collections import OrderedDict
import re
import time as time

# third party imports
import numpy as np

# local imports


TABLES = OrderedDict((
        ('station',
          OrderedDict((
           ('id', 'str primary key'), # id is net.sta
           ('network', 'str'),
           ('code', 'str'),
           ('name', 'str'),
           ('lat', 'float'),
           ('lon', 'float'),
           ('elev', 'float'),
           ('vs30', 'float'),
           ('instrumented', 'int')
           ))
          ),
         ('imt',
          OrderedDict((
           ('id', 'integer primary key'),
           ('imt_type', 'str')
           ))
          ),
         ('amp',
          OrderedDict((
           ('id', 'integer primary key'),
           ('station_id', 'str'),
           ('imt_id', 'int'),
           ('original_channel', 'str'),
           ('orientation', 'str'),
           ('amp', 'float'),
           ('uncertainty', 'float'),
           ('flag', 'str')
           ))
          )
         ))

#
# These are the netid's that indicate MMI data
#
CIIM_TUPLE = ('dyfi', 'mmi', 'intensity', 'ciim')


class StationList(object):
    """
    A class to facilitate reading ShakeMap formatted XML fies of peak
    amplitudes and MMI, and
    produce tables of station data. Seismic stations are considered to
    be 'instrumented'; MMI data is not instrumented and is indicated
    in the ShakeMap XML with a ``netid`` attribute of "DYFI," "MMI,"
    "INTENSITY," or "CIIM."

    .. note::
      Typically the user will call the class method :meth:`fromXML`
      to create a :class:`StationList` object the first time
      a set of station files are processed. (Or, as an alternative,
      the user can call :meth:`loadFromXML` and :meth:`fillTables`
      sequentially.)
      This will create a database at the location specified by the
      ``dbfile`` parameter to :meth:`fromXML`. Subsequent programs
      can use the default constructor to simply load ``dbfile``.

    """

    def __init__(self, db):
        """
        The default constructor reads a pre-built SQLite database of
        station data.

        Args:
            dbfile (str):
                A SQLite database file containing pre-processed
                station data.

        Returns:
            A :class:`StationList` object.

        """
        self.db = db
        self.cursor = self.db.cursor()

    def __del__(self):
        """
        Closes out the database when the object is destroyed.
        """
        self.db.commit()
        self.cursor.close()
        self.db.close()

    @classmethod
    def loadFromDBFile(cls, dbfile):
        """
        Create a StationList object by reading a SQLite database file.

        Args:
            dbfile (string):
                Path to a file which contains a SQLite database with station 
                data.

        Returns:
            :class:`StationList` object
        """
        db = sqlite3.connect(dbfile)
        self = cls(db)
        return self

    def __del__(self):
        """
        Closes out the database when the object is destroyed.
        """
        self.db.commit()
        self.cursor.close()
        self.db.close()


    def createDict(self):
        """Create a dictionary that maps to GeoJSON format for station data.

        :returns:
          Dictionary with fields:
            - type 'Feature'
            - id   'netid.code'
            - geometry Dictionary with fields:
              - coordinates: (X,Y) tuple
              - type: 'Point'
            - properties Dictionary with fields:
              - name Station name
              - intensity_flag ??
              - distance Station distance
              - location Station loc
              - code Station code
              - commType Station commtype
              - source Station source
              - network Station netid
              - instrumentType Station insttype
              - intensity Station intensity
              - pga (may not be present) comp->pga->value
              - pgv (may not be present) comp->pgv->value
              - channels, list of dictionaries with fields:
                - name station->comp->name
                - amplitudes, list of dictionaries with fields:
                  - name station->comp->component name
                  - flag station->comp->component name->flag
                  - value station->comp->component name->value
                  - units ('%g' for pga or any psa, 'cm/s' for pgv)
        """

    def _load_features(xmlfile):
        #each station is a feature in a geojson file
        dom = minidom.parse(xmlfile)
        for root in dom.childNodes:
            if not isinstance(root, minidom.DocumentType):
                break
        stations = root.getElementsByTagName('station')
        imt_translate = {}
        for station in stations:
            feature = {'type':'Feature'}
            netid = station.getAttribute('netid')
            code = station.getAttribute('code')
            feature['id'] = '%s.%s' % (netid,code)
            lat = code = float(station.getAttribute('lat'))
            lon = code = float(station.getAttribute('lon'))
            feature['geometry'] = {'type':'Point','coordinates':[lon,lat]}
            properties = {}
            properties['name'] = station.getAttribute('name')
            properties['intensity_flag'] = station.getAttribute('')#??
            properties['distance'] = float(station.getAttribute('distance'))
            properties['location'] = station.getAttribute('loc')
            properties['code'] = station.getAttribute('code')
            properties['commType'] = station.getAttribute('commtype')
            properties['source'] = station.getAttribute('source')
            properties['network'] = station.getAttribute('netid')
            properties['instrumentType'] = station.getAttribute('insttype')
            properties['intensity'] = float(station.getAttribute('intensity'))
            comps = station.getElementsByTagName('comp')
            channels = []
            for comp in comps:
                channel = {'name':comp.getAttribute('name')}
                for component in channel.childNodes:
                    if not isinstance(component, minidom.DocumentType):
                        break
                    pgmdict,imtset = self._getGroundMotions(component,imt_translate)
                    
    @classmethod
    def loadFromSQL(cls, sql):
        pass
    
    def dumpToSQL(self):
        pass
       
    @classmethod
    def loadFromXML(cls, xmlfiles, dbfile):
        """
        Create a StationList object by reading one or more ShakeMap XML input
        files.

        Args:
            xmlfiles (sequence of str):
                Sequence of ShakeMap XML input files to read.
            dbfile (str):
                Path to a file into which to write the SQLite database.

        Returns:
            :class:`StationList` object

        """
        # Create the database and tables
        db = sqlite3.connect(dbfile)
        self = cls(db)
        self._createTables()
        return self.addData(xmlfiles)

    def addData(self,xmlfiles):
        """
        Create a StationList object by reading one or more ShakeMap XML input
        files.

        Args:
            xmlfiles (sequence of str):
                Sequence of ShakeMap XML input files to read.
        Returns:
            :class:`StationList` object

        """
        # Parse the xml into a dictionary
        t1 = time.time()
        stationdict = {}
        imtset = set()
        for xmlfile in xmlfiles:
            stationdict, ims = self._filter_station(xmlfile, stationdict)
            imtset |= ims
        t2 = time.time()
        print('filter time %f sec' % (t2 - t1))
        # fill the database and create the object from it   
        t1 = time.time()
        self._loadFromDict(stationdict, imtset)
        t2 = time.time()
        print('load from dict time %f sec' % (t2 - t1))
        return self

    def _loadFromDict(self, stationdict, imtset):
        """
        Internal method to turn the station dictionary created from the
        ShakeMap XML input files into a SQLite database.

        Args:
            stationdictlist (list of stationdicts):
                A list of station dictionaries returned by _filter_station().
            dbfile (string):
                The path to which the SQLite database will be written.

        Returns:
            :class:`StationList` object
        """
        #
        # Get the current IMTs and their IDs and add any new ones
        #
        imts_in_db = self.getIMTtypes()
        new_imts = imtset - imts_in_db
        if any(new_imts):
            self.cursor.executemany('INSERT INTO imt (imt_type) VALUES (?)', 
                                zip(new_imts))
            self.db.commit()

        # Now get the updated list of IMTs and their IDs
        query = 'SELECT imt_type, id FROM imt'
        self.cursor.execute(query)
        imt_hash = dict(self.cursor.fetchall())

        #
        # Get the station codes for all the stations in the db            
        #
        query = 'SELECT id FROM station'
        self.cursor.execute(query)
        sta_set = set([z[0] for z in self.cursor.fetchall()])

        #
        # Insert any new stations into the station table
        #
        station_rows = []
        for sta_id, station_tpl in stationdict.items():
            if sta_id in sta_set:
                continue
            else:
                sta_set.add(sta_id)
            station_attributes, comp_dict = station_tpl
            lat = station_attributes['lat']
            lon = station_attributes['lon']
            network = station_attributes['netid']
            code = station_attributes['code']
            if 'name' in station_attributes:
                name = station_attributes['name']
            else:
                name = None
            if 'elev' in station_attributes:
                elev = station_attributes['elev']
            else:
                elev = None
            if 'vs30' in station_attributes:
                vs30 = station_attributes['vs30']
            else:
                vs30 = None

            instrumented = int(network.lower() not in CIIM_TUPLE)

            station_rows.append((sta_id, network, code, name, lat, lon,
                                 elev, vs30, instrumented))
                
        self.cursor.executemany(
                'INSERT INTO station (id, network, code, name, lat, lon, '
                'elev, vs30, instrumented) VALUES '
                '(?, ?, ?, ?, ?, ?, ?, ?, ?)', station_rows
            )
        self.db.commit()

        #
        # Now add the amps, first get the current set so we don't add
        # any duplicates; a unique amp will be (station_id, imt_id, 
        # original_channel)
        #
        query = 'SELECT station_id, imt_id, original_channel FROM amp'
        self.cursor.execute(query)
        amp_rows = self.cursor.fetchall()
        # Create a unique identifier for each amp so we don't repeat any
        amp_set = set([str(v[0]) + '.' + str(v[1]) + '.' + str(v[2]) 
                        for v in amp_rows])
                
        #
        # Insert the amps for each component
        #
        amp_rows = []
        for sta_id, station_tpl in stationdict.items():
            station_attributes, comp_dict = station_tpl
            instrumented = int(station_attributes['netid'].lower()
                               not in CIIM_TUPLE)
            for original_channel, pgm_dict in comp_dict.items():
                orientation = self._getOrientation(original_channel)
                for imt_type, imt_dict in pgm_dict.items():
                    if (instrumented == 0) and (imt_type != 'MMI'):
                        continue
                    imtid = imt_hash[imt_type]
                    amp_id = str(sta_id) + '.' + str(imtid) + '.' + \
                             str(original_channel)
                    if amp_id in amp_set:
                        continue
                    else:
                        amp_set.add(amp_id)
                    amp = imt_dict['value']
                    flag = imt_dict['flag']
                    if np.isnan(amp) or (amp <= 0):
                        amp = 'NULL'
                        flag = 'G'
                    elif imt_type == 'MMI':
                        pass
                    elif imt_type == 'PGV':
                        amp = np.log(amp)
                    else:
                        amp = np.log(amp / 100.0)

                    amp_rows.append((sta_id, imtid, original_channel,
                                     orientation, amp, flag))

        self.cursor.executemany(
                'INSERT INTO amp (station_id, imt_id, original_channel, '
                'orientation, amp, flag) VALUES (?, ?, ?, ?, ?, ?)', amp_rows
            )
        self.db.commit()
        return

    def getIMTtypes(self):
        """
        Return a set of IMT types found in the database
        
        Args:
            None
            
        Returns:
            A set of IMT types
        """
        self.cursor.execute('SELECT imt_type FROM imt')
        return set([z[0] for z in self.cursor.fetchall()])
            
    def getStationDataframe(self, instrumented):
        """
        Return a dictionary of the instrumented or non-instrumented
        stations. The keys describe the parameter, the values are Numpy
        arrays of the parameter in question.

        For the standard set of ShakeMap IMTs (mmi, pga, pgv, psa03, psa10,
        psa30), the keys in the dictionary would be:

        'id', 'network', 'code', 'name', 'lat', 'lon', 'elev', 'vs30', 
        'instrumented', 'PGA', 'PGV', 'SA(0.3)', 'SA(1.0)', 'SA(3.0)'

        For the non-instrumented dictionary, the keys would be:

        'id', 'network', 'code', 'name', 'lat', 'lon', 'elev', 'vs30', 
        'instrumented', 'MMI'

        The **id** column is **network** and **code** concatenated with a
        period (".") between them.
        
        All ground motion units are natural log units. Distances are in km.

        Args:
            instrumented (integer):
                Set to 1 (one) if the dictionary is to contain the instrumented
                stations, or to 0 (zero) if the dictionary is to contain the
                non-instrumented (MMI) stations.

        Returns:
            A dictionary of Numpy arrays.
        """

        columns = list(TABLES['station'].keys())
        dstr = ', '.join(columns)
        self.cursor.execute(
                'SELECT %s FROM station where instrumented = %d' %
                (dstr, instrumented)
            )

        station_rows = self.cursor.fetchall()
        nstation_rows = len(station_rows)
        station_columns = list(zip(*station_rows))
        df = OrderedDict()
        for ic, col in enumerate(columns):
            df[col] = np.array(station_columns[ic])

        for imt in self.getIMTtypes():
            if (instrumented and 'MMI' in imt) or \
               (not instrumented and 'MMI' not in imt):
                continue
            df[imt] = np.full(nstation_rows, np.nan)

        id_dict = dict(zip(df['id'], range(nstation_rows)))

        #
        # Get all of the unflagged amps with the proper orientation
        #
        self.cursor.execute(
                'SELECT a.amp, i.imt_type, a.station_id FROM '
                'amp a, station s, imt i WHERE a.flag = "0" '
                'AND s.id = a.station_id '
                'AND a.imt_id = i.id '
                'AND s.instrumented = %d AND a.orientation NOT IN ("Z", "U") '
                'AND a.amp IS NOT NULL' % (instrumented)
            )
        amp_rows = self.cursor.fetchall()

        #
        # Go through all the amps and put them into the data frame
        #
        for this_row in amp_rows:
            #
            # Set the cell to the peak amp
            #
            rowidx = id_dict[this_row[2]]
            cval = df[this_row[1]][rowidx]
            amp = this_row[0]
            if np.isnan(cval) or (cval < amp):
                df[this_row[1]][rowidx] = amp

        return df

    @staticmethod
    def _getOrientation(orig_channel):
        """
        Return a character representing the orientation of a channel.

        Args:
            orig_channel (string):
                String representing the seed channel (e.g. 'HNZ'). The
                final character is assumed to be the (uppercase) orientation.

        Returns:
            Character representing the channel orientation. One of 'N',
            'E', 'Z', 'H' (for horizontal), or 'U' (for unknown).
        """
        if orig_channel == 'mmi':
            orientation = 'H'           # mmi is arbitrarily horizontal
        elif orig_channel[-1] in ('N', 'E', 'Z'):
            orientation = orig_channel[-1]
        elif orig_channel[-1] == "K":   # Channel is "UNK"; assume horizontal
            orientation = 'H'
        else:
            orientation = 'U'  # this is unknown
        return orientation


    @staticmethod
    def _getGroundMotions(comp, imt_translate):
        """
        Get a dictionary of peak ground motions (values and flags).
        Output keys are one of: [pga,pgv,psa03,psa10,psa30]
        Even if flags are not specified in the input, they will
        be guaranteed to at least have a flag of '0'.
        """
        pgmdict = {}
        imtset = set()
        for pgm in comp:
            if pgm.tag == '#text':
                continue
            key = pgm.tag
            if key not in imt_translate:
                if key in ('acc', 'pga'):
                    new_key = 'PGA'
                elif key in ('vel', 'pgv'):
                    new_key = 'PGV'
                elif 'mmi' in key:
                    new_key = 'MMI'
                elif 'psa' in key:
                    pp = get_imt_period(key)
                    new_key = 'SA(' + str(pp) + ')'
                else:
                    raise ValueError('Unknown amp type in input: %s' % key)
                imt_translate[key] = new_key
            else:
                new_key = imt_translate[key]
            key = new_key

            if 'value' in pgm.attrib:
                try:
                    value = float(pgm.attrib['value'])
                except ValueError:
                    print('Unknown value in XML: ', pgm.attrib['value'],
                          ' for amp ', pgm.tag)
                    continue
            else:
                print('No value for amp ', pgm.tag)
                continue
            if 'flag' in pgm.attrib and pgm.attrib['flag'] != '':
                flag = pgm.attrib['flag']
            else:
                flag = '0'
            pgmdict[key] = {'value': value, 'flag': flag}
            imtset.add(key)
        return pgmdict, imtset

    def _filter_station(self, xmlfile, stationdict):
        """
        Filter individual xmlfile into a stationdict data structure.

        Args:
            xmlfile (string):
                Path to ShakeMap XML input file (or file-like object)
                containing station data.

        Returns:
            stationdict data structure
        """
        imt_translate = {}
        imtset = set()
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        for sl in root.iter('stationlist'):
            for station in sl:
                if station.tag != 'station':
                    continue
                #look at the station attributes to figure out if this is a DYFI-type station
                #or a station with instruments measuring PGA, PGV, etc.
                attributes = station.attrib.copy()
                netid = attributes['netid']
                instrumented = int(netid.lower() not in CIIM_TUPLE)
                    
                code = attributes['code']
                if code.startswith(netid + '.'):
                    sta_id = code
                    code = code.replace(netid + '.', '')
                else:
                    sta_id = netid + '.' + code   
    
                if sta_id in stationdict:
                    compdict = stationdict[sta_id]
                else:
                    compdict = {}
                for comp in station:
                    compname = comp.attrib['name']
                    if 'Intensity Questionnaire' in str(compname):
                        compdict['mmi'] = {}
                        continue
                    tpgmdict, ims = self._getGroundMotions(comp, imt_translate)
                    if compname in compdict:
                        pgmdict = compdict[compname]
                    else:
                        pgmdict = {}
                    pgmdict.update(tpgmdict)
                    # copy the VALUES, not REFERENCES, of the component list into
                    # our growing dictionary
                    compdict[compname] = copy.copy(pgmdict)
                    imtset |= ims
                if ('intensity' in attributes) and (instrumented == 0):
                    if 'mmi' not in compdict:
                        compdict['mmi'] = {}
                    compdict['mmi']['MMI'] = \
                        {'value': float(attributes['intensity']),
                         'flag': '0'}
                    imtset.add('MMI')
                stationdict[sta_id] = (attributes, copy.copy(compdict))
        return stationdict, imtset


    def _createTables(self):
        """
        Build the database tables.
        """
        for table in TABLES.keys():
            sql = 'CREATE TABLE %s (' % table
            nuggets = []
            for column, ctype in TABLES[table].items():
                nuggets.append('%s %s' % (column, ctype))
            sql += ','.join(nuggets) + ')'
            self.cursor.execute(sql)

        self.db.commit()
        return

def get_imt_period(imt):

    p = re.search('(?<=psa)\d+', imt)
    return float(p.group(0)[:-1] + '.' + p.group(0)[-1])

def imt_sort(key):

    if isinstance(key, tuple):
        key = key[0]
    if key == 'MMI':
        return 0
    elif key == 'PGA':
        return 1
    elif key == 'PGV':
        return 2
    elif 'SA' in key:
        return 2 + float(key[3:-1])
    else:
        raise ValueError('Error in imt_sort, unknown key=%s' % str(key))
