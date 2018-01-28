from setuptools import setup

__version__ = '0.0.3'

setup(name = 'issformat',
    version = __version__,
    description = 'LOFAR international single station metadata interface',
    long_description = open('README.md').read(),
    author = 'Griffin Foster',
    author_email = 'griffin.foster@gmail.com',
    url='https://github.com/griffinfoster/issformat',
    platforms = ['*nix'],
    license = 'GPL',
    requires = ['distutils','numpy','json'],
    py_modules = ['issformat'],
    scripts = ['scripts/issConverter.py'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Topic :: Scientific/Engineering :: Astronomy',
    ],
)
