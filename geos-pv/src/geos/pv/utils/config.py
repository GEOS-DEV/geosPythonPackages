import sys
from pathlib import Path

def update_paths() ->None:
    """Update sys path to load GEOS Python packages. """
    # Add other packages path to sys path
    geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
    geos_python_packages_path: Path = geos_pv_path.parent

    python_modules = [ "geos-pv" ]
    with open( str(geos_pv_path / "requirements.txt") ) as f:
        python_modules += f.read().splitlines()

    for m in python_modules:
        if not ( geos_python_packages_path / m ).exists():
            continue
        m_path = str( geos_python_packages_path / m / "src")
        if m_path not in sys.path:
            sys.path.insert( 0, m_path )