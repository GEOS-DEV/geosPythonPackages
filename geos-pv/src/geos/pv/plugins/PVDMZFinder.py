import sys
from pathlib import Path
from paraview.util.vtkAlgorithm import smproxy, smproperty, smdomain

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.fault.DMZFinder import DMZFinder

__doc__ = """
PVDMZFinder is a Paraview plugin that.

Input and output types are vtkUnstructuredGrid.

This filter results in a single output pipeline that contains the volume mesh.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVDMZFinder.py
* Select the .vtu grid loaded in Paraview.

"""


@smproxy.filter( name="PVDMZFinder", label="Damage Zone Finder" )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkUnstructuredGrid" ], composite_data_supported=True )
class PVDMZFinder( DMZFinder ):

    def __init__( self ) -> None:
        super().__init__()

    @smproperty.intvector( name="Fault ID", default_values=0, number_of_elements=1 )
    def SetActiveFaultID( self, value: int ) -> None:
        if self._active_fault_id != value:
            self._active_fault_id = value
            self.Modified()

    @smproperty.intvector( name="Region ID", default_values=0, number_of_elements=1 )
    def SetActiveRegionID( self, value: int ) -> None:
        if self._active_region_id != value:
            self._active_region_id = value
            self.Modified()

    @smproperty.doublevector( name="DZ Length", default_values=100.0, number_of_elements=1 )
    def SetDmzLength( self, value: float ) -> None:
        if self._dmz_len != value:
            self._dmz_len = value
            self.Modified()

    @smproperty.stringvector( name="Output Array Name", default_values="DMZ", number_of_elements=1 )
    def SetOutputArrayName( self, name: str ) -> None:
        if self._output_array_name != name:
            self._output_array_name = name
            self.Modified()

    @smproperty.stringvector( name="Region Array Name", default_values="attribute", number_of_elements=1 )
    def SetRegionArrayName( self, name: str ) -> None:
        if self._region_array_name != name:
            self._region_array_name = name
            self.Modified()
