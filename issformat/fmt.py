"""
Wrapper classes for LOFAR staion ACC, XST, SST, BST files

HDF5 wrapper support is optional
"""

import datetime
import json
import numpy as np

try:
    import h5py
    H5SUPPORT = True
except ImportError:
    H5SUPPORT = False

# TODO: function:
#   readHDF5()
#   standard modes function, e.g. all beamlets in one pointing with different subbands
# TODO: scripts
#   generate meta file from input
#   convert raw file and input to hdf5
#   convert raw and json meta file to hdf5
#   convert hdf5 to raw and json meta file
# TODO: unittests
# TODO: python2 and 3 compatible
# TODO: setup.py, layout, pip
# TODO: definition document

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
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None):
        
        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)

    def setStation(self, station=None):
        self.station = station # Station ID string

    def setRCUmode(self, rcumode=None):
        if rcumode is None:
            self.rcumode = None
        elif type(rcumode) is int:
            self.rcumode = rcumode
        elif len(rcumode) == 1: # single RCUMODE (int), all RCUs are the same mode
            self.rcumode = int(rcumode)
        else: # Mixed RCU mode (list of length the number of RCUs)
            self.rcumode = map(int, rcumode)

    def setTimestamp(self, ts=None):
        if type(ts) is str: # string of format YYYYMMDD_HHMMSS
            self.ts = datetime.datetime(year=int(ts[:4]), month=int(ts[4:6]), day=int(ts[6:8]), hour=int(ts[9:11]), minute=int(ts[11:13]), second=int(ts[13:15]))
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
        if hbaConfig is None:
            self.hbaElements = None
        elif type(hbaConfig) is list:
            self.hbaElements = hbaConfig
        else:
            self.hbaElements = [hbaConfig[i:i+4] for i in range(0, len(hbaConfig), 4)]

    def setSpecial(self, specialStr=None):
        self.special = specialStr

    def setRawFile(self, rawfile=None):
        self.rawfile = rawfile

    def setArrayProp(self, nants, npol):
        # TODO: this information could be extracted based on the station ID
        self.nants = nants
        self.npol = npol

    def printMeta(self):
        print '\n', type(self).__name__
        print 'STATION:', self.station
        print 'RCUMode:', self.rcumode
        print 'TIMESTAMP:', self.ts
        print 'HBA ELEMENTS:', self.hbaElements
        print 'SPECIAL:', self.special
        print 'RAWFILE:', self.rawfile

    def _buildDict(self):
        self.metaDict = {
            'datatype' : type(self).__name__,
            'station' : self.station,
            'rcumode' : self.rcumode,
            'timestamp' : str(self.ts),
            'hbaelements' : self.hbaElements,
            'special' : self.special,
            'rawfile' : self.rawfile
        }

    def writeJSON(self, filename, printonly=False):
        """
        filename: filename to write JSON stream to
        printonly: boolean, if true only print the output dictionary and do not write to file
        """
        self._buildDict()
        if printonly:
            print json.dumps(self.metaDict, sort_keys=True, indent=4)
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

    def setIntegration(self, integration=None):
        if integration is None:
            self.integration = None
        else: # integration in seconds
            self.integration = int(integration)

    def printMeta(self):
        super(ACC, self).printMeta()
        print 'INTEGRATION:', self.integration

    def _buildDict(self):
        super(ACC, self)._buildDict()
        self.metaDict['integration'] = self.integration

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if self.rawfile is None:
            print 'WARNING: rawfile not set, writing HDF5 file with an empty dataset'
            dd = np.zeros((1, 1, 1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = acc2npy(self.rawfile, nant=self.nants, npol=self.npol)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "subband"
        dset.dims[2].label = "antpol1"
        dset.dims[3].label = "antpol2"

        for key, val in self.metaDict.iteritems():
            if val is None: dset.attrs[key] = np.nan
            else: dset.attrs[key] = val

        dset[:] = dd[:]

        h5.close()

        print 'HDF5: written to', filename

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

    def setIntegration(self, integration=None):
        if integration is None:
            self.integration = None
        else: # integration in seconds
            self.integration = int(integration)

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
        if type(coord) is str:
            if not(coord.upper() in COORD_SYSTEMS): print 'WARNING: coordinate system %s not in defined list of coordinate systems:'%(coord), COORD_SYSTEMS
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
        print 'INTEGRATION:', self.integration
        print 'BITMODE:', self.bitmode
        print 'NBEAMLETS:', len(self.beamlets)
        for key, val in self.beamlets.iteritems():
            print 'BEAMLET%i'%key, val

    def _buildDict(self):
        super(BST, self)._buildDict()
        self.metaDict['integration'] = self.integration
        self.metaDict['bitmode'] = self.bitmode
        self.metaDict['beamlets'] = self.beamlets
        self.metaDict['pol'] = self.pol

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if self.rawfile is None:
            print 'WARNING: rawfile not set, writing HDF5 file with an empty dataset'
            dd = np.zeros((1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = bst2npy(self.rawfile, bitmode=self.bitmode)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "beamlet"

        for key, val in self.metaDict.iteritems():
            print key, val
            if val is None: dset.attrs[key] = np.nan
            elif key.startswith('beamlets'): # the beamlet dicts need to be unwound to store as HDF5 attributes
                for bkey, bval in val.iteritems():
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

        print 'HDF5: written to', filename

class SST(statData):
    """ SST subband statistics class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, rcu=None):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setRCU(rcu)

    def setRCU(self, rcu=None):
        if rcu is None:
            self.rcu = None
        else: # RCU ID
            self.rcu = int(rcu)

    def printMeta(self):
        super(SST, self).printMeta()
        print 'RCU:', self.rcu

    def _buildDict(self):
        super(SST, self)._buildDict()
        self.metaDict['rcu'] = self.rcu

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if self.rawfile is None:
            print 'WARNING: rawfile not set, writing HDF5 file with an empty dataset'
            dd = np.zeros((1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = sst2npy(self.rawfile)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "subband"

        for key, val in self.metaDict.iteritems():
            if val is None: dset.attrs[key] = np.nan
            else: dset.attrs[key] = val

        dset[:] = dd[:]

        h5.close()

        print 'HDF5: written to', filename

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

    def setIntegration(self, integration=None):
        if integration is None:
            self.integration = None
        else: # integration in seconds
            self.integration = int(integration)

    def setSubband(self, sb=None):
        if sb is None:
            self.sb = None
        else: # subband ID
            self.sb = int(sb)

    def printMeta(self):
        super(XST, self).printMeta()
        print 'INTEGRATION:', self.integration
        print 'SUBBAND:', self.sb

    def _buildDict(self):
        super(XST, self)._buildDict()
        self.metaDict['integration'] = self.integration
        self.metaDict['subband'] = self.sb

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        filename: str, output HDF5 filename
        """

        if self.rawfile is None:
            print 'WARNING: rawfile not set, writing HDF5 file with an empty dataset'
            dd = np.zeros((1, 1, 1, 1)) # place holder TODO: there is probably a better thing to do here
        else:
            dd = xst2npy(self.rawfile, nant=self.nants, npol=self.npol)

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__
        
        dset = h5.create_dataset('data',
                          shape = dd.shape,
                          dtype = dd.dtype)

        dset.dims[0].label = "time"
        dset.dims[1].label = "subband"
        dset.dims[2].label = "antpol1"
        dset.dims[3].label = "antpol2"

        for key, val in self.metaDict.iteritems():
            if val is None: dset.attrs[key] = np.nan
            else: dset.attrs[key] = val

        dset[:] = dd[:]

        h5.close()

        print 'HDF5: written to', filename

def printHBAtile(hbaStr):
    """Print active HBA tile elements based on hex string
    """
    print '________\n'
    for row in range(4):
        print '%s {0:4b} |'.format(int(hbaStr[row],16))%(hbaStr[row])
    print '________'

def readJSON(filename):
    """Read a JSON-formatted metadata file

    filename: str, filename path

    returns: statData class instance
    """
    with open(filename, 'r') as fp:
        metaDict = json.load(fp)

    if metaDict['datatype'] == 'ACC':
        s = ACC()
        s.setIntegration(metaDict['integration'])
    if metaDict['datatype'] == 'BST':
        s = BST()
        s.setIntegration(metaDict['integration'])
        s.setBitmode(metaDict['bitmode'])
        s.setPol(metaDict['pol'])
        for key, val in metaDict['beamlets'].iteritems():
            s.setBeamlet(int(key), val['theta'], val['phi'], str(val['coord']), val['sb'], val['rcus'])
    if metaDict['datatype'] == 'SST':
        s = SST()
        s.setRCU(metaDict['rcu'])
    if metaDict['datatype'] == 'XST':
        s = XST()
        s.setIntegration(metaDict['integration'])
        s.setSubband(metaDict['subband'])
    
    s.setStation(metaDict['station'])
    s.setRCUmode(metaDict['rcumode'])
    s.setTimestamp(datetime.datetime.strptime(metaDict['timestamp'], '%Y-%m-%d %H:%M:%S'))
    s.setHBAelements(metaDict['hbaelements'])
    s.setSpecial(metaDict['special'])
    s.setRawFile(metaDict['rawfile'])

    return s

def readHDF5(filename):
    pass

def read(filename):
    """Wrapper function for readJSON() and readHDF5(), selects based on file extension (.json or .h5)
    """
    if filename.endswith('.json'): return readJSON(filename)
    elif filename.endswith('.h5'): return readHDF5(filename)
    else:
        print 'ERROR: file extension not understood, only .json and .h5 file types work with this function.'

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
        print 'WARNING: bit-mode %i not standard, only (16, 8, 4) in use, defaulting to 8 bit.'
        nbeamlets = 488
    d = np.fromfile(filename, dtype='float')
    nints = d.shape[0] / nbeamlets
    return np.reshape(d, (nints, nbeamlets))

def sst2npy(filename):
    """Read an SST file and return a numpy array
    filename: str, path to binary data file

    returns (nints, 512) float array
    """
    nsb = 512 # SST have 512 subbands
    d = np.fromfile(filename, dtype='float')
    nints = d.shape[0] / 512
    return np.reshape(d, (nints, nsb))

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

if __name__ == '__main__':

    import os

    TESTDATADIR = '../test_data'
    
    print 'h5 support:', H5SUPPORT
    
    printHBAtile('fcff')

    # 20120611_124534_acc_512x192x192.dat
    acc = ACC(station='UK608', rcumode=3, ts='20120611_124534')
    acc.printMeta()
    acc.writeJSON(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.json'))

    acc0 = readJSON(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.json'))
    acc0.printMeta()

    accData = acc2npy(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.dat'))
    print 'ACC DATA SHAPE:', accData.shape

    acc.setRawFile(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.dat'))
    acc.writeHDF5(os.path.join(TESTDATADIR, '20120611_124534_acc_512x192x192.h5'))

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
    print 'BST DATA SHAPE:', bstData.shape

    bst.setRawFile(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.dat'))
    bst.writeHDF5(os.path.join(TESTDATADIR, '20170217_111340_bst_00X.h5'))

    # 20140430_153356_sst_rcu024.dat
    sst = SST(station='KAIRA', rcumode=3, ts='20140430_153356', rcu=24) 
    sst.printMeta()
    sst.writeJSON(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.json'))

    sst0 = readJSON(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.json'))
    sst0.printMeta()

    sstData = sst2npy(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.dat'))
    print 'SST DATA SHAPE:', sstData.shape

    sst.setRawFile(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.dat'))
    sst.writeHDF5(os.path.join(TESTDATADIR, '20140430_153356_sst_rcu024.h5'))

    # 20170728_184348_sb180_xst.dat
    xst = XST(station='IE613', rcumode=3, ts='20170728_184348', sb=180)
    xst.printMeta()
    xst.writeJSON(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.json'))

    xst0 = readJSON(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.json'))
    xst0.printMeta()

    xstData = xst2npy(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.dat'))
    print 'XST DATA SHAPE:', xstData.shape

    xst.setRawFile(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.dat'))
    xst.writeHDF5(os.path.join(TESTDATADIR, '20170728_184348_sb180_xst.h5'))

