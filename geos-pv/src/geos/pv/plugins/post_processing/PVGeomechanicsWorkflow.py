# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging

from pathlib import Path
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.utils.Errors import VTKError
from geos.utils.Logger import ( CountWarningHandler, getLoggerHandlerType )
from geos.utils.PhysicalConstants import ( DEFAULT_FRICTION_ANGLE_DEG, DEFAULT_GRAIN_BULK_MODULUS,
                                           DEFAULT_ROCK_COHESION, WATER_DENSITY )

from geos.pv.plugins.post_processing.PVGeosBlockExtractAndMerge import PVGeosBlockExtractAndMerge
from geos.pv.plugins.post_processing.PVGeomechanicsCalculator import PVGeomechanicsCalculator
from geos.pv.plugins.post_processing.PVSurfaceGeomechanics import PVSurfaceGeomechanics
from geos.pv.utils.details import FilterCategory

from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smproperty, smproxy )
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

__doc__ = f"""
PVGeomechanicsWorkflow is a Paraview plugin that executes multiple plugins:
    1. PVGeosBlockExtractAndMerge
    2. PVGeomechanicsCalculator
    3. PVSurfaceGeomechanics (if the input mesh contains faults)

PVGeosBlockExtractAndMerge is a Paraview plugin processing the input mesh at the current time in two steps:
    1. Extraction of domains (volume, fault and well) from a GEOS output multiBlockDataSet mesh
    2. Actions on each region of a GEOS output domain (volume, fault, wells) to:
        * Merge Ranks
        * Identify "Fluids" and "Rock" phases
        * Rename "Rock" attributes depending on the phase they refer to for more clarity
        * Convert volume meshes to surface if needed
        * Copy "geomechanics" attributes from the initial timestep to the current one if they exist

PVGeomechanicsCalculator is a paraview plugin that allows to compute basic and advanced geomechanics properties from existing ones in the mesh. This is donne on each block of the volume mesh.

The basic geomechanics properties computed on the mesh are:
    - The elastic moduli not present on the mesh
    - Biot coefficient
    - Compressibility, oedometric compressibility and real compressibility coefficient
    - Specific gravity
    - Real effective stress ratio
    - Total initial stress, total current stress and total stress ratio
    - Elastic stain
    - Real reservoir stress path and reservoir stress path in oedometric condition

The advanced geomechanics properties computed on the mesh are:
    - Fracture index and threshold
    - Critical pore pressure and pressure index

PVSurfaceGeomechanics is a Paraview plugin that allows to compute additional geomechanical attributes from the input surfaces, such as shear capacity utilization (SCU). This is donne on each block of the fault mesh.

This filter results in 3 output pipelines with the vtkMultiBlockDataSet:
    - "Volume" contains the volume domain
    - "Fault" contains the fault domain if it exist
    - "Well" contains the well domain if it exist

Input and output meshes are vtkMultiBlockDataSet.

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/post_processing/PVGeomechanicsWorkflow
* Select the Geos output .pvd file loaded in Paraview to process
* Select the filter: Filters > { FilterCategory.GEOS_POST_PROCESSING.value } > GEOS Geomechanics Workflow.
* Change the physical constants if needed
* Select computeAdvancedProperties to compute the advanced properties on volume mesh
* Apply

"""

loggerTitle: str = "GEOS Geomechanics Workflow"


@smproxy.filter(
    name="PVGeomechanicsWorkflow",
    label="GEOS Geomechanics Workflow",
)
@smproperty.xml( f"""
    <OutputPort index="0" name="Volume"/>
    <OutputPort index="1" name="Fault"/>
    <OutputPort index="2" name="Well"/>
    <Hints>
        <ShowInMenu category="{ FilterCategory.GEOS_POST_PROCESSING.value }"/>
        <View type="RenderView" port="0"/>
        <View type="None" port="1"/>
        <View type="None" port="2"/>
    </Hints>
    """ )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkMultiBlockDataSet" ], composite_data_supported=True )
class PVGeomechanicsWorkflow( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to compute geomechanics properties on volume and on surface directly from the GEOS simulation output mesh.

        This plugin is the combination of three other:
            - First PVGeosBlockExtractAndMerge
            - Secondly PVGeomechanicsCalculator
            - Thirdly PVSurfaceGeomechanics (if the input mesh contains faults)
        """
        super().__init__(
            nInputPorts=1,
            nOutputPorts=3,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkMultiBlockDataSet",
        )

        self.volumeMesh: vtkMultiBlockDataSet
        self.faultMesh: vtkMultiBlockDataSet
        self.wellMesh: vtkMultiBlockDataSet

        self.extractFault: bool = True
        self.extractWell: bool = True

        self.computeAdvancedProperties: bool = False

        # Defaults physical constants
        ## For basic properties on Volume
        self.grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.specificDensity: float = WATER_DENSITY
        ## For advanced properties on Volume and basic properties on Surface
        self.rockCohesion: float = DEFAULT_ROCK_COHESION
        self.frictionAngle: float = DEFAULT_FRICTION_ANGLE_DEG

        self.handler: logging.Handler = VTKHandler()
        self.logger = logging.getLogger( loggerTitle )
        self.logger.setLevel( logging.INFO )
        self.logger.addHandler( self.handler )
        self.logger.propagate = False

        counter: CountWarningHandler = CountWarningHandler()
        self.counter: CountWarningHandler
        self.nbWarnings: int = 0
        try:
            self.counter = getLoggerHandlerType( type( counter ), self.logger )
            self.counter.resetWarningCount()
        except ValueError:
            self.counter = counter
            self.counter.setLevel( logging.INFO )

        self.logger.addHandler( self.counter )

    @smproperty.doublevector(
        name="GrainBulkModulus",
        label="Grain bulk modulus (Pa)",
        default_values=DEFAULT_GRAIN_BULK_MODULUS,
        panel_visibility="default",
    )
    @smdomain.xml( """
                    <Documentation>
                        Reference grain bulk modulus to compute Biot coefficient.
                        The unit is Pa. Default is Quartz bulk modulus (i.e., 38GPa).
                    </Documentation>
                  """ )
    def setGrainBulkModulus( self: Self, grainBulkModulus: float ) -> None:
        """Set grain bulk modulus.

        Args:
            grainBulkModulus (float): Grain bulk modulus (Pa).
        """
        self.grainBulkModulus = grainBulkModulus
        self.Modified()

    @smproperty.doublevector(
        name="SpecificDensity",
        label="Specific Density (kg/m3)",
        default_values=WATER_DENSITY,
        panel_visibility="default",
    )
    @smdomain.xml( """
                    <Documentation>
                        Reference density to compute specific gravity.
                        The unit is kg/m3. Default is fresh water density (i.e., 1000 kg/m3).
                    </Documentation>
                  """ )
    def setSpecificDensity( self: Self, specificDensity: float ) -> None:
        """Set specific density.

        Args:
            specificDensity (float): Reference specific density (kg/m3).
        """
        self.specificDensity = specificDensity
        self.Modified()

    @smproperty.xml( """
                <PropertyGroup label="Basic properties parameters">
                    <Property name="GrainBulkModulus"/>
                    <Property name="SpecificDensity"/>
                </PropertyGroup>
                """ )
    def groupBasicPropertiesParameters( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.doublevector(
        name="RockCohesion",
        label="Rock Cohesion (Pa)",
        default_values=DEFAULT_ROCK_COHESION,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            Reference rock cohesion to compute critical pore pressure.
            The unit is Pa.Default is fractured case (i.e., 0. Pa).
        </Documentation>
    """ )
    def setRockCohesion( self: Self, rockCohesion: float ) -> None:
        """Set rock cohesion.

        Args:
            rockCohesion (float): Rock cohesion (Pa).
        """
        self.rockCohesion = rockCohesion
        self.Modified()

    @smproperty.doublevector(
        name="FrictionAngle",
        label="Friction Angle (°)",
        default_values=DEFAULT_FRICTION_ANGLE_DEG,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            Reference friction angle to compute critical pore pressure.
            The unit is °. Default is an average friction angle (i.e., 10°).
        </Documentation>
    """ )
    def setFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set friction angle.

        Args:
            frictionAngle (float): Friction angle (°).
        """
        self.frictionAngle = frictionAngle
        self.Modified()

    @smproperty.xml( """
        <PropertyGroup
            label="Surface parameters / Advanced volume parameters">
            <Property name="RockCohesion"/>
            <Property name="FrictionAngle"/>
        </PropertyGroup>
        """ )
    def groupAdvancedPropertiesAndSurfaceParameters( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.intvector(
        name="ComputeAdvancedProperties",
        label="Compute advanced geomechanics properties",
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <BooleanDomain name="ComputeAdvancedProperties"/>
        <Documentation>
            Check to compute advanced geomechanics properties including
            reservoir stress paths and fracture indexes.
        </Documentation>
    """ )
    def setComputeAdvancedProperties( self: Self, computeAdvancedProperties: bool ) -> None:
        """Set advanced properties calculation option.

        Args:
            computeAdvancedProperties (bool): True to compute advanced geomechanics properties, False otherwise.
        """
        self.computeAdvancedProperties = computeAdvancedProperties
        self.Modified()

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        assert inData is not None

        outDataCells = self.GetOutputData( outInfoVec, 0 )
        if outDataCells is None or ( not outDataCells.IsA( "vtkMultiBlockDataSet" ) ):
            outDataCells = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 0 ).Set( outDataCells.DATA_OBJECT(), outDataCells )  # type: ignore

        outDataFaults = self.GetOutputData( outInfoVec, 1 )
        if outDataFaults is None or ( not outDataFaults.IsA( "vtkMultiBlockDataSet" ) ):
            outDataFaults = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 1 ).Set( outDataFaults.DATA_OBJECT(), outDataFaults )  # type: ignore

        outDataWells = self.GetOutputData( outInfoVec, 2 )
        if outDataWells is None or ( not outDataWells.IsA( "vtkMultiBlockDataSet" ) ):
            outDataWells = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 2 ).Set( outDataWells.DATA_OBJECT(), outDataWells )  # type: ignore

        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        self.logger.info( f"Apply plugin { self.logger.name }." )

        try:
            self.volumeMesh = self.GetOutputData( outInfoVec, 0 )
            self.faultMesh = self.GetOutputData( outInfoVec, 1 )
            self.wellMesh = self.GetOutputData( outInfoVec, 2 )

            self.applyPVGeosBlockExtractAndMerge()
            self.applyPVGeomechanicsCalculator()

            if self.extractFault:
                self.applyPVSurfaceGeomechanics()

            result: str = f"The plugin { self.logger.name } succeeded"
            if self.counter.warningCount > 0:
                self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
            else:
                self.logger.info( f"{ result }." )

        except ( ValueError, VTKError, AttributeError, AssertionError ) as e:
            self.logger.error( f"The plugin { self.logger.name } failed due to:\n{ e }" )
        except Exception as e:
            mess: str = f"The plugin { self.logger.name } failed due to:\n{ e }"
            self.logger.critical( mess, exc_info=True )

        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        return 1

    def applyPVGeosBlockExtractAndMerge( self: Self ) -> None:
        """Apply PVGeosBlockExtractAndMerge."""
        extractAndMergeFilter: PVGeosBlockExtractAndMerge = PVGeosBlockExtractAndMerge()
        extractAndMergeFilter.SetInputConnection( self.GetInputConnection( 0, 0 ) )
        extractAndMergeFilter.Update()
        # Add to the warning counter the number of warning logged with the call of GeosBlockExtractAndMerge plugin
        self.counter.addExternalWarningCount( extractAndMergeFilter.nbWarnings )

        self.volumeMesh.ShallowCopy( extractAndMergeFilter.GetOutputDataObject( 0 ) )
        self.volumeMesh.Modified()

        self.extractFault = extractAndMergeFilter.extractFault
        if self.extractFault:
            self.faultMesh.ShallowCopy( extractAndMergeFilter.GetOutputDataObject( 1 ) )
            self.faultMesh.Modified()

        self.extractWell = extractAndMergeFilter.extractWell
        if self.extractWell:
            self.wellMesh.ShallowCopy( extractAndMergeFilter.GetOutputDataObject( 2 ) )
            self.wellMesh.Modified()

        return

    def applyPVGeomechanicsCalculator( self: Self ) -> None:
        """Apply PVGeomechanicsCalculator."""
        geomechanicsCalculatorPlugin = PVGeomechanicsCalculator()

        geomechanicsCalculatorPlugin.SetInputDataObject( self.volumeMesh ),
        geomechanicsCalculatorPlugin.setComputeAdvancedProperties( self.computeAdvancedProperties )
        geomechanicsCalculatorPlugin.setGrainBulkModulus( self.grainBulkModulus )
        geomechanicsCalculatorPlugin.setSpecificDensity( self.specificDensity )
        geomechanicsCalculatorPlugin.setRockCohesion( self.rockCohesion )
        geomechanicsCalculatorPlugin.setFrictionAngle( self.frictionAngle )
        geomechanicsCalculatorPlugin.Update()
        # Add to the warning counter the number of warning logged with the call of GeomechanicsCalculator plugin
        self.counter.addExternalWarningCount( geomechanicsCalculatorPlugin.nbWarnings )

        self.volumeMesh.ShallowCopy( geomechanicsCalculatorPlugin.GetOutputDataObject( 0 ) )
        self.volumeMesh.Modified()

        return

    def applyPVSurfaceGeomechanics( self: Self ) -> None:
        """Apply PVSurfaceGeomechanics."""
        surfaceGeomechanicsPlugin = PVSurfaceGeomechanics()

        surfaceGeomechanicsPlugin.SetInputDataObject( self.faultMesh )
        surfaceGeomechanicsPlugin.a01SetRockCohesion( self.rockCohesion )
        surfaceGeomechanicsPlugin.a02SetFrictionAngle( self.frictionAngle )
        surfaceGeomechanicsPlugin.Update()
        # Add to the warning counter the number of warning logged with the call of SurfaceGeomechanics plugin
        self.counter.addExternalWarningCount( surfaceGeomechanicsPlugin.nbWarnings )

        self.faultMesh.ShallowCopy( surfaceGeomechanicsPlugin.GetOutputDataObject( 0 ) )
        self.faultMesh.Modified()

        return
