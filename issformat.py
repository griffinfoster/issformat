"""
Wrapper classes for LOFAR staion ACC, XST, SST, BST files

HDF5 wrapper support is optional
"""

# python 2 and 3 support
from __future__ import print_function

import datetime
import json
import numpy as np
import os

try:
    import h5py
    H5SUPPORT = True
except ImportError:
    H5SUPPORT = False

VALIDSTATIONS = [ 'CS001', 'CS002', 'CS003', 'CS004', 'CS005', 'CS006', 'CS007',
                  'CS011', 'CS013', 'CS017', 'CS021', 'CS024', 'CS026', 'CS028',
                  'CS030', 'CS031', 'CS032', 'CS101', 'CS103', 'CS201', 'CS301',
                  'CS302', 'CS401', 'CS501', 'DE601', 'DE602', 'DE603', 'DE604',
                  'DE605', 'DE609', 'FI609', 'FR606', 'IE613', 'KAIRA', 'PL610',
                  'PL611', 'PL612', 'RS106', 'RS205', 'RS208', 'RS210', 'RS305',
                  'RS306', 'RS307', 'RS310', 'RS406', 'RS407', 'RS409', 'RS503',
                  'RS508', 'RS509', 'RS511', 'SE607', 'UK608']

# TODO: unittests

"""
From ASTRON Single Station wiki:
HADEC or AZELGEO can be used to point to fixed position (north=0,0,AZELGEO, south=3.14159,0,AZELGEO, zenith=0,1.5708,AZELGEO).
AZELGEO means geodetic Azimuth and Elevation (N through E).
J2000 can be used to track an astonomical source (12h on the Terrestrial Time scale on 2000 jan 1).
Other sources: JUPITER, MARS, MERCURY, MOON, NEPTUNE, PLUTO, SATURN, SUN, URANUS, VENUS
See station_data_cookbook_v1.1.pdf for more details
"""
COORD_SYSTEMS = ['J2000', 'HADEC', 'AZELGEO', 'ITRF', 'B1950', 'GALACTIC', 'ECLIPTIC', 'JUPITER', 'MARS', 'MERCURY', 'MOON', 'NEPTUNE', 'PLUTO', 'SATURN', 'SUN', 'URANUS', 'VENUS']

class statData(object):
    """ Statistics file super class all other classes inherit from

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=1):
        
        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setIntegration(integration)

    def setStation(self, station=None):
        #if not (station in VALIDSTATIONS): print('WARNING: %s not in valid station list.'%station)
        self.station = station # Station ID string

    def setRCUmode(self, rcumode=None):
        """rcumode is either an integer (all RCUs are the same mode), a list of integers of length the number of RCUs, or None as a placeholder.
        """
        if rcumode is None:
            self.rcumode = None
        elif type(rcumode) is int:
            self.rcumode = rcumode
        elif type(rcumode) is np.int64: # HDF5 version
            self.rcumode = int(rcumode)
        elif type(rcumode) is np.ndarray: # HDF5 version
            self.rcumode = rcumode.tolist()
        elif len(rcumode) == 1: # single RCUMODE (int), all RCUs are the same mode
            self.rcumode = int(rcumode)
        else: # Mixed RCU mode (list of length the number of RCUs)
            self.rcumode = list(map(int, rcumode))

    def setTimestamp(self, ts=None):
        # YYYY-MM-DD HH:MM:SS
        if (type(ts) is str) and (len(ts)==15): # string of format YYYYMMDD_HHMMSS
            self.ts = datetime.datetime(year=int(ts[:4]), month=int(ts[4:6]), day=int(ts[6:8]), hour=int(ts[9:11]), minute=int(ts[11:13]), second=int(ts[13:15]))
        elif type(ts) is str: # YYYY-MM-DD HH:MM:SS HDF5 version
            self.ts = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        elif type(ts) is datetime.datetime:
            self.ts = ts
        else:
            self.ts = None

    def setHBAelements(self, hbaConfig=None):
        """
        hbaConfig: string (4 x NANTS) or list (length NANTS)

        HBA element string: four hex characters per element x number of elements.
        384 characters for a standard 96 tile international HBA station.
        
        Tile numbering order is based on RCU to tile mapping specific to a station.
        
        Element numbering starts from the top left of the tile when viewed from
        above the tile and with the cable output to the bottom.
        
        This is used for putting the HBA tiles in special modes, such as 'all-sky'
        imaging mode where only a single element is enables per tile. Enabled means
        the element is set to 128 in the rspctl --hbadelays=... command. Disabled
        means the element was set to 2.

        Each character represents a row in the tile, 4 rows per tile. 

        Example: 

            setHBAelements(hbaStr=86f1...)

            x 0 0 0 -> b1000 -> 8
            0 x x 0 -> b0110 -> 6
            x x x x -> b1111 -> f
            0 0 0 x -> b0001 -> 1
            --> tile string: 86f1

            rspctl --hbadelays=128,2,2,2,2,128,128,2,128,128,128,128,2,2,2,128
        """
        if (hbaConfig is None) or np.isnan(hbaConfig):
            self.hbaElements = None
        elif type(hbaConfig) is list:
            self.hbaElements = hbaConfig
        else:
            self.hbaElements = [hbaConfig[i:i+4] for i in range(0, len(hbaConfig), 4)]

    def setSpecial(self, specialStr=None):
        #if type(specialStr) is str: self.special = specialStr
        ##elif type(specialStr) is unicode: self.special = str(specialStr) # JSON version # in py3 str==unicode
        #elif specialStr is None: self.special = specialStr
        #elif np.isnan(specialStr): self.special = None # HDF5 version

        if specialStr is None: self.special = specialStr
        elif isinstance(specialStr, float): self.special = None # HDF5 version, np.nan
        else: self.special = specialStr

    def setRawFile(self, rawfile=None):
        #if type(rawfile) is str: self.rawfile = rawfile
        ##elif type(rawfile) is unicode: self.rawfile = str(rawfile) # JSON version # in py3 str==unicode
        #elif rawfile is None: self.rawfile = rawfile
        #elif np.isnan(rawfile): self.rawfile = None # HDF5 version

        if rawfile is None: self.rawfile = rawfile
        elif isinstance(rawfile, float): self.rawfile = None # HDF5 version, np.nan
        else: # assume rawfile is a string
            self._pathrawfile = rawfile # raw file with path used when calling writeHDF5()
            self.rawfile = os.path.basename(rawfile) # file with no path

    def setIntegration(self, integration=None):
        if integration is None:
            self.integration = None
        elif np.isnan(integration):
            self.integration = None # HDF5 version
        else: # integration in seconds
            self.integration = int(integration)

    def setArrayProp(self, nants, npol):
        # TODO: this information could be extracted based on the station ID
        self.nants = nants
        self.npol = npol

    def printMeta(self):
        print('\n', type(self).__name__)
        print('STATION:', self.station)
        print('RCUMode:', self.rcumode)
        print('TIMESTAMP:', self.ts)
        print('HBA ELEMENTS:', self.hbaElements)
        print('SPECIAL:', self.special)
        print('RAWFILE:', self.rawfile)

    def _buildDict(self):
        self.metaDict = {
            'datatype' : type(self).__name__,
            'station' : self.station,
            'rcumode' : self.rcumode,
            'timestamp' : str(self.ts),
            'hbaelements' : self.hbaElements,
            'special' : self.special,
            'rawfile' : self.rawfile,
            'integration' : self.integration
        }

    def writeJSON(self, filename, printonly=False):
        """
        filename: filename to write JSON stream to
        printonly: boolean, if true only print the output dictionary and do not write to file
        """
        self._buildDict()
        if printonly:
            print(json.dumps(self.metaDict, sort_keys=True, indent=4))
        else:
            with open(filename, 'w') as fp:
                json.dump(self.metaDict, fp, sort_keys=True, indent=4)

class ACC(statData):
    """ ACC cross-correlation class

    Attributes:
        integration: seconds, default: 1
        nants: int, number of antennas in the array, default: 96
        npol: int, number of polarizations, default: 2
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=1, nants=96, npol=2):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setIntegration(integration)
        self.setArrayProp(nants, npol)

    def printMeta(self):
        super(ACC, self).printMeta()
        print('INTEGRATION:', self.integration)
        print('NANTS: %i NPOL: %i'%(self.nants, self.npol))

    def _buildDict(self):
        super(ACC, self)._buildDict()

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if not H5SUPPORT:
            print('ERROR: HDF5 is not supported, you need to install h5py')
            return 0

        if self.rawfile is None:
            print('WARNING: rawfile not set, writing HDF5 file with an empty dataset')
            dd = np.zeros((1, 1, 1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = acc2npy(self._pathrawfile, nant=self.nants, npol=self.npol)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "subband"
        dset.dims[2].label = "antpol1"
        dset.dims[3].label = "antpol2"

        #for key, val in self.metaDict.iteritems(): #py2 only
        for key, val in self.metaDict.items():
            if val is None: dset.attrs[key] = np.nan
            else: dset.attrs[key] = val

        dset[:] = dd[:]

        h5.close()

        print('HDF5: written to', filename)

class BST(statData):
    """ BST beamlet statistics class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=1, pol=None, bitmode=8):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setIntegration(integration)
        self.setBitmode(bitmode)
        self.setPol(pol)
        self.beamlets = {}

    def setBitmode(self, bitmode=None):
        if bitmode is None:
            self.bitmode = None
        else: # bit mode 16, 8, or 4 bits
            self.bitmode = int(bitmode)

    def setPol(self, pol=None):
        self.pol = pol

    def setBeamlet(self, bid, theta, phi, coord, sb, rcus=None):
        """
        bid: beamlet ID (int)
        (theta, phi, coord): pointing in given coordinate system (float, float, str)
        sb: subband ID (int)
        rcus: RCUs in the beamlet (list of ints)
        """
        # HDF5 version type checks
        if type(theta)==np.float64: theta = float(theta)
        if type(phi)==np.float64: phi = float(phi)
        if type(sb)==np.int64: sb = int(sb)

        if rcus is None: rcus = 'all'
        elif isinstance(rcus, float): rcus = 'all' # HDF5 version, np.nan
        else: rcus = rcus

        if type(coord) is str:
            if not(coord.upper() in COORD_SYSTEMS): print('WARNING: coordinate system %s not in defined list of coordinate systems:'%(coord), COORD_SYSTEMS)
            coord = coord.upper()


        self.beamlets[bid] = {
            'theta' : theta,
            'phi' : phi,
            'coord' : coord,
            'sb' : sb,
            'rcus' : rcus
        }

    def printMeta(self):
        super(BST, self).printMeta()
        print('INTEGRATION:', self.integration)
        print('BITMODE:', self.bitmode)
        print('POL:', self.pol)
        print('NBEAMLETS:', len(self.beamlets))
        #for key, val in self.beamlets.iteritems(): #py2 only
        for key, val in self.beamlets.items():
            print('BEAMLET%i'%key, val)

    def _buildDict(self):
        super(BST, self)._buildDict()
        self.metaDict['bitmode'] = self.bitmode
        self.metaDict['beamlets'] = self.beamlets
        self.metaDict['pol'] = self.pol

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if not H5SUPPORT:
            print('ERROR: HDF5 is not supported, you need to install h5py')
            return 0

        if self.rawfile is None:
            print('WARNING: rawfile not set, writing HDF5 file with an empty dataset')
            dd = np.zeros((1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = bst2npy(self._pathrawfile, bitmode=self.bitmode)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "beamlet"

        #for key, val in self.metaDict.iteritems(): # py2 only
        for key, val in self.metaDict.items():
            if val is None: dset.attrs[key] = np.nan
            elif key.startswith('beamlets'): # the beamlet dicts need to be unwound to store as HDF5 attributes
                #for bkey, bval in val.iteritems(): # py2 only
                for bkey, bval in val.items():
                    # ex. bkey: 0 bval: {'rcus': None, 'theta': 0.0, 'phi': 0.0, 'coord': 'AZELGEO', 'sb': 180}
                    dset.attrs['beamlet%03i_theta'%bkey] = bval['theta']
                    dset.attrs['beamlet%03i_phi'%bkey] = bval['phi']
                    dset.attrs['beamlet%03i_coord'%bkey] = bval['coord']
                    dset.attrs['beamlet%03i_sb'%bkey] = bval['sb']
                    if bval['rcus'] is None: dset.attrs['beamlet%03i_rcus'%bkey] = np.nan # None is the default for all RCUs
                    else: dset.attrs['beamlet%03i_rcus'%bkey] = bval['rcus']
            else: dset.attrs[key] = val

        dset[:] = dd[:]

        h5.close()

        print('HDF5: written to', filename)

class SST(statData):
    """ SST subband statistics class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=1, rcu=None):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setIntegration(integration)
        self.setRCU(rcu)

    def setRCU(self, rcu=None):
        if rcu is None:
            self.rcu = None
        elif type(rcu) is np.int64: # HDF5 version
            self.rcu = int(rcu)
        else: # RCU ID
            self.rcu = int(rcu)

    def printMeta(self):
        super(SST, self).printMeta()
        print('RCU:', self.rcu)

    def _buildDict(self):
        super(SST, self)._buildDict()
        self.metaDict['rcu'] = self.rcu

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if not H5SUPPORT:
            print('ERROR: HDF5 is not supported, you need to install h5py')
            return 0

        if self.rawfile is None:
            print('WARNING: rawfile not set, writing HDF5 file with an empty dataset')
            dd = np.zeros((1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = sst2npy(self._pathrawfile)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "subband"

        #for key, val in self.metaDict.iteritems(): # py2 only
        for key, val in self.metaDict.items():
            if val is None: dset.attrs[key] = np.nan
            else: dset.attrs[key] = val

        dset[:] = dd[:]

        h5.close()

        print('HDF5: written to', filename)

class XST(statData):
    """ XST cross-correlation class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=None, sb=None, nants=96, npol=2):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setIntegration(integration)
        self.setSubband(sb)
        self.setArrayProp(nants, npol)

    def setSubband(self, sb=None):
        if sb is None:
            self.sb = None
        else: # subband ID
            self.sb = int(sb)

    def printMeta(self):
        super(XST, self).printMeta()
        print('INTEGRATION:', self.integration)
        print('SUBBAND:', self.sb)
        print('NANTS: %i NPOL: %i'%(self.nants, self.npol))

    def _buildDict(self):
        super(XST, self)._buildDict()
        self.metaDict['subband'] = self.sb

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if not H5SUPPORT:
            print('ERROR: HDF5 is not supported, you need to install h5py')
            return 0

        if self.rawfile is None:
            print('WARNING: rawfile not set, writing HDF5 file with an empty dataset')
            dd = np.zeros((1, 1, 1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = xst2npy(self._pathrawfile, nant=self.nants, npol=self.npol)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "subband"
        dset.dims[2].label = "antpol1"
        dset.dims[3].label = "antpol2"

        #for key, val in self.metaDict.iteritems(): # py2 only
        for key, val in self.metaDict.items():
            if val is None: dset.attrs[key] = np.nan
            else: dset.attrs[key] = val

        dset[:] = dd[:]

        h5.close()

        print('HDF5: written to', filename)

def printHBAtile(hbaStr):
    """Print active HBA tile elements based on hex string
    """
    print('________\n')
    for row in range(4):
        print('%s {0:4b} |'.format(int(hbaStr[row],16))%(hbaStr[row]))
    print('________')

def readJSON(filename):
    """Read a JSON-formatted metadata file

    filename: str, filename path

    returns: statData class instance
    """
    with open(filename, 'r') as fp:
        metaDict = json.load(fp)

    if metaDict['datatype'] == 'ACC':
        s = ACC()
    if metaDict['datatype'] == 'BST':
        s = BST()
        s.setBitmode(metaDict['bitmode'])
        s.setPol(metaDict['pol'])
        #for key, val in metaDict['beamlets'].iteritems(): # py2 only
        for key, val in metaDict['beamlets'].items():
            s.setBeamlet(int(key), val['theta'], val['phi'], str(val['coord']), val['sb'], val['rcus'])
    if metaDict['datatype'] == 'SST':
        s = SST()
        s.setRCU(metaDict['rcu'])
    if metaDict['datatype'] == 'XST':
        s = XST()
        s.setSubband(metaDict['subband'])
    
    s.setIntegration(metaDict['integration'])
    s.setStation(metaDict['station'])
    s.setRCUmode(metaDict['rcumode'])
    s.setTimestamp(datetime.datetime.strptime(metaDict['timestamp'], '%Y-%m-%d %H:%M:%S'))
    s.setHBAelements(metaDict['hbaelements'])
    s.setSpecial(metaDict['special'])

    s.setRawFile(metaDict['rawfile'])

    return s

def readHDF5(filename, getdata=False):
    """Read an HDF5 file and return a class instance of the meta data and the raw data (optional)
    filename: str, path to HDF5
    getdata: boolean, if true return the raw data as a numpy array also

    returns: statData instance, numpy array (optional)
    """
    
    if not H5SUPPORT:
        print('ERROR: HDF5 is not supported, you need to install h5py')
        return 0

    h5 = h5py.File(filename, 'r')
    
    if h5.attrs['CLASS']=='ACC':
        s = ACC(station = h5['data'].attrs['station'],
                rcumode = h5['data'].attrs['rcumode'],
                ts = h5['data'].attrs['timestamp'],
                hbaStr = h5['data'].attrs['hbaelements'],
                special = h5['data'].attrs['special'],
                rawfile = h5['data'].attrs['rawfile'],
                integration = h5['data'].attrs['integration'])

    elif h5.attrs['CLASS']=='BST':
        s = BST(station = h5['data'].attrs['station'],
                rcumode = h5['data'].attrs['rcumode'],
                ts = h5['data'].attrs['timestamp'],
                hbaStr = h5['data'].attrs['hbaelements'],
                special = h5['data'].attrs['special'],
                rawfile = h5['data'].attrs['rawfile'],
                integration = h5['data'].attrs['integration'],
                pol = h5['data'].attrs['pol'],
                bitmode = h5['data'].attrs['bitmode'])

        # Find all the beamlets
        #for bkey in h5['data'].attrs.iterkeys(): # py2 only
        for bkey in h5['data'].attrs.keys():
            if bkey.endswith('_coord'): # a beamlet
                bid = int(bkey[7:10])
                s.setBeamlet(bid, theta = h5['data'].attrs['beamlet%03i_theta'%bid],
                                  phi = h5['data'].attrs['beamlet%03i_phi'%bid],
                                  coord = h5['data'].attrs['beamlet%03i_coord'%bid],
                                  sb = h5['data'].attrs['beamlet%03i_sb'%bid],
                                  rcus=h5['data'].attrs['beamlet%03i_rcus'%bid])

    elif h5.attrs['CLASS']=='SST':
        s = SST(station = h5['data'].attrs['station'],
                rcumode = h5['data'].attrs['rcumode'],
                ts = h5['data'].attrs['timestamp'],
                hbaStr = h5['data'].attrs['hbaelements'],
                special = h5['data'].attrs['special'],
                rawfile = h5['data'].attrs['rawfile'],
                rcu = h5['data'].attrs['rcu'])

    elif h5.attrs['CLASS']=='XST':
        s = XST(station = h5['data'].attrs['station'],
                rcumode = h5['data'].attrs['rcumode'],
                ts = h5['data'].attrs['timestamp'],
                hbaStr = h5['data'].attrs['hbaelements'],
                special = h5['data'].attrs['special'],
                rawfile = h5['data'].attrs['rawfile'],
                integration = h5['data'].attrs['integration'],
                sb = h5['data'].attrs['subband'])
    else:
        print('ERROR: unknown class type')
        return 0
    
    if getdata: dd = np.array(h5['data'])

    h5.close

    if getdata: return s, dd
    else: return s

def read(filename, getdata=False):
    """Wrapper function for readJSON() and readHDF5(), selects based on file extension (.json or .h5)

    getdata: boolean, if true return the raw data as a numpy array also for HDF5
    """
    if filename.endswith('.json'): return readJSON(filename)
    elif filename.endswith('.h5'): return readHDF5(filename, getdata=False)
    else:
        print('ERROR: file extension not understood, only .json and .h5 file types work with this function.')

def acc2npy(filename, nant=96, npol=2):
    """Read an ACC file and return a numpy array
    filename: str, path to binary data file
    nant: int, number of antennas/tiles in the array, 96 for an international station, 48 for KAIRA
    npol: int, number of polarizations, typically 2

    returns: (nints, nsb, nant*npol, nant*npol) complex array
    """
    nantpol = nant * npol
    nsb = 512 # ACC have 512 subbands
    nints = 1 # ACC only have a single integration
    corrMatrix = np.fromfile(filename, dtype='complex') # read in the correlation matrix
    return np.reshape(corrMatrix, (nints, nsb, nantpol, nantpol))

def npy2acc(dd, filename):
    """Write a correlation matrix numpy array to a binary raw file
    dd: complex numpy array, correlation matrix of shape (1, 512, nantpol, nantpol)
    filename: str, path to binary data file
    """
    fh = open(filename, 'wb')
    dd.astype('complex').tofile(fh)
    fh.close()

def bst2npy(filename, bitmode=8):
    """Read an BST file and return a numpy array
    filename: str, path to binary data file
    bitmode: int, 16 produces 244 beamlets, 8 produces 488 beamlets, 4 produces 976 beamlets

    returns: (nints, nbeamlets) float array
    """
    if bitmode==16: nbeamlets = 244
    elif bitmode==8: nbeamlets = 488
    elif bitmode==4: nbeamlets = 976
    else:
        print('WARNING: bit-mode %i not standard, only (16, 8, 4) in use, defaulting to 8 bit.')
        nbeamlets = 488
    d = np.fromfile(filename, dtype='float')
    nints = d.shape[0] / nbeamlets
    return np.reshape(d, (nints, nbeamlets))

def npy2bst(dd, filename):
    """Write a BST numpy array to a binary raw file
    dd: float numpy array of shape (nints, nbeamlets)
    filename: str, path to binary data file
    """
    fh = open(filename, 'wb')
    dd.astype('float').tofile(fh)
    fh.close()

def sst2npy(filename):
    """Read an SST file and return a numpy array
    filename: str, path to binary data file

    returns (nints, 512) float array
    """
    nsb = 512 # SST have 512 subbands
    d = np.fromfile(filename, dtype='float')
    nints = d.shape[0] / 512
    return np.reshape(d, (nints, nsb))

def npy2sst(dd, filename):
    """Write a SST numpy array to a binary raw file
    dd: float numpy array of shape (nints, 512)
    filename: str, path to binary data file
    """
    fh = open(filename, 'wb')
    dd.astype('float').tofile(fh)
    fh.close()

def xst2npy(filename, nant=96, npol=2):
    """Read an XST file and return a numpy array
    filename: str, path to binary data file
    nant: int, number of antennas/tiles in the array, 96 for an international station, 48 for KAIRA
    npol: int, number of polarizations, typically 2

    returns: (nints, nsb, nant*npol, nant*npol) complex array
    """
    nantpol = nant * npol
    nsb = 1 # XST only have a single subband
    corrMatrix = np.fromfile(filename, dtype='complex') # read in the correlation matrix
    nints = corrMatrix.shape[0]/(nantpol * nantpol) # number of integrations
    return np.reshape(corrMatrix, (nints, nsb, nantpol, nantpol))

def npy2xst(dd, filename):
    """Write a correlation matrix numpy array to a binary raw file
    dd: complex numpy array, correlation matrix of shape (nints, 1, nantpol, nantpol)
    filename: str, path to binary data file
    """
    fh = open(filename, 'wb')
    dd.astype('complex').tofile(fh)
    fh.close()


if __name__ == '__main__':

    # TEST BENCHES

    import os

    TESTDATADIR = 'test_data'
    
    print('h5 support:', H5SUPPORT)
    
    printHBAtile('fcff')

    # 20120611_124534_acc_512x192x192.dat
    acc = ACC(station='UK608', rcumode=3, ts='20120611_124534', rawfile='20120611_124534_acc_512x192x192.dat')
    acc.setRawFile(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.dat'))
    acc.printMeta()

    acc.writeJSON(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.json'))

    acc0 = readJSON(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.json'))
    acc0.printMeta()

    accData = acc2npy(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.dat'))
    print('ACC DATA SHAPE:', accData.shape)

    if H5SUPPORT:
        acc.writeHDF5(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.h5'))

        acc1, acc1Data = readHDF5(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.h5'), getdata=True)
        acc1.printMeta()
        print(acc1Data.shape)
    
    npy2acc(accData, 'temp_acc.dat')

    # 20170217_111340_bst_00X.dat
    bst = BST(station='KAIRA', rcumode=3, ts='20170217_111340', pol='X')
    bst.setBeamlet(0, 0., 0., 'AZELGEO', 180)
    bst.setBeamlet(1, 0., 0., 'AZELGEO', 180)
    bst.setBeamlet(2, 0., 0., 'AZELGEO', 180)
    bst.printMeta()
    bst.writeJSON(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.json'))

    bst0 = readJSON(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.json'))
    bst0.printMeta()

    bstData = bst2npy(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.dat'))
    print('BST DATA SHAPE:', bstData.shape)

    bst.setRawFile(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.dat'))

    if H5SUPPORT:
        bst.writeHDF5(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.h5'))

        bst1, bst1Data = readHDF5(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.h5'), getdata=True)
        bst1.printMeta()
        print(bst1Data.shape)

    # 20140430_153356_sst_rcu024.dat
    sst = SST(station='KAIRA', rcumode=3, ts='20140430_153356', rcu=24) 
    sst.printMeta()
    sst.writeJSON(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.json'))

    sst0 = readJSON(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.json'))
    sst0.printMeta()

    sstData = sst2npy(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.dat'))
    print('SST DATA SHAPE:', sstData.shape)

    sst.setRawFile(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.dat'))

    if H5SUPPORT:
        sst.writeHDF5(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.h5'))

        sst1, sst1Data = readHDF5(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.h5'), getdata=True)
        sst1.printMeta()
        print(sst1Data.shape)

    # 20170728_184348_sb180_xst.dat
    xst = XST(station='IE613', rcumode=3, ts='20170728_184348', sb=180)
    xst.printMeta()
    xst.writeJSON(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.json'))

    xst0 = readJSON(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.json'))
    xst0.printMeta()

    xstData = xst2npy(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.dat'))
    print('XST DATA SHAPE:', xstData.shape)

    xst.setRawFile(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.dat'))

    if H5SUPPORT:
        xst.writeHDF5(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.h5'))

        xst1, xst1Data = readHDF5(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.h5'), getdata=True)
        xst1.printMeta()
        print(xst1Data.shape)

