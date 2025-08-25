import numpy as np
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.self_intersecting_elements import get_invalid_cell_ids
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase

__doc__ = """
SelfIntersectingElements module identifies various types of invalid or problematic elements
in a vtkUnstructuredGrid. It detects elements with intersecting edges, intersecting faces, non-contiguous edges,
non-convex shapes, incorrectly oriented faces, and wrong number of points.

To use the filter:

.. code-block:: python

    from geos.mesh.doctor.filters.SelfIntersectingElements import SelfIntersectingElements

    # instantiate the filter
    selfIntersectingElementsFilter = SelfIntersectingElements(
        mesh,
        min_distance=1e-6,
        paint_invalid_elements=True
    )

    # execute the filter
    success = selfIntersectingElementsFilter.applyFilter()

    # get different types of problematic elements
    wrong_points_elements = selfIntersectingElementsFilter.getWrongNumberOfPointsElements()
    intersecting_edges_elements = selfIntersectingElementsFilter.getIntersectingEdgesElements()
    intersecting_faces_elements = selfIntersectingElementsFilter.getIntersectingFacesElements()
    non_contiguous_edges_elements = selfIntersectingElementsFilter.getNonContiguousEdgesElements()
    non_convex_elements = selfIntersectingElementsFilter.getNonConvexElements()
    wrong_oriented_faces_elements = selfIntersectingElementsFilter.getFacesOrientedIncorrectlyElements()

    # get the processed mesh
    output_mesh = selfIntersectingElementsFilter.getMesh()

    # write the output mesh
    selfIntersectingElementsFilter.writeGrid("output/mesh_with_invalid_elements.vtu")
"""

loggerTitle: str = "Self-Intersecting Elements Filter"


class SelfIntersectingElements( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        min_distance: float = 0.0,
        paint_invalid_elements: bool = False,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the self-intersecting elements detection filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze
            min_distance (float): Minimum distance parameter for intersection detection. Defaults to 0.0.
            paint_invalid_elements (bool): Whether to mark invalid elements in output. Defaults to False.
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, use_external_logger )
        self.min_distance: float = min_distance
        self.paint_invalid_elements: bool = paint_invalid_elements

        # Results storage
        self.wrong_number_of_points_elements: list[ int ] = []
        self.intersecting_edges_elements: list[ int ] = []
        self.intersecting_faces_elements: list[ int ] = []
        self.non_contiguous_edges_elements: list[ int ] = []
        self.non_convex_elements: list[ int ] = []
        self.faces_oriented_incorrectly_elements: list[ int ] = []

    def setMinDistance( self: Self, distance: float ) -> None:
        """Set the minimum distance parameter for intersection detection.

        Args:
            distance (float): Minimum distance value
        """
        self.min_distance = distance

    def setPaintInvalidElements( self: Self, paint: bool ) -> None:
        """Set whether to create arrays marking invalid elements in output data.

        Args:
            paint (bool): True to enable marking, False to disable
        """
        self.paint_invalid_elements = paint

    def getMinDistance( self: Self ) -> float:
        """Get the current minimum distance parameter.

        Returns:
            float: Minimum distance value
        """
        return self.min_distance

    def applyFilter( self: Self ) -> bool:
        """Apply the self-intersecting elements detection.

        Returns:
            bool: True if detection completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Get invalid cell IDs
            invalid_cells = get_invalid_cell_ids( self.mesh, self.min_distance )

            # Store results
            self.wrong_number_of_points_elements = invalid_cells.get( "wrong_number_of_points_elements", [] )
            self.intersecting_edges_elements = invalid_cells.get( "intersecting_edges_elements", [] )
            self.intersecting_faces_elements = invalid_cells.get( "intersecting_faces_elements", [] )
            self.non_contiguous_edges_elements = invalid_cells.get( "non_contiguous_edges_elements", [] )
            self.non_convex_elements = invalid_cells.get( "non_convex_elements", [] )
            self.faces_oriented_incorrectly_elements = invalid_cells.get( "faces_oriented_incorrectly_elements", [] )

            # Log the results
            total_invalid = sum( len( invalid_list ) for invalid_list in invalid_cells.values() )
            self.logger.info( f"Found {total_invalid} invalid elements:" )
            for criterion, cell_list in invalid_cells.items():
                if cell_list:
                    self.logger.info( f"  {criterion}: {len(cell_list)} elements - {cell_list}" )

            # Add marking arrays if requested
            if self.paint_invalid_elements:
                self._addInvalidElementsArrays( invalid_cells )

            self.logger.info( f"The filter {self.logger.name} succeeded" )
            return True

        except Exception as e:
            self.logger.error( f"Error in self-intersecting elements detection: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed" )
            return False

    def _addInvalidElementsArrays( self: Self, invalid_cells: dict[ str, list[ int ] ] ) -> None:
        """Add arrays marking different types of invalid elements."""
        num_cells = self.mesh.GetNumberOfCells()

        for criterion, cell_list in invalid_cells.items():
            if cell_list:
                array = np.zeros( num_cells, dtype=np.int32 )
                for cell_id in cell_list:
                    if 0 <= cell_id < num_cells:
                        array[ cell_id ] = 1

                vtk_array: vtkDataArray = numpy_to_vtk( array )
                # Convert criterion name to CamelCase for array name
                array_name = f"Is{criterion.replace('_', '').title()}"
                vtk_array.SetName( array_name )
                self.mesh.GetCellData().AddArray( vtk_array )

    def getWrongNumberOfPointsElements( self: Self ) -> list[ int ]:
        """Get elements with wrong number of points.

        Returns:
            list[int]: Element indices with wrong number of points
        """
        return self.wrong_number_of_points_elements

    def getIntersectingEdgesElements( self: Self ) -> list[ int ]:
        """Get elements with intersecting edges.

        Returns:
            list[int]: Element indices with intersecting edges
        """
        return self.intersecting_edges_elements

    def getIntersectingFacesElements( self: Self ) -> list[ int ]:
        """Get elements with intersecting faces.

        Returns:
            list[int]: Element indices with intersecting faces
        """
        return self.intersecting_faces_elements

    def getNonContiguousEdgesElements( self: Self ) -> list[ int ]:
        """Get elements with non-contiguous edges.

        Returns:
            list[int]: Element indices with non-contiguous edges
        """
        return self.non_contiguous_edges_elements

    def getNonConvexElements( self: Self ) -> list[ int ]:
        """Get non-convex elements.

        Returns:
            list[int]: Non-convex element indices
        """
        return self.non_convex_elements

    def getFacesOrientedIncorrectlyElements( self: Self ) -> list[ int ]:
        """Get elements with incorrectly oriented faces.

        Returns:
            list[int]: Element indices with incorrectly oriented faces
        """
        return self.faces_oriented_incorrectly_elements

    def getAllInvalidElements( self: Self ) -> dict[ str, list[ int ] ]:
        """Get all invalid elements organized by type.

        Returns:
            dict[str, list[int]]: Dictionary mapping invalid element types to their IDs
        """
        return {
            "wrong_number_of_points_elements": self.wrong_number_of_points_elements,
            "intersecting_edges_elements": self.intersecting_edges_elements,
            "intersecting_faces_elements": self.intersecting_faces_elements,
            "non_contiguous_edges_elements": self.non_contiguous_edges_elements,
            "non_convex_elements": self.non_convex_elements,
            "faces_oriented_incorrectly_elements": self.faces_oriented_incorrectly_elements,
        }


# Main function for backward compatibility and standalone use
def self_intersecting_elements(
    mesh: vtkUnstructuredGrid,
    min_distance: float = 0.0,
    paint_invalid_elements: bool = False,
    write_output: bool = False,
    output_path: str = "output/mesh_with_invalid_elements.vtu",
) -> tuple[ vtkUnstructuredGrid, dict[ str, list[ int ] ] ]:
    """Apply self-intersecting elements detection to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh
        min_distance (float): Minimum distance parameter for intersection detection. Defaults to 0.0.
        paint_invalid_elements (bool): Whether to mark invalid elements. Defaults to False.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, dict[str, list[int]]]:
            Processed mesh, dictionary of invalid element types and their IDs
    """
    filter_instance = SelfIntersectingElements( mesh, min_distance, paint_invalid_elements )
    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "Self-intersecting elements detection failed" )

    if write_output:
        filter_instance.writeGrid( output_path )

    return (
        filter_instance.getMesh(),
        filter_instance.getAllInvalidElements(),
    )


# Alias for backward compatibility
def processSelfIntersectingElements(
    mesh: vtkUnstructuredGrid,
    min_distance: float = 0.0,
) -> tuple[ vtkUnstructuredGrid, dict[ str, list[ int ] ] ]:
    """Legacy function name for backward compatibility."""
    return self_intersecting_elements( mesh, min_distance )
