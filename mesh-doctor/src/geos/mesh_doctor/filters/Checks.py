from typing import Any, Optional
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh_doctor.actions.allChecks import CheckResults, Options, meshAction
from geos.mesh_doctor.baseTypes import DefaultParameters, OptionsProtocol, UserParameters
from geos.mesh_doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import CheckFeature, displayResults
from geos.mesh_doctor.parsing.allChecksParsing import ( CHECK_FEATURES_CONFIG as cfcAllChecks, ORDERED_CHECK_NAMES as
                                                        ocnAllChecks )
from geos.mesh_doctor.parsing.mainChecksParsing import ( CHECK_FEATURES_CONFIG as cfcMainChecks, ORDERED_CHECK_NAMES as
                                                         ocnMainChecks )

__doc__ = """
Checks module performs comprehensive mesh validation checks on a vtkUnstructuredGrid.
This module contains AllChecks and MainChecks filters that run various quality checks including element validation,
node validation, topology checks, and geometric integrity verification.

To use the AllChecks filter
---------------------------

.. code-block:: python

    from geos.mesh_doctor.filters.Checks import AllChecks

    # instantiate the filter for all available checks
    allChecksFilter = AllChecks(mesh)

    # optionally customize check parameters
    allChecksFilter.setCheckParameter("collocated_nodes", "tolerance", 1e-6)
    allChecksFilter.setAllChecksParameter("tolerance", 1e-6)  # applies to all checks with tolerance parameter

    # execute the checks
    success = allChecksFilter.applyFilter()

    # get check results
    results = allChecksFilter.getResults()

    # get the processed mesh
    outputMesh = allChecksFilter.mesh

To use the MainChecks filter (subset of most important checks)
--------------------------------------------------------------

.. code-block:: python

    from geos.mesh_doctor.filters.Checks import MainChecks

    # instantiate the filter for main checks only
    mainChecksFilter = MainChecks(mesh)

    # execute the checks
    success = mainChecksFilter.applyFilter()

    # get check results
    results = mainChecksFilter.getResults()

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh_doctor.filters.Checks import allChecks, mainChecks

    # apply all checks directly
    outputMesh, results = allChecks(
        mesh,
        customParameters={"collocated_nodes": {"tolerance": 1e-6}}
    )

    # or apply main checks only
    outputMesh, results = mainChecks(
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
        speHandler: bool = False,
    ) -> None:
        """Initialize the mesh doctor checks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check.
            checksToPerform (list[str]): List of check names to perform.
            checkFeaturesConfig (dict[str, CheckFeature]): Configuration for check features.
            orderedCheckNames (list[str]): Ordered list of available check names.
            speHandler (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, speHandler )
        self.checksToPerform: list[ str ] = checksToPerform
        self.checkParameters: dict[ str, UserParameters ] = {}  # Custom parameters override
        self.results: CheckResults = {}
        self.checkFeaturesConfig: dict[ str, CheckFeature ] = checkFeaturesConfig
        self.orderedCheckNames: list[ str ] = orderedCheckNames

    def applyFilter( self: Self ) -> None:
        """Apply the mesh validation checks.

        Returns:
            bool: True if checks completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        # Build the options using the parsing logic structure
        options: Options = self._buildOptions()
        result = meshAction( self.mesh, options )
        self.results = result.checkResults

        # Display results using the standard display logic
        displayResults( options, result )

        self.logger.info( f"Performed {len(self.results)} checks" )
        self.logger.info( f"The filter {self.logger.name} succeeded" )
        return

    def getAvailableChecks( self: Self ) -> list[ str ]:
        """Get the list of available check names.

        Returns:
            list[str]: List of available check names.
        """
        return self.orderedCheckNames

    def getCheckDefaultParameters( self: Self, checkName: str ) -> DefaultParameters:
        """Get the default parameters for a specific check.

        Args:
            checkName (str): Name of the check.

        Returns:
            DefaultParameters: Dictionary of default parameters.
        """
        if checkName in self.checkFeaturesConfig:
            return self.checkFeaturesConfig[ checkName ].defaultParams
        return {}

    def getResults( self: Self ) -> CheckResults:
        """Get the results of all performed checks.

        Returns:
            dict[str, ResultProtocol]: Dictionary mapping check names to their results.
        """
        return self.results

    def setAllChecksParameter( self: Self, parameterName: str, value: Any ) -> None:
        """Set a parameter for all checks that support it.

        Args:
            parameterName (str): Name of the parameter (e.g., "tolerance").
            value (Any): Value to set for the parameter.
        """
        for checkName in self.checksToPerform:
            if checkName in self.checkFeaturesConfig:
                defaultParams = self.checkFeaturesConfig[ checkName ].defaultParams
                if parameterName in defaultParams:
                    self.setCheckParameter( checkName, parameterName, value )

    def setCheckParameter( self: Self, checkName: str, parameterName: str, value: Any ) -> None:
        """Set a parameter for a specific check.

        Args:
            checkName (str): Name of the check (e.g., "collocated_nodes").
            parameterName (str): Name of the parameter (e.g., "tolerance").
            value (Any): Value to set for the parameter.
        """
        if checkName not in self.checkParameters:
            self.checkParameters[ checkName ] = {}
        self.checkParameters[ checkName ][ parameterName ] = value

    def setChecksToPerform( self: Self, checksToPerform: list[ str ] ) -> None:
        """Set which checks to perform.

        Args:
            checksToPerform (list[str]): List of check names to perform.
        """
        self.checksToPerform = checksToPerform

    def _buildOptions( self: Self ) -> Options:
        """Build Options object using the same logic as the parsing system.

        Returns:
            Options: Properly configured options for all checks.
        """
        # Start with default parameters for all configured checks
        allDefaultParams: dict[ str, DefaultParameters ] = {
            name: feature.defaultParams.copy()
            for name, feature in self.checkFeaturesConfig.items()
        }

        # Filter out invalid checks and build parameters only for valid ones
        validChecksToPerform: list[ str ] = []
        finalCheckParams: dict[ str, dict[ str, Any ] ] = {}

        for checkName in self.checksToPerform:
            if checkName not in self.checkFeaturesConfig:
                self.logger.warning( f"Check '{checkName}' is not available. Skipping." )
                continue
            validChecksToPerform.append( checkName )
            finalCheckParams[ checkName ] = allDefaultParams[ checkName ].copy()

        # Apply any custom parameter overrides
        for checkName in validChecksToPerform:
            if checkName in self.checkParameters:
                finalCheckParams[ checkName ].update( self.checkParameters[ checkName ] )

        # Instantiate Options objects for the selected checks
        individualCheckOptions: dict[ str, OptionsProtocol ] = {}
        individualCheckDisplay: dict[ str, Any ] = {}

        for checkName in validChecksToPerform:
            params = finalCheckParams[ checkName ]
            featureConfig = self.checkFeaturesConfig[ checkName ]
            try:
                individualCheckOptions[ checkName ] = featureConfig.optionsCls( **params )
                individualCheckDisplay[ checkName ] = featureConfig.display
            except Exception as e:
                self.logger.error( f"Failed to create options for check '{checkName}': {e}. "
                                   f"This check will be skipped." )

        return Options( checksToPerform=list( individualCheckOptions.keys() ),
                        checksOptions=individualCheckOptions,
                        checkDisplays=individualCheckDisplay )


class AllChecks( Checks ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        speHandler: bool = False,
    ) -> None:
        """Initialize the AllChecks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check.
            speHandler (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh,
                          checksToPerform=ocnAllChecks,
                          checkFeaturesConfig=cfcAllChecks,
                          orderedCheckNames=ocnAllChecks,
                          speHandler=speHandler )


class MainChecks( Checks ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        speHandler: bool = False,
    ) -> None:
        """Initialize the MainChecks filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to check.
            speHandler (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh,
                          checksToPerform=ocnMainChecks,
                          checkFeaturesConfig=cfcMainChecks,
                          orderedCheckNames=ocnMainChecks,
                          speHandler=speHandler )


# Main functions for backward compatibility and standalone use
def allChecks(
    mesh: vtkUnstructuredGrid,
    customParameters: Optional[ dict[ str, UserParameters ] ] = None,
) -> tuple[ vtkUnstructuredGrid, CheckResults ]:
    """Apply all available mesh checks to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to check.
        customParameters (dict[str, UserParameters]): Custom parameters for checks. Defaults to None.

    Returns:
        tuple[vtkUnstructuredGrid, CheckResults]:
            Processed mesh, check results
    """
    filterInstance = AllChecks( mesh )

    if customParameters is None:
        customParameters = {}
    elif not isinstance( customParameters, dict ):
        raise TypeError( "customParameters must be a dictionary mapping check names to parameter dictionaries." )
    else:
        for checkName, params in customParameters.items():
            for paramName, value in params.items():
                filterInstance.setCheckParameter( checkName, paramName, value )

    filterInstance.applyFilter()
    return ( filterInstance.mesh, filterInstance.getResults() )


def mainChecks(
    mesh: vtkUnstructuredGrid,
    customParameters: Optional[ dict[ str, UserParameters ] ] = None,
) -> tuple[ vtkUnstructuredGrid, CheckResults ]:
    """Apply main mesh checks to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to check.
        customParameters (dict[str, UserParameters]): Custom parameters for checks. Defaults to None.

    Returns:
        tuple[vtkUnstructuredGrid, CheckResults]: Processed mesh, check results
    """
    filterInstance = MainChecks( mesh )

    if customParameters is None:
        customParameters = {}
    elif not isinstance( customParameters, dict ):
        raise TypeError( "customParameters must be a dictionary mapping check names to parameter dictionaries." )
    else:
        for checkName, params in customParameters.items():
            for paramName, value in params.items():
                filterInstance.setCheckParameter( checkName, paramName, value )

    filterInstance.applyFilter()
    return ( filterInstance.mesh, filterInstance.getResults() )
