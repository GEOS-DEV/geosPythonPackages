from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.parsing.cli_parsing import setup_logger
from geos.mesh.io.vtkIO import VtkOutput, write_mesh

__doc__ = """Base class for all mesh doctor VTK filters."""


class BaseMeshDoctorFilter( VTKPythonAlgorithmBase ):
    """Base class for all mesh doctor VTK filters.

    This class provides common functionality shared across all mesh doctor filters,
    including logger management, grid access, and file writing capabilities.
    """

    def __init__(
        self: Self,
        nInputPorts: int = 1,
        nOutputPorts: int = 1,
        inputType: str = 'vtkUnstructuredGrid',
        outputType: str = 'vtkUnstructuredGrid'
    ) -> None:
        """Initialize the base mesh doctor filter.

        Args:
            nInputPorts (int): Number of input ports. Defaults to 1.
            nOutputPorts (int): Number of output ports. Defaults to 1.
            inputType (str): Input data type. Defaults to 'vtkUnstructuredGrid'.
            outputType (str): Output data type. Defaults to 'vtkUnstructuredGrid'.
        """
        super().__init__(
            nInputPorts=nInputPorts,
            nOutputPorts=nOutputPorts,
            inputType=inputType if nInputPorts > 0 else None,
            outputType=outputType
        )
        self.m_logger = setup_logger

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::FillInputPortInformation.

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

    def SetLogger( self: Self, logger ) -> None:
        """Set the logger.

        Args:
            logger: Logger instance to use
        """
        self.m_logger = logger
        self.Modified()

    def getGrid( self: Self ) -> vtkUnstructuredGrid:
        """Returns the vtkUnstructuredGrid output.

        Args:
            self (Self)

        Returns:
            vtkUnstructuredGrid: The output grid
        """
        self.Update()  # triggers RequestData
        return self.GetOutputDataObject( 0 )

    def writeGrid( self: Self, filepath: str, is_data_mode_binary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of the vtkUnstructuredGrid at the specified filepath.

        Args:
            filepath (str): /path/to/your/file.vtu
            is_data_mode_binary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        mesh: vtkUnstructuredGrid = self.getGrid()
        if mesh:
            vtk_output = VtkOutput( filepath, is_data_mode_binary )
            write_mesh( mesh, vtk_output, canOverwrite )
        else:
            self.m_logger.error( f"No output grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )

    def copyInputToOutput( self: Self, input_mesh: vtkUnstructuredGrid ) -> vtkUnstructuredGrid:
        """Helper method to copy input mesh structure and attributes to a new output mesh.

        Args:
            input_mesh (vtkUnstructuredGrid): Input mesh to copy from

        Returns:
            vtkUnstructuredGrid: New mesh with copied structure and attributes
        """
        output_mesh: vtkUnstructuredGrid = input_mesh.NewInstance()
        output_mesh.CopyStructure( input_mesh )
        output_mesh.CopyAttributes( input_mesh )
        return output_mesh


class BaseMeshDoctorGeneratorFilter( BaseMeshDoctorFilter ):
    """Base class for mesh doctor generator filters (no input required).

    This class extends BaseMeshDoctorFilter for filters that generate meshes
    from scratch without requiring input meshes.
    """

    def __init__(
        self: Self,
        nOutputPorts: int = 1,
        outputType: str = 'vtkUnstructuredGrid'
    ) -> None:
        """Initialize the base mesh doctor generator filter.

        Args:
            nOutputPorts (int): Number of output ports. Defaults to 1.
            outputType (str): Output data type. Defaults to 'vtkUnstructuredGrid'.
        """
        super().__init__(
            nInputPorts=0,
            nOutputPorts=nOutputPorts,
            inputType=None,
            outputType=outputType
        )

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Generator filters don't have input ports.

        Args:
            port (int): input port (not used)
            info (vtkInformationVector): info (not used)

        Returns:
            int: Always returns 1
        """
        # Generator filters don't have input ports, so this method is not used
        return 1
