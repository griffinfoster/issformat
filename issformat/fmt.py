"""
Wrapper classes for LOFAR staion ACC, XST, SST, BST files

HDF5 wrapper support is optional
"""

import datetime
import json

# TODO: h5py optional
# TODO: python2 and 3 compatible
# TODO: unittests
# TODO: function:
#   writeHDF5()
#   readHDF5()
#   writeJSON()
#   readJSON()
# TODO: scripts
#   generate meta file from input
#   convert raw file and input to hdf5
#   convert raw and json meta file to hdf5
#   convert hdf5 to raw and json meta file

class statData(object):
    """ Statistics file super class all other classes inherit from

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None):
        
        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)

    def setStation(self, station=None):
        self.station = station # Station ID string

    def setRCUmode(self, rcumode=None):
        if rcumode is None:
            self.rcumode = None
        elif len(rcumode) == 1: # single RCUMODE (int), all RCUs are the same mode
            self.rcumode = int(rcumode)
        else: # Mixed RCU mode (list of length the number of RCUs)
            self.rcumode = map(int, rcumode)

    def setTimestamp(self, ts=None):
        if type(ts) is str: # string of format YYYYMMDD_HHMMSS
            self.ts = datetime.datetime(year=int(ts[:4]), month=int(ts[4:6]), day=int(ts[6:8]), hour=int(ts[9:11]), minute=int(ts[11:13]), second=int(ts[13:15]))
        elif type(ts) is datetime.datetime:
            selfts. ts
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

    #######

    def writeHDF5(self, filename=None):
        pass

    def readHDF5(self, filename):
        pass

    def writeJSON(self, filename=None):
        pass

    def readJSON(self, filename):
        pass

class ACC(statData):
    """ ACC cross-correlation class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, integration=None):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setIntegration(integration)

    def setIntegration(self, integration=None):
        if integration is None:
            self.integration = None
        else: # integration in seconds
            self.integration = int(integration)

    #######

    def writeHDF5(self, filename=None):
        pass

    def readHDF5(self, filename):
        pass

    def writeJSON(self, filename=None):
        pass

    def readJSON(self, filename):
        pass

class BST(statData):
    """ BST beamlet statistics class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, bitmode=None):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
        self.setBitmode(bitmode)
        self.beamlets = {}

    def setBitmode(self, bitmode=None):
        if bitmode is None:
            self.bitmode = None
        else: # bit mode 16, 8, or 4 bits
            self.bitmode = int(bitmode)

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

    #######

    def writeHDF5(self, filename=None):
        pass

    def readHDF5(self, filename):
        pass

    def writeJSON(self, filename=None):
        pass

    def readJSON(self, filename):
        pass

class SST(statData):
    """ SST subband statistics class

    Attributes:
    """

    #######

    def writeHDF5(self, filename=None):
        pass

    def readHDF5(self, filename):
        pass

    def writeJSON(self, filename=None):
        pass

    def readJSON(self, filename):
        pass

class XST(statData):
    """ XST cross-correlation class

    Attributes:
    """
    def __init__(self, station=None, rcumode=None, ts=None, hbaStr=None, special=None, integration=None, sb=None):

        self.setStation(station)
        self.setRCUmode(rcumode)
        self.setTimestamp(ts)
        self.setHBAelements(hbaStr)
        self.setSpecial(special)
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

    #######

    def writeHDF5(self, filename=None):
        pass

    def readHDF5(self, filename):
        pass

    def writeJSON(self, filename=None):
        pass

    def readJSON(self, filename):
        pass

def printHBAtile(hbaStr):
    """Print active HBA tile elements based on hex string
    """
    print '________\n'
    for row in range(4):
        print '%s {0:4b} |'.format(int(hbaStr[row],16))%(hbaStr[row])
    print '________'

printHBAtile('fcff')

