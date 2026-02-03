# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging
import numpy as np

from pathlib import Path
from typing_extensions import Self

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smdomain, smproperty  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkMultiBlockDataSet

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.utils.Logger import ( CountWarningHandler, isHandlerInLogger, getLoggerHandlerType )
from geos.utils.PhysicalConstants import ( DEFAULT_FRICTION_ANGLE_DEG, DEFAULT_GRAIN_BULK_MODULUS,
                                           DEFAULT_ROCK_COHESION, WATER_DENSITY )
from geos.mesh.utils.multiblockHelpers import ( getBlockElementIndexesFlatten, getBlockNameFromIndex )
from geos.processing.post_processing.GeomechanicsCalculator import GeomechanicsCalculator
from geos.pv.utils.details import ( SISOFilter, FilterCategory )

__doc__ = f"""
PVGeomechanicsCalculator is a paraview plugin that allows to compute additional geomechanics properties from existing ones in the mesh.

To compute the geomechanics outputs, the mesh must have the following properties:
    - The Young modulus and the Poisson's ratio named "youngModulus" and "poissonRatio" or bulk and shear moduli named "bulkModulus" and "shearModulus"
    - The initial Young modulus and Poisson's ratio named "youngModulusInitial" and "poissonRatioInitial" or the initial bulk modulus named "bulkModulusInitial"
    - The porosity named "porosity"
    - The initial porosity named "porosityInitial"
    - The delta of pressure named "deltaPressure"
    - The density named "density"
    - The effective stress named "stressEffective"
    - The initial effective stress named "stressEffectiveInitial"
    - The pressure named "pressure"

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

PVGeomechanicsCalculator paraview plugin input mesh can be a vtkUnstructuredGrid or a vtkMultiBlockDataSet of vtkUnstructuredGrid.
If the input mesh is a vtkMultiBlockDataSet, the geomechanics properties will be computed on each vtkUnstructuredGrid.
The output mesh has the same type than the input one.

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/post_processing/PVGeomechanicsCalculator
* Select the mesh you want to compute geomechanics properties on
* Select the filter: Filters > { FilterCategory.GEOS_POST_PROCESSING.value } > GEOS Geomechanics Calculator
* Change the physical constants if needed
* Select computeAdvancedProperties to compute the advanced properties
* Apply

"""

loggerTitle: str = "Geomechanics Calculator"


@SISOFilter( category=FilterCategory.GEOS_POST_PROCESSING,
             decoratedLabel="GEOS Geomechanics Calculator",
             decoratedType=[ "vtkUnstructuredGrid", "vtkMultiBlockDataSet" ] )
class PVGeomechanicsCalculator( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to compute additional geomechanical properties."""
        self.computeAdvancedProperties: bool = False

        # Defaults physical constants
        ## For basic properties
        self.grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.specificDensity: float = WATER_DENSITY
        ## For advanced properties
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
            The unit is °. Default is no friction case (i.e., 10.°).
        </Documentation>
    """ )
    def setFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set friction angle.

        Args:
            frictionAngle (float): Friction angle (°).
        """
        self.frictionAngle = frictionAngle * np.pi / 180
        self.Modified()

    @smproperty.xml( """
        <PropertyGroup label="Advanced properties parameters" panel_visibility="advanced">
            <Property name="RockCohesion"/>
            <Property name="FrictionAngle"/>
            <Hints>
                <PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility"
                    property="ComputeAdvancedProperties"
                    value="1" />
            </Hints>
        </PropertyGroup>
    """ )
    def groupAdvancedPropertiesParameters( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    def ApplyFilter(
        self: Self,
        inputMesh: vtkUnstructuredGrid | vtkMultiBlockDataSet,
        outputMesh: vtkUnstructuredGrid | vtkMultiBlockDataSet,
    ) -> None:
        """Is applying GeomechanicsCalculator to the mesh, computing geomechanics properties from the elastics moduli.

        Args:
            inputMesh (vtkUnstructuredGrid|vtkMultiBlockDataSet): A mesh to transform.
            outputMesh (vtkUnstructuredGrid|vtkMultiBlockDataSet): A mesh transformed.
        """
        geomechanicsCalculatorFilter: GeomechanicsCalculator
        outputMesh.ShallowCopy( inputMesh )
        mess: str
        if isinstance( outputMesh, vtkUnstructuredGrid ):
            geomechanicsCalculatorFilter = GeomechanicsCalculator(
                outputMesh,
                self.computeAdvancedProperties,
                loggerName="Geomechanics Calculators on the unstructured grid",
                speHandler=True,
            )

            if not isHandlerInLogger( self.handler, geomechanicsCalculatorFilter.logger ):
                geomechanicsCalculatorFilter.setLoggerHandler( self.handler )

            geomechanicsCalculatorFilter.physicalConstants.grainBulkModulus = self.grainBulkModulus
            geomechanicsCalculatorFilter.physicalConstants.specificDensity = self.specificDensity
            geomechanicsCalculatorFilter.physicalConstants.rockCohesion = self.rockCohesion
            geomechanicsCalculatorFilter.physicalConstants.frictionAngle = self.frictionAngle

            try:
                geomechanicsCalculatorFilter.applyFilter()
                # Add to the warning counter the number of warning logged with the call of GeomechanicsCalculator filter (useful for the PVGeomechanicsWorkflow)
                self.counter.addExternalWarningCount( geomechanicsCalculatorFilter.nbWarnings )

                outputMesh.ShallowCopy( geomechanicsCalculatorFilter.getOutput() )
            except ( ValueError, AttributeError ) as e:
                geomechanicsCalculatorFilter.logger.error(
                    f"The filter { geomechanicsCalculatorFilter.logger.name } failed due to:\n{ e }" )
            except Exception as e:
                mess = f"The filter { geomechanicsCalculatorFilter.logger.name } failed due to:\n{ e }"
                geomechanicsCalculatorFilter.logger.critical( mess, exc_info=True )

        elif isinstance( outputMesh, vtkMultiBlockDataSet ):
            self.logger.info( f"Apply plugin { self.logger.name }." )

            volumeBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( outputMesh )
            for blockIndex in volumeBlockIndexes:
                volumeBlock: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast(
                    outputMesh.GetDataSet( blockIndex ) )
                volumeBlockName: str = getBlockNameFromIndex( outputMesh, blockIndex )
                filterName: str = f"Geomechanics Calculator for the block { volumeBlockName }"

                geomechanicsCalculatorFilter = GeomechanicsCalculator(
                    volumeBlock,
                    self.computeAdvancedProperties,
                    filterName,
                    True,
                )

                if not isHandlerInLogger( self.handler, geomechanicsCalculatorFilter.logger ):
                    geomechanicsCalculatorFilter.setLoggerHandler( self.handler )

                geomechanicsCalculatorFilter.physicalConstants.grainBulkModulus = self.grainBulkModulus
                geomechanicsCalculatorFilter.physicalConstants.specificDensity = self.specificDensity
                geomechanicsCalculatorFilter.physicalConstants.rockCohesion = self.rockCohesion
                geomechanicsCalculatorFilter.physicalConstants.frictionAngle = self.frictionAngle

                try:
                    geomechanicsCalculatorFilter.applyFilter()
                    # Add to the warning counter the number of warning logged with the call of GeomechanicsCalculator filter
                    self.counter.addExternalWarningCount( geomechanicsCalculatorFilter.nbWarnings )

                    volumeBlock.ShallowCopy( geomechanicsCalculatorFilter.getOutput() )
                    volumeBlock.Modified()
                except ( ValueError, AttributeError ) as e:
                    geomechanicsCalculatorFilter.logger.error(
                        f"The filter { geomechanicsCalculatorFilter.logger.name } failed due to:\n{ e }" )
                except Exception as e:
                    mess = f"The filter { geomechanicsCalculatorFilter.logger.name } failed due to:\n{ e }"
                    geomechanicsCalculatorFilter.logger.critical( mess, exc_info=True )

            result: str = f"The filter { self.logger.name } succeeded"
            if self.counter.warningCount > 0:
                self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
            else:
                self.logger.info( f"{ result }." )

        outputMesh.Modified()
        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        return
