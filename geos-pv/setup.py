from pathlib import Path
from setuptools import setup

# geos python package dependencies are read from requirements.txt
# WARNING: only local dependencies must be included in the requirements.txt

geos_pv_path: Path = Path( __file__ ).parent
geos_python_packages_path: Path = geos_pv_path.parent
local_package_names = []
with open( str( geos_pv_path / "requirements.txt" ) ) as f:
    local_package_names = f.read().splitlines()

install_requires = []
for name in local_package_names:
    if ( geos_python_packages_path / name ).exists():
        install_requires += [ f"{name} @ {(geos_python_packages_path / name).as_uri()}" ]
    else:
        install_requires += [ name ]

setup( install_requires=install_requires )
