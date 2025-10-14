# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Union
from typing_extensions import Self
from dataclasses import dataclass, field

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
GeomechanicsCalculator module is a vtk filter that allows to compute additional geomechanical properties from existing ones:
    - The Young modulus and the Poisson's ratio named "youngModulus" and "poissonRatio" or bulk and shear moduli named "bulkModulus" and "shearModulus"
    - The initial Young modulus and Poisson's ratio named "youngModulusInitial" and "poissonRatioInitial" or the initial bulk modulus named "bulkModulusInitial"
    - The porosity named "porosity"
    - The initial porosity named "porosityInitial"
    - The delta of pressure named "deltaPressure"
    - The density named "density"
    - The effective stress named "stressEffective"
    - The initial effective stress named "stressEffectiveInitial"
    - The pressure named "pressure"

The basic geomechanics outputs are:
    - Biot coefficient
    - Compressibility, oedometric compressibility and real compressibility coefficient
    - Specific gravity
    - Real effective stress ratio
    - Total initial stress, total current stress and total stress ratio
    - Lithostatic stress (physic to update)
    - Elastic stain
    - Reservoir stress path and reservoir stress path in oedometric condition

The advanced geomechanics outputs are:
    - Fracture index and threshold
    - Critical pore pressure and pressure index

GeomechanicsCalculator filter input mesh is either vtkPointSet or vtkUnstructuredGrid
and returned mesh is of same type as input.

  .. Important::
            Please refer to the GeosExtractMergeBlockVolume* filters to provide the correct input.

.. Note::
    - The default physical constants used by the filter are:
        - grainBulkModulus = 38e9 Pa ( quartz value )
        - specificDensity = 1000.0 kg/m³ ( water value )
        - rockCohesion = 0.0 Pa ( fractured case )
        - frictionAngle = 10.0°

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

# Elastic Moduli:
BULK_MODULUS: AttributeEnum = GeosMeshOutputsEnum.BULK_MODULUS
SHEAR_MODULUS: AttributeEnum = GeosMeshOutputsEnum.SHEAR_MODULUS
YOUNG_MODULUS: AttributeEnum = PostProcessingOutputsEnum.YOUNG_MODULUS
POISSON_RATIO: AttributeEnum = PostProcessingOutputsEnum.POISSON_RATIO
BULK_MODULUS_T0: AttributeEnum = PostProcessingOutputsEnum.BULK_MODULUS_INITIAL
YOUNG_MODULUS_T0: AttributeEnum = PostProcessingOutputsEnum.YOUNG_MODULUS_INITIAL
POISSON_RATIO_T0: AttributeEnum = PostProcessingOutputsEnum.POISSON_RATIO_INITIAL

# Mandatory attributes:
POROSITY: AttributeEnum = GeosMeshOutputsEnum.POROSITY
POROSITY_T0: AttributeEnum = GeosMeshOutputsEnum.POROSITY_INI
PRESSURE: AttributeEnum = GeosMeshOutputsEnum.PRESSURE
DELTA_PRESSURE: AttributeEnum = GeosMeshOutputsEnum.DELTA_PRESSURE
DENSITY: AttributeEnum = GeosMeshOutputsEnum.ROCK_DENSITY
STRESS_EFFECTIVE: AttributeEnum = GeosMeshOutputsEnum.STRESS_EFFECTIVE
STRESS_EFFECTIVE_T0: AttributeEnum = PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL

# Basic outputs:
BIOT_COEFFICIENT: AttributeEnum = PostProcessingOutputsEnum.BIOT_COEFFICIENT
COMPRESSIBILITY: AttributeEnum = PostProcessingOutputsEnum.COMPRESSIBILITY
COMPRESSIBILITY_OED: AttributeEnum = PostProcessingOutputsEnum.COMPRESSIBILITY_OED
COMPRESSIBILITY_REAL: AttributeEnum = PostProcessingOutputsEnum.COMPRESSIBILITY_REAL
SPECIFIC_GRAVITY: AttributeEnum = PostProcessingOutputsEnum.SPECIFIC_GRAVITY
STRESS_EFFECTIVE_RATIO_REAL: AttributeEnum = PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_REAL
STRESS_TOTAL: AttributeEnum = PostProcessingOutputsEnum.STRESS_TOTAL
STRESS_TOTAL_T0: AttributeEnum = PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL
STRESS_TOTAL_RATIO_REAL: AttributeEnum = PostProcessingOutputsEnum.STRESS_TOTAL_RATIO_REAL
LITHOSTATIC_STRESS: AttributeEnum = PostProcessingOutputsEnum.LITHOSTATIC_STRESS
STRAIN_ELASTIC: AttributeEnum = PostProcessingOutputsEnum.STRAIN_ELASTIC
STRESS_TOTAL_DELTA: AttributeEnum = PostProcessingOutputsEnum.STRESS_TOTAL_DELTA
RSP_REAL: AttributeEnum = PostProcessingOutputsEnum.RSP_REAL
RSP_OED: AttributeEnum = PostProcessingOutputsEnum.RSP_OED
STRESS_EFFECTIVE_RATIO_OED: AttributeEnum = PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_OED

# Advanced outputs:
CRITICAL_TOTAL_STRESS_RATIO: AttributeEnum = PostProcessingOutputsEnum.CRITICAL_TOTAL_STRESS_RATIO
TOTAL_STRESS_RATIO_THRESHOLD: AttributeEnum = PostProcessingOutputsEnum.TOTAL_STRESS_RATIO_THRESHOLD
CRITICAL_PORE_PRESSURE: AttributeEnum = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE
CRITICAL_PORE_PRESSURE_THRESHOLD: AttributeEnum = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE_THRESHOLD


class GeomechanicsCalculator:

    @dataclass
    class PhysicalConstants:
        ## Basic outputs
        _grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        _specificDensity: float = WATER_DENSITY
        ## Advanced outputs
        _rockCohesion: float = DEFAULT_ROCK_COHESION
        _frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        @property
        def grainBulkModulus( self: Self ) -> float:
            return self._grainBulkModulus

        @grainBulkModulus.setter
        def grainBulkModulus( self: Self, value: float ) -> None:
            self._grainBulkModulus = value

        @property
        def specificDensity( self: Self ) -> float:
            return self._specificDensity

        @specificDensity.setter
        def specificDensity( self: Self, value: float ) -> None:
            self._specificDensity = value

        @property
        def rockCohesion( self: Self ) -> float:
            return self._rockCohesion

        @rockCohesion.setter
        def rockCohesion( self: Self, value: float ) -> None:
            self._rockCohesion = value

        @property
        def frictionAngle( self: Self ) -> float:
            return self._frictionAngle

        @frictionAngle.setter
        def frictionAngle( self: Self, value: float ) -> None:
            self._frictionAngle = value

    physicalConstants: PhysicalConstants = PhysicalConstants()

    @dataclass
    class MandatoryAttributes:
        _dictMandatoryAttribute: dict[ AttributeEnum, npt.NDArray[ np.float64 ] ] = field( default_factory=dict )

        @property
        def dictMandatoryAttribute( self: Self ) -> dict[ AttributeEnum, npt.NDArray[ np.float64 ] ]:
            return self._dictMandatoryAttribute

        @dictMandatoryAttribute.setter
        def dictMandatoryAttribute( self: Self, attributeValue: tuple[ AttributeEnum, npt.NDArray[ np.float64 ] ] ) -> None:
            self._dictMandatoryAttribute[ attributeValue[ 0 ] ] = attributeValue[ 1 ]

        @property
        def porosity( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictMandatoryAttribute[ POROSITY ]

        @property
        def porosityInitial( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictMandatoryAttribute[ POROSITY_T0 ]

        @property
        def pressure( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictMandatoryAttribute[ PRESSURE ]

        @property
        def deltaPressure( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictMandatoryAttribute[ DELTA_PRESSURE ]

        @property
        def density( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictMandatoryAttribute[ DENSITY ]

        @property
        def effectiveStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictMandatoryAttribute[ STRESS_EFFECTIVE ]

        @property
        def effectiveStressT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictMandatoryAttribute[ STRESS_EFFECTIVE_T0 ]

    _mandatoryAttributes: MandatoryAttributes = MandatoryAttributes()

    @dataclass
    class ElasticModuli:
        _dictElasticModuli: dict[ AttributeEnum, npt.NDArray[ np.float64 ] ] = field( default_factory=dict)

        @property
        def dictElasticModuli( self: Self ) -> dict[ AttributeEnum, npt.NDArray[ np.float64 ] ]:
            return self._dictElasticModuli

        @dictElasticModuli.setter
        def dictElasticModuli( self: Self, value: tuple[ AttributeEnum, npt.NDArray[ np.float64 ] ] ) -> None:
            self._dictElasticModuli[ value[ 0 ] ] = value[ 1 ]

        @property
        def bulkModulus( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictElasticModuli[ BULK_MODULUS ]

        @bulkModulus.setter
        def bulkModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictElasticModuli[ BULK_MODULUS ] = value

        @property
        def shearModulus( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictElasticModuli[ SHEAR_MODULUS ]

        @shearModulus.setter
        def shearModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictElasticModuli[ SHEAR_MODULUS ] = value

        @property
        def youngModulus( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictElasticModuli[ YOUNG_MODULUS ]

        @youngModulus.setter
        def youngModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictElasticModuli[ YOUNG_MODULUS ] = value

        @property
        def poissonRatio( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictElasticModuli[ POISSON_RATIO ]

        @poissonRatio.setter
        def poissonRatio( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictElasticModuli[ POISSON_RATIO ] = value

        @property
        def bulkModulusT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictElasticModuli[ BULK_MODULUS_T0 ]

        @bulkModulusT0.setter
        def bulkModulusT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictElasticModuli[ BULK_MODULUS_T0 ] = value

        @property
        def youngModulusT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictElasticModuli[ YOUNG_MODULUS_T0 ]

        @youngModulusT0.setter
        def youngModulusT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictElasticModuli[ YOUNG_MODULUS_T0 ] = value

        @property
        def poissonRatioT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictElasticModuli[ POISSON_RATIO_T0 ]

        @poissonRatioT0.setter
        def poissonRatioT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictElasticModuli[ POISSON_RATIO_T0 ] = value

    _elasticModuli: ElasticModuli = ElasticModuli()

    @dataclass
    class BasicOutput:
        _dictBasicOutput: dict[ AttributeEnum, npt.NDArray[ np.float64 ] ] = field( default_factory=dict )

        @property
        def dictBasicOutput( self: Self ) -> dict[ AttributeEnum, npt.NDArray[ np.float64 ] ]:
            return self._dictBasicOutput

        @property
        def biotCoefficient( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ BIOT_COEFFICIENT ]

        @biotCoefficient.setter
        def biotCoefficient( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ BIOT_COEFFICIENT ] = value

        @property
        def compressibility( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ COMPRESSIBILITY ]

        @compressibility.setter
        def compressibility( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ COMPRESSIBILITY ] = value

        @property
        def compressibilityOed( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ COMPRESSIBILITY_OED ]

        @compressibilityOed.setter
        def compressibilityOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ COMPRESSIBILITY_OED ] = value

        @property
        def compressibilityReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ COMPRESSIBILITY_REAL ]

        @compressibilityReal.setter
        def compressibilityReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ COMPRESSIBILITY_REAL ] = value

        @property
        def specificGravity( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ SPECIFIC_GRAVITY ]

        @specificGravity.setter
        def specificGravity( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ SPECIFIC_GRAVITY ] = value

        @property
        def effectiveStressRatioReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ STRESS_EFFECTIVE_RATIO_REAL ]

        @effectiveStressRatioReal.setter
        def effectiveStressRatioReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ STRESS_EFFECTIVE_RATIO_REAL ] = value

        @property
        def totalStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ STRESS_TOTAL ]

        @totalStress.setter
        def totalStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ STRESS_TOTAL ] = value

        @property
        def totalStressT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ STRESS_TOTAL_T0 ]

        @totalStressT0.setter
        def totalStressT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ STRESS_TOTAL_T0 ] = value

        @property
        def totalStressRatioReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ STRESS_TOTAL_RATIO_REAL ]

        @totalStressRatioReal.setter
        def totalStressRatioReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ STRESS_TOTAL_RATIO_REAL ] = value

        @property
        def lithostaticStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ LITHOSTATIC_STRESS ]

        @lithostaticStress.setter
        def lithostaticStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ LITHOSTATIC_STRESS ] = value

        @property
        def elasticStrain( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ STRAIN_ELASTIC ]

        @elasticStrain.setter
        def elasticStrain( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ STRAIN_ELASTIC ] = value

        @property
        def deltaTotalStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ STRESS_TOTAL_DELTA ]

        @deltaTotalStress.setter
        def deltaTotalStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ STRESS_TOTAL_DELTA ] = value

        @property
        def rspReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ RSP_REAL ]

        @rspReal.setter
        def rspReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ RSP_REAL ] = value

        @property
        def rspOed( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ RSP_OED ]

        @rspOed.setter
        def rspOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ RSP_OED ] = value

        @property
        def effectiveStressRatioOed( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictBasicOutput[ STRESS_EFFECTIVE_RATIO_OED ]

        @effectiveStressRatioOed.setter
        def effectiveStressRatioOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictBasicOutput[ STRESS_EFFECTIVE_RATIO_OED ] = value

    _basicOutput: BasicOutput = BasicOutput()

    @dataclass
    class AdvancedOutput:
        _dictAdvancedOutput: dict[ AttributeEnum, npt.NDArray[ np.float64 ] ] = field( default_factory=dict )

        @property
        def dictAdvancedOutput( self: Self ) -> dict[ AttributeEnum, npt.NDArray[ np.float64 ] ]:
            return self._dictAdvancedOutput

        @property
        def criticalTotalStressRatio( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictAdvancedOutput[ CRITICAL_TOTAL_STRESS_RATIO ]

        @criticalTotalStressRatio.setter
        def criticalTotalStressRatio( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictAdvancedOutput[ CRITICAL_TOTAL_STRESS_RATIO ] = value

        @property
        def stressRatioThreshold( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictAdvancedOutput[ TOTAL_STRESS_RATIO_THRESHOLD ]

        @stressRatioThreshold.setter
        def stressRatioThreshold( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictAdvancedOutput[ TOTAL_STRESS_RATIO_THRESHOLD ] = value

        @property
        def criticalPorePressure( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictAdvancedOutput[ CRITICAL_PORE_PRESSURE ]

        @criticalPorePressure.setter
        def criticalPorePressure( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictAdvancedOutput[ CRITICAL_PORE_PRESSURE ] = value

        @property
        def criticalPorePressureIndex( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._dictAdvancedOutput[ CRITICAL_PORE_PRESSURE_THRESHOLD ]

        @criticalPorePressureIndex.setter
        def criticalPorePressureIndex( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._dictAdvancedOutput[ CRITICAL_PORE_PRESSURE_THRESHOLD ] = value

    _advancedOutput: AdvancedOutput = AdvancedOutput()

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
        self.output: Union[ vtkPointSet, vtkUnstructuredGrid ] = mesh.NewInstance()
        self.output.DeepCopy( mesh )

        self.doComputeAdvancedOutputs: bool = computeAdvancedOutputs

        self._mandatoryAttributes._dictMandatoryAttribute = {
            POROSITY: np.array( [] ),
            POROSITY_T0: np.array( [] ),
            PRESSURE: np.array( [] ),
            DELTA_PRESSURE: np.array( [] ),
            DENSITY: np.array( [] ),
            STRESS_EFFECTIVE: np.array( [] ),
            STRESS_EFFECTIVE_T0: np.array( [] ),
        }
        self._elasticModuli._dictElasticModuli = {
            BULK_MODULUS: np.array( [] ),
            SHEAR_MODULUS: np.array( [] ),
            YOUNG_MODULUS: np.array( [] ),
            POISSON_RATIO: np.array( [] ),
            BULK_MODULUS_T0: np.array( [] ),
            YOUNG_MODULUS_T0: np.array( [] ),
            POISSON_RATIO_T0: np.array( [] ),
        }
        self._basicOutput._dictBasicOutput = {
            BIOT_COEFFICIENT: np.array( [] ),
            COMPRESSIBILITY: np.array( [] ),
            COMPRESSIBILITY_OED: np.array( [] ),
            COMPRESSIBILITY_REAL: np.array( [] ),
            SPECIFIC_GRAVITY: np.array( [] ),
            STRESS_EFFECTIVE_RATIO_REAL: np.array( [] ),
            STRESS_TOTAL: np.array( [] ),
            STRESS_TOTAL_T0: np.array( [] ),
            STRESS_TOTAL_RATIO_REAL: np.array( [] ),
            # LITHOSTATIC_STRESS: np.array( [] ),
            STRAIN_ELASTIC: np.array( [] ),
            STRESS_TOTAL_DELTA: np.array( [] ),
            RSP_REAL: np.array( [] ),
            RSP_OED: np.array( [] ),
            STRESS_EFFECTIVE_RATIO_OED: np.array( [] ),
        }
        self._advancedOutput._dictAdvancedOutput = {
            CRITICAL_TOTAL_STRESS_RATIO: np.array( [] ),
            TOTAL_STRESS_RATIO_THRESHOLD: np.array( [] ),
            CRITICAL_PORE_PRESSURE: np.array( [] ),
            CRITICAL_PORE_PRESSURE_THRESHOLD: np.array( [] ),
        }

        self._outputPresent: list[ str ] = []

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
        if not self._checkMandatoryAttributes():
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

    def getOutputType( self: Self ) -> str:
        """Get output object type.

        Returns:
            str: Type of output object.
        """
        return self.output.GetClassName()

    def _checkMandatoryAttributes( self: Self ) -> bool:
        """Check that mandatory attributes are present in the mesh.

        The mesh must contains:
            - The Young modulus and the Poisson's ratio named "youngModulus" and "poissonRatio" or bulk and shear moduli named "bulkModulus" and "shearModulus"
            - The initial Young modulus and Poisson's ratio named "youngModulusInitial" and "poissonRatioInitial" or the initial bulk modulus named "bulkModulusInitial"
            - The porosity named "porosity"
            - The initial porosity named "porosityInitial"
            - The pressure named "pressure"
            - The delta of pressure named "deltaPressure"
            - The density named "density"
            - The effective stress named "stressEffective"
            - The initial effective stress named "stressEffectiveInitial"

        Returns:
            bool: True if all needed attributes are present, False otherwise
        """
        for elasticModulus in self._elasticModuli.dictElasticModuli:
            elasticModulusName: str = elasticModulus.attributeName
            elasticModulusOnPoints: bool = elasticModulus.isOnPoints
            if isAttributeInObject( self.output, elasticModulusName, elasticModulusOnPoints ):
                self._elasticModuli._dictElasticModuli = ( elasticModulus, getArrayInObject( self.output, elasticModulusName, elasticModulusOnPoints ) )

        # Check the presence of the elastic moduli at the current time.
        self.computeYoungPoisson: bool
        if self._elasticModuli.youngModulus.size == 0 and self._elasticModuli.poissonRatio.size == 0:
            if self._elasticModuli.bulkModulus.size != 0 and self._elasticModuli.shearModulus.size != 0:
                self._elasticModuli.youngModulus = fcts.youngModulus( self._elasticModuli.bulkModulus,
                                                                      self._elasticModuli.shearModulus )
                self._elasticModuli.poissonRatio = fcts.poissonRatio( self._elasticModuli.bulkModulus,
                                                                      self._elasticModuli.shearModulus )
                self.computeYoungPoisson = True
            else:
                self.logger.error(
                    f"{ BULK_MODULUS.attributeName } or { SHEAR_MODULUS.attributeName } are missing to compute geomechanical outputs."
                )
                return False
        elif self._elasticModuli.bulkModulus.size == 0 and self._elasticModuli.shearModulus.size == 0:
            if self._elasticModuli.youngModulus.size != 0 and self._elasticModuli.poissonRatio.size != 0:
                self._elasticModuli.bulkModulus = fcts.bulkModulus( self._elasticModuli.youngModulus,
                                                                    self._elasticModuli.poissonRatio )
                self._elasticModuli.shearModulus = fcts.shearModulus( self._elasticModuli.youngModulus,
                                                                      self._elasticModuli.poissonRatio )
                self.computeYoungPoisson = False
            else:
                self.logger.error(
                    f"{ YOUNG_MODULUS.attributeName } or { POISSON_RATIO.attributeName } are missing to compute geomechanical outputs."
                )
                return False
        else:
            self.logger.error(
                f"{ BULK_MODULUS.attributeName } and { SHEAR_MODULUS.attributeName } or { YOUNG_MODULUS.attributeName } and { POISSON_RATIO.attributeName } are mandatory to compute geomechanical outputs."
            )
            return False

        # Check the presence of the elastic moduli at the initial time.
        if self._elasticModuli.bulkModulusT0.size == 0:
            if self._elasticModuli.youngModulusT0.size != 0 and self._elasticModuli.poissonRatioT0.size != 0:
                self._elasticModuli.bulkModulusT0 = fcts.bulkModulus( self._elasticModuli.youngModulusT0,
                                                                      self._elasticModuli.poissonRatioT0 )
            else:
                self.logger.error(
                    f"{ BULK_MODULUS_T0.attributeName } or { YOUNG_MODULUS_T0.attributeName } and { POISSON_RATIO_T0.attributeName } are mandatory to compute geomechanical outputs."
                )
                return False

        # Check the presence of the other mandatory attributes
        for mandatoryAttribute in self._mandatoryAttributes.dictMandatoryAttribute:
            mandatoryAttributeName: str = mandatoryAttribute.attributeName
            mandatoryAttributeOnPoints: bool = mandatoryAttribute.isOnPoints
            if not isAttributeInObject( self.output, mandatoryAttributeName, mandatoryAttributeOnPoints ):
                self.logger.error(
                    f"The mandatory attribute { mandatoryAttributeName } is missing to compute geomechanical outputs." )
                return False
            else:
                self._mandatoryAttributes.dictMandatoryAttribute = ( mandatoryAttribute, getArrayInObject( self.output, mandatoryAttributeName, mandatoryAttributeOnPoints ) )

        return True

    def computeBasicOutputs( self: Self ) -> bool:
        """Compute basic geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not self._computeBiotCoefficient():
            self.logger.error( "Biot coefficient computation failed." )
            return False

        if not self._computeCompressibilityCoefficient():
            return False

        if not self._computeRealEffectiveStressRatio():
            self.logger.error( "Effective stress ratio computation failed." )
            return False

        if not self._computeSpecificGravity():
            self.logger.error( "Specific gravity computation failed." )
            return False

        # TODO: deactivate lithostatic stress calculation until right formula
        # if not self.computeLithostaticStress():
        #     self.logger.error( "Lithostatic stress computation failed." )
        #     return False

        if not self._computeTotalStresses():
            return False

        if not self._computeElasticStrain():
            self.logger.error( "Elastic strain computation failed." )
            return False

        if not self._computeEffectiveStressRatioOed():
            self.logger.error( "Effective stress ration in oedometric condition computation failed." )
            return False

        if not self._computeReservoirStressPathOed():
            self.logger.error( "Reservoir stress path in oedometric condition computation failed." )
            return False

        if not self._computeReservoirStressPathReal():
            return False

        # Create an attribute on the mesh for each basic outputs
        for basicOutput, array in self._basicOutput.dictBasicOutput.items():
            # Basic outputs with multiple components:
            if basicOutput.attributeName in [ STRESS_TOTAL.attributeName, STRESS_TOTAL_T0.attributeName, STRESS_TOTAL_DELTA.attributeName, STRAIN_ELASTIC.attributeName, RSP_REAL.attributeName ]:
                if not createAttribute( self.output, array, basicOutput.attributeName, componentNames=ComponentNameEnum.XYZ.value, onPoints=basicOutput.isOnPoints, logger=self.logger ):
                    return False
            # Other basic outputs:
            elif basicOutput.attributeName not in self._outputPresent and not createAttribute( self.output, array, basicOutput.attributeName, onPoints=basicOutput.isOnPoints, logger=self.logger ):
                    return False

        self.logger.info( "All geomechanical basic outputs were successfully computed." )
        return True

    def computeAdvancedOutputs( self: Self ) -> bool:
        """Compute advanced geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not self._computeCriticalTotalStressRatio():
            return False

        if not self._computeCriticalPorePressure():
            return False

        # Create an attribute on the mesh for each advanced outputs
        for advancedOutput, array in self._advancedOutput.dictAdvancedOutput.items():
            if advancedOutput not in self._outputPresent and not createAttribute( self.output, array, advancedOutput.attributeName, onPoints=advancedOutput.isOnPoints, logger=self.logger ):
                return False

        self.logger.info( "All geomechanical advanced outputs were successfully computed." )
        return True

    def _computeBiotCoefficient( self: Self ) -> bool:
        """Compute Biot coefficient from default and grain bulk modulus.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        if not isAttributeInObject( self.output, BIOT_COEFFICIENT.attributeName, BIOT_COEFFICIENT.isOnPoints ):
            self._basicOutput.biotCoefficient = fcts.biotCoefficient( self.physicalConstants.grainBulkModulus,
                                                                      self._elasticModuli.bulkModulus )
        else:
            self._outputPresent.append( BIOT_COEFFICIENT.attributeName )
            self._basicOutput.biotCoefficient = getArrayInObject( self.output, BIOT_COEFFICIENT.attributeName,
                                                                  BIOT_COEFFICIENT.isOnPoints )
            self.logger.warning(
                f"{ BIOT_COEFFICIENT.attributeName } is already on the mesh, it has not been computed by the filter." )

        return True

    def _computeCompressibilityCoefficient( self: Self ) -> bool:
        """Compute compressibility coefficient from simulation outputs.

        Compressibility coefficient is computed from Poisson's ratio, bulk
        modulus, Biot coefficient and Porosity.

        Returns:
            bool: True if the attribute is correctly created, False otherwise.
        """
        if not isAttributeInObject( self.output, COMPRESSIBILITY.attributeName, COMPRESSIBILITY.isOnPoints ):
            self._basicOutput.compressibility = fcts.compressibility( self._elasticModuli.poissonRatio,
                                                                      self._elasticModuli.bulkModulus,
                                                                      self._basicOutput.biotCoefficient,
                                                                      self._mandatoryAttributes.porosity )
        else:
            self._outputPresent.append( COMPRESSIBILITY.attributeName )
            self._basicOutput.compressibility = getArrayInObject( self.output, COMPRESSIBILITY.attributeName,
                                                                  COMPRESSIBILITY.isOnPoints )
            self.logger.warning(
                f"{ COMPRESSIBILITY.attributeName } is already on the mesh, it has not been computed by the filter." )

        # oedometric compressibility
        if not isAttributeInObject( self.output, COMPRESSIBILITY_OED.attributeName, COMPRESSIBILITY_OED.isOnPoints ):
            self._basicOutput.compressibilityOed = fcts.compressibilityOed( self._elasticModuli.shearModulus,
                                                                         self._elasticModuli.bulkModulus,
                                                                         self._mandatoryAttributes.porosity )
        else:
            self._outputPresent.append( COMPRESSIBILITY_OED.attributeName )
            self._basicOutput.compressibilityOed = getArrayInObject( self.output, COMPRESSIBILITY_OED.attributeName,
                                                                  COMPRESSIBILITY_OED.isOnPoints )
            self.logger.warning(
                f"{ COMPRESSIBILITY_OED.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        # real compressibility
        if not isAttributeInObject( self.output, COMPRESSIBILITY_REAL.attributeName, COMPRESSIBILITY_REAL.isOnPoints ):
            self._basicOutput.compressibilityReal = fcts.compressibilityReal(
                self._mandatoryAttributes.deltaPressure, self._mandatoryAttributes.porosity,
                self._mandatoryAttributes.porosityInitial )
        else:
            self._outputPresent.append( COMPRESSIBILITY_REAL.attributeName )
            self._basicOutput.compressibilityReal = getArrayInObject( self.output, COMPRESSIBILITY_REAL.attributeName,
                                                                      COMPRESSIBILITY_REAL.isOnPoints )
            self.logger.warning(
                f"{ COMPRESSIBILITY_REAL.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return True

    def _computeSpecificGravity( self: Self ) -> bool:
        """Create Specific gravity attribute.

        Specific gravity is computed from rock density attribute and specific
        density input.

        Returns:
            bool: True if the attribute is correctly created, False otherwise.
        """
        if not isAttributeInObject( self.output, SPECIFIC_GRAVITY.attributeName, SPECIFIC_GRAVITY.isOnPoints ):
            self._basicOutput.specificGravity = fcts.specificGravity( self._mandatoryAttributes.density,
                                                                      self.physicalConstants.specificDensity )
        else:
            self._outputPresent.append( SPECIFIC_GRAVITY.attributeName )
            self._basicOutput.specificGravity = getArrayInObject( self.output, SPECIFIC_GRAVITY.attributeName,
                                                                  SPECIFIC_GRAVITY.isOnPoints )
            self.logger.warning(
                f"{ SPECIFIC_GRAVITY.attributeName } is already on the mesh, it has not been computed by the filter." )

        return True

    def _doComputeStressRatioReal( self: Self, stress: npt.NDArray[ np.float64 ],
                                   basicOutput: AttributeEnum ) -> npt.NDArray[ np.float64 ]:
        """Compute the ratio between horizontal and vertical effective stress.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        verticalStress: npt.NDArray[ np.float64 ] = stress[ :, 2 ]
        # keep the minimum of the 2 horizontal components
        horizontalStress: npt.NDArray[ np.float64 ] = np.min( stress[ :, :2 ], axis=1 )

        stressRatioReal: npt.NDArray[ np.float64 ]
        if not isAttributeInObject( self.output, basicOutput.attributeName, basicOutput.isOnPoints ):
            stressRatioReal = fcts.stressRatio( horizontalStress, verticalStress )
        else:
            self._outputPresent.append( basicOutput.attributeName )
            stressRatioReal = getArrayInObject( self.output, basicOutput.attributeName, basicOutput.isOnPoints )
            self.logger.warning(
                f"{ basicOutput.attributeName } is already on the mesh, it has not been computed by the filter." )

        return stressRatioReal

    def _computeRealEffectiveStressRatio( self: Self ) -> bool:
        """Compute effective stress ratio.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        self._basicOutput.effectiveStressRatioReal = self._doComputeStressRatioReal(
            self._mandatoryAttributes.effectiveStress, STRESS_EFFECTIVE_RATIO_REAL )

        return True

    def _doComputeTotalStress(
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

    def _computeTotalStressInitial( self: Self ) -> bool:
        """Compute total stress at initial time step.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # Compute Biot at initial time step.
        biotCoefficientT0: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( self.physicalConstants.grainBulkModulus,
                                                                             self._elasticModuli.bulkModulusT0 )

        pressureT0: Union[ npt.NDArray[ np.float64 ], None ] = None
        # Case pressureT0 is None, total stress = effective stress
        # (managed by doComputeTotalStress function)
        if self._mandatoryAttributes.pressure is not None:
            # Get delta pressure to recompute pressure at initial time step (pressureTo)
            pressureT0 = self._mandatoryAttributes.pressure - self._mandatoryAttributes.deltaPressure

        if not isAttributeInObject( self.output, STRESS_TOTAL_T0.attributeName, STRESS_TOTAL_T0.isOnPoints ):
            self._basicOutput.totalStressT0 = self._doComputeTotalStress( self._mandatoryAttributes.effectiveStressT0,
                                                                          pressureT0, biotCoefficientT0 )
        else:
            self._outputPresent.append( STRESS_TOTAL_T0.attributeName )
            self._basicOutput.totalStressT0 = getArrayInObject( self.output, STRESS_TOTAL_T0.attributeName,
                                                                STRESS_TOTAL_T0.isOnPoints )
            self.logger.warning(
                f"{ STRESS_TOTAL_T0.attributeName } is already on the mesh, it has not been computed by the filter." )

        return True

    def _computeTotalStresses( self: Self ) -> bool:
        """Compute total stress total stress ratio.

        Total stress is computed at the initial and current time steps.
        Total stress ratio is computed at current time step only.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # Compute total stress at initial time step.
        if not self._computeTotalStressInitial():
            self.logger.error( "Total stress at initial time step computation failed." )
            return False

        # Compute total stress at current time step.
        if not isAttributeInObject( self.output, STRESS_TOTAL.attributeName, STRESS_TOTAL.isOnPoints ):
            self._basicOutput.totalStress = self._doComputeTotalStress( self._mandatoryAttributes.effectiveStress,
                                                                        self._mandatoryAttributes.pressure,
                                                                        self._basicOutput.biotCoefficient )
        else:
            self._outputPresent.append( STRESS_TOTAL.attributeName )
            self._basicOutput.totalStress = getArrayInObject( self.output, STRESS_TOTAL.attributeName,
                                                              STRESS_TOTAL.isOnPoints )
            self.logger.warning(
                f"{ STRESS_TOTAL.attributeName } is already on the mesh, it has not been computed by the filter." )

        # Compute total stress ratio.
        self._basicOutput.totalStressRatioReal = self._doComputeStressRatioReal( self._basicOutput.totalStress,
                                                                                 STRESS_TOTAL_RATIO_REAL )

        return True

    def computeLithostaticStress( self: Self ) -> bool:
        """Compute lithostatic stress.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        if not isAttributeInObject( self.output, LITHOSTATIC_STRESS.attributeName, LITHOSTATIC_STRESS.isOnPoints ):
            depth: npt.NDArray[ np.float64 ] = self._doComputeDepthAlongLine(
            ) if LITHOSTATIC_STRESS.isOnPoints else self._doComputeDepthInMesh()
            self._basicOutput.lithostaticStress = fcts.lithostaticStress( depth, self._mandatoryAttributes.density,
                                                                          GRAVITY )
        else:
            self._outputPresent.append( LITHOSTATIC_STRESS.attributeName )
            self._basicOutput.lithostaticStress = getArrayInObject( self.output, LITHOSTATIC_STRESS.attributeName,
                                                                    LITHOSTATIC_STRESS.isOnPoints )
            self.logger.warning(
                f"{ LITHOSTATIC_STRESS.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return True

    def _doComputeDepthAlongLine( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Compute depth along a line.

        Returns:
            npt.NDArray[np.float64]: 1D array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ] = self._getZcoordinates( True )
        assert zCoord is not None, "Depth coordinates cannot be computed."

        # TODO: to find how to compute depth in a general case
        # GEOS z axis is upward
        depth: npt.NDArray[ np.float64 ] = -1.0 * zCoord
        return depth

    def _doComputeDepthInMesh( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Compute depth of each cell in a mesh.

        Returns:
            npt.NDArray[np.float64]: array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ] = self._getZcoordinates( False )
        assert zCoord is not None, "Depth coordinates cannot be computed."

        # TODO: to find how to compute depth in a general case
        depth: npt.NDArray[ np.float64 ] = -1.0 * zCoord
        return depth

    def _getZcoordinates( self: Self, onPoints: bool ) -> npt.NDArray[ np.float64 ]:
        """Get z coordinates from self.output.

        Args:
            onPoints (bool): True if the attribute is on points, False if it is on cells.

        Returns:
            npt.NDArray[np.float64]: 1D array with depth property
        """
        # get z coordinate
        zCoord: npt.NDArray[ np.float64 ]
        pointCoords: npt.NDArray[ np.float64 ] = self._getPointCoordinates( onPoints )
        assert pointCoords is not None, "Point coordinates are undefined."
        assert pointCoords.shape[ 1 ] == 2, "Point coordinates are undefined."
        zCoord = pointCoords[ :, 2 ]
        return zCoord

    def _getPointCoordinates( self: Self, onPoints: bool ) -> npt.NDArray[ np.float64 ]:
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

    def _computeElasticStrain( self: Self ) -> bool:
        """Compute elastic strain from effective stress and elastic modulus.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        deltaEffectiveStress = self._mandatoryAttributes.effectiveStress - self._mandatoryAttributes.effectiveStressT0

        if not isAttributeInObject( self.output, STRAIN_ELASTIC.attributeName, STRAIN_ELASTIC.isOnPoints ):
            if self.computeYoungPoisson:
                self._basicOutput.elasticStrain = fcts.elasticStrainFromBulkShear( deltaEffectiveStress,
                                                                                   self._elasticModuli.bulkModulus,
                                                                                   self._elasticModuli.shearModulus )
            else:
                self._basicOutput.elasticStrain = fcts.elasticStrainFromYoungPoisson(
                    deltaEffectiveStress, self._elasticModuli.youngModulus, self._elasticModuli.poissonRatio )
        else:
            self._outputPresent.append( STRAIN_ELASTIC.attributeName )
            self._basicOutput.totalStressT0 = getArrayInObject( self.output, STRAIN_ELASTIC.attributeName,
                                                                STRAIN_ELASTIC.isOnPoints )
            self.logger.warning(
                f"{ STRAIN_ELASTIC.attributeName } is already on the mesh, it has not been computed by the filter." )

        return True

    def _computeReservoirStressPathReal( self: Self ) -> bool:
        """Compute reservoir stress paths.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # create delta stress attribute for QC
        if not isAttributeInObject( self.output, STRESS_TOTAL_DELTA.attributeName, STRESS_TOTAL_DELTA.isOnPoints ):
            self._basicOutput.deltaTotalStress = self._basicOutput.totalStress - self._basicOutput.totalStressT0
        else:
            self._outputPresent.append( STRESS_TOTAL_DELTA.attributeName )
            self._basicOutput.deltaTotalStress = getArrayInObject( self.output, STRESS_TOTAL_DELTA.attributeName,
                                                                   STRESS_TOTAL_DELTA.isOnPoints )
            self.logger.warning(
                f"{ STRESS_TOTAL_DELTA.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        if not isAttributeInObject( self.output, RSP_REAL.attributeName, RSP_REAL.isOnPoints ):
            self._basicOutput.rspReal = fcts.reservoirStressPathReal( self._basicOutput.deltaTotalStress,
                                                                      self._mandatoryAttributes.deltaPressure )
        else:
            self._outputPresent.append( RSP_REAL.attributeName )
            self._basicOutput.rspReal = getArrayInObject( self.output, RSP_REAL.attributeName, RSP_REAL.isOnPoints )
            self.logger.warning(
                f"{ RSP_REAL.attributeName } is already on the mesh, it has not been computed by the filter." )

        return True

    def _computeReservoirStressPathOed( self: Self ) -> bool:
        """Compute Reservoir Stress Path in oedometric conditions.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not isAttributeInObject( self.output, RSP_OED.attributeName, RSP_OED.isOnPoints ):
            self._basicOutput.rspOed = fcts.reservoirStressPathOed( self._basicOutput.biotCoefficient,
                                                                    self._elasticModuli.poissonRatio )
        else:
            self._outputPresent.append( RSP_OED.attributeName )
            self._basicOutput.rspOed = getArrayInObject( self.output, RSP_OED.attributeName, RSP_OED.isOnPoints )
            self.logger.warning(
                f"{ RSP_OED.attributeName } is already on the mesh, it has not been computed by the filter." )

        return True

    def _computeEffectiveStressRatioOed( self: Self ) -> bool:
        """Compute the effective stress ratio in oedometric conditions.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        if not isAttributeInObject( self.output, STRESS_EFFECTIVE_RATIO_OED.attributeName,
                                    STRESS_EFFECTIVE_RATIO_OED.isOnPoints ):
            self._basicOutput.effectiveStressRatioOed = fcts.deviatoricStressPathOed( self._elasticModuli.poissonRatio )
        else:
            self._outputPresent.append( STRESS_EFFECTIVE_RATIO_OED.attributeName )
            self._basicOutput.effectiveStressRatioOed = getArrayInObject( self.output,
                                                                          STRESS_EFFECTIVE_RATIO_OED.attributeName,
                                                                          STRESS_EFFECTIVE_RATIO_OED.isOnPoints )
            self.logger.warning(
                f"{ STRESS_EFFECTIVE_RATIO_OED.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return True

    def _computeCriticalTotalStressRatio( self: Self ) -> bool:
        """Compute fracture index and fracture threshold.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not isAttributeInObject( self.output, CRITICAL_TOTAL_STRESS_RATIO.attributeName,
                                    CRITICAL_TOTAL_STRESS_RATIO.isOnPoints ):
            verticalStress: npt.NDArray[ np.float64 ] = self._basicOutput.totalStress[ :, 2 ]
            self._advancedOutput.criticalTotalStressRatio = fcts.criticalTotalStressRatio(
                self._mandatoryAttributes.pressure, verticalStress )
        else:
            self._outputPresent.append( CRITICAL_TOTAL_STRESS_RATIO.attributeName )
            self._advancedOutput.criticalTotalStressRatio = getArrayInObject( self.output,
                                                                              CRITICAL_TOTAL_STRESS_RATIO.attributeName,
                                                                              CRITICAL_TOTAL_STRESS_RATIO.isOnPoints )
            self.logger.warning(
                f"{ CRITICAL_TOTAL_STRESS_RATIO.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        if not isAttributeInObject( self.output, TOTAL_STRESS_RATIO_THRESHOLD.attributeName,
                                    TOTAL_STRESS_RATIO_THRESHOLD.isOnPoints ):
            mask: npt.NDArray[ np.bool_ ] = np.argmin( np.abs( self._basicOutput.totalStress[ :, :2 ] ), axis=1 )
            horizontalStress: npt.NDArray[ np.float64 ] = self._basicOutput.totalStress[ :, :2 ][
                np.arange( self._basicOutput.totalStress[ :, :2 ].shape[ 0 ] ), mask ]
            self._advancedOutput.stressRatioThreshold = fcts.totalStressRatioThreshold(
                self._mandatoryAttributes.pressure, horizontalStress )
        else:
            self._outputPresent.append( TOTAL_STRESS_RATIO_THRESHOLD.attributeName )
            self._advancedOutput.stressRatioThreshold = getArrayInObject( self.output,
                                                                          TOTAL_STRESS_RATIO_THRESHOLD.attributeName,
                                                                          TOTAL_STRESS_RATIO_THRESHOLD.isOnPoints )
            self.logger.warning(
                f"{ TOTAL_STRESS_RATIO_THRESHOLD.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return True

    def _computeCriticalPorePressure( self: Self ) -> bool:
        """Compute the critical pore pressure and the pressure index.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not isAttributeInObject( self.output, CRITICAL_PORE_PRESSURE.attributeName,
                                    CRITICAL_PORE_PRESSURE.isOnPoints ):
            self._advancedOutput.criticalPorePressure = fcts.criticalPorePressure(
                -1.0 * self._basicOutput.totalStress, self.physicalConstants.rockCohesion,
                self.physicalConstants.frictionAngle )
        else:
            self._outputPresent.append( CRITICAL_PORE_PRESSURE.attributeName )
            self._advancedOutput.criticalPorePressure = getArrayInObject( self.output,
                                                                          CRITICAL_PORE_PRESSURE.attributeName,
                                                                          CRITICAL_PORE_PRESSURE.isOnPoints )
            self.logger.warning(
                f"{ CRITICAL_PORE_PRESSURE.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        # Add critical pore pressure index (i.e., ratio between pressure and criticalPorePressure)
        if not isAttributeInObject( self.output, CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName,
                                    CRITICAL_PORE_PRESSURE_THRESHOLD.isOnPoints ):
            self._advancedOutput.criticalPorePressureIndex = fcts.criticalPorePressureThreshold(
                self._mandatoryAttributes.pressure, self._advancedOutput.criticalPorePressure )
        else:
            self._outputPresent.append( CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName )
            self._advancedOutput.criticalPorePressureIndex = getArrayInObject(
                self.output, CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName,
                CRITICAL_PORE_PRESSURE_THRESHOLD.isOnPoints )
            self.logger.warning(
                f"{ CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return True
