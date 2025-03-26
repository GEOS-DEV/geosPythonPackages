from pathlib import Path
from setuptools import setup

# This is where you add any fancy path resolution to the local lib:
local_path: str = (Path(__file__).parent).as_uri()

setup(
    install_requires=[
        f"geos-utils @ {local_path}",
    ]
)