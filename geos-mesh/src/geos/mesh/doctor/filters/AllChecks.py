from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.all_checks import get_check_results
from geos.mesh.doctor.filters.BaseMeshDoctorFilter import BaseMeshDoctorFilter

__doc__ = """
AllChecks module is a vtk filter that ...

One filter input is vtkUnstructuredGrid, one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.AllChecks import AllChecks

    # instanciate the filter
    allChecksFilter: AllChecks = AllChecks()

"""


class AllChecks( BaseMeshDoctorFilter ):

    def __init__( self: Self ) -> None:
        """Vtk filter to ... of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )

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
        results: dict[ str, any ] = get_check_results( ... )
        output = vtkUnstructuredGrid.GetData( outInfo )

        output_mesh: vtkUnstructuredGrid = input_mesh.NewInstance()
        output_mesh.CopyStructure( input_mesh )
        output_mesh.CopyAttributes( input_mesh )
        output.ShallowCopy( output_mesh )

        return 1