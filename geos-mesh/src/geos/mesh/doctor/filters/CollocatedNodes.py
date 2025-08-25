from typing_extensions import Self
import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.collocated_nodes import find_collocated_nodes_buckets, find_wrong_support_elements
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase

__doc__ = """
CollocatedNodes module identifies and handles duplicated/collocated nodes in a vtkUnstructuredGrid.
The filter can detect nodes that are within a specified tolerance distance and optionally identify elements
that have support nodes appearing more than once (wrong support elements).

To use the filter:

.. code-block:: python

    from geos.mesh.doctor.filters.CollocatedNodes import CollocatedNodes

    # instantiate the filter
    collocatedNodesFilter = CollocatedNodes(mesh, tolerance=1e-6, paint_wrong_support_elements=True)

    # execute the filter
    success = collocatedNodesFilter.applyFilter()

    # get results
    collocated_buckets = collocatedNodesFilter.getCollocatedNodeBuckets()
    wrong_support_elements = collocatedNodesFilter.getWrongSupportElements()

    # get the processed mesh
    output_mesh = collocatedNodesFilter.getMesh()

    # write the output mesh
    collocatedNodesFilter.writeGrid("output/mesh_with_collocated_info.vtu")
"""

loggerTitle: str = "Collocated Nodes Filter"


class CollocatedNodes( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        tolerance: float = 0.0,
        paint_wrong_support_elements: bool = False,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the collocated nodes filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze
            tolerance (float): Distance tolerance for detecting collocated nodes. Defaults to 0.0.
            paint_wrong_support_elements (bool): Whether to mark wrong support elements in output. Defaults to False.
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, use_external_logger )
        self.tolerance: float = tolerance
        self.paint_wrong_support_elements: bool = paint_wrong_support_elements

        # Results storage
        self.collocated_node_buckets: list[ tuple[ int ] ] = []
        self.wrong_support_elements: list[ int ] = []

    def setTolerance( self: Self, tolerance: float ) -> None:
        """Set the tolerance parameter to define if two points are collocated or not.

        Args:
            tolerance (float): Distance tolerance
        """
        self.tolerance = tolerance

    def setPaintWrongSupportElements( self: Self, paint: bool ) -> None:
        """Set whether to create arrays marking wrong support elements in output data.

        Args:
            paint (bool): True to enable marking, False to disable
        """
        self.paint_wrong_support_elements = paint

    def applyFilter( self: Self ) -> bool:
        """Apply the collocated nodes analysis.

        Returns:
            bool: True if analysis completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Find collocated nodes
            self.collocated_node_buckets = find_collocated_nodes_buckets( self.mesh, self.tolerance )
            self.logger.info( f"Found {len(self.collocated_node_buckets)} groups of collocated nodes" )

            # Find wrong support elements
            self.wrong_support_elements = find_wrong_support_elements( self.mesh )
            self.logger.info( f"Found {len(self.wrong_support_elements)} elements with wrong support" )

            # Add marking arrays if requested
            if self.paint_wrong_support_elements and self.wrong_support_elements:
                self._addWrongSupportElementsArray()

            self.logger.info( f"The filter {self.logger.name} succeeded" )
            return True

        except Exception as e:
            self.logger.error( f"Error in collocated nodes analysis: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed" )
            return False

    def _addWrongSupportElementsArray( self: Self ) -> None:
        """Add array marking wrong support elements."""
        num_cells = self.mesh.GetNumberOfCells()
        wrong_support_array = np.zeros( num_cells, dtype=np.int32 )

        for element_id in self.wrong_support_elements:
            if 0 <= element_id < num_cells:
                wrong_support_array[ element_id ] = 1

        vtk_array: vtkDataArray = numpy_to_vtk( wrong_support_array )
        vtk_array.SetName( "WrongSupportElements" )
        self.mesh.GetCellData().AddArray( vtk_array )

    def getCollocatedNodeBuckets( self: Self ) -> list[ tuple[ int ] ]:
        """Returns the nodes buckets that contain the duplicated node indices.

        Returns:
            list[tuple[int]]: Groups of collocated node indices
        """
        return self.collocated_node_buckets

    def getWrongSupportElements( self: Self ) -> list[ int ]:
        """Returns the element indices with support node indices appearing more than once.

        Returns:
            list[int]: Element indices with problematic support nodes
        """
        return self.wrong_support_elements


# Main function for backward compatibility and standalone use
def collocated_nodes(
    mesh: vtkUnstructuredGrid,
    tolerance: float = 0.0,
    paint_wrong_support_elements: bool = False,
    write_output: bool = False,
    output_path: str = "output/mesh_with_collocated_info.vtu",
) -> tuple[ vtkUnstructuredGrid, list[ tuple[ int ] ], list[ int ] ]:
    """Apply collocated nodes analysis to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh
        tolerance (float): Distance tolerance for detecting collocated nodes. Defaults to 0.0.
        paint_wrong_support_elements (bool): Whether to mark wrong support elements. Defaults to False.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, list[tuple[int]], list[int]]:
            Processed mesh, collocated node buckets, wrong support elements
    """
    filter_instance = CollocatedNodes( mesh, tolerance, paint_wrong_support_elements )
    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "Collocated nodes analysis failed" )

    if write_output:
        filter_instance.writeGrid( output_path )

    return (
        filter_instance.getMesh(),
        filter_instance.getCollocatedNodeBuckets(),
        filter_instance.getWrongSupportElements(),
    )


# Alias for backward compatibility
def processCollocatedNodes(
    mesh: vtkUnstructuredGrid,
    tolerance: float = 0.0,
    paint_wrong_support_elements: bool = False,
) -> tuple[ vtkUnstructuredGrid, list[ tuple[ int ] ], list[ int ] ]:
    """Legacy function name for backward compatibility."""
    return collocated_nodes( mesh, tolerance, paint_wrong_support_elements )
