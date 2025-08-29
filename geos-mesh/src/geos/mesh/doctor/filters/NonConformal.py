import numpy as np
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.non_conformal import Options, find_non_conformal_cells
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing.non_conformal_parsing import logger_results

__doc__ = """
NonConformal module detects non-conformal mesh interfaces in a vtkUnstructuredGrid.
Non-conformal interfaces occur when adjacent cells do not share nodes or faces properly, which can indicate
mesh quality issues or intentional non-matching grid interfaces that require special handling.

To use the filter
-----------------

.. code-block:: python

    from geos.mesh.doctor.filters.NonConformal import NonConformal

    # instantiate the filter
    nonConformalFilter = NonConformal(
        mesh,
        pointTolerance=1e-6,
        faceTolerance=1e-6,
        angleTolerance=10.0,
        writeNonConformalCells=True
    )

    # execute the filter
    success = nonConformalFilter.applyFilter()

    # get non-conformal cell pairs
    nonConformalCells = nonConformalFilter.getNonConformalCells()
    # returns list of tuples with (cell1_id, cell2_id) for non-conformal interfaces

    # get the processed mesh
    output_mesh = nonConformalFilter.getMesh()

    # write the output mesh
    nonConformalFilter.writeGrid("output/mesh_with_non_conformal_info.vtu")

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.NonConformal import nonConformal

    # apply filter directly
    outputMesh, nonConformalCells = nonConformal(
        mesh,
        outputPath="output/mesh_with_non_conformal_info.vtu",
        pointTolerance=1e-6,
        faceTolerance=1e-6,
        angleTolerance=10.0,
        writeNonConformalCells=True
    )
"""

loggerTitle: str = "Non-Conformal Filter"


class NonConformal( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        pointTolerance: float = 0.0,
        faceTolerance: float = 0.0,
        angleTolerance: float = 10.0,
        writeNonConformalCells: bool = False,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the non-conformal detection filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze.
            pointTolerance (float): Tolerance for point matching. Defaults to 0.0.
            faceTolerance (float): Tolerance for face matching. Defaults to 0.0.
            angleTolerance (float): Angle tolerance in degrees. Defaults to 10.0.
            writeNonConformalCells (bool): Whether to mark non-conformal cells in output. Defaults to False.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, useExternalLogger )
        self.pointTolerance: float = pointTolerance
        self.faceTolerance: float = faceTolerance
        self.angleTolerance: float = angleTolerance
        self.writeNonConformalCells: bool = writeNonConformalCells

        # Results storage
        self.nonConformalCells: list[ tuple[ int, int ] ] = []

    def applyFilter( self: Self ) -> bool:
        """Apply the non-conformal detection.

        Returns:
            bool: True if detection completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        # Create options and find non-conformal cells
        options = Options( self.angleTolerance, self.pointTolerance, self.faceTolerance )
        self.nonConformalCells = find_non_conformal_cells( self.mesh, options )

        logger_results( self.logger, self.nonConformalCells )

        # Add marking arrays if requested
        if self.writeNonConformalCells and self.nonConformalCells:
            self._addNonConformalCellsArray( self.nonConformalCells )

        self.logger.info( f"The filter {self.logger.name} succeeded." )
        return True

    def getAngleTolerance( self: Self ) -> float:
        """Get the current angle tolerance.

        Returns:
            float: Angle tolerance in degrees.
        """
        return self.angleTolerance

    def getFaceTolerance( self: Self ) -> float:
        """Get the current face tolerance.

        Returns:
            float: Face tolerance value.
        """
        return self.faceTolerance

    def getNonConformalCells( self: Self ) -> list[ tuple[ int, int ] ]:
        """Get the detected non-conformal cell pairs.

        Returns:
            list[tuple[int, int]]: List of cell ID pairs that are non-conformal.
        """
        return self.nonConformalCells

    def getPointTolerance( self: Self ) -> float:
        """Get the current point tolerance.

        Returns:
            float: Point tolerance value.
        """
        return self.pointTolerance

    def setAngleTolerance( self: Self, tolerance: float ) -> None:
        """Set the angle tolerance parameter in degrees.

        Args:
            tolerance (float): Angle tolerance in degrees.
        """
        self.angleTolerance = tolerance

    def setFaceTolerance( self: Self, tolerance: float ) -> None:
        """Set the face tolerance parameter.

        Args:
            tolerance (float): Face tolerance value.
        """
        self.faceTolerance = tolerance

    def setPointTolerance( self: Self, tolerance: float ) -> None:
        """Set the point tolerance parameter.

        Args:
            tolerance (float): Point tolerance value.
        """
        self.pointTolerance = tolerance

    def setWriteNonConformalCells( self: Self, write: bool ) -> None:
        """Set whether to create anarray marking non-conformal cells in output data.

        Args:
            write (bool): True to enable marking, False to disable.
        """
        self.writeNonConformalCells = write

    def _addNonConformalCellsArray( self: Self ) -> None:
        """Add array marking non-conformal cells."""
        numCells: int = self.mesh.GetNumberOfCells()
        uniqueNonConformalCells = frozenset( [ cell_id for pair in self.nonConformalCells for cell_id in pair ] )
        nonConformalArray = np.zeros( numCells, dtype=np.int32 )
        nonConformalArray[ list( uniqueNonConformalCells ) ] = 1

        vtkArray: vtkDataArray = numpy_to_vtk( nonConformalArray )
        vtkArray.SetName( "IsNonConformal" )
        self.mesh.GetCellData().AddArray( vtkArray )


# Main function for standalone use
def nonConformal(
    mesh: vtkUnstructuredGrid,
    outputPath: str,
    pointTolerance: float = 0.0,
    faceTolerance: float = 0.0,
    angleTolerance: float = 10.0,
    writeNonConformalCells: bool = False
) -> tuple[ vtkUnstructuredGrid, list[ tuple[ int, int ] ] ]:
    """Apply non-conformal detection to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        pointTolerance (float): Tolerance for point matching. Defaults to 0.0.
        faceTolerance (float): Tolerance for face matching. Defaults to 0.0.
        angleTolerance (float): Angle tolerance in degrees. Defaults to 10.0.
        writeNonConformalCells (bool): Whether to mark non-conformal cells. Defaults to False.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, list[tuple[int, int]]]:
            Processed mesh, non-conformal cell pairs.
    """
    filterInstance = NonConformal( mesh, pointTolerance, faceTolerance, angleTolerance, writeNonConformalCells )
    filterInstance.applyFilter()

    if writeNonConformalCells:
        filterInstance.writeGrid( outputPath )

    return (
        filterInstance.getMesh(),
        filterInstance.getNonConformalCells(),
    )
