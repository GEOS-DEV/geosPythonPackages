import os
import sys

# Add other packages path to sys path
dir_path = os.path.dirname( os.path.realpath( __file__ ) )
python_root = '../../..'

python_modules = [ "geos-pv" ]
with open( "./requirements.txt" ) as f:
    python_modules += f.read().splitlines()

for m in python_modules:
    m_path = os.path.abspath( os.path.join( dir_path, python_root, m, 'src' ) )
    if m_path not in sys.path:
        sys.path.insert( 0, m_path )
