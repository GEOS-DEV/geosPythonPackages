from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.all_checks import get_check_results
from geos.mesh.doctor.parsing.cli_parsing import setup_logger
from geos.mesh.io.vtkIO import VtkOutput, write_mesh

__doc__ = """
AllChecks module is a vtk filter that ...

One filter input is vtkUnstructuredGrid, one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.AllChecks import AllChecks

    # instanciate the filter
    allChecksFilter: AllChecks = AllChecks()

"""


class AllChecks( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to ... of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )
        self.m_logger = setup_logger

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid" )
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()  # noqa: F841
        outInfo = outInfoVec.GetInformationObject( 0 )  # noqa: F841
        return 1

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

    def SetLogger( self: Self, logger ) -> None:
        """Set the logger.

        Args:
            logger
        """
        self.m_logger = logger
        self.Modified()

    def getGrid( self: Self ) -> vtkUnstructuredGrid:
        """Returns the vtkUnstructuredGrid with volumes.

        Args:
            self (Self)

        Returns:
            vtkUnstructuredGrid
        """
        self.Update()  # triggers RequestData
        return self.GetOutputDataObject( 0 )

    def writeGrid( self: Self, filepath: str, is_data_mode_binary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of the vtkUnstructuredGrid at the specified filepath with volumes.

        Args:
            filepath (str): /path/to/your/file.vtu
            is_data_mode_binary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        mesh: vtkUnstructuredGrid = self.getGrid()
        if mesh:
            write_mesh( filepath, VtkOutput( filepath, is_data_mode_binary ), canOverwrite )
        else:
            self.m_logger.error( f"No output grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )
