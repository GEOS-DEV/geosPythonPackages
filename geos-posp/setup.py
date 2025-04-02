from pathlib import Path
from setuptools import setup

# This is where you add any fancy path resolution to the local lib:
install_requires_external = [
    "vtk >= 9.3",
    "numpy >= 1.26",
    "pandas >= 2.2",
    "typing_extensions >= 4.12",
]
local_package_names = [ "geos-utils", "geos-geomechanics" ]

geos_python_packages_path: Path = Path( __file__ ).parent.parent
install_requires_local = [
    f"{name} @ {(geos_python_packages_path / name).as_uri()}" for name in local_package_names
    if ( geos_python_packages_path / name ).exists()
]

setup( install_requires=install_requires_external + install_requires_local )
