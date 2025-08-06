from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.all_checks import Options, Result
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import CheckFeature
from geos.mesh.doctor.parsing.cli_parsing import setup_logger
from geos.mesh.io.vtkIO import VtkOutput, write_mesh

__doc__ = """Base class for all mesh doctor VTK filters."""


class MeshDoctorBase( VTKPythonAlgorithmBase ):
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


class MeshDoctorGenerator( MeshDoctorBase ):
    """Base class for mesh doctor generator filters (no input required).

    This class extends MeshDoctorBase for filters that generate meshes
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


class MeshDoctorChecks( MeshDoctorBase ):

    def __init__(
        self: Self,
        checks_to_perform: list[ str ],
        check_features_config: dict[ str, CheckFeature ],
        ordered_check_names: list[ str ]
    ) -> None:
        super().__init__()
        self.m_checks_to_perform: list[ str ] = checks_to_perform
        self.m_check_parameters: dict[ str, dict[ str, any ] ] = dict()  # Custom parameters override
        self.m_check_results: dict[ str, any ] = dict()
        self.m_CHECK_FEATURES_CONFIG: dict[ str, CheckFeature ] = check_features_config
        self.m_ORDERED_CHECK_NAMES: list[ str ] = ordered_check_names

    def _buildOptions( self: Self ) -> Options:
        """Build Options object using the same logic as the parsing system.

        Returns:
            Options: Properly configured options for all checks
        """
        # Start with default parameters for all configured checks
        default_params: dict[ str, dict[ str, any ] ] = {
            name: feature.default_params.copy() for name, feature in self.m_CHECK_FEATURES_CONFIG.items()
        }
        final_check_params: dict[ str, dict[ str, any ] ] = {
            name: default_params[ name ] for name in self.m_checks_to_perform
        }

        # Apply any custom parameter overrides
        for check_name in self.m_checks_to_perform:
            if check_name in self.m_check_parameters:
                final_check_params[check_name].update(self.m_check_parameters[check_name])

        # Instantiate Options objects for the selected checks
        individual_check_options: dict[ str, any ] = dict()
        individual_check_display: dict[ str, any ] = dict()

        for check_name in self.m_checks_to_perform:
            if check_name not in self.m_CHECK_FEATURES_CONFIG:
                self.m_logger.warning(f"Check '{check_name}' is not available. Skipping.")
                continue

            params = final_check_params[ check_name ]
            feature_config = self.m_CHECK_FEATURES_CONFIG[ check_name ]
            try:
                individual_check_options[ check_name ] = feature_config.options_cls( **params )
                individual_check_display[ check_name ] = feature_config.display
            except Exception as e:
                self.m_logger.error( f"Failed to create options for check '{check_name}': {e}. "
                                     f"This check will be skipped." )

        return Options( checks_to_perform=list(individual_check_options.keys()),
                        checks_options=individual_check_options,
                        check_displays=individual_check_display )

    def getAvailableChecks( self: Self ) -> list[str]:
        """Returns the list of available check names.

        Returns:
            list[str]: List of available check names
        """
        return self.m_ORDERED_CHECK_NAMES

    def getCheckResults( self: Self ) -> dict[ str, any ]:
        """Returns the results of all performed checks.

        Args:
            self (Self)

        Returns:
            dict[str, any]: Dictionary mapping check names to their results
        """
        return self.m_check_results

    def getDefaultParameters( self: Self, check_name: str ) -> dict[str, any]:
        """Get the default parameters for a specific check.

        Args:
            check_name (str): Name of the check

        Returns:
            dict[str, any]: Dictionary of default parameters
        """
        if check_name in self.m_CHECK_FEATURES_CONFIG:
            return self.m_CHECK_FEATURES_CONFIG[check_name].default_params
        return {}

    def setChecksToPerform( self: Self, checks_to_perform: list[str] ) -> None:
        """Set which checks to perform.

        Args:
            self (Self)
            checks_to_perform (list[str]): List of check names to perform.
        """
        self.m_checks_to_perform = checks_to_perform
        self.Modified()

    def setCheckParameter( self: Self, check_name: str, parameter_name: str, value: any ) -> None:
        """Set a parameter for a specific check.

        Args:
            self (Self)
            check_name (str): Name of the check (e.g., "collocated_nodes")
            parameter_name (str): Name of the parameter (e.g., "tolerance")
            value (any): Value to set for the parameter
        """
        if check_name not in self.m_check_parameters:
            self.m_check_parameters[check_name] = {}
        self.m_check_parameters[check_name][parameter_name] = value
        self.Modified()

    def setAllChecksParameter( self: Self, parameter_name: str, value: any ) -> None:
        """Set a parameter for all checks that support it.

        Args:
            self (Self)
            parameter_name (str): Name of the parameter (e.g., "tolerance")
            value (any): Value to set for the parameter
        """
        for check_name in self.m_checks_to_perform:
            if check_name in self.m_CHECK_FEATURES_CONFIG:
                default_params = self.m_CHECK_FEATURES_CONFIG[check_name].default_params
                if parameter_name in default_params:
                    self.setCheckParameter(check_name, parameter_name, value)
        self.Modified()
