from typing_extensions import Self
import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.collocated_nodes import find_collocated_nodes_buckets, find_wrong_support_elements
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing.collocated_nodes_parsing import logger_results

__doc__ = """
CollocatedNodes module identifies and handles duplicated/collocated nodes in a vtkUnstructuredGrid.
The filter can detect nodes that are within a specified tolerance distance and optionally identify elements
that have support nodes appearing more than once (wrong support elements).

To use the filter
-----------------

.. code-block:: python

    from geos.mesh.doctor.filters.CollocatedNodes import CollocatedNodes

    # instantiate the filter
    collocatedNodesFilter = CollocatedNodes(mesh, tolerance=1e-6, writeWrongSupportElements=True)

    # execute the filter
    success = collocatedNodesFilter.applyFilter()

    # get results
    collocatedBuckets = collocatedNodesFilter.getCollocatedNodeBuckets()
    wrongSupportElements = collocatedNodesFilter.getWrongSupportElements()

    # get the processed mesh
    outputMesh = collocatedNodesFilter.getMesh()

    # write the output mesh
    collocatedNodesFilter.writeGrid("output/mesh_with_collocated_info.vtu")

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.CollocatedNodes import collocatedNodes

    # apply filter directly
    outputMesh, collocatedBuckets, wrongSupportElements = collocatedNodes(
        mesh,
        outputPath="output/mesh_with_collocated_info.vtu",
        tolerance=1e-6,
        writeWrongSupportElements=True
    )
"""

loggerTitle: str = "Collocated Nodes Filter"


class CollocatedNodes( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        tolerance: float = 0.0,
        writeWrongSupportElements: bool = False,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the collocated nodes filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze.
            tolerance (float): Distance tolerance for detecting collocated nodes. Defaults to 0.0.
            writeWrongSupportElements (bool): Whether to mark wrong support elements in output. Defaults to False.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, useExternalLogger )
        self.tolerance: float = tolerance
        self.writeWrongSupportElements: bool = writeWrongSupportElements
        self.collocatedNodeBuckets: list[ tuple[ int ] ] = []
        self.wrongSupportElements: list[ int ] = []

    def applyFilter( self: Self ) -> bool:
        """Apply the collocated nodes analysis.

        Returns:
            bool: True if analysis completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        self.collocatedNodeBuckets: list[ tuple[ int ] ] = find_collocated_nodes_buckets( self.mesh, self.tolerance )
        self.wrongSupportElements: list[ int ] = find_wrong_support_elements( self.mesh )

        # Add marking arrays if requested
        if self.writeWrongSupportElements and self.wrongSupportElements:
            self._addWrongSupportElementsArray()

        logger_results( self.logger, self.collocatedNodeBuckets, self.wrongSupportElements )

        self.logger.info( f"The filter {self.logger.name} succeeded." )
        return True

    def getCollocatedNodeBuckets( self: Self ) -> list[ tuple[ int ] ]:
        """Returns the nodes buckets that contain the duplicated node indices.

        Returns:
            list[tuple[int]]: Groups of collocated node indices.
        """
        return self.collocatedNodeBuckets

    def getWrongSupportElements( self: Self ) -> list[ int ]:
        """Returns the element indices with support node indices appearing more than once.

        Returns:
            list[int]: Element indices with problematic support nodes.
        """
        return self.wrongSupportElements

    def setTolerance( self: Self, tolerance: float ) -> None:
        """Set the tolerance parameter to define if two points are collocated or not.

        Args:
            tolerance (float): Distance tolerance.
        """
        self.tolerance = tolerance

    def setWriteWrongSupportElements( self: Self, write: bool ) -> None:
        """Set whether to create arrays marking wrong support elements in output data.

        Args:
            write (bool): True to enable marking, False to disable.
        """
        self.writeWrongSupportElements = write

    def _addWrongSupportElementsArray( self: Self ) -> None:
        """Add array marking wrong support elements."""
        numCells: int = self.mesh.GetNumberOfCells()
        wrongSupportArray = np.zeros( numCells, dtype=np.int32 )
        wrongSupportArray[ self.wrongSupportElements ] = 1

        vtkArray: vtkDataArray = numpy_to_vtk( wrongSupportArray )
        vtkArray.SetName( "WrongSupportElements" )
        self.mesh.GetCellData().AddArray( vtkArray )


# Main function for standalone use
def collocatedNodes(
    mesh: vtkUnstructuredGrid,
    outputPath: str,
    tolerance: float = 0.0,
    writeWrongSupportElements: bool = False,
) -> tuple[ vtkUnstructuredGrid, list[ tuple[ int ] ], list[ int ] ]:
    """Apply collocated nodes analysis to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        outputPath (str): Output file path if writeOutput is True.
        tolerance (float): Distance tolerance for detecting collocated nodes. Defaults to 0.0.
        writeWrongSupportElements (bool): Whether to mark wrong support elements. Defaults to False.
        writeOutput (bool): Whether to write output mesh to file. Defaults to False.

    Returns:
        tuple[vtkUnstructuredGrid, list[tuple[int]], list[int]]:
            Processed mesh, collocated node buckets, wrong support elements.
    """
    filterInstance = CollocatedNodes( mesh, tolerance, writeWrongSupportElements )
    filterInstance.applyFilter()
    filterInstance.writeGrid( outputPath )

    return (
        filterInstance.getMesh(),
        filterInstance.getCollocatedNodeBuckets(),
        filterInstance.getWrongSupportElements(),
    )
