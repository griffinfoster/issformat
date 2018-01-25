## issformat

---

Contact: griffin.foster@gmail.com

Metadata and wrapper format for LOFAR international single station data sets. Useful to generate JSON metadata files and HDF5 wrappers around raw data files produced at a LOFAR international station. Supports total correlation (ACC), beamlet statistics (BST), subband statistics SST, subband correlation (XST) files.

#### Required Python Modules

* numpy
* json

#### Optional Python Modules

* h5py

#### Install

The latest release (0.0.2 as of January 25, 2018) can be installed via pip:

```
pip install issformat
```

Otherwise, the standard install will install the package:

```
git clone https://github.com/griffinfoster/issformat
cd issformat
sudo python setup.py install
```

While developing it is useful to do a developer install:

```
sudo python setup.py develop
```

A generic usage script `issConverter.py` will be install globally.

#### Usage

#### Documentation

The format definition and module usage is documented [here](https://github.com/griffinfoster/issformat/blob/master/docs/pdf/format_definition.pdf).
