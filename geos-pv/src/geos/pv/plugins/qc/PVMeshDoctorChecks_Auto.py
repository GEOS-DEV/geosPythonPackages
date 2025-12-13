# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
# ruff: noqa: F401 # disable imported but unused
import sys
import multiprocessing
from pathlib import Path
from typing_extensions import Self
from typing import Any

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smdomain, smproperty  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonCore import vtkDataArraySelection
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
import numpy  # noqa: F401

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh_doctor.actions.allChecks import CheckResults
from geos.mesh_doctor.filters.Checks import AllChecks
from geos.mesh_doctor.parsing.allChecksParsing import CHECK_FEATURES_CONFIG, ORDERED_CHECK_NAMES
from geos.pv.utils.checkboxFunction import createModifiedCallback  # type: ignore[attr-defined]
from geos.pv.utils.paraviewTreatments import getArrayChoices
from geos.pv.utils.details import SISOFilter, FilterCategory
from geos.pv.utils.pvWidgetGenerator import add_widgets_to_class

__doc__ = f"""
The ``Mesh Doctor Checks`` filter performs comprehensive mesh validation checks on unstructured grids.
This plugin provides access to all mesh-doctor checks including element validation, node validation,
topology checks, and geometric integrity verification.

The filter outputs the input mesh with added diagnostic information based on the selected checks.

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ...
  .../geosPythonPackages/geos-pv/src/geos/pv/plugins/qc/PVMeshDoctorChecks
* Select the input mesh to validate
* Select the filter: Filters > { FilterCategory.QC.value } > Mesh Doctor Checks
* Select which checks to perform
* Optionally adjust check parameters (tolerance, thresholds, etc.)
* Apply

.. Note::
    Check results are logged in the Output Messages view and may add diagnostic arrays to the output mesh.
"""


# we cannot use supportedElements check in the ParaView plugin because of multiprocessing library
AVAILABLE_CHECKS = [ check for check in ORDERED_CHECK_NAMES if check != "supportedElements" ]


@SISOFilter( category=FilterCategory.QC,
             decoratedLabel="Mesh Doctor Checks",
             decoratedType="vtkUnstructuredGrid" )
class PVMeshDoctorChecksAuto( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Initialize the Mesh Doctor Checks filter."""
        # Checks selection
        self._checksSelection: vtkDataArraySelection = vtkDataArraySelection()
        self._initChecksSelection()

        # Parameters for customization
        self._customParameters: dict[ str, dict[ str, Any ] ] = {}

    def _initChecksSelection( self: Self ) -> None:
        """Initialize the available checks selection."""
        self._checksSelection.RemoveAllArrays()
        self._checksSelection.AddObserver(
            "ModifiedEvent",  # type: ignore[arg-type]
            createModifiedCallback( self ) )

        # Add all available checks to the selection
        for checkName in AVAILABLE_CHECKS:
            self._checksSelection.AddArray( checkName, 1 )

    @smproperty.dataarrayselection( name="ChecksToPerform" )
    def SetChecksSelection( self: Self ) -> vtkDataArraySelection:
        """Set which checks to perform.

        Returns:
            vtkDataArraySelection: The checks selection object
        """
        return self._checksSelection

    def ApplyFilter( self: Self, inputMesh: vtkUnstructuredGrid, outputMesh: vtkUnstructuredGrid ) -> None:
        """Apply the mesh validation checks.

        Args:
            inputMesh (vtkUnstructuredGrid): The input mesh to check.
            outputMesh (vtkUnstructuredGrid): The output mesh (copy of input with diagnostic arrays).
        """

        # Get selected checks
        selectedChecks: set[ str ] = getArrayChoices( self._checksSelection )
        checksToPerform: list[ str ] = list( selectedChecks )

        # Create AllChecks filter instance
        allChecksFilter: AllChecks = AllChecks( inputMesh, speHandler=True )

        # Set up VTK logger handler
        if len( allChecksFilter.logger.handlers ) == 0:
            allChecksFilter.setLoggerHandler( VTKHandler() )

        # Configure which checks to perform
        allChecksFilter.setChecksToPerform( checksToPerform )

        # Apply custom parameters for each check based on user input
        for checkName in checksToPerform:
            if checkName in self._customParameters:
                # Get the parameters from the custom parameters dict
                params = self._customParameters[ checkName ]
                
                # Set the parameters on the filter's options
                if hasattr( allChecksFilter, 'setCheckOptions' ):
                    allChecksFilter.setCheckOptions( checkName, params )
                else:
                    # Fallback: set options directly if available
                    check_options = allChecksFilter._checks.get( checkName )
                    if check_options:
                        for param_name, param_value in params.items():
                            if hasattr( check_options.options, param_name ):
                                setattr( check_options.options, param_name, param_value )

        try:
            # Execute the checks
            checkResults: CheckResults = allChecksFilter.ApplyFilter()
            
            # Copy input to output
            outputMesh.ShallowCopy( inputMesh )
            
            # Log summary of results
            for checkName, result in checkResults.items():
                if result:
                    allChecksFilter.logger.info( f"{checkName}: Check completed" )

        except ( ValueError, IndexError, TypeError, AttributeError ) as e:
            allChecksFilter.logger.error( f"Error during mesh check: {e}" )
            raise
        except Exception as e:
            allChecksFilter.logger.error( f"Unexpected error during mesh check: {e}" )
            raise


# Dynamically add widget methods to the class based on CHECK_FEATURES_CONFIG
# This replaces all the manually-written property setters and grouping methods
add_widgets_to_class( PVMeshDoctorChecksAuto, CHECK_FEATURES_CONFIG )
