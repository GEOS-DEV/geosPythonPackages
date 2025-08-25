import numpy as np
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.non_conformal import Options, find_non_conformal_cells
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase

__doc__ = """
NonConformal module detects non-conformal mesh interfaces in a vtkUnstructuredGrid.
Non-conformal interfaces occur when adjacent cells do not share nodes or faces properly, which can indicate
mesh quality issues or intentional non-matching grid interfaces that require special handling.

To use the filter:

.. code-block:: python

    from geos.mesh.doctor.filters.NonConformal import NonConformal

    # instantiate the filter
    nonConformalFilter = NonConformal(
        mesh,
        point_tolerance=1e-6,
        face_tolerance=1e-6,
        angle_tolerance=10.0,
        paint_non_conformal_cells=True
    )

    # execute the filter
    success = nonConformalFilter.applyFilter()

    # get non-conformal cell pairs
    non_conformal_cells = nonConformalFilter.getNonConformalCells()
    # returns list of tuples with (cell1_id, cell2_id) for non-conformal interfaces

    # get the processed mesh
    output_mesh = nonConformalFilter.getMesh()

    # write the output mesh
    nonConformalFilter.writeGrid("output/mesh_with_nonconformal_info.vtu")
"""

loggerTitle: str = "Non-Conformal Filter"


class NonConformal( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        point_tolerance: float = 0.0,
        face_tolerance: float = 0.0,
        angle_tolerance: float = 10.0,
        paint_non_conformal_cells: bool = False,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the non-conformal detection filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze
            point_tolerance (float): Tolerance for point matching. Defaults to 0.0.
            face_tolerance (float): Tolerance for face matching. Defaults to 0.0.
            angle_tolerance (float): Angle tolerance in degrees. Defaults to 10.0.
            paint_non_conformal_cells (bool): Whether to mark non-conformal cells in output. Defaults to False.
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, use_external_logger )
        self.point_tolerance: float = point_tolerance
        self.face_tolerance: float = face_tolerance
        self.angle_tolerance: float = angle_tolerance
        self.paint_non_conformal_cells: bool = paint_non_conformal_cells

        # Results storage
        self.non_conformal_cells: list[ tuple[ int, int ] ] = []

    def setPointTolerance( self: Self, tolerance: float ) -> None:
        """Set the point tolerance parameter.

        Args:
            tolerance (float): Point tolerance value
        """
        self.point_tolerance = tolerance

    def setFaceTolerance( self: Self, tolerance: float ) -> None:
        """Set the face tolerance parameter.

        Args:
            tolerance (float): Face tolerance value
        """
        self.face_tolerance = tolerance

    def setAngleTolerance( self: Self, tolerance: float ) -> None:
        """Set the angle tolerance parameter in degrees.

        Args:
            tolerance (float): Angle tolerance in degrees
        """
        self.angle_tolerance = tolerance

    def setPaintNonConformalCells( self: Self, paint: bool ) -> None:
        """Set whether to create arrays marking non-conformal cells in output data.

        Args:
            paint (bool): True to enable marking, False to disable
        """
        self.paint_non_conformal_cells = paint

    def getPointTolerance( self: Self ) -> float:
        """Get the current point tolerance.

        Returns:
            float: Point tolerance value
        """
        return self.point_tolerance

    def getFaceTolerance( self: Self ) -> float:
        """Get the current face tolerance.

        Returns:
            float: Face tolerance value
        """
        return self.face_tolerance

    def getAngleTolerance( self: Self ) -> float:
        """Get the current angle tolerance.

        Returns:
            float: Angle tolerance in degrees
        """
        return self.angle_tolerance

    def applyFilter( self: Self ) -> bool:
        """Apply the non-conformal detection.

        Returns:
            bool: True if detection completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Create options and find non-conformal cells
            options = Options( self.angle_tolerance, self.point_tolerance, self.face_tolerance )
            self.non_conformal_cells = find_non_conformal_cells( self.mesh, options )

            # Extract all unique cell IDs from pairs
            non_conformal_cells_extended = [ cell_id for pair in self.non_conformal_cells for cell_id in pair ]
            unique_non_conformal_cells = frozenset( non_conformal_cells_extended )

            self.logger.info( f"Found {len(unique_non_conformal_cells)} non-conformal cells" )
            if non_conformal_cells_extended:
                self.logger.info(
                    f"Non-conformal cell IDs: {', '.join(map(str, sorted(non_conformal_cells_extended)))}" )

            # Add marking arrays if requested
            if self.paint_non_conformal_cells and unique_non_conformal_cells:
                self._addNonConformalCellsArray( unique_non_conformal_cells )

            self.logger.info( f"The filter {self.logger.name} succeeded" )
            return True

        except Exception as e:
            self.logger.error( f"Error in non-conformal detection: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed" )
            return False

    def _addNonConformalCellsArray( self: Self, unique_non_conformal_cells: frozenset[ int ] ) -> None:
        """Add array marking non-conformal cells."""
        num_cells = self.mesh.GetNumberOfCells()
        non_conformal_array = np.zeros( num_cells, dtype=np.int32 )

        for cell_id in unique_non_conformal_cells:
            if 0 <= cell_id < num_cells:
                non_conformal_array[ cell_id ] = 1

        vtk_array: vtkDataArray = numpy_to_vtk( non_conformal_array )
        vtk_array.SetName( "IsNonConformal" )
        self.mesh.GetCellData().AddArray( vtk_array )

    def getNonConformalCells( self: Self ) -> list[ tuple[ int, int ] ]:
        """Get the detected non-conformal cell pairs.

        Returns:
            list[tuple[int, int]]: List of cell ID pairs that are non-conformal
        """
        return self.non_conformal_cells


# Main function for backward compatibility and standalone use
def non_conformal(
    mesh: vtkUnstructuredGrid,
    point_tolerance: float = 0.0,
    face_tolerance: float = 0.0,
    angle_tolerance: float = 10.0,
    paint_non_conformal_cells: bool = False,
    write_output: bool = False,
    output_path: str = "output/mesh_with_nonconformal_info.vtu",
) -> tuple[ vtkUnstructuredGrid, list[ tuple[ int, int ] ] ]:
    """Apply non-conformal detection to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh
        point_tolerance (float): Tolerance for point matching. Defaults to 0.0.
        face_tolerance (float): Tolerance for face matching. Defaults to 0.0.
        angle_tolerance (float): Angle tolerance in degrees. Defaults to 10.0.
        paint_non_conformal_cells (bool): Whether to mark non-conformal cells. Defaults to False.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, list[tuple[int, int]]]:
            Processed mesh, non-conformal cell pairs
    """
    filter_instance = NonConformal( mesh, point_tolerance, face_tolerance, angle_tolerance, paint_non_conformal_cells )
    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "Non-conformal detection failed" )

    if write_output:
        filter_instance.writeGrid( output_path )

    return (
        filter_instance.getMesh(),
        filter_instance.getNonConformalCells(),
    )


# Alias for backward compatibility
def processNonConformal(
    mesh: vtkUnstructuredGrid,
    point_tolerance: float = 0.0,
    face_tolerance: float = 0.0,
    angle_tolerance: float = 10.0,
) -> tuple[ vtkUnstructuredGrid, list[ tuple[ int, int ] ] ]:
    """Legacy function name for backward compatibility."""
    return non_conformal( mesh, point_tolerance, face_tolerance, angle_tolerance )
