import sys
from pathlib import Path
geos_pv_path: Path = Path( __file__ ).parent.parent.parent
print(geos_pv_path)