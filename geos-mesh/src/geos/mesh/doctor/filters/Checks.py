from types import SimpleNamespace
from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.all_checks import Options, get_check_results
from geos.mesh.doctor.filters.MeshDoctorBase import MeshDoctorBase
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import CheckFeature, display_results
from geos.mesh.doctor.parsing.all_checks_parsing import ( CHECK_FEATURES_CONFIG as cfc_all_checks,
                                                          ORDERED_CHECK_NAMES as ocn_all_checks )
from geos.mesh.doctor.parsing.main_checks_parsing import ( CHECK_FEATURES_CONFIG as cfc_main_checks,
                                                           ORDERED_CHECK_NAMES as ocn_main_checks )

__doc__ = """
AllChecks module is a vtk filter that ...

One filter input is vtkUnstructuredGrid, one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.AllChecks import AllChecks

    # instanciate the filter
    allChecksFilter: AllChecks = AllChecks()

"""


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

        # Build the options using the parsing logic structure
        options = self._buildOptions()
        self.m_check_results = get_check_results( input_mesh, options )

        results_wrapper = SimpleNamespace( check_results=self.m_check_results )
        display_results( options, results_wrapper )

        output_mesh: vtkUnstructuredGrid = self.copyInputToOutput( input_mesh )
        output.ShallowCopy( output_mesh )

        return 1

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
                final_check_params[ check_name ].update( self.m_check_parameters[ check_name ] )

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

        return Options( checks_to_perform=list( individual_check_options.keys() ),
                        checks_options=individual_check_options,
                        check_displays=individual_check_display )

    def getAvailableChecks( self: Self ) -> list[ str ]:
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

    def getDefaultParameters( self: Self, check_name: str ) -> dict[ str, any ]:
        """Get the default parameters for a specific check.

        Args:
            check_name (str): Name of the check

        Returns:
            dict[str, any]: Dictionary of default parameters
        """
        if check_name in self.m_CHECK_FEATURES_CONFIG:
            return self.m_CHECK_FEATURES_CONFIG[ check_name ].default_params
        return {}

    def setChecksToPerform( self: Self, checks_to_perform: list[ str ] ) -> None:
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
            self.m_check_parameters[ check_name ] = {}
        self.m_check_parameters[ check_name ][ parameter_name ] = value
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
                default_params = self.m_CHECK_FEATURES_CONFIG[ check_name ].default_params
                if parameter_name in default_params:
                    self.setCheckParameter( check_name, parameter_name, value )
        self.Modified()


class AllChecks( MeshDoctorChecks ):

    def __init__( self: Self ) -> None:
        """Vtk filter to ... of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__(
            checks_to_perform=ocn_all_checks,
            check_features_config=cfc_all_checks,
            ordered_check_names=ocn_all_checks
        )


class MainChecks( MeshDoctorChecks ):

    def __init__( self: Self ) -> None:
        """Vtk filter to ... of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__(
            checks_to_perform=ocn_main_checks,
            check_features_config=cfc_main_checks,
            ordered_check_names=ocn_main_checks
        )
