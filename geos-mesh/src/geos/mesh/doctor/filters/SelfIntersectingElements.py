import numpy as np
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.self_intersecting_elements import get_invalid_cell_ids
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing.self_intersecting_elements_parsing import logger_results

__doc__ = """
SelfIntersectingElements module identifies various types of invalid or problematic elements
in a vtkUnstructuredGrid. It detects elements with intersecting edges, intersecting faces, non-contiguous edges,
non-convex shapes, incorrectly oriented faces, wrong number of points, non planar faces elements and degenerate
faces elements.

To use the filter
-----------------

.. code-block:: python

    from geos.mesh.doctor.filters.SelfIntersectingElements import SelfIntersectingElements

    # instantiate the filter
    selfIntersectingElementsFilter = SelfIntersectingElements(
        mesh,
        minDistance=1e-6,
        writeInvalidElements=True
    )

    # execute the filter
    success = selfIntersectingElementsFilter.applyFilter()

    # get the ids of problematic elements for every error types
    selfIntersectingElementsFilter.getInvalidCells()

    # get the processed mesh
    output_mesh = selfIntersectingElementsFilter.getMesh()

    # write the output mesh
    selfIntersectingElementsFilter.writeGrid("output/mesh_with_invalid_elements.vtu")

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.SelfIntersectingElements import selfIntersectingElements

    # apply filter directly
    outputMesh, invalidCellIds = selfIntersectingElements(
        mesh,
        outputPath="output/mesh_with_invalid_elements.vtu",
        minDistance=1e-6,
        writeInvalidElements=True
    )
"""

loggerTitle: str = "Self-Intersecting Elements Filter"


class SelfIntersectingElements( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        minDistance: float = 0.0,
        writeInvalidElements: bool = False,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the self-intersecting elements detection filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze.
            minDistance (float): Minimum distance parameter for intersection detection. Defaults to 0.0.
            writeInvalidElements (bool): Whether to mark invalid elements in output. Defaults to False.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, useExternalLogger )
        self.invalidCellIds: dict[ str, list[ int ] ] = {}
        self.minDistance: float = minDistance
        self.writeInvalidElements: bool = writeInvalidElements

    def applyFilter( self: Self ) -> bool:
        """Apply the self-intersecting elements detection.

        Returns:
            bool: True if detection completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        self.invalidCellIds = get_invalid_cell_ids( self.mesh, self.minDistance )
        logger_results( self.logger, self.invalidCellIds )

        # Add marking arrays if requested
        if self.writeInvalidElements:
            self._addInvalidElementsArrays()

        self.logger.info( f"The filter {self.logger.name} succeeded." )
        return True

    def getInvalidCellIds( self: Self ) -> dict[ str, list[ int ] ]:
        """Get all invalid elements organized by type.

        Returns:
            dict[str, list[int]]: Dictionary mapping invalid element types to their IDs.
        """
        return self.invalidCellIds

    def getMinDistance( self: Self ) -> float:
        """Get the current minimum distance parameter.

        Returns:
            float: Minimum distance value.
        """
        return self.minDistance

    def setMinDistance( self: Self, distance: float ) -> None:
        """Set the minimum distance parameter for intersection detection.

        Args:
            distance (float): Minimum distance value.
        """
        self.minDistance = distance

    def setWriteInvalidElements( self: Self, write: bool ) -> None:
        """Set whether to create arrays marking invalid elements in output data.

        Args:
            write (bool): True to enable marking, False to disable.
        """
        self.writeInvalidElements = write

    def _addInvalidElementsArrays( self: Self ) -> None:
        """Add arrays marking different types of invalid elements."""
        numCells: int = self.mesh.GetNumberOfCells()
        if self.writeInvalidElements:
            for invalidTypeName, invalidTypeData in self.invalidCellIds.items():
                if invalidTypeData:
                    array = np.zeros( numCells, dtype=np.int32 )
                    array[ invalidTypeData ] = 1
                    vtkArray: vtkDataArray = numpy_to_vtk( array )
                    vtkArray.SetName( f"Is{invalidTypeName}" )
                    self.mesh.GetCellData().AddArray( vtkArray )


# Main function for standalone use
def selfIntersectingElements(
        mesh: vtkUnstructuredGrid,
        outputPath: str,
        minDistance: float = 0.0,
        writeInvalidElements: bool = False ) -> tuple[ vtkUnstructuredGrid, dict[ str, list[ int ] ] ]:
    """Apply self-intersecting elements detection to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        outputPath (str): Output file path if write_output is True.
        minDistance (float): Minimum distance parameter for intersection detection. Defaults to 0.0.
        writeInvalidElements (bool): Whether to mark invalid elements. Defaults to False.

    Returns:
        tuple[vtkUnstructuredGrid, dict[str, list[int]]]:
            Processed mesh, dictionary of invalid element types and their IDs
    """
    filter_instance = SelfIntersectingElements( mesh, minDistance, writeInvalidElements )
    success = filter_instance.applyFilter()
    if not success:
        raise RuntimeError( "Self-intersecting elements detection failed" )

    filter_instance.writeGrid( outputPath )

    return (
        filter_instance.getMesh(),
        filter_instance.getInvalidCellIds(),
    )
