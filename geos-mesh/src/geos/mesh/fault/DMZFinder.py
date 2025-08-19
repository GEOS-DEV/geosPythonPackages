import numpy as np
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkUnstructuredGrid
from vtkmodules.vtkFiltersCore import vtkCellCenters
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase


class DMZFinder( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        super().__init__( nInputPorts=1,
                          nOutputPorts=1,
                          inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )
        self._region_array_name: str = "attribute"  # Default name for region in GEOS
        self._fault_region_id: int = 0  # Default id for fault region attribute in GEOS
        self._output_array_name: str = "isDMZ"  # New CellArray to create with value 0 if cell not in DMZ, 1 if in DMZ
        self._dmz_len: float = 50.0
        self._plane_point: list[ float ] = [ 0.0, 0.0, 0.0 ]
        self._plane_normal: list[ float ] = [ 0.0, 0.0, 1.0 ]

    def RequestData( self, request, inInfo, outInfo ) -> None:
        input_vtk_grid = vtkUnstructuredGrid.GetData( inInfo[ 0 ] )
        input_grid = dsa.WrapDataObject( input_vtk_grid )
        output_grid = dsa.WrapDataObject( vtkDataSet.GetData( outInfo ) )

        if not self._check_inputs( input_grid ):
            return 0

        # Get the array that defines the geological regions
        region_array = input_grid.CellData[ self._region_array_name ]

        # Use vtkCellCenters to get centroids
        cell_centers_filter = vtkCellCenters()
        cell_centers_filter.SetInputData( input_vtk_grid )
        # We don't want it to generate cell data, just the points
        # The output is a vtkPolyData where each point is a centroid.
        # We can grab these points as a NumPy array.
        cell_centers_filter.VertexCellsOn()
        cell_centers_filter.Update()
        centers_polydata = dsa.WrapDataObject( cell_centers_filter.GetOutput() )
        all_centroids = centers_polydata.Points

        # Identify which cells are in the DMZ
        dmz_mask = self._find_dmz_cells_vectorized( all_centroids )
        active_region_mask = ( region_array == self._fault_region_id )
        final_mask = np.logical_and( dmz_mask, active_region_mask )

        # Create the new CellData array
        new_region_id_array = np.zeros( region_array.shape, dtype=int )
        new_region_id_array[ final_mask ] = 1

        # Add new isDMZ array to the output_grid
        output_grid.ShallowCopy( input_vtk_grid )
        output_grid.CellData.append( new_region_id_array, self._output_array_name )

        return 1

    def _check_inputs( self, dsa_mesh: dsa.UnstructuredGrid ) -> bool:
        for attr in self.__dict__.keys():
            if self.__dict__[ attr ] is None:
                print( f"Error: {attr} is not set." )
                return False

        if self._output_array_name == self._region_array_name:
            print( "Error: Output array name cannot be the same as region array name." )
            return False

        if dsa_mesh is None:
            print( "Error: Input mesh is not set." )
            return False

        region_array = dsa_mesh.CellData[ self._region_array_name ]
        if region_array is None:
            print( f"Error: Region array '{self._region_array_name}' is not found in input mesh." )
            return False
        else:
            if self._fault_region_id not in region_array:
                print( f"Error: Fault region ID '{self._fault_region_id}' is not found in region array." )
                return False

        bounds = dsa_mesh.GetBounds()
        isInBounds = ( bounds[ 0 ] <= self._plane_point[ 0 ] <= bounds[ 1 ]
                       and bounds[ 2 ] <= self._plane_point[ 1 ] <= bounds[ 3 ]
                       and bounds[ 4 ] <= self._plane_point[ 2 ] <= bounds[ 5 ] )
        if not isInBounds:
            print( f"Error: Plane point {self._plane_point} is out of bounds of the mesh {bounds}." )
            return False

        return True

    def _find_dmz_cells_vectorized( self, cell_centers: np.ndarray ) -> np.ndarray:
        """
        Determines which cells are within the DMZ using vectorized operations.
        """
        vectors_to_centers = cell_centers - self._plane_point
        distances = np.abs( np.dot( vectors_to_centers, self._plane_normal ) )
        return distances < self._dmz_len

    def SetFaultRegionID( self, value: int ) -> None:
        if self._fault_region_id != value:
            self._fault_region_id = value
            self.Modified()

    def SetRegionArrayName( self, name: str ) -> None:
        if self._region_array_name != name:
            self._region_array_name = name
            self.Modified()

    def SetDmzLength( self, value: float ) -> None:
        if self._dmz_len != value:
            self._dmz_len = value
            self.Modified()

    def SetOutputArrayName( self, name: str ) -> None:
        if self._output_array_name != name:
            self._output_array_name = name
            self.Modified()

    def SetPlanePoint( self, x: float, y: float, z: float ) -> None:
        new_point = np.array( [ x, y, z ] )
        if not np.array_equal( self._plane_point, new_point ):
            self._plane_point = new_point
            self.Modified()

    def SetPlaneNormal( self, x: float, y: float, z: float ) -> None:
        norm = np.linalg.norm( [ x, y, z ] )
        if norm == 0:
            print( "Warning: Plane normal cannot be a zero vector. Using [0,0,1]." )
            new_normal = np.array( [ 0.0, 0.0, 1.0 ] )
        else:
            new_normal = np.array( [ x, y, z ] ) / norm

        if not np.array_equal( self._plane_normal, new_normal ):
            self._plane_normal = new_normal
            self.Modified()
