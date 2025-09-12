import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector, vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.self_intersecting_elements import get_invalid_cell_ids
from geos.mesh.doctor.filters.MeshDoctorBase import MeshDoctorBase

__doc__ = """
SelfIntersectingElements module is a vtk filter that identifies various types of invalid or problematic elements
in a vtkUnstructuredGrid. It detects elements with intersecting edges, intersecting faces, non-contiguous edges,
non-convex shapes, incorrectly oriented faces, and wrong number of points.

One filter input is vtkUnstructuredGrid, one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.SelfIntersectingElements import SelfIntersectingElements

    # instantiate the filter
    selfIntersectingElementsFilter: SelfIntersectingElements = SelfIntersectingElements()

    # set minimum distance parameter for intersection detection
    selfIntersectingElementsFilter.setMinDistance(1e-6)

    # optionally enable painting of invalid elements
    selfIntersectingElementsFilter.setPaintInvalidElements(1)  # 1 to enable, 0 to disable

    # set input mesh
    selfIntersectingElementsFilter.SetInputData(mesh)

    # execute the filter
    output_mesh: vtkUnstructuredGrid = selfIntersectingElementsFilter.getGrid()

    # get different types of problematic elements
    wrong_points_elements = selfIntersectingElementsFilter.getWrongNumberOfPointsElements()
    intersecting_edges_elements = selfIntersectingElementsFilter.getIntersectingEdgesElements()
    intersecting_faces_elements = selfIntersectingElementsFilter.getIntersectingFacesElements()
    non_contiguous_edges_elements = selfIntersectingElementsFilter.getNonContiguousEdgesElements()
    non_convex_elements = selfIntersectingElementsFilter.getNonConvexElements()
    wrong_oriented_faces_elements = selfIntersectingElementsFilter.getFacesOrientedIncorrectlyElements()

    # write the output mesh
    selfIntersectingElementsFilter.writeGrid("output/mesh_with_invalid_elements.vtu")
"""


class SelfIntersectingElements( MeshDoctorBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to find invalid elements of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=1,
                          nOutputPorts=1,
                          inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )
        self.m_min_distance: float = 0.0
        self.m_wrong_number_of_points_elements: list[ int ] = list()
        self.m_intersecting_edges_elements: list[ int ] = list()
        self.m_intersecting_faces_elements: list[ int ] = list()
        self.m_non_contiguous_edges_elements: list[ int ] = list()
        self.m_non_convex_elements: list[ int ] = list()
        self.m_faces_oriented_incorrectly_elements: list[ int ] = list()
        self.m_paintInvalidElements: int = 0

    def RequestData( self: Self, request: vtkInformation, inInfoVec: list[ vtkInformationVector ],
                     outInfo: vtkInformationVector ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        input_mesh: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
        output = vtkUnstructuredGrid.GetData( outInfo )

        invalid_cells = get_invalid_cell_ids( input_mesh, self.m_min_distance )

        self.m_wrong_number_of_points_elements = invalid_cells.get( "wrong_number_of_points_elements", [] )
        self.m_intersecting_edges_elements = invalid_cells.get( "intersecting_edges_elements", [] )
        self.m_intersecting_faces_elements = invalid_cells.get( "intersecting_faces_elements", [] )
        self.m_non_contiguous_edges_elements = invalid_cells.get( "non_contiguous_edges_elements", [] )
        self.m_non_convex_elements = invalid_cells.get( "non_convex_elements", [] )
        self.m_faces_oriented_incorrectly_elements = invalid_cells.get( "faces_oriented_incorrectly_elements", [] )

        # Log the results
        total_invalid = sum( len( invalid_list ) for invalid_list in invalid_cells.values() )
        self.m_logger.info( f"Found {total_invalid} invalid elements:" )
        for criterion, cell_list in invalid_cells.items():
            if cell_list:
                self.m_logger.info( f"  {criterion}: {len( cell_list )} elements - {cell_list}" )

        output_mesh: vtkUnstructuredGrid = input_mesh.NewInstance()
        output_mesh.CopyStructure( input_mesh )
        output_mesh.CopyAttributes( input_mesh )

        if self.m_paintInvalidElements:
            # Create arrays to mark invalid elements
            for criterion, cell_list in invalid_cells.items():
                if cell_list:
                    array: npt.NDArray = np.zeros( ( output_mesh.GetNumberOfCells(), 1 ), dtype=int )
                    array[ cell_list ] = 1
                    vtkArray: vtkDataArray = numpy_to_vtk( array )
                    vtkArray.SetName( f"Is{criterion.replace('_', '').title()}" )
                    output_mesh.GetCellData().AddArray( vtkArray )

        output.ShallowCopy( output_mesh )

        return 1

    def getMinDistance( self: Self ) -> float:
        """Returns the minimum distance.

        Args:
            self (Self)

        Returns:
            float
        """
        return self.m_min_distance

    def getWrongNumberOfPointsElements( self: Self ) -> list[ int ]:
        """Returns elements with wrong number of points.

        Args:
            self (Self)

        Returns:
            list[int]
        """
        return self.m_wrong_number_of_points_elements

    def getIntersectingEdgesElements( self: Self ) -> list[ int ]:
        """Returns elements with intersecting edges.

        Args:
            self (Self)

        Returns:
            list[int]
        """
        return self.m_intersecting_edges_elements

    def getIntersectingFacesElements( self: Self ) -> list[ int ]:
        """Returns elements with intersecting faces.

        Args:
            self (Self)

        Returns:
            list[int]
        """
        return self.m_intersecting_faces_elements

    def getNonContiguousEdgesElements( self: Self ) -> list[ int ]:
        """Returns elements with non-contiguous edges.

        Args:
            self (Self)

        Returns:
            list[int]
        """
        return self.m_non_contiguous_edges_elements

    def getNonConvexElements( self: Self ) -> list[ int ]:
        """Returns non-convex elements.

        Args:
            self (Self)

        Returns:
            list[int]
        """
        return self.m_non_convex_elements

    def getFacesOrientedIncorrectlyElements( self: Self ) -> list[ int ]:
        """Returns elements with incorrectly oriented faces.

        Args:
            self (Self)

        Returns:
            list[int]
        """
        return self.m_faces_oriented_incorrectly_elements

    def setPaintInvalidElements( self: Self, choice: int ) -> None:
        """Set 0 or 1 to choose if you want to create arrays marking invalid elements in your output data.

        Args:
            self (Self)
            choice (int): 0 or 1
        """
        if choice not in [ 0, 1 ]:
            self.m_logger.error( f"setPaintInvalidElements: Please choose either 0 or 1 not '{choice}'." )
        else:
            self.m_paintInvalidElements = choice
            self.Modified()

    def setMinDistance( self: Self, distance: float ) -> None:
        """Set the minimum distance parameter.

        Args:
            self (Self)
            distance (float)
        """
        self.m_min_distance = distance
        self.Modified()
