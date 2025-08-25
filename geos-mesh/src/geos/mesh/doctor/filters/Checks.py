from types import SimpleNamespace
from typing import Any
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.all_checks import Options, get_check_results
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import CheckFeature, display_results
from geos.mesh.doctor.parsing.all_checks_parsing import ( CHECK_FEATURES_CONFIG as cfc_all_checks, ORDERED_CHECK_NAMES
                                                          as ocn_all_checks )
from geos.mesh.doctor.parsing.main_checks_parsing import ( CHECK_FEATURES_CONFIG as cfc_main_checks, ORDERED_CHECK_NAMES
                                                           as ocn_main_checks )

__doc__ = """
Checks module performs comprehensive mesh validation checks on a vtkUnstructuredGrid.
This module contains AllChecks and MainChecks filters that run various quality checks including element validation,
node validation, topology checks, and geometric integrity verification.

To use the AllChecks filter:

.. code-block:: python

    from geos.mesh.doctor.filters.Checks import AllChecks

    # instantiate the filter for all available checks
    allChecksFilter = AllChecks(mesh)

    # optionally customize check parameters
    allChecksFilter.setCheckParameter("collocated_nodes", "tolerance", 1e-6)
    allChecksFilter.setAllChecksParameter("tolerance", 1e-6)  # applies to all checks with tolerance parameter

    # execute the checks
    success = allChecksFilter.applyFilter()

    # get check results
    check_results = allChecksFilter.getCheckResults()

    # get the processed mesh
    output_mesh = allChecksFilter.getMesh()

To use the MainChecks filter (subset of most important checks):

.. code-block:: python

    from geos.mesh.doctor.filters.Checks import MainChecks

    # instantiate the filter for main checks only
    mainChecksFilter = MainChecks(mesh)

    # execute the checks
    success = mainChecksFilter.applyFilter()
"""

loggerTitle: str = "Mesh Doctor Checks Filter"


class MeshDoctorChecks( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        checks_to_perform: list[ str ],
        check_features_config: dict[ str, CheckFeature ],
        ordered_check_names: list[ str ],
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the mesh doctor checks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check
            checks_to_perform (list[str]): List of check names to perform
            check_features_config (dict[str, CheckFeature]): Configuration for check features
            ordered_check_names (list[str]): Ordered list of available check names
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, use_external_logger )
        self.checks_to_perform: list[ str ] = checks_to_perform
        self.check_parameters: dict[ str, dict[ str, Any ] ] = {}  # Custom parameters override
        self.check_results: dict[ str, Any ] = {}
        self.check_features_config: dict[ str, CheckFeature ] = check_features_config
        self.ordered_check_names: list[ str ] = ordered_check_names

    def setChecksToPerform( self: Self, checks_to_perform: list[ str ] ) -> None:
        """Set which checks to perform.

        Args:
            checks_to_perform (list[str]): List of check names to perform
        """
        self.checks_to_perform = checks_to_perform

    def setCheckParameter( self: Self, check_name: str, parameter_name: str, value: Any ) -> None:
        """Set a parameter for a specific check.

        Args:
            check_name (str): Name of the check (e.g., "collocated_nodes")
            parameter_name (str): Name of the parameter (e.g., "tolerance")
            value (Any): Value to set for the parameter
        """
        if check_name not in self.check_parameters:
            self.check_parameters[ check_name ] = {}
        self.check_parameters[ check_name ][ parameter_name ] = value

    def setAllChecksParameter( self: Self, parameter_name: str, value: Any ) -> None:
        """Set a parameter for all checks that support it.

        Args:
            parameter_name (str): Name of the parameter (e.g., "tolerance")
            value (Any): Value to set for the parameter
        """
        for check_name in self.checks_to_perform:
            if check_name in self.check_features_config:
                default_params = self.check_features_config[ check_name ].default_params
                if parameter_name in default_params:
                    self.setCheckParameter( check_name, parameter_name, value )

    def applyFilter( self: Self ) -> bool:
        """Apply the mesh validation checks.

        Returns:
            bool: True if checks completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Build the options using the parsing logic structure
            options = self._buildOptions()
            self.check_results = get_check_results( self.mesh, options )

            # Display results using the standard display logic
            results_wrapper = SimpleNamespace( check_results=self.check_results )
            display_results( options, results_wrapper )

            self.logger.info( f"Performed {len(self.check_results)} checks" )
            self.logger.info( f"The filter {self.logger.name} succeeded" )
            return True

        except Exception as e:
            self.logger.error( f"Error in mesh checks: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed" )
            return False

    def _buildOptions( self: Self ) -> Options:
        """Build Options object using the same logic as the parsing system.

        Returns:
            Options: Properly configured options for all checks
        """
        # Start with default parameters for all configured checks
        default_params: dict[ str, dict[ str, Any ] ] = {
            name: feature.default_params.copy()
            for name, feature in self.check_features_config.items()
        }
        final_check_params: dict[ str, dict[ str, Any ] ] = {
            name: default_params[ name ]
            for name in self.checks_to_perform
        }

        # Apply any custom parameter overrides
        for check_name in self.checks_to_perform:
            if check_name in self.check_parameters:
                final_check_params[ check_name ].update( self.check_parameters[ check_name ] )

        # Instantiate Options objects for the selected checks
        individual_check_options: dict[ str, Any ] = {}
        individual_check_display: dict[ str, Any ] = {}

        for check_name in self.checks_to_perform:
            if check_name not in self.check_features_config:
                self.logger.warning( f"Check '{check_name}' is not available. Skipping." )
                continue

            params = final_check_params[ check_name ]
            feature_config = self.check_features_config[ check_name ]
            try:
                individual_check_options[ check_name ] = feature_config.options_cls( **params )
                individual_check_display[ check_name ] = feature_config.display
            except Exception as e:
                self.logger.error( f"Failed to create options for check '{check_name}': {e}. "
                                   f"This check will be skipped." )

        return Options( checks_to_perform=list( individual_check_options.keys() ),
                        checks_options=individual_check_options,
                        check_displays=individual_check_display )

    def getAvailableChecks( self: Self ) -> list[ str ]:
        """Get the list of available check names.

        Returns:
            list[str]: List of available check names
        """
        return self.ordered_check_names

    def getCheckResults( self: Self ) -> dict[ str, Any ]:
        """Get the results of all performed checks.

        Returns:
            dict[str, Any]: Dictionary mapping check names to their results
        """
        return self.check_results

    def getDefaultParameters( self: Self, check_name: str ) -> dict[ str, Any ]:
        """Get the default parameters for a specific check.

        Args:
            check_name (str): Name of the check

        Returns:
            dict[str, Any]: Dictionary of default parameters
        """
        if check_name in self.check_features_config:
            return self.check_features_config[ check_name ].default_params
        return {}


class AllChecks( MeshDoctorChecks ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the all checks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh,
                          checks_to_perform=ocn_all_checks,
                          check_features_config=cfc_all_checks,
                          ordered_check_names=ocn_all_checks,
                          use_external_logger=use_external_logger )


class MainChecks( MeshDoctorChecks ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the main checks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh,
                          checks_to_perform=ocn_main_checks,
                          check_features_config=cfc_main_checks,
                          ordered_check_names=ocn_main_checks,
                          use_external_logger=use_external_logger )


# Main functions for backward compatibility and standalone use
def all_checks(
    mesh: vtkUnstructuredGrid,
    custom_parameters: dict[ str, dict[ str, Any ] ] = None,
    write_output: bool = False,
    output_path: str = "output/mesh_all_checks.vtu",
) -> tuple[ vtkUnstructuredGrid, dict[ str, Any ] ]:
    """Apply all available mesh checks to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh
        custom_parameters (dict[str, dict[str, Any]]): Custom parameters for checks. Defaults to None.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, dict[str, Any]]:
            Processed mesh, check results
    """
    filter_instance = AllChecks( mesh )

    if custom_parameters:
        for check_name, params in custom_parameters.items():
            for param_name, value in params.items():
                filter_instance.setCheckParameter( check_name, param_name, value )

    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "All checks execution failed" )

    if write_output:
        filter_instance.writeGrid( output_path )

    return (
        filter_instance.getMesh(),
        filter_instance.getCheckResults(),
    )


def main_checks(
    mesh: vtkUnstructuredGrid,
    custom_parameters: dict[ str, dict[ str, Any ] ] = None,
    write_output: bool = False,
    output_path: str = "output/mesh_main_checks.vtu",
) -> tuple[ vtkUnstructuredGrid, dict[ str, Any ] ]:
    """Apply main mesh checks to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh
        custom_parameters (dict[str, dict[str, Any]]): Custom parameters for checks. Defaults to None.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, dict[str, Any]]:
            Processed mesh, check results
    """
    filter_instance = MainChecks( mesh )

    if custom_parameters:
        for check_name, params in custom_parameters.items():
            for param_name, value in params.items():
                filter_instance.setCheckParameter( check_name, param_name, value )

    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "Main checks execution failed" )

    if write_output:
        filter_instance.writeGrid( output_path )

    return (
        filter_instance.getMesh(),
        filter_instance.getCheckResults(),
    )


# Aliases for backward compatibility
def processAllChecks(
    mesh: vtkUnstructuredGrid,
    custom_parameters: dict[ str, dict[ str, Any ] ] = None,
) -> tuple[ vtkUnstructuredGrid, dict[ str, Any ] ]:
    """Legacy function name for backward compatibility."""
    return all_checks( mesh, custom_parameters )


def processMainChecks(
    mesh: vtkUnstructuredGrid,
    custom_parameters: dict[ str, dict[ str, Any ] ] = None,
) -> tuple[ vtkUnstructuredGrid, dict[ str, Any ] ]:
    """Legacy function name for backward compatibility."""
    return main_checks( mesh, custom_parameters )
