"""
Wrapper classes for LOFAR staion ACC, XST, SST, BST files

HDF5 wrapper support is optional
"""

import datetime
import json

try:
    import h5py
    H5SUPPORT = True
except ImportError:
    H5SUPPORT = False

# TODO: function:
#   writeHDF5()
#   readHDF5()
#	binary reader functions
# TODO: scripts
#   generate meta file from input
#   convert raw file and input to hdf5
#   convert raw and json meta file to hdf5
#   convert hdf5 to raw and json meta file
# TODO: unittests
# TODO: python2 and 3 compatible
# TODO: setup.py, layout, pip
# TODO: definition document

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

    def setHBAelements(self, hbaStr=None):
        # TODO: define tile counting order
        # TODO: define element counting order
        """HBA element string: four hex characters per element x number of elements

        Each character represents a row in the tile, 4 rows per tile

        Example: 
            x 0 0 0 -> 8
            0 x x 0 -> 6
            x x x x -> f
            0 0 0 x -> 1
            --> tile string: 86f1
        """
        if hbaStr is None:
            self.hbaElements = None
        else:
            self.hbaElements = [hbaStr[i:i+4] for i in range(0, len(hbaStr), 4)]

    def setSpecial(self, specialStr=None):
        self.special = specialStr

    def setRawFile(self, rawfile=None):
        self.rawfile = rawfile

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

    def writeHDF5(self, filename):
        """Write metadata and statistics data to HDF5 file
        """

        h5 = h5py.File(filename, 'w')

        h5.attrs['CLASS'] = type(self).__name__

		#dset = h5.create_dataset('data',
        #                  shape=data_shape,
        #                  dtype=data_dtype)

        #dset.dims[0].label = "frequency"
        #dset.dims[1].label = "feed_id"
        #dset.dims[2].label = "time"

        for key, val in self.metaDict.iteritems():
            dset.attrs[key] = val

class ACC(statData):
    """ ACC cross-correlation class

    Attributes:
        integration: seconds, default: 1
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=1):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setIntegration(integration)

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

class BST(statData):
    """ BST beamlet statistics class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=1, bitmode=None, pol=None):

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
        # TODO: define coordinate systems and pointing units
        """
        bid: beamlet ID (int)
        (theta, phi, coord): pointing in given coordinate system (float, float, str)
        sb: subband ID (int)
        rcus: RCUs in the beamlet (list of ints)
        """
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

class XST(statData):
    """ XST cross-correlation class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, rawfile=None, integration=None, sb=None):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setRawFile(rawfile)
        self.setIntegration(integration)
        self.setSubband(sb)

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

if __name__ == '__main__':

    print 'h5 support:', H5SUPPORT
    
    printHBAtile('fcff')

    # 20120611_124534_acc_512x192x192.dat
    acc = ACC(station='UK608', rcumode=3, ts='20120611_124534')
    acc.printMeta()
    acc.writeJSON('20120611_124534_acc_512x192x192.json')

    acc0 = readJSON('20120611_124534_acc_512x192x192.json')
    acc0.printMeta()

    # 20170217_111340_bst_00X.dat
    bst = BST(station='KAIRA', rcumode=3, ts='20170217_111340', pol='X')
    bst.setBeamlet(0, 0., 0., 'AZEL', 180)
    bst.setBeamlet(1, 0., 0., 'AZEL', 180)
    bst.setBeamlet(2, 0., 0., 'AZEL', 180)
    bst.printMeta()
    bst.writeJSON('20170217_111340_bst_00X.json')

    bst0 = readJSON('20170217_111340_bst_00X.json')
    bst0.printMeta()

    # 20140430_153356_sst_rcu024.dat
    sst = SST(station='KAIRA', rcumode=3, ts='20140430_153356', rcu=24) 
    sst.printMeta()
    sst.writeJSON('20140430_153356_sst_rcu024.json')

    sst0 = readJSON('20140430_153356_sst_rcu024.json')
    sst0.printMeta()

    # 20170728_184348_sb180_xst.dat
    xst = XST(station='IE613', rcumode=3, ts='20170728_184348', sb=180)
    xst.printMeta()
    xst.writeJSON('20170728_184348_sb180_xst.json')

    xst0 = readJSON('20170728_184348_sb180_xst.json')
    xst0.printMeta()

