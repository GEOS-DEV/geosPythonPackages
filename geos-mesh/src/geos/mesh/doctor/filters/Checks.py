from types import SimpleNamespace
from typing import Any
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.all_checks import Options, get_check_results
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import CheckFeature, display_results
from geos.mesh.doctor.parsing.all_checks_parsing import ( CHECK_FEATURES_CONFIG as cfc_all_checks, ORDERED_CHECK_NAMES
                                                          as ocn_all_checks )
from geos.mesh.doctor.parsing.main_checks_parsing import ( CHECK_FEATURES_CONFIG as cfcMainChecks, ORDERED_CHECK_NAMES
                                                           as ocnMainChecks )

__doc__ = """
Checks module performs comprehensive mesh validation checks on a vtkUnstructuredGrid.
This module contains AllChecks and MainChecks filters that run various quality checks including element validation,
node validation, topology checks, and geometric integrity verification.

To use the AllChecks filter
---------------------------

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
    checkResults = allChecksFilter.getCheckResults()

    # get the processed mesh
    output_mesh = allChecksFilter.getMesh()

To use the MainChecks filter (subset of most important checks)
--------------------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.Checks import MainChecks

    # instantiate the filter for main checks only
    mainChecksFilter = MainChecks(mesh)

    # execute the checks
    success = mainChecksFilter.applyFilter()

    # get check results
    checkResults = mainChecksFilter.getCheckResults()

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.Checks import allChecks, mainChecks

    # apply all checks directly
    outputMesh, checkResults = allChecks(
        mesh,
        customParameters={"collocated_nodes": {"tolerance": 1e-6}}
    )

    # or apply main checks only
    outputMesh, checkResults = mainChecks(
        mesh,
        customParameters={"element_volumes": {"minVolume": 0.0}}
    )
"""

loggerTitle: str = "Mesh Doctor Checks Filter"


class Checks( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        checksToPerform: list[ str ],
        checkFeaturesConfig: dict[ str, CheckFeature ],
        orderedCheckNames: list[ str ],
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the mesh doctor checks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check
            checksToPerform (list[str]): List of check names to perform
            checkFeaturesConfig (dict[str, CheckFeature]): Configuration for check features
            orderedCheckNames (list[str]): Ordered list of available check names
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, useExternalLogger )
        self.checksToPerform: list[ str ] = checksToPerform
        self.checkParameters: dict[ str, dict[ str, Any ] ] = {}  # Custom parameters override
        self.checkResults: dict[ str, Any ] = {}
        self.checkFeaturesConfig: dict[ str, CheckFeature ] = checkFeaturesConfig
        self.orderedCheckNames: list[ str ] = orderedCheckNames

    def applyFilter( self: Self ) -> bool:
        """Apply the mesh validation checks.

        Returns:
            bool: True if checks completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        # Build the options using the parsing logic structure
        options = self._buildOptions()
        self.checkResults = get_check_results( self.mesh, options )

        # Display results using the standard display logic
        resultsWrapper = SimpleNamespace( checkResults=self.checkResults )
        display_results( options, resultsWrapper )

        self.logger.info( f"Performed {len(self.checkResults)} checks" )
        self.logger.info( f"The filter {self.logger.name} succeeded" )
        return True

    def getAvailableChecks( self: Self ) -> list[ str ]:
        """Get the list of available check names.

        Returns:
            list[str]: List of available check names
        """
        return self.orderedCheckNames

    def getCheckResults( self: Self ) -> dict[ str, Any ]:
        """Get the results of all performed checks.

        Returns:
            dict[str, Any]: Dictionary mapping check names to their results.
        """
        return self.checkResults

    def getDefaultParameters( self: Self, checkName: str ) -> dict[ str, Any ]:
        """Get the default parameters for a specific check.

        Args:
            checkName (str): Name of the check.

        Returns:
            dict[str, Any]: Dictionary of default parameters.
        """
        if checkName in self.checkFeaturesConfig:
            return self.checkFeaturesConfig[ checkName ].default_params
        return {}

    def setAllChecksParameter( self: Self, parameterName: str, value: Any ) -> None:
        """Set a parameter for all checks that support it.

        Args:
            parameterName (str): Name of the parameter (e.g., "tolerance")
            value (Any): Value to set for the parameter
        """
        for checkName in self.checksToPerform:
            if checkName in self.checkFeaturesConfig:
                defaultParams = self.checkFeaturesConfig[ checkName ].default_params
                if parameterName in defaultParams:
                    self.setCheckParameter( checkName, parameterName, value )

    def setCheckParameter( self: Self, checkName: str, parameterName: str, value: Any ) -> None:
        """Set a parameter for a specific check.

        Args:
            checkName (str): Name of the check (e.g., "collocated_nodes")
            parameterName (str): Name of the parameter (e.g., "tolerance")
            value (Any): Value to set for the parameter
        """
        if checkName not in self.checkParameters:
            self.checkParameters[ checkName ] = {}
        self.checkParameters[ checkName ][ parameterName ] = value

    def setChecksToPerform( self: Self, checksToPerform: list[ str ] ) -> None:
        """Set which checks to perform.

        Args:
            checksToPerform (list[str]): List of check names to perform
        """
        self.checksToPerform = checksToPerform

    def _buildOptions( self: Self ) -> Options:
        """Build Options object using the same logic as the parsing system.

        Returns:
            Options: Properly configured options for all checks.
        """
        # Start with default parameters for all configured checks
        defaultParams: dict[ str, dict[ str, Any ] ] = {
            name: feature.default_params.copy()
            for name, feature in self.checkFeaturesConfig.items()
        }
        finalCheckParams: dict[ str, dict[ str, Any ] ] = {
            name: defaultParams[ name ]
            for name in self.checksToPerform
        }

        # Apply any custom parameter overrides
        for checkName in self.checksToPerform:
            if checkName in self.checkParameters:
                finalCheckParams[ checkName ].update( self.checkParameters[ checkName ] )

        # Instantiate Options objects for the selected checks
        individualCheckOptions: dict[ str, Any ] = {}
        individualCheckDisplay: dict[ str, Any ] = {}

        for checkName in self.checksToPerform:
            if checkName not in self.checkFeaturesConfig:
                self.logger.warning( f"Check '{checkName}' is not available. Skipping." )
                continue

            params = finalCheckParams[ checkName ]
            featureConfig = self.checkFeaturesConfig[ checkName ]
            try:
                individualCheckOptions[ checkName ] = featureConfig.options_cls( **params )
                individualCheckDisplay[ checkName ] = featureConfig.display
            except Exception as e:
                self.logger.error( f"Failed to create options for check '{checkName}': {e}. "
                                   f"This check will be skipped." )

        return Options( checks_to_perform=list( individualCheckOptions.keys() ),
                        checks_options=individualCheckOptions,
                        check_displays=individualCheckDisplay )


class AllChecks( Checks ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the all_checks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh,
                          checksToPerform=ocn_all_checks,
                          checkFeaturesConfig=cfc_all_checks,
                          orderedCheckNames=ocn_all_checks,
                          useExternalLogger=useExternalLogger )


class MainChecks( Checks ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the main checks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh,
                          checksToPerform=ocnMainChecks,
                          checkFeaturesConfig=cfcMainChecks,
                          orderedCheckNames=ocnMainChecks,
                          useExternalLogger=useExternalLogger )


# Main functions for backward compatibility and standalone use
def allChecks(
        mesh: vtkUnstructuredGrid,
        customParameters: dict[ str, dict[ str, Any ] ] = None ) -> tuple[ vtkUnstructuredGrid, dict[ str, Any ] ]:
    """Apply all available mesh checks to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to check.
        customParameters (dict[str, dict[str, Any]]): Custom parameters for checks. Defaults to None.

    Returns:
        tuple[vtkUnstructuredGrid, dict[str, Any]]:
            Processed mesh, check results
    """
    filterInstance = AllChecks( mesh )

    if customParameters:
        for checkName, params in customParameters.items():
            for param_name, value in params.items():
                filterInstance.setCheckParameter( checkName, param_name, value )

    success = filterInstance.applyFilter()
    if not success:
        raise RuntimeError( "allChecks calculation failed." )

    return (
        filterInstance.getMesh(),
        filterInstance.getCheckResults(),
    )


def mainChecks(
        mesh: vtkUnstructuredGrid,
        customParameters: dict[ str, dict[ str, Any ] ] = None ) -> tuple[ vtkUnstructuredGrid, dict[ str, Any ] ]:
    """Apply main mesh checks to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to check.
        customParameters (dict[str, dict[str, Any]]): Custom parameters for checks. Defaults to None.

    Returns:
        tuple[vtkUnstructuredGrid, dict[str, Any]]:
            Processed mesh, check results
    """
    filterInstance = MainChecks( mesh )

    if customParameters:
        for checkName, params in customParameters.items():
            for param_name, value in params.items():
                filterInstance.setCheckParameter( checkName, param_name, value )

    success = filterInstance.applyFilter()
    if not success:
        raise RuntimeError( "mainChecks calculation failed." )

    return (
        filterInstance.getMesh(),
        filterInstance.getCheckResults(),
    )
