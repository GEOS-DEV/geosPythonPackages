# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Union
from typing_extensions import Self
from dataclasses import dataclass

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
ELASTIC_MODULI: tuple[ AttributeEnum, ...] = ( BULK_MODULUS, SHEAR_MODULUS, YOUNG_MODULUS, POISSON_RATIO,
                                               BULK_MODULUS_T0, YOUNG_MODULUS_T0, POISSON_RATIO_T0 )

# Mandatory attributes:
POROSITY: AttributeEnum = GeosMeshOutputsEnum.POROSITY
POROSITY_T0: AttributeEnum = GeosMeshOutputsEnum.POROSITY_INI
PRESSURE: AttributeEnum = GeosMeshOutputsEnum.PRESSURE
DELTA_PRESSURE: AttributeEnum = GeosMeshOutputsEnum.DELTA_PRESSURE
DENSITY: AttributeEnum = GeosMeshOutputsEnum.ROCK_DENSITY
STRESS_EFFECTIVE: AttributeEnum = GeosMeshOutputsEnum.STRESS_EFFECTIVE
STRESS_EFFECTIVE_T0: AttributeEnum = PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL
MANDATORY_ATTRIBUTES: tuple[ AttributeEnum, ...] = ( POROSITY, POROSITY_T0, PRESSURE, DELTA_PRESSURE, DENSITY,
                                                     STRESS_EFFECTIVE, STRESS_EFFECTIVE_T0 )

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
BASIC_OUTPUTS: tuple[ AttributeEnum,
                      ...] = ( BIOT_COEFFICIENT, COMPRESSIBILITY, COMPRESSIBILITY_OED, COMPRESSIBILITY_REAL,
                               SPECIFIC_GRAVITY, STRESS_EFFECTIVE_RATIO_REAL, STRESS_TOTAL, STRESS_TOTAL_T0,
                               STRESS_TOTAL_RATIO_REAL, LITHOSTATIC_STRESS, STRAIN_ELASTIC, STRESS_TOTAL_DELTA,
                               RSP_REAL, RSP_OED, STRESS_EFFECTIVE_RATIO_OED )

# Advanced outputs:
CRITICAL_TOTAL_STRESS_RATIO: AttributeEnum = PostProcessingOutputsEnum.CRITICAL_TOTAL_STRESS_RATIO
TOTAL_STRESS_RATIO_THRESHOLD: AttributeEnum = PostProcessingOutputsEnum.TOTAL_STRESS_RATIO_THRESHOLD
CRITICAL_PORE_PRESSURE: AttributeEnum = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE
CRITICAL_PORE_PRESSURE_THRESHOLD: AttributeEnum = PostProcessingOutputsEnum.CRITICAL_PORE_PRESSURE_THRESHOLD
ADVANCED_OUTPUTS: tuple[ AttributeEnum, ...] = ( CRITICAL_TOTAL_STRESS_RATIO, TOTAL_STRESS_RATIO_THRESHOLD,
                                                 CRITICAL_PORE_PRESSURE, CRITICAL_PORE_PRESSURE_THRESHOLD )


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
    class ElasticModuliValue:
        _bulkModulus: npt.NDArray[ np.float64 ] = np.array( [] )
        _shearModulus: npt.NDArray[ np.float64 ] = np.array( [] )
        _youngModulus: npt.NDArray[ np.float64 ] = np.array( [] )
        _poissonRatio: npt.NDArray[ np.float64 ] = np.array( [] )
        _bulkModulusT0: npt.NDArray[ np.float64 ] = np.array( [] )
        _youngModulusT0: npt.NDArray[ np.float64 ] = np.array( [] )
        _poissonRatioT0: npt.NDArray[ np.float64 ] = np.array( [] )

        @property
        def bulkModulus( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._bulkModulus

        @bulkModulus.setter
        def bulkModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._bulkModulus = value

        @property
        def shearModulus( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._shearModulus

        @shearModulus.setter
        def shearModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._shearModulus = value

        @property
        def youngModulus( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._youngModulus

        @youngModulus.setter
        def youngModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._youngModulus = value

        @property
        def poissonRatio( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._poissonRatio

        @poissonRatio.setter
        def poissonRatio( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._poissonRatio = value

        @property
        def bulkModulusT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._bulkModulusT0

        @bulkModulusT0.setter
        def bulkModulusT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._bulkModulusT0 = value

        @property
        def youngModulusT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._youngModulusT0

        @youngModulusT0.setter
        def youngModulusT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._youngModulusT0 = value

        @property
        def poissonRatioT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._poissonRatioT0

        @poissonRatioT0.setter
        def poissonRatioT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._poissonRatioT0 = value

        def setElasticModulusValue( self: Self, name: str, value: npt.NDArray[ np.float64 ] ) -> None:
            if name == BULK_MODULUS.attributeName:
                self.bulkModulus = value
            elif name == BULK_MODULUS_T0.attributeName:
                self.bulkModulusT0 = value
            elif name == SHEAR_MODULUS.attributeName:
                self.shearModulus = value
            elif name == YOUNG_MODULUS.attributeName:
                self.youngModulus = value
            elif name == YOUNG_MODULUS_T0.attributeName:
                self.youngModulusT0 = value
            elif name == POISSON_RATIO.attributeName:
                self.poissonRatio = value
            elif name == POISSON_RATIO_T0.attributeName:
                self.poissonRatioT0 = value

        def getElasticModulusValue( self: Self, name: str ) -> npt.NDArray[ np.float64 ]:
            if name == BULK_MODULUS.attributeName:
                return self.bulkModulus
            elif name == BULK_MODULUS_T0.attributeName:
                return self.bulkModulusT0
            elif name == SHEAR_MODULUS.attributeName:
                return self.shearModulus
            elif name == YOUNG_MODULUS.attributeName:
                return self.youngModulus
            elif name == YOUNG_MODULUS_T0.attributeName:
                return self.youngModulusT0
            elif name == POISSON_RATIO.attributeName:
                return self.poissonRatio
            elif name == POISSON_RATIO_T0.attributeName:
                return self.poissonRatioT0
            else:
                raise NameError

    _elasticModuli: ElasticModuliValue = ElasticModuliValue()

    @dataclass
    class MandatoryAttributesValue:
        _porosity: npt.NDArray[ np.float64 ] = np.array( [] )
        _porosityInitial: npt.NDArray[ np.float64 ] = np.array( [] )
        _pressure: npt.NDArray[ np.float64 ] = np.array( [] )
        _deltaPressure: npt.NDArray[ np.float64 ] = np.array( [] )
        _density: npt.NDArray[ np.float64 ] = np.array( [] )
        _effectiveStress: npt.NDArray[ np.float64 ] = np.array( [] )
        _effectiveStressT0: npt.NDArray[ np.float64 ] = np.array( [] )

        @property
        def porosity( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._porosity

        @property
        def porosityInitial( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._porosityInitial

        @property
        def pressure( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._pressure

        @property
        def deltaPressure( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._deltaPressure

        @property
        def density( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._density

        @property
        def effectiveStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._effectiveStress

        @property
        def effectiveStressT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._effectiveStressT0

        def setMandatoryAttributeValue( self: Self, name: str, value: npt.NDArray[ np.float64 ] ) -> None:
            if name == POROSITY.attributeName:
                self._porosity = value
            elif name == POROSITY_T0.attributeName:
                self._porosityInitial = value
            elif name == PRESSURE.attributeName:
                self._pressure = value
            elif name == DELTA_PRESSURE.attributeName:
                self._deltaPressure = value
            elif name == DENSITY.attributeName:
                self._density = value
            elif name == STRESS_EFFECTIVE.attributeName:
                self._effectiveStress = value
            elif name == STRESS_EFFECTIVE_T0.attributeName:
                self._effectiveStressT0 = value

    _mandatoryAttributes: MandatoryAttributesValue = MandatoryAttributesValue()

    @dataclass
    class BasicOutputValue:
        _biotCoefficient: npt.NDArray[ np.float64 ] = np.array( [] )
        _compressibility: npt.NDArray[ np.float64 ] = np.array( [] )
        _compressibilityOed: npt.NDArray[ np.float64 ] = np.array( [] )
        _compressibilityReal: npt.NDArray[ np.float64 ] = np.array( [] )
        _specificGravity: npt.NDArray[ np.float64 ] = np.array( [] )
        _effectiveStressRatioReal: npt.NDArray[ np.float64 ] = np.array( [] )
        _totalStress: npt.NDArray[ np.float64 ] = np.array( [] )
        _totalStressT0: npt.NDArray[ np.float64 ] = np.array( [] )
        _totalStressRatioReal: npt.NDArray[ np.float64 ] = np.array( [] )
        # _lithostaticStress: npt.NDArray[ np.float64 ] = np.array( [] )
        _elasticStrain: npt.NDArray[ np.float64 ] = np.array( [] )
        _deltaTotalStress: npt.NDArray[ np.float64 ] = np.array( [] )
        _rspReal: npt.NDArray[ np.float64 ] = np.array( [] )
        _rspOed: npt.NDArray[ np.float64 ] = np.array( [] )
        _effectiveStressRatioOed: npt.NDArray[ np.float64 ] = np.array( [] )

        @property
        def biotCoefficient( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._biotCoefficient

        @biotCoefficient.setter
        def biotCoefficient( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._biotCoefficient = value

        @property
        def compressibility( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._compressibility

        @compressibility.setter
        def compressibility( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._compressibility = value

        @property
        def compressibilityOed( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._compressibilityOed

        @compressibilityOed.setter
        def compressibilityOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._compressibilityOed = value

        @property
        def compressibilityReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._compressibilityReal

        @compressibilityReal.setter
        def compressibilityReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._compressibilityReal = value

        @property
        def specificGravity( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._specificGravity

        @specificGravity.setter
        def specificGravity( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._specificGravity = value

        @property
        def effectiveStressRatioReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._effectiveStressRatioReal

        @effectiveStressRatioReal.setter
        def effectiveStressRatioReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._effectiveStressRatioReal = value

        @property
        def totalStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._totalStress

        @totalStress.setter
        def totalStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._totalStress = value

        @property
        def totalStressT0( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._totalStressT0

        @totalStressT0.setter
        def totalStressT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._totalStressT0 = value

        @property
        def totalStressRatioReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._totalStressRatioReal

        @totalStressRatioReal.setter
        def totalStressRatioReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._totalStressRatioReal = value

        @property
        def lithostaticStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._lithostaticStress

        @lithostaticStress.setter
        def lithostaticStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._lithostaticStress = value

        @property
        def elasticStrain( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._elasticStrain

        @elasticStrain.setter
        def elasticStrain( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._elasticStrain = value

        @property
        def deltaTotalStress( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._deltaTotalStress

        @deltaTotalStress.setter
        def deltaTotalStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._deltaTotalStress = value

        @property
        def rspReal( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._rspReal

        @rspReal.setter
        def rspReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._rspReal = value

        @property
        def rspOed( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._rspOed

        @rspOed.setter
        def rspOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._rspOed = value

        @property
        def effectiveStressRatioOed( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._effectiveStressRatioOed

        @effectiveStressRatioOed.setter
        def effectiveStressRatioOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._effectiveStressRatioOed = value

        def getBasicOutputValue( self: Self, name: str ) -> npt.NDArray[ np.float64 ]:
            if name == BIOT_COEFFICIENT.attributeName:
                return self.biotCoefficient
            elif name == COMPRESSIBILITY.attributeName:
                return self.compressibility
            elif name == COMPRESSIBILITY_OED.attributeName:
                return self.compressibilityOed
            elif name == COMPRESSIBILITY_REAL.attributeName:
                return self.compressibilityReal
            elif name == SPECIFIC_GRAVITY.attributeName:
                return self.specificGravity
            elif name == STRESS_EFFECTIVE_RATIO_REAL.attributeName:
                return self.effectiveStressRatioReal
            elif name == STRESS_TOTAL.attributeName:
                return self.totalStress
            elif name == STRESS_TOTAL_T0.attributeName:
                return self.totalStressT0
            elif name == STRESS_TOTAL_RATIO_REAL.attributeName:
                return self.totalStressRatioReal
            elif name == LITHOSTATIC_STRESS.attributeName:
                return self.lithostaticStress
            elif name == STRAIN_ELASTIC.attributeName:
                return self.elasticStrain
            elif name == STRESS_TOTAL_DELTA.attributeName:
                return self.deltaTotalStress
            elif name == RSP_REAL.attributeName:
                return self.rspReal
            elif name == RSP_OED.attributeName:
                return self.rspOed
            elif name == STRESS_EFFECTIVE_RATIO_OED.attributeName:
                return self.effectiveStressRatioOed
            else:
                raise NameError

    _basicOutput: BasicOutputValue = BasicOutputValue()

    @dataclass
    class AdvancedOutputValue:
        _criticalTotalStressRatio: npt.NDArray[ np.float64 ] = np.array( [] )
        _stressRatioThreshold: npt.NDArray[ np.float64 ] = np.array( [] )
        _criticalPorePressure: npt.NDArray[ np.float64 ] = np.array( [] )
        _criticalPorePressureIndex: npt.NDArray[ np.float64 ] = np.array( [] )

        @property
        def criticalTotalStressRatio( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._criticalTotalStressRatio

        @criticalTotalStressRatio.setter
        def criticalTotalStressRatio( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._criticalTotalStressRatio = value

        @property
        def stressRatioThreshold( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._stressRatioThreshold

        @stressRatioThreshold.setter
        def stressRatioThreshold( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._stressRatioThreshold = value

        @property
        def criticalPorePressure( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._criticalPorePressure

        @criticalPorePressure.setter
        def criticalPorePressure( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._criticalPorePressure = value

        @property
        def criticalPorePressureIndex( self: Self ) -> npt.NDArray[ np.float64 ]:
            return self._criticalPorePressureIndex

        @criticalPorePressureIndex.setter
        def criticalPorePressureIndex( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._criticalPorePressureIndex = value

        def getAdvancedOutputValue( self: Self, name: str ) -> npt.NDArray[ np.float64 ]:
            if name == CRITICAL_TOTAL_STRESS_RATIO.attributeName:
                return self.criticalTotalStressRatio
            elif name == TOTAL_STRESS_RATIO_THRESHOLD.attributeName:
                return self.stressRatioThreshold
            elif name == CRITICAL_PORE_PRESSURE.attributeName:
                return self.criticalPorePressure
            elif name == CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName:
                return self.criticalPorePressureIndex
            else:
                raise NameError

    _advancedOutput: AdvancedOutputValue = AdvancedOutputValue()

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
        self._attributesToCreate: list[ AttributeEnum ] = []

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

        if self.doComputeAdvancedOutputs and not self.computeAdvancedOutputs():
            return False

        # Create an attribute on the mesh for each geomechanics outputs computed:
        for attribute in self._attributesToCreate:
            attributeName: str = attribute.attributeName
            onPoints: bool = attribute.isOnPoints
            array: npt.NDArray[ np.float64 ]
            if attribute in ELASTIC_MODULI:
                array = self._elasticModuli.getElasticModulusValue( attributeName )
            elif attribute in BASIC_OUTPUTS:
                array = self._basicOutput.getBasicOutputValue( attributeName )
            elif attribute in ADVANCED_OUTPUTS:
                array = self._advancedOutput.getAdvancedOutputValue( attributeName )
            componentNames: tuple[ str, ...] = ()
            if attribute.nbComponent == 6:
                componentNames = ComponentNameEnum.XYZ.value

            if not createAttribute( self.output,
                                    array,
                                    attributeName,
                                    componentNames=componentNames,
                                    onPoints=onPoints,
                                    logger=self.logger ):
                return False

        self.logger.info( "All the geomechanics properties have been add to the mesh." )
        self.logger.info( "The filter succeeded." )
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
        for elasticModulus in ELASTIC_MODULI:
            elasticModulusName: str = elasticModulus.attributeName
            elasticModulusOnPoints: bool = elasticModulus.isOnPoints
            if isAttributeInObject( self.output, elasticModulusName, elasticModulusOnPoints ):
                self._elasticModuli.setElasticModulusValue(
                    elasticModulus.attributeName,
                    getArrayInObject( self.output, elasticModulusName, elasticModulusOnPoints ) )

        # Check the presence of the elastic moduli at the current time.
        self.computeYoungPoisson: bool
        if self._elasticModuli.youngModulus.size == 0 and self._elasticModuli.poissonRatio.size == 0:
            if self._elasticModuli.bulkModulus.size != 0 and self._elasticModuli.shearModulus.size != 0:
                self._elasticModuli.youngModulus = fcts.youngModulus( self._elasticModuli.bulkModulus,
                                                                      self._elasticModuli.shearModulus )
                self._attributesToCreate.append( YOUNG_MODULUS )
                self._elasticModuli.poissonRatio = fcts.poissonRatio( self._elasticModuli.bulkModulus,
                                                                      self._elasticModuli.shearModulus )
                self._attributesToCreate.append( POISSON_RATIO )
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
                self._attributesToCreate.append( BULK_MODULUS )
                self._elasticModuli.shearModulus = fcts.shearModulus( self._elasticModuli.youngModulus,
                                                                      self._elasticModuli.poissonRatio )
                self._attributesToCreate.append( SHEAR_MODULUS )
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
                self._attributesToCreate.append( BULK_MODULUS_T0 )
            else:
                self.logger.error(
                    f"{ BULK_MODULUS_T0.attributeName } or { YOUNG_MODULUS_T0.attributeName } and { POISSON_RATIO_T0.attributeName } are mandatory to compute geomechanical outputs."
                )
                return False

        # Check the presence of the other mandatory attributes
        for mandatoryAttribute in MANDATORY_ATTRIBUTES:
            mandatoryAttributeName: str = mandatoryAttribute.attributeName
            mandatoryAttributeOnPoints: bool = mandatoryAttribute.isOnPoints
            if not isAttributeInObject( self.output, mandatoryAttributeName, mandatoryAttributeOnPoints ):
                self.logger.error(
                    f"The mandatory attribute { mandatoryAttributeName } is missing to compute geomechanical outputs." )
                return False
            else:
                self._mandatoryAttributes.setMandatoryAttributeValue(
                    mandatoryAttributeName,
                    getArrayInObject( self.output, mandatoryAttributeName, mandatoryAttributeOnPoints ) )

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
            self._attributesToCreate.append( BIOT_COEFFICIENT )
        else:
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
            self._attributesToCreate.append( COMPRESSIBILITY )
        else:
            self._basicOutput.compressibility = getArrayInObject( self.output, COMPRESSIBILITY.attributeName,
                                                                  COMPRESSIBILITY.isOnPoints )
            self.logger.warning(
                f"{ COMPRESSIBILITY.attributeName } is already on the mesh, it has not been computed by the filter." )

        # oedometric compressibility
        if not isAttributeInObject( self.output, COMPRESSIBILITY_OED.attributeName, COMPRESSIBILITY_OED.isOnPoints ):
            self._basicOutput.compressibilityOed = fcts.compressibilityOed( self._elasticModuli.shearModulus,
                                                                            self._elasticModuli.bulkModulus,
                                                                            self._mandatoryAttributes.porosity )
            self._attributesToCreate.append( COMPRESSIBILITY_OED )
        else:
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
            self._attributesToCreate.append( COMPRESSIBILITY_REAL )
        else:
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
            self._attributesToCreate.append( SPECIFIC_GRAVITY )
        else:
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
            self._attributesToCreate.append( basicOutput )
        else:
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
            self._attributesToCreate.append( STRESS_TOTAL_T0 )
        else:
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
            self._attributesToCreate.append( STRESS_TOTAL )
        else:
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
            self._attributesToCreate.append( LITHOSTATIC_STRESS )
        else:
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
            self._attributesToCreate.append( STRAIN_ELASTIC )
        else:
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
            self._attributesToCreate.append( STRESS_TOTAL_DELTA )
        else:
            self._basicOutput.deltaTotalStress = getArrayInObject( self.output, STRESS_TOTAL_DELTA.attributeName,
                                                                   STRESS_TOTAL_DELTA.isOnPoints )
            self.logger.warning(
                f"{ STRESS_TOTAL_DELTA.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        if not isAttributeInObject( self.output, RSP_REAL.attributeName, RSP_REAL.isOnPoints ):
            self._basicOutput.rspReal = fcts.reservoirStressPathReal( self._basicOutput.deltaTotalStress,
                                                                      self._mandatoryAttributes.deltaPressure )
            self._attributesToCreate.append( RSP_REAL )
        else:
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
            self._attributesToCreate.append( RSP_OED )
        else:
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
            self._attributesToCreate.append( STRESS_EFFECTIVE_RATIO_OED )
        else:
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
            self._attributesToCreate.append( CRITICAL_TOTAL_STRESS_RATIO )
        else:
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
            self._attributesToCreate.append( TOTAL_STRESS_RATIO_THRESHOLD )
        else:
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
            self._attributesToCreate.append( CRITICAL_PORE_PRESSURE )
        else:
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
            self._attributesToCreate.append( CRITICAL_PORE_PRESSURE_THRESHOLD )
        else:
            self._advancedOutput.criticalPorePressureIndex = getArrayInObject(
                self.output, CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName,
                CRITICAL_PORE_PRESSURE_THRESHOLD.isOnPoints )
            self.logger.warning(
                f"{ CRITICAL_PORE_PRESSURE_THRESHOLD.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return True
