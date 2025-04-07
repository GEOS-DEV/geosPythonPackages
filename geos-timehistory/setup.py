from pathlib import Path
from setuptools import setup

# This is where you add any fancy path resolution to the local lib:
package_name = "hdf5-wrapper"
geos_utils_path: str = ( Path( __file__ ).parent.parent / package_name ).as_uri()

setup( install_requires=[
    "matplotlib",
    "h5py",
    "numpy",
    f"{package_name} @ {geos_utils_path}",
] )
