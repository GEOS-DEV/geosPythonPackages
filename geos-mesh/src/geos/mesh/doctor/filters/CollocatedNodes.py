import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector, vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.collocated_nodes import find_collocated_nodes_buckets, find_wrong_support_elements
from geos.mesh.doctor.filters.MeshDoctorBase import MeshDoctorBase

__doc__ = """
CollocatedNodes module is a vtk filter that allows to find the duplicated nodes of a vtkUnstructuredGrid.

One filter input is vtkUnstructuredGrid, one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.CollocatedNodes import CollocatedNodes

    # instanciate the filter
    collocatedNodesFilter: CollocatedNodes = CollocatedNodes()

"""


class CollocatedNodes( MeshDoctorBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to find the duplicated nodes of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )
        self.m_collocatedNodesBuckets: list[ tuple[ int ] ] = list()
        self.m_paintWrongSupportElements: int = 0
        self.m_tolerance: float = 0.0
        self.m_wrongSupportElements: list[ int ] = list()

    def RequestData(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfo: vtkInformationVector
    ) -> int:
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

        self.m_collocatedNodesBuckets = find_collocated_nodes_buckets( input_mesh, self.m_tolerance )
        self.m_wrongSupportElements = find_wrong_support_elements( input_mesh )

        self.m_logger.info( "The following list displays the nodes buckets that contains the duplicated node indices." )
        self.m_logger.info( self.getCollocatedNodeBuckets() )

        self.m_logger.info( "The following list displays the indexes of the cells with support node indices "
                            " appearing twice or more." )
        self.m_logger.info( self.getWrongSupportElements() )

        output_mesh: vtkUnstructuredGrid = input_mesh.NewInstance()
        output_mesh.CopyStructure( input_mesh )
        output_mesh.CopyAttributes( input_mesh )

        if self.m_paintWrongSupportElements:
            arrayWSP: npt.NDArray = np.zeros( ( output_mesh.GetNumberOfCells(), 1 ), dtype=int )
            arrayWSP[ self.m_wrongSupportElements ] = 1
            vtkArrayWSP: vtkDataArray = numpy_to_vtk( arrayWSP )
            vtkArrayWSP.SetName( "HasDuplicatedNodes" )
            output_mesh.GetCellData().AddArray( vtkArrayWSP )

        output.ShallowCopy( output_mesh )

        return 1

    def getCollocatedNodeBuckets( self: Self ) -> list[ tuple[ int ] ]:
        """Returns the nodes buckets that contains the duplicated node indices.

        Args:
            self (Self)

        Returns:
            list[ tuple[ int ] ]
        """
        return self.m_collocatedNodesBuckets

    def getWrongSupportElements( self: Self ) -> list[ int ]:
        """Returns the element indices with support node indices appearing more than once.

        Args:
            self (Self)

        Returns:
            list[ int ]
        """
        return self.m_wrongSupportElements

    def setPaintWrongSupportElements( self: Self, choice: int ) -> None:
        """Set 0 or 1 to choose if you want to create a new "WrongSupportElements" array in your output data.

        Args:
            self (Self)
            choice (int): 0 or 1
        """
        if choice not in [ 0, 1 ]:
            self.m_logger.error( f"setPaintWrongSupportElements: Please choose either 0 or 1 not '{choice}'." )
        else:
            self.m_paintWrongSupportElements = choice
            self.Modified()

    def setTolerance( self: Self, tolerance: float ) -> None:
        """Set the tolerance parameter to define if two points are collocated or not.

        Args:
            self (Self)
            tolerance (float)
        """
        self.m_tolerance = tolerance
        self.Modified()
