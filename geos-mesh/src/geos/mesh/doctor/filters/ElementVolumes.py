import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector, vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter
from geos.mesh.doctor.filters.MeshDoctorBase import MeshDoctorBase

__doc__ = """
ElementVolumes module is a vtk filter that allows to calculate the volumes of every elements in a vtkUnstructuredGrid.

One filter input is vtkUnstructuredGrid one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.ElementVolumes import ElementVolumes

    # instanciate the filter
    elementVolumesFilter: ElementVolumes = ElementVolumes()

"""


class ElementVolumes( MeshDoctorBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to calculate the volume of every element of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )
        self.m_returnNegativeZeroVolumes: bool = False
        self.m_volumes: npt.NDArray = None

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

        cellSize = vtkCellSizeFilter()
        cellSize.ComputeAreaOff()
        cellSize.ComputeLengthOff()
        cellSize.ComputeSumOff()
        cellSize.ComputeVertexCountOff()
        cellSize.ComputeVolumeOn()
        volume_array_name: str = "MESH_DOCTOR_VOLUME"
        cellSize.SetVolumeArrayName( volume_array_name )

        cellSize.SetInputData( input_mesh )
        cellSize.Update()
        volumes: vtkDataArray = cellSize.GetOutput().GetCellData().GetArray( volume_array_name )
        self.m_volumes = volumes

        output_mesh: vtkUnstructuredGrid = input_mesh.NewInstance()
        output_mesh.CopyStructure( input_mesh )
        output_mesh.CopyAttributes( input_mesh )
        output_mesh.GetCellData().AddArray( volumes )
        output.ShallowCopy( output_mesh )

        if self.m_returnNegativeZeroVolumes:
            self.m_logger.info( "The following table displays the indexes of the cells with a zero or negative volume" )
            self.m_logger.info( self.getNegativeZeroVolumes() )

        return 1

    def getNegativeZeroVolumes( self: Self ) -> npt.NDArray:
        """Returns a numpy array of all the negative and zero volumes of the input vtkUnstructuredGrid.

        Args:
            self (Self)

        Returns:
            npt.NDArray
        """
        assert self.m_volumes is not None
        volumes_np: npt.NDArray = vtk_to_numpy( self.m_volumes )
        indices = np.where( volumes_np <= 0 )[ 0 ]
        return np.column_stack( ( indices, volumes_np[ indices ] ) )

    def setReturnNegativeZeroVolumes( self: Self, returnNegativeZeroVolumes: bool ) -> None:
        """Set the condition to return or not the negative and Zero volumes when calculating the volumes.

        Args:
            self (Self)
            returnNegativeZeroVolumes (bool)
        """
        self.m_returnNegativeZeroVolumes = returnNegativeZeroVolumes
        self.Modified()
