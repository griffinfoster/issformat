#!/usr/bin/env python
"""
Convert between raw LOFAR single station data and issformat

Can be used to:
* Generate JSON metadata files
* Generate HDF5-wrapped data files
* Extract raw data and JSON metadata from HDF5 files

Input options override JSON/HDF5 input metadata, to override an option to be type None, use 'none' string
"""

# python 2 and 3 support
from __future__ import print_function

import sys,os
import issformat
import pkg_resources  # part of setuptools, for version

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] JSON/HDF5/dat files')
    o.set_description(__doc__)
    o.add_option('-o', '--outputtype', dest='outputType', default=None,
        help = 'Type of file to output, can be multiple with comma separated list: hdf5, json, raw, default: None')
    o.add_option('--obasename', dest='obasename', default=None,
        help = 'Output filename base, e.g. --outputtype=json --obasename=basename will return basename.json. default: if --rawfile is set, use the same file basename, else \'meta\'')
    o.add_option('--print', dest='printMeta', action='store_true',
        help = 'Print metadata')
    o.add_option('--force', dest='force', action='store_true',
        help = 'Force overwriting of an already existing metadata file, otherwise skip')

    o.add_option('--standard', dest='standard', action='store_true',
        help = 'Assume the standard filenaming format for the input rawfile, the timestamp and data class can be determined from this. Additional information RCU (SST), pol (BST), subband (XST) is also extracted. Note: this option overrides an input JSON or HDF5 file. Example standard formats: 20120611_124534_acc_512x192x192.dat (ACC) 20170217_111340_bst_00X.dat (BST) 20140430_153356_sst_rcu024.dat (SST) 20170728_184348_sb180_xst.dat (XST) 20170728_184348_xst.dat (XST)')
    o.add_option('--beamlet', dest='beamlet', default=None,
        help = '(BST) Beamlet file, list of entries: BID THETA PHI COORD SB RCUS, see documentation for details, default: None')
    o.add_option('--bitmode', dest='bitmode', choices=['4','8','16', 'None'], default=None,
        help = '(BST) Beamlet bitmode (4, 8, or 16), default: None')
    o.add_option('--bpol', dest='bpol', default=None,
        help = '(BST) Beamlet polarization, default: None')
    o.add_option('--hba', dest='hbaStr', default=None,
        help = 'HBA active element list, documentation for details, default: None')
    o.add_option('--integration', dest='integration', default=1, type=int,
        help = 'Integration length in seconds, default: 1')
    o.add_option('--nant', dest='nant', default=96, type=int,
        help = 'Number of antennas in the array, default: 96')
    o.add_option('--npol', dest='npol', default=2, type=int,
        help = 'Number of polarizations per element, default: 2')
    o.add_option('--rawfile', dest='rawfile', default=None,
        help = 'Filename of raw data file, default: None')
    o.add_option('--rcu', dest='rcu', default=None,
        help = '(SST) rcu ID, default: None')
    o.add_option('--rcumode', dest='rcumode', default=None,
        help = 'rcumode, can be a single integer (1:7) or a comma separated list of integers for each rcu, default: None')
    o.add_option('--sclass', dest='sclass', default=None,
        help = 'Statistics file class, required for reading in raw data or generating meta data file, ACC, BST, SST, XST, default: None')
    o.add_option('--special', dest='specialStr', default=None,
        help = 'Comment space, default: None')
    o.add_option('--station', dest='station', default=None,
        help = 'Station name, e.g. SE607, default: None')
    o.add_option('--subband', dest='subband', default=None,
        help = '(XST) subband ID, default: None')
    o.add_option('--ts', dest='ts', default=None,
        help = 'Timestamp of format YYYY-MM-DD HH:MM:SS or YYYYMMDD_HHMMSS, default: None')
    o.add_option('-v', '--version', action='store_true',
        help = 'Print version and exit')
    opts, args = o.parse_args(sys.argv[1:])

    if opts.version:
        print('Version', pkg_resources.require('issformat')[0].version)
        exit()

    # Parse output types
    if opts.outputType is None: outputTypes = []
    else: outputTypes = opts.outputType.split(',')
    # Check that outputTypes are valid
    valOutputTypes = ['json', 'hdf5', 'raw']
    for otype in outputTypes:
        if not (otype in valOutputTypes):
            print('WARNING: %s output type unknown, only valid types are:'%otype, valOutputTypes)

    dd = None # extracted data
    s = None # meta data class instance

    # read in inputs
    for fn in args:
        if fn.endswith('.h5'): # HDF5
            if 'raw' in outputTypes: # extract data
                s, dd = issformat.read(fn, getdata=True)
            else:
                s = issformat.read(fn)
        elif fn.endswith('.json'): # JSON
            s = issformat.read(fn)
        elif fn.endswith('.dat'): # raw statistics file
            if opts.sclass is None:
                print('WARNING: --sclass option not set, class unknown, skipping file read')
            else:
                if opts.sclass.upper().startswith('ACC'): dd = issformat.acc2npy(fn, opts.nant, opts.npol) 
                elif opts.sclass.upper().startswith('BST'):
                    if opts.bitmode is None: print('WARNING: --bitmode option not set')
                    dd = issformat.bst2npy(fn, int(opts.bitmode))
                elif opts.sclass.upper().startswith('SST'): dd = issformat.sst2npy(fn) 
                elif opts.sclass.upper().startswith('XST'): dd = issformat.xst2npy(fn, opts.nant, opts.npol) 

    # generate a metadata instance or override metadata
    if (opts.standard):
        if opts.rawfile is None:
            print('WARNING: Using --standard flag but no --rawfile set')
        else:
            # examples:
            # ACC: 20120611_124534_acc_512x192x192.dat
            # BST: 20170217_111340_bst_00X.dat
            # SST: 20140430_153356_sst_rcu024.dat
            # XST: 20170728_184348_sb180_xst.dat
            # XST: 20170728_184348_xst.dat
            rawfile = os.path.basename(opts.rawfile)
            ts = rawfile.split('_')[0] + '_' + rawfile.split('_')[1]

            if '_acc_' in rawfile: # ACC
                nants = int(rawfile.split('x')[1]) / 2
                s = issformat.ACC(ts=ts, rawfile=rawfile, nants=nants, npol=2)
            elif '_bst_' in rawfile: # BST
                pol = rawfile.split('.')[0][-1]
                s = issformat.BST(ts=ts, rawfile=rawfile, pol=pol)
            elif '_sst_' in rawfile: # SST
                rcu = int(rawfile.split('.')[0].split('rcu')[1])
                s = issformat.SST(ts=ts, rawfile=rawfile, rcu=rcu)
            elif '_xst' in rawfile: # XST
                if '_sb' in rawfile: # some stations add in the subband ID
                    sb = int(rawfile.split('_')[2].split('sb')[1])
                    s = issformat.XST(ts=ts, rawfile=rawfile, sb=sb)
                else: s = issformat.XST(ts=ts, rawfile=rawfile) # the default mode is not to include the subband in the filename
            else:
                print('WARNING: unknown file type %s when using --standard flag.'%rawfile)

    if (opts.sclass is None) and (s is None):
        print('ERROR: --sclass is nor defined and there is no input metadata file, can not go on.')
        exit()

    elif not(s is None): # check for any options override
        if not(opts.station is None):
            if opts.station=='none': s.setStation(station=None)
            else: s.setStation(station=opts.station)

        if not(opts.rcumode is None):
            if opts.rcumode=='none': s.setRCUmode(rcumode=None)
            else: s.setRCUmode(rcumode=opts.rcumode)

        if not(opts.ts is None):
            if opts.ts=='none': s.setTimestamp(ts=None)
            else: s.setTimestamp(ts=opts.ts)

        if not(opts.hbaStr is None):
            if opts.hbaStr=='none': s.setHBAelements(hbaConfig=None)
            else: s.setHBAelements(hbaConfig=opts.hbaStr)

        if not(opts.specialStr is None):
            if opts.specialStr=='none': s.setSpecial(specialStr=None)
            else: s.setSpecial(specialStr=opts.specialStr)

        if not(opts.rawfile is None):
            if opts.rawfile=='none': s.setRawFile(rawfile=None)
            else: s.setRawFile(rawfile=opts.rawfile)

        if not(opts.rawfile is None):
            if opts.rawfile=='none': s.setRawFile(rawfile=None)
            else: s.setRawFile(rawfile=opts.rawfile)

        if not(opts.integration is None):
            if opts.integration=='none': s.setIntegration(integration=None)
            else: s.setIntegration(integration=opts.integration)

        if type(s).__name__=='ACC':
            if not(opts.nant is None): s.setArrayProp(nants=opts.nant, npol=opts.npol)

        if type(s).__name__=='BST':
            if not(opts.bpol is None):
                if opts.bpol=='none': s.setPol(pol=None)
                else: s.setPol(pol=opts.bpol)

            if not(opts.bitmode is None):
                if opts.bitmode=='none': s.setBitmode(bitmode=None)
                else: s.setBitmode(bitmode=opts.bitmode)

        if type(s).__name__=='SST':
            if not(opts.rcu is None):
                if opts.rcu=='none': s.setRCU(rcu=None)
                else: s.setRCU(rcu=opts.rcu)

        if type(s).__name__=='XST':
            if not(opts.nant is None): s.setArrayProp(nants=opts.nant, npol=opts.npol)

            if not(opts.subband is None):
                if opts.subband=='none': s.setSubband(sb=None)
                else: s.setSubband(sb=opts.subband)

    else: # generate a new meta data instance
        if opts.sclass.upper().startswith('ACC'):
            s = issformat.ACC(station = opts.station,
                        rcumode = opts.rcumode,
                        ts = opts.ts,
                        hbaStr = opts.hbaStr,
                        special = opts.specialStr,
                        rawfile = opts.rawfile,
                        integration = opts.integration,
                        nants = opts.nant,
                        npol = opts.npol)

        elif opts.sclass.upper().startswith('BST'):
            s = issformat.BST(station = opts.station,
                        rcumode = opts.rcumode,
                        ts = opts.ts,
                        hbaStr = opts.hbaStr,
                        special = opts.specialStr,
                        rawfile = opts.rawfile,
                        integration = opts.integration,
                        pol = opts.bpol,
                        bitmode = opts.bitmode)

        elif opts.sclass.upper().startswith('SST'):
            s = issformat.SST(station = opts.station,
                        rcumode = opts.rcumode,
                        ts = opts.ts,
                        hbaStr = opts.hbaStr,
                        special = opts.specialStr,
                        rawfile = opts.rawfile,
                        integration = opts.integration,
                        rcu = opts.rcu)

        elif opts.sclass.upper().startswith('XST'):
            s = issformat.XST(station = opts.station,
                        rcumode = opts.rcumode,
                        ts = opts.ts,
                        hbaStr = opts.hbaStr,
                        special = opts.specialStr,
                        rawfile = opts.rawfile,
                        integration = opts.integration,
                        sb = opts.subband,
                        nants = opts.nant,
                        npol = opts.npol)

    if type(s).__name__=='BST' and not(opts.beamlet is None): # Read beamlet file
        import csv

        with open(opts.beamlet, 'r') as fh:
            reader = csv.reader(fh, delimiter=' ')
            for row in reader:
                if row[0].startswith('#'): continue
                s.setBeamlet(int(row[0]), float(row[1]), float(row[2]), row[3], int(row[4]), rcus=row[5])
    
    if opts.printMeta: s.printMeta()

    # Outputs
    if opts.obasename is None:
        if opts.rawfile is None:
            obasename = 'meta'
        else:
            rawfile = os.path.basename(opts.rawfile)
            obasename = os.path.splitext(rawfile)[0] 
    else: obasename = opts.obasename

    if 'raw' in outputTypes:
        oraw = obasename + '.dat'
        if not os.path.exists(oraw) or opts.force:
            print('Writing data to RAW', oraw)
            if type(s).__name__=='ACC': issformat.npy2acc(oraw)
            elif type(s).__name__=='BST': issformat.npy2bst(oraw)
            elif type(s).__name__=='SST': issformat.npy2sst(oraw)
            elif type(s).__name__=='XST': issformat.npy2xst(oraw)
        else: print('WARNING: %s exists, skipping. Use --force option to overwrite'%oraw)

    if 'json' in outputTypes:
        ojson = obasename + '.json'
        if not os.path.exists(ojson) or opts.force:
            print('Writing data to JSON', ojson)
            s.writeJSON(ojson)
        else: print('WARNING: %s exists, skipping. Use --force option to overwrite'%ojson)
    if 'hdf5' in outputTypes:
        ohdf5 = obasename + '.h5'
        if not os.path.exists(ohdf5) or opts.force:
            print('Writing data to HDF5', ohdf5)
            s.writeHDF5(ohdf5)
        else: print('WARNING: %s exists, skipping. Use --force option to overwrite'%ohdf5)

