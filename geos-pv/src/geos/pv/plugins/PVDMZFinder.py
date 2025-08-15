import numpy as np
from vtkmodules.vtkCommonDataModel import vtkDataSet
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from paraview.util.vtkAlgorithm import smproxy, smproperty, smdomain


__doc__ = """
PVDMZFinder is a Paraview plugin that.

Input and output types are vtkUnstructuredGrid.

This filter results in a single output pipeline that contains the volume mesh.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>geos_dz.py
* Select the Geos output .pvd file loaded in Paraview.

"""


@smproxy.filter(label="DZ Finder")
@smproperty.input(name="Input")
class PVDMZFinder( VTKPythonAlgorithmBase ):

    def __init__( self ):
        VTKPythonAlgorithmBase.__init__( self, nInputPorts=1, nOutputPorts=1, outputType='vtkUnstructuredGrid' )
        # Default values.
        self._DMZ_len = 50.0
        self._active_region = 80
        self._plane_point = np.array( [ 0.0, 0.0, 0.0 ] )
        self._plane_normal = np.array( [ 0.0, 0.0, 1.0 ] )

    def RequestData( self, request, inInfo, outInfo ):
        # Input data
        input0 = dsa.WrapDataObject( vtkDataSet.GetData( inInfo[ 0 ] ) )
        self.CellDataLabels = input0.CellData.keys()

        print( f"Total number of cells: {input0.GetNumberOfCells()}" )

        # call the main routine to identify the damage zone.
        new_array = self.process_cells( input0 )

        # Output
        output = dsa.WrapDataObject( vtkDataSet.GetData( outInfo ) )
        output.ShallowCopy( input0.VTKObject )
        output.CellData.append( new_array, "Reservoir_with_DZ" )

        return 1

    def process_cells( self, input0 ):
        """This function aims to traverse the model and identify the cells that are part of the damage zone, and in this process, form new regions in the domain's property map that represent the damage zone of the geological fault."""
        num_cells = input0.GetNumberOfCells()
        cell_array = input0.CellData[ self.CellDataLabels[ 0 ] ]
        vtk_dataset = input0.VTKObject

        new_array = np.zeros( num_cells )

        for i in range( num_cells ):
            original_value = cell_array[ i ]
            new_value = original_value

            if self._active_region == new_value:
                center = self.get_cell_centroid( vtk_dataset, i )
                flag = self.check_is_dmz( center )

                if flag:
                    new_value += 10

            new_array[ i ] = new_value

        return new_array

    def get_cell_centroid( self, vtk_dataset, cell_id ):
        cell = vtk_dataset.GetCell( cell_id )
        num_points = cell.GetNumberOfPoints()

        coords = np.zeros( 3 )
        for j in range( num_points ):
            point = cell.GetPoints().GetPoint( j )
            coords += np.array( point )

        centroid = coords / num_points if num_points > 0 else np.array( [ 0.0, 0.0, 0.0 ] )
        # print(f"  Centroid of Cell {cell_id}: ({centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f})")
        return centroid

    def check_is_dmz( self, cell_center ):
        """ Returns True if the distance from the point to the defined plane is greater than the threshold. """
        if not hasattr( self, "_plane_point" ) or not hasattr( self, "_plane_normal" ):
            print( "Plane has not been defined yet." )
            return False

        vec = cell_center - self._plane_point
        distance = abs( np.dot( vec, self._plane_normal ) )
        return distance < self._DMZ_len

    @smproperty.intvector( name="Active Region", default_values=80, number_of_elements=1 )
    def SetActReg( self, value ):
        self._active_region = int( value )
        print( f"The active region flag is: {self._active_region}" )
        self.Modified()

    @smproperty.doublevector( name="DZ Length", default_values=100.0, number_of_elements=1 )
    def SetDmzLen( self, value ):
        self._DMZ_len = float( value )
        print( f"DMZ length set to: {self._DMZ_len}" )
        self.Modified()

    # -----------------------------------------------------------------
    # TEMPORARY IMPLEMENTATION ---- IN FUTURE THIS IS NOT GONNA BE USED
    # -----------------------------------------------------------------
    @smproperty.doublevector( name="PlanePoint", default_values=[ 0.0, 0.0, 0.0 ], number_of_elements=3 )
    def SetPlanePoint( self, x, y, z ):
        """Defines a point that lies on the plane (x, y, z)"""
        self._plane_point = np.array( [ x, y, z ] )
        print( f"Point defined at: {self._plane_point}" )
        self.Modified()

    @smproperty.doublevector( name="PlaneNormal", default_values=[ 0.0, 0.0, 1.0 ], number_of_elements=3 )
    def SetPlaneNormal( self, x, y, z ):
        """Defines the normal vector of the plane (nx, ny, nz)"""
        self._plane_normal = np.array( [ x, y, z ] )
        print( f"Plane normal defined as: {self._plane_normal}" )
        self.Modified()
