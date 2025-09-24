# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Union
from typing_extensions import Self

import logging
import numpy as np
import numpy.typing as npt

import geos.geomechanics.processing.geomechanicsCalculatorFunctions as fcts

from geos.mesh.utils.arrayModifiers import createAttribute
from geos.mesh.utils.arrayHelpers import (
    getArrayInObject,
    isAttributeInObject,
)

from geos.utils.Logger import (
    Logger,
    getLogger,
)
from geos.utils.GeosOutputsConstants import (
    AttributeEnum,
    ComponentNameEnum,
    GeosMeshOutputsEnum,
    PostProcessingOutputsEnum,
)
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_GRAIN_BULK_MODULUS,
    DEFAULT_ROCK_COHESION,
    GRAVITY,
    WATER_DENSITY,
)

from vtkmodules.vtkCommonDataModel import vtkPointSet, vtkUnstructuredGrid
from vtkmodules.vtkFiltersCore import vtkCellCenters

__doc__ = """
GeomechanicsCalculator module is a vtk filter that allows to compute additional
Geomechanical properties from existing ones.

The basic geomechanics outputs are:
    - Elastic modulus (young modulus and poisson ratio or bulk modulus and shear modulus)
    - Biot coefficient
    - Compressibility, oedometric compressibility and real compressibility coefficient
    - Specific gravity
    - Real effective stress ratio
    - Total initial stress, total current stress and total stress ratio
    - Lithostatic stress (physic to update)
    - Elastic stain
    - Reservoir stress path and reservoir stress path in oedometric condition

The advanced geomechanics outputs are:
    - fracture index and threshold
    - Critical pore pressure and pressure index

GeomechanicsCalculator filter input mesh is either vtkPointSet or vtkUnstructuredGrid
and returned mesh is of same type as input.

.. Note::
    - The default physical constants used by the filter are:
        - grainBulkModulus = 38e9 Pa (the one of the Quartz)
        - specificDensity = 1000.0 kg/m³ (the one of the water)
        - rockCohesion = 0.0 Pa
        - frictionAngle = 10.0 / 180.0 * np.pi rad

To use the filter:

.. code-block:: python

    import numpy as np
    from geos.mesh.processing.GeomechanicsCalculator import GeomechanicsCalculator

    # Define filter inputs
    mesh: Union[ vtkPointSet, vtkUnstructuredGrid ]
    computeAdvancedOutputs: bool # optional, defaults to False
    speHandler: bool # optional, defaults to False

    # Instantiate the filter
    filter: GeomechanicsCalculator = GeomechanicsCalculator( mesh, computeAdvancedOutputs, speHandler )

    # Use your own handler (if speHandler is True)
    yourHandler: logging.Handler
    filter.setLoggerHandler( yourHandler )

    # Change the physical constants if needed
    ## Basic outputs
    grainBulkModulus: float
    specificDensity: float
    filter.SetGrainBulkModulus(grainBulkModulus)
    filter.SetSpecificDensity(specificDensity)

    ## Advanced outputs
    rockCohesion: float
    frictionAngle: float
    filter.SetRockCohesion(rockCohesion)
    filter.SetFrictionAngle(frictionAngle)

    # Do calculations
    filter.applyFilter()

    # Get the mesh with the geomechanical output as attribute
    output :Union[vtkPointSet, vtkUnstructuredGrid]
    output = filter.getOutput()
"""

loggerTitle: str = "Geomechanical Calculator Filter"


class GeomechanicsCalculator():

    def __init__(
        self: Self,
        mesh: Union[ vtkPointSet, vtkUnstructuredGrid ],
        computeAdvancedOutputs: bool = False,
        speHandler: bool = False,
    ) -> None:
        """VTK Filter to perform Geomechanical output computation.

        Args:
            mesh (Union[vtkPointsSet, vtkUnstructuredGrid]): Input mesh.
            computeAdvancedOutputs (bool, optional): True to compute advanced geomechanical parameters, False otherwise.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.output: Union[ vtkPointSet, vtkUnstructuredGrid ]
        if mesh.IsA( "vtkUnstructuredGrid" ):
            self.output = vtkUnstructuredGrid()
        elif mesh.IsA( "vtkPointSet" ):
            self.output = vtkPointSet()
        self.output.DeepCopy( mesh )

        self.doComputeAdvancedOutputs: bool = computeAdvancedOutputs

        # Defaults physical constants
        ## Basic outputs
        self.grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.specificDensity: float = WATER_DENSITY
        ## Advanced outputs
        self.rockCohesion: float = DEFAULT_ROCK_COHESION
        self.frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def applyFilter( self: Self ) -> bool:
        """Compute the geomechanical outputs of the mesh.

        Returns:
            Boolean (bool): True if calculation successfully ended, False otherwise.
        """
        if not self.checkMandatoryAttributes():
            self.logger.error( "The filter failed." )
            return False

        if not self.computeBasicOutputs():
            return False

        if self.doComputeAdvancedOutputs:
            return self.computeAdvancedOutputs()

        return True

    def getOutput( self: Self ) -> Union[ vtkPointSet, vtkUnstructuredGrid ]:
        """Get the mesh with the geomechanical outputs as attributes.

        Returns:
            Union[vtkPointSet, vtkUnstructuredGrid]: The mesh with the geomechanical outputs as attributes.
        """
        return self.output

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            self.logger.warning(
                "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization."
            )

    def setGrainBulkModulus( self: Self, grainBulkModulus: float ) -> None:
        """Set the grain bulk modulus.

        Args:
            grainBulkModulus (float): Grain bulk modulus.
        """
        self.grainBulkModulus = grainBulkModulus

    def setSpecificDensity( self: Self, specificDensity: float ) -> None:
        """Set the specific density.

        Args:
            specificDensity (float): Specific density.
        """
        self.specificDensity = specificDensity

    def setRockCohesion( self: Self, rockCohesion: float ) -> None:
        """Set the rock cohesion.

        Args:
            rockCohesion (float): Rock cohesion.
        """
        self.rockCohesion = rockCohesion

    def setFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set the friction angle.

        Args:
            frictionAngle (float): Friction angle (rad)
        """
        self.frictionAngle = frictionAngle

    def getOutputType( self: Self ) -> str:
        """Get output object type.

        Returns:
            str: Type of output object.
        """
        return self.output.GetClassName()

    def checkMandatoryAttributes( self: Self ) -> bool:
        """Check that mandatory attributes are present in the mesh.

        The mesh must contains either the young Modulus and Poisson's ratio
        (computeYoungPoisson=False) or the bulk and shear moduli
        (computeYoungPoisson=True)

        Returns:
            bool: True if all needed attributes are present, False otherwise
        """
        self.youngModulusAttributeName: str = PostProcessingOutputsEnum.YOUNG_MODULUS.attributeName
        self.youngModulusOnPoints: bool = PostProcessingOutputsEnum.YOUNG_MODULUS.isOnPoints
        youngModulusOnMesh: bool = isAttributeInObject( self.output, self.youngModulusAttributeName,
                                                        self.youngModulusOnPoints )

        self.poissonRatioAttributeName: str = PostProcessingOutputsEnum.POISSON_RATIO.attributeName
        self.poissonRatioOnPoints: bool = PostProcessingOutputsEnum.POISSON_RATIO.isOnPoints
        poissonRationOnMesh: bool = isAttributeInObject( self.output, self.poissonRatioAttributeName,
                                                         self.poissonRatioOnPoints )

        self.bulkModulusAttributeName: str = GeosMeshOutputsEnum.BULK_MODULUS.attributeName
        self.bulkModulusOnPoints: bool = GeosMeshOutputsEnum.BULK_MODULUS.isOnPoints
        bulkModulusOnMesh: bool = isAttributeInObject( self.output, self.bulkModulusAttributeName,
                                                       self.bulkModulusOnPoints )

        self.shearModulusAttributeName: str = GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName
        self.shearModulusOnPoints: bool = GeosMeshOutputsEnum.SHEAR_MODULUS.isOnPoints
        shearModulusOnMesh: bool = isAttributeInObject( self.output, self.shearModulusAttributeName,
                                                        self.shearModulusOnPoints )

        if not youngModulusOnMesh and not poissonRationOnMesh:
            if bulkModulusOnMesh and shearModulusOnMesh:
                self.computeYoungPoisson = True
            else:
                self.logger.error(
                    f"{ self.bulkModulusAttributeName } or { self.shearModulusAttributeName } are missing to compute geomechanical outputs."
                )
                return False
        elif not bulkModulusOnMesh and not shearModulusOnMesh:
            if youngModulusOnMesh and poissonRationOnMesh:
                self.computeYoungPoisson = False
            else:
                self.logger.error(
                    f"{ self.youngModulusAttributeName } or { self.poissonRatioAttributeName } are missing to compute geomechanical outputs."
                )
        else:
            self.logger.error(
                f"{ self.bulkModulusAttributeName } and { self.shearModulusAttributeName } or { self.youngModulusAttributeName } and { self.poissonRatioAttributeName } are mandatory to compute geomechanical outputs."
            )
            return False

        porosityAttributeName: str = GeosMeshOutputsEnum.POROSITY.attributeName
        porosityOnPoints: bool = GeosMeshOutputsEnum.POROSITY.isOnPoints
        if not isAttributeInObject( self.output, porosityAttributeName, porosityOnPoints ):
            self.logger.error(
                f"The mandatory attribute { porosityAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.porosity: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, porosityAttributeName,
                                                                         porosityOnPoints )

        porosityInitialAttributeName: str = GeosMeshOutputsEnum.POROSITY_INI.attributeName
        porosityInitialOnPoints: bool = GeosMeshOutputsEnum.POROSITY_INI.isOnPoints
        if not isAttributeInObject( self.output, porosityInitialAttributeName, porosityInitialOnPoints ):
            self.logger.error(
                f"The mandatory attribute { porosityInitialAttributeName } is missing to compute geomechanical outputs."
            )
            return False
        else:
            self.porosityInitial: npt.NDArray[ np.float64 ] = getArrayInObject( self.output,
                                                                                porosityInitialAttributeName,
                                                                                porosityInitialOnPoints )

        deltaPressureAttributeName: str = GeosMeshOutputsEnum.DELTA_PRESSURE.attributeName
        deltaPressureOnPoint: bool = GeosMeshOutputsEnum.DELTA_PRESSURE.isOnPoints
        if not isAttributeInObject( self.output, deltaPressureAttributeName, deltaPressureOnPoint ):
            self.logger.error(
                f"The mandatory attribute { deltaPressureAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.deltaPressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, deltaPressureAttributeName,
                                                                              deltaPressureOnPoint )

        densityAttributeName: str = GeosMeshOutputsEnum.ROCK_DENSITY.attributeName
        densityOnPoints: bool = GeosMeshOutputsEnum.ROCK_DENSITY.isOnPoints
        if not isAttributeInObject( self.output, densityAttributeName, densityOnPoints ):
            self.logger.error(
                f"The mandatory attribute { densityAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.density: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, densityAttributeName,
                                                                        densityOnPoints )

        effectiveStressAttributeName: str = GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName
        effectiveStressOnPoints: str = GeosMeshOutputsEnum.STRESS_EFFECTIVE.isOnPoints
        if not isAttributeInObject( self.output, effectiveStressAttributeName, effectiveStressOnPoints ):
            self.logger.error(
                f"The mandatory attribute { effectiveStressAttributeName } is missing to compute geomechanical outputs."
            )
            return False
        else:
            self.effectiveStress: npt.NDArray[ np.float64 ] = getArrayInObject( self.output,
                                                                                effectiveStressAttributeName,
                                                                                effectiveStressOnPoints )

        effectiveStressT0AttributeName: str = PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL.attributeName
        effectiveStressT0OnPoints: bool = PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL.isOnPoints
        if not isAttributeInObject( self.output, effectiveStressT0AttributeName, effectiveStressT0OnPoints ):
            self.logger.error(
                f"The mandatory attribute { effectiveStressT0AttributeName } is missing to compute geomechanical outputs."
            )
            return False
        else:
            self.effectiveStressT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.output,
                                                                                  effectiveStressT0AttributeName,
                                                                                  effectiveStressT0OnPoints )

        pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
        pressureOnPoints: bool = GeosMeshOutputsEnum.PRESSURE.isOnPoints
        if not isAttributeInObject( self.output, pressureAttributeName, pressureOnPoints ):
            self.logger.error(
                f"The mandatory attribute { pressureAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, pressureAttributeName,
                                                                         pressureOnPoints )

        return True

    def computeBasicOutputs( self: Self ) -> bool:
        """Compute basic geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not self.computeElasticModulus():
            self.logger.error( "Elastic modulus computation failed." )
            return False

        if not self.computeBiotCoefficient():
            self.logger.error( "Biot coefficient computation failed." )
            return False

        if not self.computeCompressibilityCoefficient():
            return False

        if not self.computeRealEffectiveStressRatio():
            self.logger.error( "Effective stress ratio computation failed." )
            return False

        if not self.computeSpecificGravity():
            self.logger.error( "Specific gravity computation failed." )
            return False

        # TODO: deactivate lithostatic stress calculation until right formula
        # if not self.computeLithostaticStress():
        #     self.logger.error( "Lithostatic stress computation failed." )
        #     return False

        if not self.computeTotalStresses():
            return False

        if not self.computeElasticStrain():
            self.logger.error( "Elastic strain computation failed." )
            return False

        # oedometric DRSP (effective stress ratio in oedometric conditions)
        if not self.computeEffectiveStressRatioOed():
            self.logger.error( "Effective stress ration in oedometric condition computation failed." )
            return False

        if not self.computeReservoirStressPathOed():
            self.logger.error( "Reservoir stress path in oedometric condition computation failed." )
            return False

        if not self.computeReservoirStressPathReal():
            return False

        self.logger.info( "All geomechanical basic outputs were successfully computed." )
        return True

    def computeAdvancedOutputs( self: Self ) -> bool:
        """Compute advanced geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not self.computeCriticalTotalStressRatio():
            return False

        if not self.computeCriticalPorePressure():
            return False

        mess: str = ( "All geomechanical advanced outputs were successfully computed." )
        self.logger.info( mess )
        return True

    def computeElasticModulus( self: Self ) -> bool:
        """Compute elastic moduli.

        Young modulus and the poisson ratio computed from shear and bulk moduli
        if needed.

        Returns:
            bool: True if elastic moduli are already present or if calculation
            successfully ended, False otherwise.
        """
        self.bulkModulus: npt.NDArray[ np.float64 ]
        self.shearModulus: npt.NDArray[ np.float64 ]
        self.youngModulus: npt.NDArray[ np.float64 ]
        self.poissonRatio: npt.NDArray[ np.float64 ]
        if self.computeYoungPoisson:
            return self.computeElasticModulusFromBulkShear()
        return self.computeElasticModulusFromYoungPoisson()

    def computeElasticModulusFromBulkShear( self: Self ) -> bool:
        """Compute Young modulus Poisson's ratio from bulk and shear moduli.

        Returns:
            bool: True if calculation successfully ended, False otherwise
        """
        self.bulkModulus = getArrayInObject( self.output, self.bulkModulusAttributeName, self.bulkModulusOnPoints )
        self.shearModulus = getArrayInObject( self.output, self.shearModulusAttributeName, self.shearModulusOnPoints )

        self.youngModulus = fcts.youngModulus( self.bulkModulus, self.shearModulus )
        if np.any( self.youngModulus < 0 ):
            self.logger.error( "Young modulus yields negative values. Check Bulk and Shear modulus values." )
            return False

        if not createAttribute( self.output,
                                self.youngModulus,
                                self.youngModulusAttributeName,
                                onPoints=self.youngModulusOnPoints,
                                logger=self.logger ):
            self.logger.error( "Young modulus computation failed." )
            return False

        self.poissonRatio = fcts.poissonRatio( self.bulkModulus, self.shearModulus )
        if np.any( self.poissonRatio < 0 ):
            self.logger.error( "Poisson ratio yields negative values. Check Bulk and Shear modulus values." )
            return False

        if not createAttribute( self.output,
                                self.poissonRatio,
                                self.poissonRatioAttributeName,
                                onPoints=self.poissonRatioOnPoints,
                                logger=self.logger ):
            self.logger.error( "Poisson ration computation failed." )
            return False

        return True

    def computeElasticModulusFromYoungPoisson( self: Self ) -> bool:
        """Compute bulk modulus from Young Modulus and Poisson's ratio.

        Returns:
            bool: True if bulk modulus was successfully computed, False otherwise
        """
        self.youngModulus = getArrayInObject( self.output, self.youngModulusAttributeName, self.youngModulusOnPoints )
        self.poissonRatio = getArrayInObject( self.output, self.poissonRatioAttributeName, self.poissonRatioOnPoints )

        self.bulkModulus = fcts.bulkModulus( self.youngModulus, self.poissonRatio )
        if np.any( self.bulkModulus < 0 ):
            self.logger.error( "Bulk modulus yields negative values. Check Young modulus and Poisson ratio values." )
            return False

        if not createAttribute( self.output,
                                self.bulkModulus,
                                self.bulkModulusAttributeName,
                                onPoints=self.bulkModulusOnPoints,
                                logger=self.logger ):
            self.logger.error( "Bulk modulus computation failed." )
            return False

        self.shearModulus = fcts.shearModulus( self.youngModulus, self.poissonRatio )
        if np.any( self.shearModulus < 0 ):
            self.logger.error( "Shear modulus yields negative values. Check Young modulus and Poisson ratio values." )
            return False

        if not createAttribute( self.output,
                                self.shearModulus,
                                self.shearModulusAttributeName,
                                onPoints=self.shearModulusOnPoints,
                                logger=self.logger ):
            self.logger.error( "Shear modulus computation failed." )
            return False

        return True

    def computeBiotCoefficient( self: Self ) -> bool:
        """Compute Biot coefficient from default and grain bulk modulus.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        biotCoefficientAttributeName: str = PostProcessingOutputsEnum.BIOT_COEFFICIENT.attributeName
        biotCoefficientOnPoints: bool = PostProcessingOutputsEnum.BIOT_COEFFICIENT.isOnPoints
        self.biotCoefficient: npt.NDArray[ np.float64 ]

        if not isAttributeInObject( self.output, biotCoefficientAttributeName, biotCoefficientOnPoints ):
            self.biotCoefficient = fcts.biotCoefficient( self.grainBulkModulus, self.bulkModulus )
            return createAttribute( self.output,
                                    self.biotCoefficient,
                                    biotCoefficientAttributeName,
                                    onPoints=biotCoefficientOnPoints,
                                    logger=self.logger )
        else:
            self.biotCoefficient = getArrayInObject( self.output, biotCoefficientAttributeName,
                                                     biotCoefficientOnPoints )
            self.logger.warning(
                f"{ biotCoefficientAttributeName } is already on the mesh, it has not been computed by the filter." )
            return True

    def computeCompressibilityCoefficient( self: Self ) -> bool:
        """Compute compressibility coefficient from simulation outputs.

        Compressibility coefficient is computed from Poisson's ratio, bulk
        modulus, Biot coefficient and Porosity.

        Returns:
            bool: True if the attribute is correctly created, False otherwise.
        """
        compressibilityAttributeName: str = PostProcessingOutputsEnum.COMPRESSIBILITY.attributeName
        compressibilityOnPoints: bool = PostProcessingOutputsEnum.COMPRESSIBILITY.isOnPoints
        compressibility: npt.NDArray[ np.float64 ] = fcts.compressibility( self.poissonRatio, self.bulkModulus,
                                                                           self.biotCoefficient, self.porosity )
        if not createAttribute( self.output,
                                compressibility,
                                compressibilityAttributeName,
                                onPoints=compressibilityOnPoints,
                                logger=self.logger ):
            self.logger.error( "Compressibility coefficient computation failed." )
            return False

        # oedometric compressibility
        compressibilityOedAttributeName: str = PostProcessingOutputsEnum.COMPRESSIBILITY_OED.attributeName
        compressibilityOedOnPoints: bool = PostProcessingOutputsEnum.COMPRESSIBILITY_OED.isOnPoints
        compressibilityOed: npt.NDArray[ np.float64 ] = fcts.compressibilityOed( self.shearModulus, self.bulkModulus,
                                                                                 self.porosity )
        if not createAttribute( self.output,
                                compressibilityOed,
                                compressibilityOedAttributeName,
                                onPoints=compressibilityOedOnPoints,
                                logger=self.logger ):
            self.logger.error( "Oedometric compressibility coefficient computation failed." )
            return False

        # real compressibility
        compressibilityRealAttributeName: str = PostProcessingOutputsEnum.COMPRESSIBILITY_REAL.attributeName
        compressibilityRealOnPoint: bool = PostProcessingOutputsEnum.COMPRESSIBILITY_REAL.isOnPoints
        compressibilityReal: npt.NDArray[ np.float64 ] = fcts.compressibilityReal( self.deltaPressure, self.porosity,
                                                                                   self.porosityInitial )
        if not createAttribute( self.output,
                                compressibilityReal,
                                compressibilityRealAttributeName,
                                onPoints=compressibilityRealOnPoint,
                                logger=self.logger ):
            self.logger.error( "Real compressibility coefficient computation failed." )
            return False

        return True

    def computeSpecificGravity( self: Self ) -> bool:
        """Create Specific gravity attribute.

        Specific gravity is computed from rock density attribute and specific
        density input.

        Returns:
            bool: True if the attribute is correctly created, False otherwise.
        """
        specificGravityAttributeName: str = PostProcessingOutputsEnum.SPECIFIC_GRAVITY.attributeName
        specificGravityOnPoints: bool = PostProcessingOutputsEnum.SPECIFIC_GRAVITY.isOnPoints
        specificGravity: npt.NDArray[ np.float64 ] = fcts.specificGravity( self.density, self.specificDensity )
        return createAttribute( self.output,
                                specificGravity,
                                specificGravityAttributeName,
                                onPoints=specificGravityOnPoints,
                                logger=self.logger )

    def computeRealEffectiveStressRatio( self: Self ) -> bool:
        """Compute effective stress ratio.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        return self.computeStressRatioReal( self.effectiveStress,
                                            PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_REAL )

    def computeTotalStresses( self: Self ) -> bool:
        """Compute total stress total stress ratio.

        Total stress is computed at the initial and current time steps.
        Total stress ratio is computed at current time step only.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # Compute total stress at initial time step.
        if not self.computeTotalStressInitial():
            self.logger.error( "Total stress at initial time step computation failed." )
            return False

        # Compute total stress at current time step.
        totalStressAttributeName: str = PostProcessingOutputsEnum.STRESS_TOTAL.attributeName
        totalStressOnPoints: bool = PostProcessingOutputsEnum.STRESS_TOTAL.isOnPoints
        self.totalStress: npt.NDArray[ np.float64 ] = self.doComputeTotalStress( self.effectiveStress, self.pressure,
                                                                                 self.biotCoefficient )
        if not createAttribute( self.output,
                                self.totalStress,
                                totalStressAttributeName,
                                componentNames=ComponentNameEnum.XYZ.value,
                                onPoints=totalStressOnPoints,
                                logger=self.logger ):
            self.logger.error( "Total stress at current time step computation failed." )
            return False

        # Compute total stress ratio.
        if not self.computeStressRatioReal( self.totalStress, PostProcessingOutputsEnum.STRESS_TOTAL_RATIO_REAL ):
            self.logger.error( "Total stress ratio computation failed." )
            return False

        return True

    def computeTotalStressInitial( self: Self ) -> bool:
        """Compute total stress at initial time step.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        bulkModulusT0AttributeName: str = PostProcessingOutputsEnum.BULK_MODULUS_INITIAL.attributeName
        youngModulusT0AttributeName: str = PostProcessingOutputsEnum.YOUNG_MODULUS_INITIAL.attributeName
        poissonRatioT0AttributeName: str = PostProcessingOutputsEnum.POISSON_RATIO_INITIAL.attributeName

        bulkModulusT0OnPoints: bool = PostProcessingOutputsEnum.BULK_MODULUS_INITIAL.isOnPoints
        youngModulusT0OnPoints: bool = PostProcessingOutputsEnum.YOUNG_MODULUS_INITIAL.isOnPoints
        poissonRatioT0OnPoints: bool = PostProcessingOutputsEnum.POISSON_RATIO_INITIAL.isOnPoints

        # Compute BulkModulus at initial time step.
        bulkModulusT0: npt.NDArray[ np.float64 ]
        if isAttributeInObject( self.output, bulkModulusT0AttributeName, bulkModulusT0OnPoints ):
            bulkModulusT0 = getArrayInObject( self.output, bulkModulusT0AttributeName, bulkModulusT0OnPoints )
        elif isAttributeInObject( self.output, youngModulusT0AttributeName, youngModulusT0OnPoints ) \
             and isAttributeInObject( self.output, poissonRatioT0AttributeName, poissonRatioT0OnPoints ):
            youngModulusT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, youngModulusT0AttributeName,
                                                                          youngModulusT0OnPoints )
            poissonRatioT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, poissonRatioT0AttributeName,
                                                                          poissonRatioT0OnPoints )
            bulkModulusT0 = fcts.bulkModulus( youngModulusT0, poissonRatioT0 )
        else:
            self.logger( "Elastic moduli at initial time are absent." )
            return False

        # Compute Biot at initial time step.
        biotCoefficientT0: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( self.grainBulkModulus, bulkModulusT0 )

        pressureT0: Union[ npt.NDArray[ np.float64 ], None ] = None
        # Case pressureT0 is None, total stress = effective stress
        # (managed by doComputeTotalStress function)
        if self.pressure is not None:
            # Get delta pressure to recompute pressure at initial time step (pressureTo)
            pressureT0 = self.pressure - self.deltaPressure

        totalStressT0AttributeName: str = PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL.attributeName
        totalStressT0OnPoints: bool = PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL.isOnPoints
        self.totalStressT0 = self.doComputeTotalStress( self.effectiveStressT0, pressureT0, biotCoefficientT0 )
        return createAttribute( self.output,
                                self.totalStressT0,
                                totalStressT0AttributeName,
                                componentNames=ComponentNameEnum.XYZ.value,
                                onPoints=totalStressT0OnPoints,
                                logger=self.logger )

    def doComputeTotalStress(
        self: Self,
        effectiveStress: npt.NDArray[ np.float64 ],
        pressure: Union[ npt.NDArray[ np.float64 ], None ],
        biotCoefficient: npt.NDArray[ np.float64 ],
    ) -> npt.NDArray[ np.float64 ]:
        """Compute total stress from effective stress and pressure.

        Args:
            effectiveStress (npt.NDArray[np.float64]): Effective stress.
            pressure (npt.NDArray[np.float64] | None): Pressure.
            biotCoefficient (npt.NDArray[np.float64]): Biot coefficient.

        Returns:
            npt.NDArray[ np.float64 ]: TotalStress.
        """
        totalStress: npt.NDArray[ np.float64 ]
        if pressure is None:
            totalStress = np.copy( effectiveStress )
            self.logger.warning( "Pressure attribute is undefined, total stress will be equal to effective stress." )
        else:
            if np.isnan( pressure ).any():
                self.logger.warning( "Some cells do not have pressure data, for those cells, pressure is set to 0." )
                pressure[ np.isnan( pressure ) ] = 0.0

            totalStress = fcts.totalStress( effectiveStress, biotCoefficient, pressure )

        return totalStress

    def computeLithostaticStress( self: Self ) -> bool:
        """Compute lithostatic stress.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        lithostaticStressAttributeName: str = PostProcessingOutputsEnum.LITHOSTATIC_STRESS.attributeName
        lithostaticStressOnPoint: bool = PostProcessingOutputsEnum.LITHOSTATIC_STRESS.isOnPoints

        depth: npt.NDArray[
            np.float64 ] = self.computeDepthAlongLine() if lithostaticStressOnPoint else self.computeDepthInMesh()
        lithostaticStress = fcts.lithostaticStress( depth, self.density, GRAVITY )
        return createAttribute( self.output,
                                lithostaticStress,
                                lithostaticStressAttributeName,
                                onPoints=lithostaticStressOnPoint,
                                logger=self.logger )

    def computeDepthAlongLine( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Compute depth along a line.

        Returns:
            npt.NDArray[np.float64]: 1D array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ] = self.getZcoordinates( True )
        assert zCoord is not None, "Depth coordinates cannot be computed."

        # TODO: to find how to compute depth in a general case
        # GEOS z axis is upward
        depth: npt.NDArray[ np.float64 ] = -1.0 * zCoord
        return depth

    def computeDepthInMesh( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Compute depth of each cell in a mesh.

        Returns:
            npt.NDArray[np.float64]: array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ] = self.getZcoordinates( False )
        assert zCoord is not None, "Depth coordinates cannot be computed."

        # TODO: to find how to compute depth in a general case
        depth: npt.NDArray[ np.float64 ] = -1.0 * zCoord
        return depth

    def getZcoordinates( self: Self, onPoints: bool ) -> npt.NDArray[ np.float64 ]:
        """Get z coordinates from self.output.

        Args:
            onPoints (bool): True if the attribute is on points, False if it is on cells.

        Returns:
            npt.NDArray[np.float64]: 1D array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ]
        pointCoords: npt.NDArray[ np.float64 ] = self.getPointCoordinates( onPoints )
        assert pointCoords is not None, "Point coordinates are undefined."
        assert pointCoords.shape[ 1 ] == 2, "Point coordinates are undefined."
        zCoord = pointCoords[ :, 2 ]
        return zCoord

    def computeElasticStrain( self: Self ) -> bool:
        """Compute elastic strain from effective stress and elastic modulus.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        deltaEffectiveStress = self.effectiveStress - self.effectiveStressT0

        elasticStrainAttributeName: str = PostProcessingOutputsEnum.STRAIN_ELASTIC.attributeName
        elasticStrainOnPoints: bool = PostProcessingOutputsEnum.STRAIN_ELASTIC.isOnPoints
        elasticStrain: npt.NDArray[ np.float64 ]
        if self.computeYoungPoisson:
            elasticStrain = fcts.elasticStrainFromBulkShear( deltaEffectiveStress, self.bulkModulus, self.shearModulus )
        else:
            elasticStrain = fcts.elasticStrainFromYoungPoisson( deltaEffectiveStress, self.youngModulus,
                                                                self.poissonRatio )

        return createAttribute( self.output,
                                elasticStrain,
                                elasticStrainAttributeName,
                                componentNames=ComponentNameEnum.XYZ.value,
                                onPoints=elasticStrainOnPoints,
                                logger=self.logger )

    def computeReservoirStressPathReal( self: Self ) -> bool:
        """Compute reservoir stress paths.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # create delta stress attribute for QC
        deltaTotalStressAttributeName: str = PostProcessingOutputsEnum.STRESS_TOTAL_DELTA.attributeName
        deltaTotalStressOnPoints: bool = PostProcessingOutputsEnum.STRESS_TOTAL_DELTA.isOnPoints
        self.deltaTotalStress: npt.NDArray[ np.float64 ] = self.totalStress - self.totalStressT0
        if not createAttribute( self.output,
                                self.deltaTotalStress,
                                deltaTotalStressAttributeName,
                                componentNames=ComponentNameEnum.XYZ.value,
                                onPoints=deltaTotalStressOnPoints,
                                logger=self.logger ):
            self.logger.error( "Delta total stress computation failed." )
            return False

        rspRealAttributeName: str = PostProcessingOutputsEnum.RSP_REAL.attributeName
        rspRealOnPoints: bool = PostProcessingOutputsEnum.RSP_REAL.isOnPoints
        self.rspReal: npt.NDArray[ np.float64 ] = fcts.reservoirStressPathReal( self.deltaTotalStress,
                                                                                self.deltaPressure )
        if not createAttribute( self.output,
                                self.rspReal,
                                rspRealAttributeName,
                                componentNames=ComponentNameEnum.XYZ.value,
                                onPoints=rspRealOnPoints,
                                logger=self.logger ):
            self.logger.error( "Reservoir stress real path computation failed." )
            return False

        return True

    def computeReservoirStressPathOed( self: Self ) -> bool:
        """Compute Reservoir Stress Path in oedometric conditions.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        rspOedAttributeName: str = PostProcessingOutputsEnum.RSP_OED.attributeName
        rspOedOnPoints: bool = PostProcessingOutputsEnum.RSP_OED.isOnPoints
        self.rspOed: npt.NDArray[ np.float64 ] = fcts.reservoirStressPathOed( self.biotCoefficient, self.poissonRatio )
        return createAttribute( self.output,
                                self.rspOed,
                                rspOedAttributeName,
                                onPoints=rspOedOnPoints,
                                logger=self.logger )

    def computeStressRatioReal( self: Self, stress: npt.NDArray[ np.float64 ], outputAttribute: AttributeEnum ) -> bool:
        """Compute the ratio between horizontal and vertical effective stress.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        verticalStress: npt.NDArray[ np.float64 ] = stress[ :, 2 ]
        # keep the minimum of the 2 horizontal components
        horizontalStress: npt.NDArray[ np.float64 ] = np.min( stress[ :, :2 ], axis=1 )

        stressRatioRealAttributeName: str = outputAttribute.attributeName
        stressRatioRealOnPoints: bool = outputAttribute.isOnPoints
        self.stressRatioReal: npt.NDArray[ np.float64 ] = fcts.stressRatio( horizontalStress, verticalStress )
        return createAttribute( self.output,
                                self.stressRatioReal,
                                stressRatioRealAttributeName,
                                onPoints=stressRatioRealOnPoints,
                                logger=self.logger )

    def computeEffectiveStressRatioOed( self: Self ) -> bool:
        """Compute the effective stress ratio in oedometric conditions.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        effectiveStressRatioOedAttributeName: str = PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_OED.attributeName
        effectiveStressRatioOedOnPoints: bool = PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_OED.isOnPoints
        effectiveStressRatioOed: npt.NDArray[ np.float64 ] = fcts.deviatoricStressPathOed( self.poissonRatio )
        return createAttribute( self.output,
                                effectiveStressRatioOed,
                                effectiveStressRatioOedAttributeName,
                                onPoints=effectiveStressRatioOedOnPoints,
                                logger=self.logger )

    def computeCriticalTotalStressRatio( self: Self ) -> bool:
        """Compute fracture index and fracture threshold.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        fractureIndexAttributeName: str = PostProcessingOutputsEnum.CRITICAL_TOTAL_STRESS_RATIO.attributeName
        fractureIndexOnPoints: bool = PostProcessingOutputsEnum.CRITICAL_TOTAL_STRESS_RATIO.isOnPoints
        verticalStress: npt.NDArray[ np.float64 ] = self.totalStress[ :, 2 ]
        criticalTotalStressRatio: npt.NDArray[ np.float64 ] = fcts.criticalTotalStressRatio(
            self.pressure, verticalStress )
        if not createAttribute( self.output,
                                criticalTotalStressRatio,
                                fractureIndexAttributeName,
                                onPoints=fractureIndexOnPoints,
                                logger=self.logger ):
            self.logger.error( "Fracture index computation failed." )
            return False

        mask: npt.NDArray[ np.bool_ ] = np.argmin( np.abs( self.totalStress[ :, :2 ] ), axis=1 )
        horizontalStress: npt.NDArray[ np.float64 ] = self.totalStress[ :, :2 ][
            np.arange( self.totalStress[ :, :2 ].shape[ 0 ] ), mask ]

        stressRatioThreshold: npt.NDArray[ np.float64 ] = fcts.totalStressRatioThreshold(
            self.pressure, horizontalStress )
        fractureThresholdAttributeName: str = PostProcessingOutputsEnum.TOTAL_STRESS_RATIO_THRESHOLD.attributeName
        fractureThresholdOnPoints: bool = PostProcessingOutputsEnum.TOTAL_STRESS_RATIO_THRESHOLD.isOnPoints
        if not createAttribute( self.output,
                                stressRatioThreshold,
                                fractureThresholdAttributeName,
                                onPoints=fractureThresholdOnPoints,
                                logger=self.logger ):
            self.logger.error( "Fracture threshold computation failed." )
            return False

        return True

    def computeCriticalPorePressure( self: Self ) -> bool:
        """Compute the critical pore pressure and the pressure index.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        criticalPorePressureAttributeName: str = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE.attributeName
        criticalPorePressureOnPoints: bool = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE.isOnPoints
        criticalPorePressure: npt.NDArray[ np.float64 ] = fcts.criticalPorePressure( -1.0 * self.totalStress,
                                                                                     self.rockCohesion,
                                                                                     self.frictionAngle )
        if not createAttribute( self.output,
                                criticalPorePressure,
                                criticalPorePressureAttributeName,
                                onPoints=criticalPorePressureOnPoints,
                                logger=self.logger ):
            self.logger.error( "Critical pore pressure computation failed." )
            return False

        # add critical pore pressure index (i.e., ratio between pressure and criticalPorePressure)
        criticalPorePressureIndex: npt.NDArray[ np.float64 ] = fcts.criticalPorePressureThreshold(
            self.pressure, criticalPorePressure )
        criticalPorePressureIndexAttributeName: str = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName
        criticalPorePressureIndexOnPoint: bool = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE_THRESHOLD.isOnPoints
        if not createAttribute( self.output,
                                criticalPorePressureIndex,
                                criticalPorePressureIndexAttributeName,
                                onPoints=criticalPorePressureIndexOnPoint,
                                logger=self.logger ):
            self.logger.error( "Critical pore pressure indexes computation failed." )
            return False

        return True

    def getPointCoordinates( self: Self, onPoints: bool ) -> npt.NDArray[ np.float64 ]:
        """Get the coordinates of Points or Cell center.

        Args:
            onPoints (bool): True if the attribute is on points, False if it is on cells.

        Returns:
            npt.NDArray[np.float64]: points/cell center coordinates
        """
        if onPoints:
            return self.output.GetPoints()  # type: ignore[no-any-return]
        else:
            # Find cell centers
            filter = vtkCellCenters()
            filter.SetInputDataObject( self.output )
            filter.Update()
            return filter.GetOutput().GetPoints()  # type: ignore[no-any-return]
