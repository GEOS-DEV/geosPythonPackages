from pathlib import Path

from setuptools import setup

# This is where you add any fancy path resolution to the local lib:
geos_geomecha_path: str = ( Path( __file__ ).parent.parent / "geos-geomechanics" ).as_uri()
geos_utils_path: str = ( Path( __file__ ).parent.parent / "geos-utils" ).as_uri()

setup( install_requires=[
    "vtk >= 9.3",
    "numpy >= 1.26",
    "pandas >= 2.2",
    "typing_extensions >= 4.12",
    "types-setuptools >= 78.1.0",
    f"geos-geomechanics @ {geos_geomecha_path}",
    f"geos-utils @ {geos_utils_path}",
] )
