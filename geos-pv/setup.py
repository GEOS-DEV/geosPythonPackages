from pathlib import Path
from setuptools import setup

# geos python package dependencies are read from requirements.txt
# WARNING: only local dependencies must be included in the requirements.txt

local_package_names = []
with open( "./requirements.txt" ) as f:
    local_package_names = f.read().splitlines()

geos_python_packages_path: Path = Path( __file__ ).parent.parent
install_requires = [
    f"{name} @ {(geos_python_packages_path / name).as_uri()}" for name in local_package_names
    if ( geos_python_packages_path / name ).exists()
]
setup( install_requires=install_requires )
