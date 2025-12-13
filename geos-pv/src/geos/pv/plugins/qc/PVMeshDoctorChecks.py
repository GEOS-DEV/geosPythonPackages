# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
# ruff: noqa: F401 # disable imported but unused
import sys
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
class PVMeshDoctorChecks( VTKPythonAlgorithmBase ):

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

    # ========================================================================
    # COLLOCATED_NODES parameters
    # ========================================================================
    @smproperty.doublevector(
        name="DistanceTolerance",
        label="Tolerance",
        default_values=0.0,
        number_of_elements=1,
    )
    @smdomain.xml( """<DoubleRangeDomain name="range" min="0" />
                      <Documentation>
                        The absolute distance between two nodes for them to be considered collocated.
                      </Documentation>""" )
    def SetCollocatedNodesTolerance( self: Self, tolerance: float ) -> None:
        """Set tolerance for collocated nodes check.

        Args:
            tolerance (float): Tolerance value
        """
        if not hasattr( self, '_cn_tolerance' ) or self._cn_tolerance != tolerance:
            self._cn_tolerance = tolerance
            self.Modified()

    @smproperty.xml( """
                    <PropertyGroup label="Collocated Nodes Parameters" panel_widget="Line">
                        <Property name="CollocatedNodes_Tolerance"/>
                        <Hints>
                            <PropertyWidgetDecorator type="ArraySelectionWidgetDecorator"
                            property="ChecksToPerform"
                            array_name="collocated_nodes" />
                        </Hints>
                    </PropertyGroup>
                    """ )
    def a01GroupCollocatedNodesParams( self: Self ) -> None:
        """Group collocated nodes parameters."""
        pass

    # ========================================================================
    # ELEMENT_VOLUMES parameters
    # ========================================================================
    @smproperty.doublevector(
        name="ElementVolumes_MinVolume",
        label="Minimum Volume",
        default_values=0.0,
        number_of_elements=1,
    )
    @smdomain.xml( """
                    <DoubleRangeDomain name="range" />
                    <Documentation>
                        The minimum acceptable volume for elements.
                    </Documentation>
                  """ )
    def SetElementVolumesMinVolume( self: Self, minVolume: float ) -> None:
        """Set minimum volume for element volumes check.

        Args:
            minVolume (float): Minimum volume threshold
        """
        if not hasattr( self, '_ev_minVolume' ) or self._ev_minVolume != minVolume:
            self._ev_minVolume = minVolume
            self.Modified()

    @smproperty.xml( """
                    <PropertyGroup label="Element Volumes Parameters" panel_widget="Line">
                        <Property name="ElementVolumes_MinVolume"/>
                        <Hints>
                            <PropertyWidgetDecorator type="ArraySelectionWidgetDecorator"
                            property="ChecksToPerform"
                            array_name="element_volumes" />
                        </Hints>
                    </PropertyGroup>
                    """ )
    def a02GroupElementVolumesParams( self: Self ) -> None:
        """Group element volumes parameters."""
        pass

    # ========================================================================
    # NON_CONFORMAL parameters
    # ========================================================================
    @smproperty.doublevector(
        name="NonConformal_AngleTolerance",
        label="Angle Tolerance (degrees)",
        default_values=10.0,
        number_of_elements=1,
    )
    @smdomain.xml( """
                    <DoubleRangeDomain name="range" min="0" />
                    <Documentation>
                        Angle tolerance in degrees for non-conformal detection.
                    </Documentation>
                  """ )
    def SetNonConformalAngleTolerance( self: Self, angleTolerance: float ) -> None:
        """Set angle tolerance for non-conformal check.

        Args:
            angleTolerance (float): Angle tolerance in degrees
        """
        if not hasattr( self, '_nc_angleTolerance' ) or self._nc_angleTolerance != angleTolerance:
            self._nc_angleTolerance = angleTolerance
            self.Modified()

    @smproperty.doublevector(
        name="NonConformal_PointTolerance",
        label="Point Tolerance",
        default_values=0.0,
        number_of_elements=1,
    )
    @smdomain.xml( """
                    <DoubleRangeDomain name="range" min="0" />
                    <Documentation>
                        Tolerance for two points to be considered collocated in non-conformal check.
                    </Documentation>
                  """ )
    def SetNonConformalPointTolerance( self: Self, pointTolerance: float ) -> None:
        """Set point tolerance for non-conformal check.

        Args:
            pointTolerance (float): Point tolerance
        """
        if not hasattr( self, '_nc_pointTolerance' ) or self._nc_pointTolerance != pointTolerance:
            self._nc_pointTolerance = pointTolerance
            self.Modified()

    @smproperty.doublevector(
        name="NonConformal_FaceTolerance",
        label="Face Tolerance",
        default_values=0.0,
        number_of_elements=1,
    )
    @smdomain.xml( """
                    <DoubleRangeDomain name="range" min="0" />
                    <Documentation>
                        Tolerance for face comparison in non-conformal check.
                    </Documentation>
                  """ )
    def SetNonConformalFaceTolerance( self: Self, faceTolerance: float ) -> None:
        """Set face tolerance for non-conformal check.

        Args:
            faceTolerance (float): Face tolerance
        """
        if not hasattr( self, '_nc_faceTolerance' ) or self._nc_faceTolerance != faceTolerance:
            self._nc_faceTolerance = faceTolerance
            self.Modified()

    @smproperty.xml( """
                    <PropertyGroup label="Non-Conformal Parameters" panel_widget="Line">
                        <Property name="NonConformal_AngleTolerance"/>
                        <Property name="NonConformal_PointTolerance"/>
                        <Property name="NonConformal_FaceTolerance"/>
                        <Hints>
                            <PropertyWidgetDecorator type="ArraySelectionWidgetDecorator"
                            property="ChecksToPerform"
                            array_name="non_conformal" />
                        </Hints>
                    </PropertyGroup>
                    """ )
    def a03GroupNonConformalParams( self: Self ) -> None:
        """Group non-conformal parameters."""
        pass

    # ========================================================================
    # SELF_INTERSECTING_ELEMENTS parameters
    # ========================================================================
    @smproperty.doublevector(
        name="SelfIntersecting_MinDistance",
        label="Minimum Distance",
        default_values=float( numpy.finfo( float ).eps ),
        number_of_elements=1,
    )
    @smdomain.xml( """
                    <DoubleRangeDomain name="range" min="0" />
                    <Documentation>
                        The minimum distance in the computation. Defaults to machine precision.
                    </Documentation>
                  """ )
    def SetSelfIntersectingMinDistance( self: Self, minDistance: float ) -> None:
        """Set minimum distance for self-intersecting elements check.

        Args:
            minDistance (float): Minimum distance
        """
        if not hasattr( self, '_sie_minDistance' ) or self._sie_minDistance != minDistance:
            self._sie_minDistance = minDistance
            self.Modified()

    @smproperty.xml( """
                    <PropertyGroup label="Self-Intersecting Elements Parameters" panel_widget="Line">
                        <Property name="SelfIntersecting_MinDistance"/>
                        <Hints>
                            <PropertyWidgetDecorator type="ArraySelectionWidgetDecorator"
                            property="ChecksToPerform"
                            array_name="self_intersecting_elements" />
                        </Hints>
                    </PropertyGroup>
                    """ )
    def a04GroupSelfIntersectingParams( self: Self ) -> None:
        """Group self-intersecting elements parameters."""
        pass

    # ========================================================================
    # SUPPORTED_ELEMENTS parameters
    # ========================================================================
    @smproperty.intvector(
        name="SupportedElements_ChunkSize",
        label="Chunk Size",
        default_values=1,
        number_of_elements=1,
    )
    @smdomain.xml( """
                    <IntRangeDomain name="range" min="1" />
                    <Documentation>
                        Chunk size for parallel processing in supported elements check.
                    </Documentation>
                  """ )
    def SetSupportedElementsChunkSize( self: Self, chunkSize: int ) -> None:
        """Set chunk size for supported elements check.

        Args:
            chunkSize (int): Chunk size for parallel processing
        """
        if not hasattr( self, '_se_chunkSize' ) or self._se_chunkSize != chunkSize:
            self._se_chunkSize = chunkSize
            self.Modified()

    @smproperty.intvector(
        name="SupportedElements_NumProc",
        label="Number of Processors",
        default_values=multiprocessing.cpu_count(),
        number_of_elements=1,
    )
    @smdomain.xml( """
                    <IntRangeDomain name="range" min="1" />
                    <Documentation>
                        Number of threads used for parallel processing. Defaults to CPU count.
                    </Documentation>
                  """ )
    def SetSupportedElementsNumProc( self: Self, nproc: int ) -> None:
        """Set number of processors for supported elements check.

        Args:
            nproc (int): Number of processors
        """
        if not hasattr( self, '_se_nproc' ) or self._se_nproc != nproc:
            self._se_nproc = nproc
            self.Modified()

    @smproperty.xml( """
                    <PropertyGroup label="Supported Elements Parameters" panel_widget="Line">
                        <Property name="SupportedElements_ChunkSize"/>
                        <Property name="SupportedElements_NumProc"/>
                        <Hints>
                            <PropertyWidgetDecorator type="ArraySelectionWidgetDecorator"
                            property="ChecksToPerform"
                            array_name="supported_elements" />
                        </Hints>
                    </PropertyGroup>
                    """ )
    def a05GroupSupportedElementsParams( self: Self ) -> None:
        """Group supported elements parameters."""
        pass

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
            if checkName == "collocated_nodes" and hasattr( self, '_cn_tolerance' ):
                allChecksFilter.setCheckParameter( "collocated_nodes", "tolerance", self._cn_tolerance )

            elif checkName == "element_volumes" and hasattr( self, '_ev_minVolume' ):
                allChecksFilter.setCheckParameter( "element_volumes", "minVolume", self._ev_minVolume )

            elif checkName == "non_conformal":
                if hasattr( self, '_nc_angleTolerance' ):
                    allChecksFilter.setCheckParameter( "non_conformal", "angleTolerance", self._nc_angleTolerance )
                if hasattr( self, '_nc_pointTolerance' ):
                    allChecksFilter.setCheckParameter( "non_conformal", "pointTolerance", self._nc_pointTolerance )
                if hasattr( self, '_nc_faceTolerance' ):
                    allChecksFilter.setCheckParameter( "non_conformal", "faceTolerance", self._nc_faceTolerance )

            elif checkName == "self_intersecting_elements" and hasattr( self, '_sie_minDistance' ):
                allChecksFilter.setCheckParameter( "self_intersecting_elements", "minDistance", self._sie_minDistance )

            elif checkName == "supported_elements":
                if hasattr( self, '_se_chunkSize' ):
                    allChecksFilter.setCheckParameter( "supported_elements", "chunkSize", self._se_chunkSize )
                if hasattr( self, '_se_nproc' ):
                    allChecksFilter.setCheckParameter( "supported_elements", "nproc", self._se_nproc )

        try:
            # Apply the filter
            allChecksFilter.applyFilter()
            
            # Copy the output mesh (which may have diagnostic arrays added)
            outputMesh.ShallowCopy( allChecksFilter.mesh )

            # Get and log results
            results: CheckResults = allChecksFilter.getResults()
            allChecksFilter.logger.info( f"Performed { len( results ) } checks successfully." )
            
            # Log summary of each check result
            for checkName, result in results.items():
                allChecksFilter.logger.info( f"Check '{ checkName }': { result }" )

        except ( ValueError, IndexError, TypeError, AttributeError ) as e:
            allChecksFilter.logger.error(
                f"The filter { allChecksFilter.logger.name } failed due to:\n{ e }" )
        except Exception as e:
            mess: str = f"The filter { allChecksFilter.logger.name } failed due to:\n{ e }"
            allChecksFilter.logger.critical( mess, exc_info=True )
