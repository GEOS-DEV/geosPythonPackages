# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Union

import geos.geomechanics.processing.geomechanicsCalculatorFunctions as fcts

import numpy as np
import numpy.typing as npt
import logging

from geos.utils.GeosOutputsConstants import (
    AttributeEnum,
    ComponentNameEnum,
    GeosMeshOutputsEnum,
    PostProcessingOutputsEnum,
)
from geos.utils.Logger import Logger, getLogger
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_GRAIN_BULK_MODULUS,
    DEFAULT_ROCK_COHESION,
    GRAVITY,
    WATER_DENSITY,
)
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import (
    vtkDataSet,
    vtkPointSet,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkFiltersCore import vtkCellCenters
from geos.mesh.utils.arrayModifiers import createAttribute
from geos.mesh.utils.arrayHelpers import (
    getArrayInObject,
    getComponentNames,
    isAttributeInObject,
)

__doc__ = """
GeomechanicsCalculator module is a vtk filter that allows to compute additional
Geomechanical properties from existing ones.

GeomechanicsCalculator filter inputs are either vtkPointSet or vtkUnstructuredGrid
and returned object is of same type as input.

To use the filter:

.. code-block:: python

    import numpy as np
    from geos.mesh.processing.GeomechanicsCalculator import GeomechanicsCalculator

    # filter inputs
    logger :Logger
    # input object
    input :Union[vtkPointSet, vtkUnstructuredGrid]
    # grain bulk modulus in Pa (e.g., use a very high value to get a Biot coefficient equal to 1)
    grainBulkModulus :float = 1e26
    # Reference density to compute specific gravity (e.g. fresh water density) in kg.m^-3
    specificDensity :float = 1000.
    # rock cohesion in Pa
    rockCohesion :float = 1e8
    # friction angle in °
    frictionAngle :float = 10 * np.pi / 180.

    # instantiate the filter
    geomechanicsCalculatorFilter :GeomechanicsCalculator = GeomechanicsCalculator()

    # set filter attributes
    # set logger
    geomechanicsCalculatorFilter.SetLogger(logger)
    # set input object
    geomechanicsCalculatorFilter.SetInputDataObject(input)
    # set computeAdvancedOutputsOn or computeAdvancedOutputsOff to compute or
    # not advanced outputs...
    geomechanicsCalculatorFilter.computeAdvancedOutputsOn()
    # set other parameters
    geomechanicsCalculatorFilter.SetGrainBulkModulus(grainBulkModulus)
    geomechanicsCalculatorFilter.SetSpecificDensity(specificDensity)
    # rock cohesion and friction angle are used for advanced outputs only
    geomechanicsCalculatorFilter.SetRockCohesion(rockCohesion)
    geomechanicsCalculatorFilter.SetFrictionAngle(frictionAngle)
    # do calculations
    geomechanicsCalculatorFilter.Update()
    # get filter output (same type as input)
    output :Union[vtkPointSet, vtkUnstructuredGrid] = geomechanicsCalculatorFilter.GetOutputDataObject(0)
"""

TYPE_ERROR_MESSAGE = ( "Input object must by either a vtkPointSet or a vtkUnstructuredGrid." )
UNDEFINED_ATTRIBUTE_MESSAGE = " attribute is undefined."

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

        self.mesh: Union[ vtkPointSet, vtkUnstructuredGrid ] = mesh
        self.output: Union[ vtkPointSet, vtkUnstructuredGrid ] = vtkDataSet()
        self.output.DeepCopy( self.mesh )

        # additional parameters
        self.m_computeAdvancedOutputs: bool = computeAdvancedOutputs
        self.m_grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.m_specificDensity: float = WATER_DENSITY
        self.m_rockCohesion: float = DEFAULT_ROCK_COHESION
        self.m_frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        # elastic moduli are either bulk and Shear moduli (m_computeYoungPoisson=True)
        # or young Modulus and poisson's ratio (m_computeYoungPoisson=False)
        self.m_computeYoungPoisson: bool = True

        # Logger.
        self.m_logger: Logger
        if not speHandler:
            self.m_logger = getLogger( loggerTitle, True )
        else:
            self.m_logger = logging.getLogger( loggerTitle )
            self.m_logger.setLevel( logging.INFO )


    def applyFilter( self: Self ) -> bool:
        """Compute the geomechanical coefficient of the mesh.

        Returns:
            Boolean (bool): True if calculation successfully ended, False otherwise.
        """
        if not self.checkMandatoryAttributes():
            self.m_logger.error( "The filter failed." )
            return False

        if not self.computeBasicOutputs():
            return False

        if self.m_computeAdvancedOutputs:
            if not self.computeAdvancedOutputs():
                return False

        return True

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.m_logger.hasHandlers():
            self.m_logger.addHandler( handler )
        else:
            self.m_logger.warning(
                "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization."
            )

    def setGrainBulkModulus( self: Self, grainBulkModulus: float ) -> None:
        """Set the grain bulk modulus.

        Args:
            grainBulkModulus (float): Grain bulk modulus.
        """
        self.m_grainBulkModulus = grainBulkModulus

    def setSpecificDensity( self: Self, specificDensity: float ) -> None:
        """Set the specific density.

        Args:
            specificDensity (float): Specific density.
        """
        self.m_specificDensity = specificDensity

    def setRockCohesion( self: Self, rockCohesion: float ) -> None:
        """Set the rock cohesion.

        Args:
            rockCohesion (float): Rock cohesion.
        """
        self.m_rockCohesion = rockCohesion

    def setFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set the friction angle.

        Args:
            frictionAngle (float): Friction angle (rad)
        """
        self.m_frictionAngle = frictionAngle

    def getOutputType( self: Self ) -> str:
        """Get output object type.

        Returns:
            str: Type of output object.
        """
        return self.output.GetClassName()

    def checkMandatoryAttributes( self: Self ) -> bool:
        """Check that mandatory attributes are present in the mesh.

        The mesh must contains either the young Modulus and Poisson's ratio
        (m_computeYoungPoisson=False) or the bulk and shear moduli
        (m_computeYoungPoisson=True)

        Returns:
            bool: True if all needed attributes are present, False otherwise
        """
        self.youngModulusAttributeName: str = PostProcessingOutputsEnum.YOUNG_MODULUS.attributeName
        self.poissonRatioAttributeName: str = PostProcessingOutputsEnum.POISSON_RATIO.attributeName
        self.youngModulusOnPoints: bool = PostProcessingOutputsEnum.YOUNG_MODULUS.isOnPoints
        self.poissonRatioOnPoints: bool = PostProcessingOutputsEnum.POISSON_RATIO.isOnPoints

        self.m_computeYoungPoisson = not isAttributeInObject( self.output, self.youngModulusAttributeName, self.youngModulusOnPoints ) \
                                     or not isAttributeInObject( self.output, self.poissonRatioAttributeName, self.poissonRatioOnPoints )

        # if none of elastic moduli is present, return False
        if self.m_computeYoungPoisson:
            self.bulkModulusAttributeName: str = GeosMeshOutputsEnum.BULK_MODULUS.attributeName
            self.shearModulusAttributeName: str = GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName
            self.bulkModulusOnPoints: str = GeosMeshOutputsEnum.BULK_MODULUS.isOnPoints
            self.shearModulusOnPoints: str = GeosMeshOutputsEnum.SHEAR_MODULUS.isOnPoints

            if not isAttributeInObject( self.output, self.bulkModulusAttributeName, self.bulkModulusOnPoints ) \
               or not isAttributeInObject( self.output, self.shearModulusAttributeName, self.shearModulusOnPoints ):
                mess: str = ( "Mandatory properties are missing to compute geomechanical outputs:" )
                mess += ( f"Either { self.bulkModulusAttributeName } and { self.shearModulusAttributeName } or { self.youngModulusAttributeName } and { self.poissonRatioAttributeName } must be present in the table data." )
                self.m_logger.error( mess )
                return False
        
        porosityAttributeName: str = GeosMeshOutputsEnum.POROSITY.attributeName
        porosityOnPoints: bool = GeosMeshOutputsEnum.POROSITY.isOnPoints
        if not isAttributeInObject( self.output, porosityAttributeName, porosityOnPoints ):
            self.m_logger.error( f"The mandatory attribute { porosityAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.porosity: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, porosityAttributeName, porosityOnPoints )

        porosityInitialAttributeName: str = GeosMeshOutputsEnum.POROSITY_INI.attributeName
        porosityInitialOnPoints: bool = GeosMeshOutputsEnum.POROSITY_INI.isOnPoints
        if not isAttributeInObject( self.output, porosityInitialAttributeName, porosityInitialOnPoints ):
            self.m_logger.error( f"The mandatory attribute { porosityInitialAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.porosityInitial: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, porosityInitialAttributeName, porosityInitialOnPoints )

        deltaPressureAttributeName: str = GeosMeshOutputsEnum.DELTA_PRESSURE.attributeName
        deltaPressureOnPoint: bool = GeosMeshOutputsEnum.DELTA_PRESSURE.isOnPoints
        if not isAttributeInObject( self.output, deltaPressureAttributeName, deltaPressureOnPoint ):
            self.m_logger.error( f"The mandatory attribute { deltaPressureAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.deltaPressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, deltaPressureAttributeName, deltaPressureOnPoint )

        densityAttributeName: str = GeosMeshOutputsEnum.ROCK_DENSITY.attributeName
        densityOnPoints: bool = GeosMeshOutputsEnum.ROCK_DENSITY.isOnPoints
        if not isAttributeInObject( self.output, densityAttributeName, densityOnPoints ):
            self.m_logger.error( f"The mandatory attribute { densityAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.density: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, densityAttributeName, densityOnPoints )

        effectiveStressAttributeName: str = GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName
        effectiveStressOnPoints: str = GeosMeshOutputsEnum.STRESS_EFFECTIVE.isOnPoints
        if not isAttributeInObject( self.output, effectiveStressAttributeName, effectiveStressOnPoints ):
            self.m_logger.error( f"The mandatory attribute { effectiveStressAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.effectiveStress: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, effectiveStressAttributeName, effectiveStressOnPoints )

        effectiveStressT0AttributeName: str = PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL.attributeName
        effectiveStressT0OnPoints: bool = PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL.isOnPoints
        if not isAttributeInObject( self.output, effectiveStressT0AttributeName, effectiveStressT0OnPoints ):
            self.m_logger.error( f"The mandatory attribute { effectiveStressT0AttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.effectiveStressT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, effectiveStressT0AttributeName, effectiveStressT0OnPoints )

        pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
        pressureOnPoints: bool = GeosMeshOutputsEnum.PRESSURE.isOnPoints
        if not isAttributeInObject( self.output, pressureAttributeName, pressureOnPoints ):
            self.m_logger.error( f"The mandatory attribute { pressureAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, pressureAttributeName, pressureOnPoints )

        deltaPressureAttributeName: str = GeosMeshOutputsEnum.DELTA_PRESSURE.attributeName
        deltaPressureOnPoint: bool = GeosMeshOutputsEnum.DELTA_PRESSURE.isOnPoints
        if not isAttributeInObject( self.output, deltaPressureAttributeName, deltaPressureOnPoint ):
            self.m_logger.error( f"The mandatory attribute { deltaPressureAttributeName } is missing to compute geomechanical outputs." )
            return False
        else:
            self.deltaPressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, deltaPressureAttributeName, deltaPressureOnPoint )

        return True

    def computeBasicOutputs( self: Self ) -> bool:
        """Compute basic geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not self.computeElasticModulus():
            self.m_logger.error( "Elastic modulus computation failed." )
            return False

        if not self.computeBiotCoefficient():
            self.m_logger.error( "Biot coefficient computation failed." )
            return False

        if not self.computeCompressibilityCoefficient():
            return False

        if not self.computeRealEffectiveStressRatio():
            self.m_logger.error( "Effective stress ratio computation failed." )
            return False

        if not self.computeSpecificGravity():
            self.m_logger.error( "Specific gravity computation failed.")
            return False

        # TODO: deactivate lithostatic stress calculation until right formula
        # if not self.computeLithostaticStress():
        #     self.m_logger.error( "Lithostatic stress computation failed." )
        #     return False

        if not self.computeTotalStresses():
            return False

        if not self.computeElasticStrain():
            self.m_logger.error( "Elastic strain computation failed." )
            return False

        # oedometric DRSP (effective stress ratio in oedometric conditions)
        if not self.computeEffectiveStressRatioOed():
            self.m_logger.error( "Effective stress ration in oedometric condition computation failed." )
            return False

        if not self.computeReservoirStressPathOed():
            self.m_logger.error( "Reservoir stress path in oedometric condition computation failed." )
            return False

        if not self.computeReservoirStressPathReal():
            return False

        self.m_logger.info( "All geomechanical basic outputs were successfully computed." )
        return True

    def computeAdvancedOutputs( self: Self ) -> bool:
        """Compute advanced geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        fractureIndexesComputed: bool = False
        criticalPorePressure: bool = False
        if self.m_totalStressComputed:
            fractureIndexesComputed = self.computeCriticalTotalStressRatio()
            criticalPorePressure = self.computeCriticalPorePressure()

        if ( self.m_effectiveStressRatioOedComputed and fractureIndexesComputed and criticalPorePressure ):
            mess: str = ( "All geomechanical advanced outputs were " + "successfully computed." )
            self.m_logger.info( mess )
            return True
        else:
            mess0: str = ( "Some geomechanical advanced outputs were " + "not computed." )
            self.m_logger.error( mess0 )
            return False

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
        if self.m_computeYoungPoisson:
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
            self.m_logger.error( "Young modulus yields negative values. Check Bulk and Shear modulus values." )
            return False
        
        if not createAttribute( self.output,
                                self.youngModulus,
                                self.youngModulusAttributeName,
                                onPoints=self.youngModulusOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Young modulus computation failed." )
            return False

        self.poissonRatio = fcts.poissonRatio( self.bulkModulus, self.shearModulus )
        if np.any( self.poissonRatio < 0 ):
            self.m_logger.error( "Poisson ratio yields negative values. Check Bulk and Shear modulus values.")
            return False

        if not createAttribute( self.output,
                                self.poissonRatio,
                                self.poissonRatioAttributeName,
                                onPoints=self.poissonRatioOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Poisson ration computation failed." )
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
            self.m_logger.error( "Bulk modulus yields negative values. Check Young modulus and Poisson ratio values.")
            return False
        
        if not createAttribute( self.output,
                                self.bulkModulus,
                                self.bulkModulusAttributeName,
                                onPoints=self.bulkModulusOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Bulk modulus computation failed." )
            return False
            
        self.shearModulus = fcts.shearModulus( self.youngModulus, self.poissonRatio )
        if np.any( self.shearModulus < 0 ):
            self.m_logger.error( "Shear modulus yields negative values. Check Young modulus and Poisson ratio values.")
            return False
        
        if not createAttribute( self.output,
                                self.shearModulus,
                                self.shearModulusAttributeName,
                                onPoints=self.shearModulusOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Shear modulus computation failed." )
            return False
        
        return True

    def computeBiotCoefficient( self: Self ) -> bool:
        """Compute Biot coefficient from default and grain bulk modulus.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        biotCoefficientAttributeName: str = PostProcessingOutputsEnum.BIOT_COEFFICIENT.attributeName
        biotCoefficientOnPoints: bool = PostProcessingOutputsEnum.BIOT_COEFFICIENT.isOnPoints
        self.biotCoefficient: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( self.m_grainBulkModulus, self.bulkModulus )
        return createAttribute( self.output,
                                self.biotCoefficient,
                                biotCoefficientAttributeName,
                                onPoints=biotCoefficientOnPoints,
                                logger=self.m_logger )

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
                                logger=self.m_logger ):
            self.m_logger.error( "Compressibility coefficient computation failed." )
            return False

        # oedometric compressibility
        compressibilityOedAttributeName: str = PostProcessingOutputsEnum.COMPRESSIBILITY_OED.attributeName
        compressibilityOedOnPoints: bool = PostProcessingOutputsEnum.COMPRESSIBILITY_OED.isOnPoints
        compressibilityOed: npt.NDArray[ np.float64 ] = fcts.compressibilityOed( self.shearModulus, self.bulkModulus, self.porosity )
        if not createAttribute( self.output,
                                compressibilityOed,
                                compressibilityOedAttributeName,
                                onPoints=compressibilityOedOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Oedometric compressibility coefficient computation failed." )
            return False

        # real compressibility
        compressibilityRealAttributeName: str = PostProcessingOutputsEnum.COMPRESSIBILITY_REAL.attributeName
        compressibilityRealOnPoint: bool = PostProcessingOutputsEnum.COMPRESSIBILITY_REAL.isOnPoints
        compressibilityReal: npt.NDArray[ np.float64 ] = fcts.compressibilityReal( self.deltaPressure, self.porosity, self.porosityInitial )
        if not createAttribute( self.output,
                                compressibilityReal,
                                compressibilityRealAttributeName,
                                onPoints=compressibilityRealOnPoint,
                                logger=self.m_logger ):
            self.m_logger.error( "Real compressibility coefficient computation failed.")
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
        specificGravity: npt.NDArray[ np.float64 ] = fcts.specificGravity( self.density, self.m_specificDensity )
        return createAttribute( self.output,
                                specificGravity,
                                specificGravityAttributeName,
                                onPoints=specificGravityOnPoints,
                                logger=self.m_logger )

    def computeRealEffectiveStressRatio( self: Self ) -> bool:
        """Compute effective stress ratio.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        return self.computeStressRatioReal( self.effectiveStress, PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_REAL )

    def computeTotalStresses( self: Self ) -> bool:
        """Compute total stress total stress ratio.

        Total stress is computed at the initial and current time steps.
        Total stress ratio is computed at current time step only.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # Compute total stress at initial time step.
        if not self.computeTotalStressInitial():
            self.m_logger.error( "Total stress at initial time step computation failed.")
            return False

        # Compute total stress at current time step.
        totalStressAttributeName: str = PostProcessingOutputsEnum.STRESS_TOTAL.attributeName
        totalStressOnPoints: bool = PostProcessingOutputsEnum.STRESS_TOTAL.isOnPoints
        totalStressComponentNames: tuple[ str, ...] = tuple()
        if PostProcessingOutputsEnum.STRESS_TOTAL.nbComponent > 1:
            totalStressComponentNames = getComponentNames( self.output, totalStressAttributeName, totalStressOnPoints )
        self.totalStress: npt.NDArray[ np.float64 ] = self.doComputeTotalStress( self.effectiveStress, self.pressure, self.biotCoefficient )
        if not createAttribute( self.output,
                                self.totalStress,
                                totalStressAttributeName,
                                componentNames=totalStressComponentNames,
                                onPoints=totalStressOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Total stress at current time step computation failed.")
            return False
        
        # Compute total stress ratio.
        if not self.computeStressRatioReal( self.totalStress, PostProcessingOutputsEnum.STRESS_TOTAL_RATIO_REAL ):
            self.m_logger.error( "Total stress ratio computation failed.")
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
            youngModulusT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, youngModulusT0AttributeName, youngModulusT0OnPoints )
            poissonRatioT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, poissonRatioT0AttributeName, poissonRatioT0OnPoints )
            bulkModulusT0 = fcts.bulkModulus( youngModulusT0, poissonRatioT0 )
        else:
            self.m_logger( "Elastic moduli at initial time are absent." )

        # Compute Biot at initial time step.
        biotCoefficientT0: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( self.m_grainBulkModulus, bulkModulusT0 )

        pressureT0: npt.NDArray[ np.float64 ]
        # Case pressureT0 is None, total stress = effective stress
        # (managed by doComputeTotalStress function)
        if self.pressure is not None:
            # Get delta pressure to recompute pressure at initial time step (pressureTo)
            pressureT0 = self.pressure - self.deltaPressure

        totalStressT0AttributeName: str = PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL.attributeName
        totalStressT0OnPoints: bool = PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL.isOnPoints
        totalStressT0ComponentNames: tuple[ str, ...] = tuple()
        if PostProcessingOutputsEnum.STRESS_TOTAL.nbComponent > 1:
            totalStressT0ComponentNames = getComponentNames( self.output, totalStressT0AttributeName, totalStressT0OnPoints )
        self.totalStressT0 = self.doComputeTotalStress( self.effectiveStressT0, pressureT0, biotCoefficientT0 )
        return createAttribute( self.output,
                                self.totalStressT0,
                                totalStressT0AttributeName,
                                componentNames=totalStressT0ComponentNames,
                                onPoints=totalStressT0OnPoints,
                                logger=self.m_logger )

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
            self.m_logger.warning( "Pressure attribute is undefined, total stress will be equal to effective stress." )
        else:
            if np.isnan( pressure ).any():
                self.m_logger.warning( "Some cells do not have pressure data, for those cells, pressure is set to 0." )
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

        depth: npt.NDArray[ np.float64 ] = self.computeDepthAlongLine() if lithostaticStressOnPoint else self.computeDepthInMesh()
        lithostaticStress = fcts.lithostaticStress( depth, self.density, GRAVITY )
        return createAttribute( self.output,
                                lithostaticStress,
                                lithostaticStressAttributeName,
                                onPoints=lithostaticStressOnPoint,
                                logger=self.m_logger)

    def computeDepthAlongLine( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Compute depth along a line.

        Returns:
            npt.NDArray[np.float64]: 1D array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ] = self.getZcoordinates()
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
        zCoord: npt.NDArray[ np.float64 ] = self.getZcoordinates()
        assert zCoord is not None, "Depth coordinates cannot be computed."

        # TODO: to find how to compute depth in a general case
        depth: npt.NDArray[ np.float64 ] = -1.0 * zCoord
        return depth

    def getZcoordinates( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Get z coordinates from self.output.

        Returns:
            npt.NDArray[np.float64]: 1D array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ]
        pointCoords: npt.NDArray[ np.float64 ] = self.getPointCoordinates()
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
        elasticStrainComponentNames: tuple[ str, ...] = tuple()
        if PostProcessingOutputsEnum.STRESS_TOTAL.nbComponent > 1:
            elasticStrainComponentNames = getComponentNames( self.output, elasticStrainAttributeName, elasticStrainOnPoints )
        
        if self.m_computeYoungPoisson:
            elasticStrain: npt.NDArray[ np.float64 ] = fcts.elasticStrainFromBulkShear( deltaEffectiveStress, self.bulkModulus, self.shearModulus )
        else:
            elasticStrain: npt.NDArray[ np.float64 ] = fcts.elasticStrainFromYoungPoisson( deltaEffectiveStress, self.youngModulus, self.poissonRatio )

        return createAttribute( self.output,
                                elasticStrain,
                                elasticStrainAttributeName,
                                componentNames=elasticStrainComponentNames,
                                onPoints=elasticStrainOnPoints,
                                logger=self.m_logger )

    def computeReservoirStressPathReal( self: Self ) -> bool:
        """Compute reservoir stress paths.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        # create delta stress attribute for QC
        deltaTotalStressAttributeName: str = PostProcessingOutputsEnum.STRESS_TOTAL_DELTA.attributeName
        deltaTotalStressOnPoints: bool = PostProcessingOutputsEnum.STRESS_TOTAL_DELTA.isOnPoints
        deltaTotalStressComponentNames: tuple[ str, ...] = tuple()
        if PostProcessingOutputsEnum.STRESS_TOTAL_DELTA.nbComponent > 1 :
            deltaTotalStressComponentNames = getComponentNames( self.output, deltaTotalStressAttributeName, deltaTotalStressOnPoints )
        self.deltaTotalStress: npt.NDArray[ np.float64 ] = self.totalStress - self.totalStressT0
        if not createAttribute( self.output,
                                self.deltaTotalStress,
                                deltaTotalStressAttributeName,
                                componentNames=deltaTotalStressComponentNames,
                                onPoints=deltaTotalStressOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Delta total stress computation failed.")
            return False

        rspRealAttributeName: str = PostProcessingOutputsEnum.RSP_REAL.attributeName
        rspRealOnPoints: bool = PostProcessingOutputsEnum.RSP_REAL.isOnPoints
        rspRealComponentNames: tuple[ str, ...] = tuple()
        if PostProcessingOutputsEnum.RSP_REAL.nbComponent > 1 :
            rspRealComponentNames = getComponentNames( self.output, rspRealAttributeName, rspRealOnPoints )
        self.rspReal: npt.NDArray[ np.float64 ] = fcts.reservoirStressPathReal( self.deltaTotalStress, self.deltaPressure )
        if not createAttribute( self.output,
                                self.rspReal,
                                rspRealAttributeName,
                                componentNames=rspRealComponentNames,
                                onPoints=rspRealOnPoints,
                                logger=self.m_logger ):
            self.m_logger.error( "Reservoir stress real path computation failed." )
            return False

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
                                logger=self.m_logger )

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
                                logger=self.m_logger)

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
                                logger=self.m_logger )

    def computeCriticalTotalStressRatio( self: Self ) -> bool:
        """Compute fracture index and fracture threshold.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        ret: bool = True

        fractureIndexAttributeName = ( PostProcessingOutputsEnum.CRITICAL_TOTAL_STRESS_RATIO.attributeName )
        if not isAttributeInObject( self.output, fractureIndexAttributeName, self.m_attributeOnPoints ):

            stressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL.attributeName )
            stress: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, stressAttributeName,
                                                                  self.m_attributeOnPoints )

            pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
            pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, pressureAttributeName,
                                                                    self.m_attributeOnPoints )

            try:
                assert stress is not None, ( f"{stressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert pressure is not None, ( f"{pressureAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert stress.shape[ 1 ] >= 3
            except AssertionError as e:
                self.m_logger.error( "Critical total stress ratio and threshold were not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

            # fracture index
            try:
                verticalStress: npt.NDArray[ np.float64 ] = stress[ :, 2 ]
                criticalTotalStressRatio: npt.NDArray[ np.float64 ] = ( fcts.criticalTotalStressRatio(
                    pressure, verticalStress ) )
                createAttribute(
                    self.output,
                    criticalTotalStressRatio,
                    fractureIndexAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Critical total stress ratio was not computed due to:" )
                self.m_logger.error( str( e ) )
                ret = False

            # fracture threshold
            try:
                mask: npt.NDArray[ np.bool_ ] = np.argmin( np.abs( stress[ :, :2 ] ), axis=1 )
                horizontalStress: npt.NDArray[ np.float64 ] = stress[ :, :2 ][ np.arange( stress[ :, :2 ].shape[ 0 ] ),
                                                                               mask ]

                stressRatioThreshold: npt.NDArray[ np.float64 ] = ( fcts.totalStressRatioThreshold(
                    pressure, horizontalStress ) )
                fractureThresholdAttributeName = (
                    PostProcessingOutputsEnum.TOTAL_STRESS_RATIO_THRESHOLD.attributeName )
                createAttribute(
                    self.output,
                    stressRatioThreshold,
                    fractureThresholdAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Total stress ratio threshold was not computed due to:" )
                self.m_logger.error( str( e ) )
                ret = False

        return ret

    def computeCriticalPorePressure( self: Self ) -> bool:
        """Compute the critical pore pressure and the pressure index.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        ret: bool = True
        criticalPorePressureAttributeName = ( PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE.attributeName )
        if not isAttributeInObject( self.output, criticalPorePressureAttributeName, self.m_attributeOnPoints ):

            stressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL.attributeName )
            stress: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, stressAttributeName,
                                                                  self.m_attributeOnPoints )

            pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
            pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.output, pressureAttributeName,
                                                                    self.m_attributeOnPoints )

            try:
                assert self.m_rockCohesion is not None, "Rock cohesion is undefined."
                assert self.m_frictionAngle is not None, "Friction angle is undefined."
                assert stress is not None, ( f"{stressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert pressure is not None, ( f"{pressureAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert stress.shape[ 1 ] >= 3
            except AssertionError as e:
                self.m_logger.error( "Critical pore pressure and threshold were not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

            try:
                criticalPorePressure: npt.NDArray[ np.float64 ] = ( fcts.criticalPorePressure(
                    -1.0 * stress, self.m_rockCohesion, self.m_frictionAngle ) )
                createAttribute(
                    self.output,
                    criticalPorePressure,
                    criticalPorePressureAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Critical pore pressure was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

            try:
                # add critical pore pressure index (i.e., ratio between pressure and criticalPorePressure)
                assert criticalPorePressure is not None, ( "Critical pore pressure attribute" + " was not created" )
                criticalPorePressureIndex: npt.NDArray[ np.float64 ] = ( fcts.criticalPorePressureThreshold(
                    pressure, criticalPorePressure ) )
                criticalPorePressureIndexAttributeName = (
                    PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName )
                createAttribute(
                    self.output,
                    criticalPorePressureIndex,
                    criticalPorePressureIndexAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Pore pressure threshold was not computed due to:" )
                self.m_logger.error( str( e ) )
                ret = False

        return ret

    def getPointCoordinates( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Get the coordinates of Points or Cell center.

        Returns:
            npt.NDArray[np.float64]: points/cell center coordinates
        """
        if self.m_attributeOnPoints:
            return self.output.GetPoints()  # type: ignore[no-any-return]
        else:
            # Find cell centers
            filter = vtkCellCenters()
            filter.SetInputDataObject( self.output )
            filter.Update()
            return filter.GetOutput().GetPoints()  # type: ignore[no-any-return]
