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

from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
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
    - The elastic moduli not present on the mesh
    - Biot coefficient
    - Compressibility, oedometric compressibility and real compressibility coefficient
    - Specific gravity
    - Real effective stress ratio
    - Total initial stress, total current stress and total stress ratio
    - Lithostatic stress (physic to update)
    - Elastic stain
    - Real reservoir stress path and reservoir stress path in oedometric condition

The advanced geomechanics outputs are:
    - Fracture index and threshold
    - Critical pore pressure and pressure index

GeomechanicsCalculator vtk filter input and output meshes are vtkUnstructuredGrid.

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
    mesh: vtkUnstructuredGrid
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
    filter.physicalConstants.grainBulkModulus = grainBulkModulus
    filter.physicalConstants.specificDensity = specificDensity

    ## Advanced outputs
    rockCohesion: float
    frictionAngle: float
    filter.physicalConstants.rockCohesion = rockCohesion
    filter.physicalConstants.frictionAngle = frictionAngle

    # Do calculations
    filter.applyFilter()

    # Get the mesh with the geomechanical output as attribute
    output: vtkUnstructuredGrid
    output = filter.getOutput()
"""

loggerTitle: str = "Geomechanics Calculator"

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
        """The dataclass with the  value of the physical constant used to compute geomechanics properties."""
        ## Basic outputs
        _grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        _specificDensity: float = WATER_DENSITY
        ## Advanced outputs
        _rockCohesion: float = DEFAULT_ROCK_COHESION
        _frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        @property
        def grainBulkModulus( self: Self ) -> float:
            """Get the grain bulk modulus value."""
            return self._grainBulkModulus

        @grainBulkModulus.setter
        def grainBulkModulus( self: Self, value: float ) -> None:
            self._grainBulkModulus = value

        @property
        def specificDensity( self: Self ) -> float:
            """Get the specific density value."""
            return self._specificDensity

        @specificDensity.setter
        def specificDensity( self: Self, value: float ) -> None:
            self._specificDensity = value

        @property
        def rockCohesion( self: Self ) -> float:
            """Get the rock cohesion value."""
            return self._rockCohesion

        @rockCohesion.setter
        def rockCohesion( self: Self, value: float ) -> None:
            self._rockCohesion = value

        @property
        def frictionAngle( self: Self ) -> float:
            """Get the friction angle value."""
            return self._frictionAngle

        @frictionAngle.setter
        def frictionAngle( self: Self, value: float ) -> None:
            self._frictionAngle = value

    @dataclass
    class ElasticModuliValue:
        """The dataclass with the value of the elastic moduli."""
        _bulkModulus: npt.NDArray[ np.float64 ] | None = None
        _shearModulus: npt.NDArray[ np.float64 ] | None = None
        _youngModulus: npt.NDArray[ np.float64 ] | None = None
        _poissonRatio: npt.NDArray[ np.float64 ] | None = None
        _bulkModulusT0: npt.NDArray[ np.float64 ] | None = None
        _youngModulusT0: npt.NDArray[ np.float64 ] | None = None
        _poissonRatioT0: npt.NDArray[ np.float64 ] | None = None

        @property
        def bulkModulus( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the bulk modulus value."""
            return self._bulkModulus

        @bulkModulus.setter
        def bulkModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._bulkModulus = value

        @property
        def shearModulus( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the shear modulus value."""
            return self._shearModulus

        @shearModulus.setter
        def shearModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._shearModulus = value

        @property
        def youngModulus( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the young modulus value."""
            return self._youngModulus

        @youngModulus.setter
        def youngModulus( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._youngModulus = value

        @property
        def poissonRatio( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the poisson ratio value."""
            return self._poissonRatio

        @poissonRatio.setter
        def poissonRatio( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._poissonRatio = value

        @property
        def bulkModulusT0( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the bulk modulus at the initial time value."""
            return self._bulkModulusT0

        @bulkModulusT0.setter
        def bulkModulusT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._bulkModulusT0 = value

        @property
        def youngModulusT0( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the young modulus at the initial time value."""
            return self._youngModulusT0

        @youngModulusT0.setter
        def youngModulusT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._youngModulusT0 = value

        @property
        def poissonRatioT0( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the poisson ration at the initial time value."""
            return self._poissonRatioT0

        @poissonRatioT0.setter
        def poissonRatioT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._poissonRatioT0 = value

        def setElasticModulusValue( self: Self, name: str, value: npt.NDArray[ np.float64 ] ) -> None:
            """Set the elastic modulus value wanted.

            Args:
                name (str): The name of the elastic modulus.
                value (npt.NDArray[np.float64]): The value to set.
            """
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

        def getElasticModulusValue( self: Self, name: str ) -> npt.NDArray[ np.float64 ] | None:
            """Get the wanted elastic modulus value.

            Args:
                name (str): The name of the wanted elastic modulus.

            Returns:
                npt.NDArray[np.float64]: The value of the elastic modulus.
            """
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

    @dataclass
    class MandatoryAttributesValue:
        """The dataclass with the value of mandatory properties to have to compute other geomechanics properties."""
        _porosity: npt.NDArray[ np.float64 ] | None = None
        _porosityInitial: npt.NDArray[ np.float64 ] | None = None
        _pressure: npt.NDArray[ np.float64 ] | None = None
        _deltaPressure: npt.NDArray[ np.float64 ] | None = None
        _density: npt.NDArray[ np.float64 ] | None = None
        _effectiveStress: npt.NDArray[ np.float64 ] | None = None
        _effectiveStressT0: npt.NDArray[ np.float64 ] | None = None

        @property
        def porosity( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the porosity value."""
            return self._porosity

        @property
        def porosityInitial( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the initial porosity value."""
            return self._porosityInitial

        @property
        def pressure( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the pressure value."""
            return self._pressure

        @property
        def deltaPressure( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the delta pressure value."""
            return self._deltaPressure

        @property
        def density( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the density value."""
            return self._density

        @property
        def effectiveStress( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the effective stress value."""
            return self._effectiveStress

        @property
        def effectiveStressT0( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the initial effective stress value."""
            return self._effectiveStressT0

        def setMandatoryAttributeValue( self: Self, name: str, value: npt.NDArray[ np.float64 ] ) -> None:
            """Set the value of a mandatory property.

            Args:
                name (str): The name of the property.
                value (npt.NDArray[np.float64]): The value to set.
            """
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

    @dataclass
    class BasicOutputValue:
        """The dataclass with the value of the basic geomechanics outputs."""
        _biotCoefficient: npt.NDArray[ np.float64 ] | None = None
        _compressibility: npt.NDArray[ np.float64 ] | None = None
        _compressibilityOed: npt.NDArray[ np.float64 ] | None = None
        _compressibilityReal: npt.NDArray[ np.float64 ] | None = None
        _specificGravity: npt.NDArray[ np.float64 ] | None = None
        _effectiveStressRatioReal: npt.NDArray[ np.float64 ] | None = None
        _totalStress: npt.NDArray[ np.float64 ] | None = None
        _totalStressT0: npt.NDArray[ np.float64 ] | None = None
        _totalStressRatioReal: npt.NDArray[ np.float64 ] | None = None
        # _lithostaticStress: npt.NDArray[ np.float64 ] | None = None
        _elasticStrain: npt.NDArray[ np.float64 ] | None = None
        _deltaTotalStress: npt.NDArray[ np.float64 ] | None = None
        _rspReal: npt.NDArray[ np.float64 ] | None = None
        _rspOed: npt.NDArray[ np.float64 ] | None = None
        _effectiveStressRatioOed: npt.NDArray[ np.float64 ] | None = None

        @property
        def biotCoefficient( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the biot coefficient value."""
            return self._biotCoefficient

        @biotCoefficient.setter
        def biotCoefficient( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._biotCoefficient = value

        @property
        def compressibility( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the compressibility value."""
            return self._compressibility

        @compressibility.setter
        def compressibility( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._compressibility = value

        @property
        def compressibilityOed( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the compressibility in oedometric condition value."""
            return self._compressibilityOed

        @compressibilityOed.setter
        def compressibilityOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._compressibilityOed = value

        @property
        def compressibilityReal( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the real compressibility value."""
            return self._compressibilityReal

        @compressibilityReal.setter
        def compressibilityReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._compressibilityReal = value

        @property
        def specificGravity( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the specific gravity value."""
            return self._specificGravity

        @specificGravity.setter
        def specificGravity( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._specificGravity = value

        @property
        def effectiveStressRatioReal( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the real effective stress ratio value."""
            return self._effectiveStressRatioReal

        @effectiveStressRatioReal.setter
        def effectiveStressRatioReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._effectiveStressRatioReal = value

        @property
        def totalStress( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the total stress value."""
            return self._totalStress

        @totalStress.setter
        def totalStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._totalStress = value

        @property
        def totalStressT0( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the initial total stress value."""
            return self._totalStressT0

        @totalStressT0.setter
        def totalStressT0( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._totalStressT0 = value

        @property
        def totalStressRatioReal( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the total real stress ratio value."""
            return self._totalStressRatioReal

        @totalStressRatioReal.setter
        def totalStressRatioReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._totalStressRatioReal = value

        @property
        def lithostaticStress( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the lithostatic stress value."""
            return self._lithostaticStress

        @lithostaticStress.setter
        def lithostaticStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._lithostaticStress = value

        @property
        def elasticStrain( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the elastic strain value."""
            return self._elasticStrain

        @elasticStrain.setter
        def elasticStrain( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._elasticStrain = value

        @property
        def deltaTotalStress( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the total delta stress value."""
            return self._deltaTotalStress

        @deltaTotalStress.setter
        def deltaTotalStress( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._deltaTotalStress = value

        @property
        def rspReal( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the real reservoir stress path value."""
            return self._rspReal

        @rspReal.setter
        def rspReal( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._rspReal = value

        @property
        def rspOed( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the reservoir stress path in oedometric condition value."""
            return self._rspOed

        @rspOed.setter
        def rspOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._rspOed = value

        @property
        def effectiveStressRatioOed( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the effective stress ratio oedometric value."""
            return self._effectiveStressRatioOed

        @effectiveStressRatioOed.setter
        def effectiveStressRatioOed( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._effectiveStressRatioOed = value

        def getBasicOutputValue( self: Self, name: str ) -> npt.NDArray[ np.float64 ] | None:
            """Get the value of the basic output wanted.

            Args:
                name (str): The name of the basic output.

            Returns:
                npt.NDArray[ np.float64 ]: the value of the basic output.
            """
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

    @dataclass
    class AdvancedOutputValue:
        """The dataclass with the value of the advanced geomechanics outputs."""
        _criticalTotalStressRatio: npt.NDArray[ np.float64 ] | None = None
        _stressRatioThreshold: npt.NDArray[ np.float64 ] | None = None
        _criticalPorePressure: npt.NDArray[ np.float64 ] | None = None
        _criticalPorePressureIndex: npt.NDArray[ np.float64 ] | None = None

        @property
        def criticalTotalStressRatio( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the critical total stress ratio value."""
            return self._criticalTotalStressRatio

        @criticalTotalStressRatio.setter
        def criticalTotalStressRatio( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._criticalTotalStressRatio = value

        @property
        def stressRatioThreshold( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the stress ratio threshold value."""
            return self._stressRatioThreshold

        @stressRatioThreshold.setter
        def stressRatioThreshold( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._stressRatioThreshold = value

        @property
        def criticalPorePressure( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the critical pore pressure value."""
            return self._criticalPorePressure

        @criticalPorePressure.setter
        def criticalPorePressure( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._criticalPorePressure = value

        @property
        def criticalPorePressureIndex( self: Self ) -> npt.NDArray[ np.float64 ] | None:
            """Get the critical pore pressure index value."""
            return self._criticalPorePressureIndex

        @criticalPorePressureIndex.setter
        def criticalPorePressureIndex( self: Self, value: npt.NDArray[ np.float64 ] ) -> None:
            self._criticalPorePressureIndex = value

        def getAdvancedOutputValue( self: Self, name: str ) -> npt.NDArray[ np.float64 ] | None:
            """Get the value of the advanced output wanted.

            Args:
                name (str): The name of the advanced output.

            Returns:
                npt.NDArray[ np.float64 ]: the value of the advanced output.
            """
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

    physicalConstants: PhysicalConstants
    _elasticModuli: ElasticModuliValue
    _mandatoryAttributes: MandatoryAttributesValue
    _basicOutput: BasicOutputValue
    _advancedOutput: AdvancedOutputValue

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        computeAdvancedOutputs: bool = False,
        speHandler: bool = False,
    ) -> None:
        """VTK Filter to perform Geomechanical output computation.

        Args:
            mesh (vtkUnstructuredGrid): Input mesh.
            computeAdvancedOutputs (bool, optional): True to compute advanced geomechanical parameters, False otherwise.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.output: vtkUnstructuredGrid = mesh.NewInstance()
        self.output.DeepCopy( mesh )

        self.doComputeAdvancedOutputs: bool = computeAdvancedOutputs
        self.physicalConstants = self.PhysicalConstants()
        self._elasticModuli = self.ElasticModuliValue()
        self._mandatoryAttributes = self.MandatoryAttributesValue()
        self._basicOutput = self.BasicOutputValue()
        self._advancedOutput = self.AdvancedOutputValue()

        self._attributesToCreate: list[ AttributeEnum ] = []

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def applyFilter( self: Self ) -> None:
        """Compute the geomechanics properties and create attributes on the mesh."""
        self.logger.info( f"Apply filter { self.logger.name }." )

        try:
            self._checkMandatoryAttributes()
            self._computeBasicOutputs()

            if self.doComputeAdvancedOutputs:
                self._computeAdvancedOutputs()

            # Create an attribute on the mesh for each geomechanics outputs computed:
            for attribute in self._attributesToCreate:
                attributeName: str = attribute.attributeName
                onPoints: bool = attribute.isOnPoints
                array: npt.NDArray[ np.float64 ] | None
                if attribute in ELASTIC_MODULI:
                    array = self._elasticModuli.getElasticModulusValue( attributeName )
                elif attribute in BASIC_OUTPUTS:
                    array = self._basicOutput.getBasicOutputValue( attributeName )
                elif attribute in ADVANCED_OUTPUTS:
                    array = self._advancedOutput.getAdvancedOutputValue( attributeName )
                componentNames: tuple[ str, ...] = ()
                if attribute.nbComponent == 6:
                    componentNames = ComponentNameEnum.XYZ.value

                createAttribute( self.output,
                                 array,
                                 attributeName,
                                 componentNames=componentNames,
                                 onPoints=onPoints,
                                 logger=self.logger )

            self.logger.info( "All the geomechanics properties have been added to the mesh." )
            self.logger.info( "The filter succeeded." )
        except ValueError as ve:
            self.logger.error( f"The filter failed.\n{ ve }." )
        except TypeError as te:
            self.logger.error( f"The filter failed.\n{ te }." )

        return

    def getOutput( self: Self ) -> vtkUnstructuredGrid:
        """Get the mesh with the geomechanical outputs as attributes.

        Returns:
            vtkUnstructuredGrid: The mesh with the geomechanical outputs as attributes.
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

    def _checkMandatoryAttributes( self: Self ) -> None:
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
        """
        mess: str
        for elasticModulus in ELASTIC_MODULI:
            elasticModulusName: str = elasticModulus.attributeName
            elasticModulusOnPoints: bool = elasticModulus.isOnPoints
            if isAttributeInObject( self.output, elasticModulusName, elasticModulusOnPoints ):
                self._elasticModuli.setElasticModulusValue(
                    elasticModulus.attributeName,
                    getArrayInObject( self.output, elasticModulusName, elasticModulusOnPoints ) )

        # Check the presence of the elastic moduli at the current time.
        self.computeYoungPoisson: bool
        if self._elasticModuli.youngModulus is None and self._elasticModuli.poissonRatio is None:
            if self._elasticModuli.bulkModulus is not None and self._elasticModuli.shearModulus is not None:
                self._elasticModuli.youngModulus = fcts.youngModulus( self._elasticModuli.bulkModulus,
                                                                      self._elasticModuli.shearModulus )
                self._attributesToCreate.append( YOUNG_MODULUS )
                self._elasticModuli.poissonRatio = fcts.poissonRatio( self._elasticModuli.bulkModulus,
                                                                      self._elasticModuli.shearModulus )
                self._attributesToCreate.append( POISSON_RATIO )
                self.computeYoungPoisson = True
            else:
                mess = f"{ BULK_MODULUS.attributeName } or { SHEAR_MODULUS.attributeName } are missing to compute geomechanical outputs."
                raise ValueError( mess )
        elif self._elasticModuli.bulkModulus is None and self._elasticModuli.shearModulus is None:
            if self._elasticModuli.youngModulus is not None and self._elasticModuli.poissonRatio is not None:
                self._elasticModuli.bulkModulus = fcts.bulkModulus( self._elasticModuli.youngModulus,
                                                                    self._elasticModuli.poissonRatio )
                self._attributesToCreate.append( BULK_MODULUS )
                self._elasticModuli.shearModulus = fcts.shearModulus( self._elasticModuli.youngModulus,
                                                                      self._elasticModuli.poissonRatio )
                self._attributesToCreate.append( SHEAR_MODULUS )
                self.computeYoungPoisson = False
            else:
                mess = f"{ YOUNG_MODULUS.attributeName } or { POISSON_RATIO.attributeName } are missing to compute geomechanical outputs."
                raise ValueError( mess )
        else:
            mess = f"{ BULK_MODULUS.attributeName } and { SHEAR_MODULUS.attributeName } or { YOUNG_MODULUS.attributeName } and { POISSON_RATIO.attributeName } are mandatory to compute geomechanical outputs."
            raise ValueError( mess )

        # Check the presence of the elastic moduli at the initial time.
        if self._elasticModuli.bulkModulusT0 is None:
            if self._elasticModuli.youngModulusT0 is not None and self._elasticModuli.poissonRatioT0 is not None:
                self._elasticModuli.bulkModulusT0 = fcts.bulkModulus( self._elasticModuli.youngModulusT0,
                                                                      self._elasticModuli.poissonRatioT0 )
                self._attributesToCreate.append( BULK_MODULUS_T0 )
            else:
                mess = f"{ BULK_MODULUS_T0.attributeName } or { YOUNG_MODULUS_T0.attributeName } and { POISSON_RATIO_T0.attributeName } are mandatory to compute geomechanical outputs."
                raise ValueError( mess )

        # Check the presence of the other mandatory attributes
        for mandatoryAttribute in MANDATORY_ATTRIBUTES:
            mandatoryAttributeName: str = mandatoryAttribute.attributeName
            mandatoryAttributeOnPoints: bool = mandatoryAttribute.isOnPoints
            if not isAttributeInObject( self.output, mandatoryAttributeName, mandatoryAttributeOnPoints ):
                mess = f"The mandatory attribute { mandatoryAttributeName } is missing to compute geomechanical outputs."
                raise ValueError( mess )
            else:
                self._mandatoryAttributes.setMandatoryAttributeValue(
                    mandatoryAttributeName,
                    getArrayInObject( self.output, mandatoryAttributeName, mandatoryAttributeOnPoints ) )

        return

    def _computeBasicOutputs( self: Self ) -> None:
        """Compute the basic geomechanics outputs."""
        self._computeBiotCoefficient()
        self._computeCompressibilityCoefficient()
        self._computeRealEffectiveStressRatio()
        self._computeSpecificGravity()
        # TODO: deactivate lithostatic stress calculation until right formula
        # self._computeLithostaticStress()
        self._computeTotalStresses()
        self._computeElasticStrain()
        self._computeEffectiveStressRatioOed()
        self._computeReservoirStressPathOed()
        self._computeReservoirStressPathReal()

        self.logger.info( "All geomechanics basic outputs were successfully computed." )
        return

    def _computeAdvancedOutputs( self: Self ) -> None:
        """Compute the advanced geomechanics outputs."""
        self._computeCriticalTotalStressRatio()
        self._computeCriticalPorePressure()

        self.logger.info( "All geomechanics advanced outputs were successfully computed." )
        return

    def _computeBiotCoefficient( self: Self ) -> None:
        """Compute the Biot coefficient from default and grain bulk modulus."""
        if not isAttributeInObject( self.output, BIOT_COEFFICIENT.attributeName, BIOT_COEFFICIENT.isOnPoints ):
            self._basicOutput.biotCoefficient = fcts.biotCoefficient( self.physicalConstants.grainBulkModulus,
                                                                      self._elasticModuli.bulkModulus )
            self._attributesToCreate.append( BIOT_COEFFICIENT )
        else:
            self._basicOutput.biotCoefficient = getArrayInObject( self.output, BIOT_COEFFICIENT.attributeName,
                                                                  BIOT_COEFFICIENT.isOnPoints )
            self.logger.warning(
                f"{ BIOT_COEFFICIENT.attributeName } is already on the mesh, it has not been computed by the filter." )

        return

    def _computeCompressibilityCoefficient( self: Self ) -> None:
        """Compute the normal, the oedometric and the real compressibility coefficient from Poisson's ratio, bulk modulus, Biot coefficient and Porosity."""
        # normal compressibility
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

        return

    def _computeSpecificGravity( self: Self ) -> None:
        """Compute the specific gravity from rock density and specific density."""
        if not isAttributeInObject( self.output, SPECIFIC_GRAVITY.attributeName, SPECIFIC_GRAVITY.isOnPoints ):
            self._basicOutput.specificGravity = fcts.specificGravity( self._mandatoryAttributes.density,
                                                                      self.physicalConstants.specificDensity )
            self._attributesToCreate.append( SPECIFIC_GRAVITY )
        else:
            self._basicOutput.specificGravity = getArrayInObject( self.output, SPECIFIC_GRAVITY.attributeName,
                                                                  SPECIFIC_GRAVITY.isOnPoints )
            self.logger.warning(
                f"{ SPECIFIC_GRAVITY.attributeName } is already on the mesh, it has not been computed by the filter." )

        return

    def _doComputeRatio(
        self: Self,
        array: npt.NDArray[ np.float64 ],
        geomechanicProperty: AttributeEnum,
    ) -> npt.NDArray[ np.float64 ]:
        """Compute the ratio between horizontal and vertical value of an array.

        Args:
            array (npt.NDArray[np.float64]): The array with the ratio to compute.
            geomechanicProperty (AttributeEnum): The geomechanic property link to the computed ratio.

        Returns:
            npt.NDArray[np.float64]: The computed ratio.
        """
        verticalStress: npt.NDArray[ np.float64 ] = array[ :, 2 ]
        # keep the minimum of the 2 horizontal components
        horizontalStress: npt.NDArray[ np.float64 ] = np.min( array[ :, :2 ], axis=1 )

        ratio: npt.NDArray[ np.float64 ]
        if not isAttributeInObject( self.output, geomechanicProperty.attributeName, geomechanicProperty.isOnPoints ):
            ratio = fcts.stressRatio( horizontalStress, verticalStress )
            self._attributesToCreate.append( geomechanicProperty )
        else:
            ratio = getArrayInObject( self.output, geomechanicProperty.attributeName, geomechanicProperty.isOnPoints )
            self.logger.warning(
                f"{ geomechanicProperty.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return ratio

    def _computeRealEffectiveStressRatio( self: Self ) -> None:
        """Compute the real effective stress ratio from the effective stress."""
        if self._mandatoryAttributes.effectiveStress is not None:
            self._basicOutput.effectiveStressRatioReal = self._doComputeRatio(
                self._mandatoryAttributes.effectiveStress, STRESS_EFFECTIVE_RATIO_REAL )

        return

    def _doComputeTotalStress(
        self: Self,
        effectiveStress: npt.NDArray[ np.float64 ],
        pressure: Union[ npt.NDArray[ np.float64 ], None ],
        biotCoefficient: npt.NDArray[ np.float64 ],
        geomechanicProperty: AttributeEnum,
    ) -> npt.NDArray[ np.float64 ]:
        """Compute the total stress from the effective stress, the Biot coefficient and the pressure.

        Args:
            effectiveStress (npt.NDArray[np.float64]): The array with the effective stress.
            pressure (npt.NDArray[np.float64] | None): The array with the Pressure.
            biotCoefficient (npt.NDArray[np.float64]): The array with the Biot coefficient.
            geomechanicProperty (AttributeEnum): The geomechanic property link to the total stress computed.

        Returns:
            npt.NDArray[ np.float64 ]: The array with the totalStress computed.
        """
        totalStress: npt.NDArray[ np.float64 ]
        if not isAttributeInObject( self.output, geomechanicProperty.attributeName, geomechanicProperty.isOnPoints ):
            if pressure is None:
                totalStress = np.copy( effectiveStress )
                self.logger.warning( "There is no pressure, the total stress is equal to the effective stress." )
            else:
                if np.isnan( pressure ).any():
                    self.logger.warning(
                        "Some cells do not have pressure data, for those cells, pressure is set to 0." )
                    pressure[ np.isnan( pressure ) ] = 0.0

                totalStress = fcts.totalStress( effectiveStress, biotCoefficient, pressure )
            self._attributesToCreate.append( geomechanicProperty )
        else:
            totalStress = getArrayInObject( self.output, geomechanicProperty.attributeName,
                                            geomechanicProperty.isOnPoints )
            self.logger.warning(
                f"{ geomechanicProperty.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return totalStress

    def _doComputeTotalStressInitial( self: Self ) -> None:
        """Compute the total stress at the initial time step from the initial effective stress, the initial Biot coefficient and the initial pressure."""
        # Compute the Biot coefficient at the initial time step.
        biotCoefficientT0: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( self.physicalConstants.grainBulkModulus,
                                                                             self._elasticModuli.bulkModulusT0 )

        # Compute the pressure at the initial time step.
        pressureT0: npt.NDArray[ np.float64 ] | None = None
        if self._mandatoryAttributes.pressure is not None and self._mandatoryAttributes.deltaPressure is not None:
            pressureT0 = self._mandatoryAttributes.pressure - self._mandatoryAttributes.deltaPressure

        if self._mandatoryAttributes.effectiveStressT0 is not None:
            self._basicOutput.totalStressT0 = self._doComputeTotalStress( self._mandatoryAttributes.effectiveStressT0,
                                                                          pressureT0, biotCoefficientT0,
                                                                          STRESS_TOTAL_T0 )

        return

    def _computeTotalStresses( self: Self ) -> None:
        """Compute total stress and the total stress ratio from the effective stress, the Biot coefficient and the pressure.

        Total stress is computed at the initial and current time steps.
        Total stress ratio is computed at current time step only.
        """
        # Compute the total stress at the initial time step.
        self._doComputeTotalStressInitial()

        mess: str
        # Compute the total stress at the current time step.
        if self._mandatoryAttributes.effectiveStress is not None and self._basicOutput.biotCoefficient is not None:
            self._basicOutput.totalStress = self._doComputeTotalStress( self._mandatoryAttributes.effectiveStress,
                                                                        self._mandatoryAttributes.pressure,
                                                                        self._basicOutput.biotCoefficient,
                                                                        STRESS_TOTAL )
        else:
            mess = f"{ STRESS_TOTAL.attributeName } has not been computed, geomechanics property { STRESS_EFFECTIVE.attributeName } or { BIOT_COEFFICIENT.attributeName } are missing."
            raise ValueError( mess )

        # Compute the total stress ratio.
        if self._basicOutput.totalStress is not None:
            self._basicOutput.totalStressRatioReal = self._doComputeRatio( self._basicOutput.totalStress,
                                                                           STRESS_TOTAL_RATIO_REAL )

        return

    def _computeLithostaticStress( self: Self ) -> None:
        """Compute the lithostatic stress."""
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

        return

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

    def _computeElasticStrain( self: Self ) -> None:
        """Compute the elastic strain from the effective stress and the elastic modulus."""
        if self._mandatoryAttributes.effectiveStress is not None and self._mandatoryAttributes.effectiveStressT0 is not None:
            deltaEffectiveStress = self._mandatoryAttributes.effectiveStress - self._mandatoryAttributes.effectiveStressT0

            if not isAttributeInObject( self.output, STRAIN_ELASTIC.attributeName, STRAIN_ELASTIC.isOnPoints ):
                if self.computeYoungPoisson:
                    self._basicOutput.elasticStrain = fcts.elasticStrainFromBulkShear(
                        deltaEffectiveStress, self._elasticModuli.bulkModulus, self._elasticModuli.shearModulus )
                else:
                    self._basicOutput.elasticStrain = fcts.elasticStrainFromYoungPoisson(
                        deltaEffectiveStress, self._elasticModuli.youngModulus, self._elasticModuli.poissonRatio )
                self._attributesToCreate.append( STRAIN_ELASTIC )
            else:
                self._basicOutput.totalStressT0 = getArrayInObject( self.output, STRAIN_ELASTIC.attributeName,
                                                                    STRAIN_ELASTIC.isOnPoints )
                self.logger.warning(
                    f"{ STRAIN_ELASTIC.attributeName } is already on the mesh, it has not been computed by the filter."
                )

        return

    def _computeReservoirStressPathReal( self: Self ) -> None:
        """Compute reservoir stress paths."""
        # create delta stress attribute for QC
        if not isAttributeInObject( self.output, STRESS_TOTAL_DELTA.attributeName, STRESS_TOTAL_DELTA.isOnPoints ):
            if self._basicOutput.totalStress is not None and self._basicOutput.totalStressT0 is not None:
                self._basicOutput.deltaTotalStress = self._basicOutput.totalStress - self._basicOutput.totalStressT0
                self._attributesToCreate.append( STRESS_TOTAL_DELTA )
            else:
                mess: str = f"{ STRESS_TOTAL_DELTA.attributeName } has not been computed, geomechanics properties { STRESS_TOTAL.attributeName } or { STRESS_TOTAL_T0.attributeName } are missing."
                raise ValueError( mess )
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

        return

    def _computeReservoirStressPathOed( self: Self ) -> None:
        """Compute Reservoir Stress Path in oedometric conditions."""
        if not isAttributeInObject( self.output, RSP_OED.attributeName, RSP_OED.isOnPoints ):
            self._basicOutput.rspOed = fcts.reservoirStressPathOed( self._basicOutput.biotCoefficient,
                                                                    self._elasticModuli.poissonRatio )
            self._attributesToCreate.append( RSP_OED )
        else:
            self._basicOutput.rspOed = getArrayInObject( self.output, RSP_OED.attributeName, RSP_OED.isOnPoints )
            self.logger.warning(
                f"{ RSP_OED.attributeName } is already on the mesh, it has not been computed by the filter." )

        return

    def _computeEffectiveStressRatioOed( self: Self ) -> None:
        """Compute the effective stress ratio in oedometric conditions."""
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

        return

    def _computeCriticalTotalStressRatio( self: Self ) -> None:
        """Compute fracture index and fracture threshold."""
        mess: str
        if not isAttributeInObject( self.output, CRITICAL_TOTAL_STRESS_RATIO.attributeName,
                                    CRITICAL_TOTAL_STRESS_RATIO.isOnPoints ):
            if self._basicOutput.totalStress is not None:
                verticalStress: npt.NDArray[ np.float64 ] = self._basicOutput.totalStress[ :, 2 ]
                self._advancedOutput.criticalTotalStressRatio = fcts.criticalTotalStressRatio(
                    self._mandatoryAttributes.pressure, verticalStress )
                self._attributesToCreate.append( CRITICAL_TOTAL_STRESS_RATIO )
            else:
                mess = f"{ CRITICAL_TOTAL_STRESS_RATIO.attributeName } has not been computed, geomechanics property { STRESS_TOTAL.attributeName } is missing."
                raise ValueError( mess )
        else:
            self._advancedOutput.criticalTotalStressRatio = getArrayInObject( self.output,
                                                                              CRITICAL_TOTAL_STRESS_RATIO.attributeName,
                                                                              CRITICAL_TOTAL_STRESS_RATIO.isOnPoints )
            self.logger.warning(
                f"{ CRITICAL_TOTAL_STRESS_RATIO.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        if not isAttributeInObject( self.output, TOTAL_STRESS_RATIO_THRESHOLD.attributeName,
                                    TOTAL_STRESS_RATIO_THRESHOLD.isOnPoints ):
            if self._basicOutput.totalStress is not None:
                mask: npt.NDArray[ np.bool_ ] = np.argmin( np.abs( self._basicOutput.totalStress[ :, :2 ] ), axis=1 )
                horizontalStress: npt.NDArray[ np.float64 ] = self._basicOutput.totalStress[ :, :2 ][
                    np.arange( self._basicOutput.totalStress[ :, :2 ].shape[ 0 ] ), mask ]
                self._advancedOutput.stressRatioThreshold = fcts.totalStressRatioThreshold(
                    self._mandatoryAttributes.pressure, horizontalStress )
                self._attributesToCreate.append( TOTAL_STRESS_RATIO_THRESHOLD )
            else:
                mess = f"{ TOTAL_STRESS_RATIO_THRESHOLD.attributeName } has not been computed, geomechanics property { STRESS_TOTAL.attributeName } is missing."
                raise ValueError( mess )
        else:
            self._advancedOutput.stressRatioThreshold = getArrayInObject( self.output,
                                                                          TOTAL_STRESS_RATIO_THRESHOLD.attributeName,
                                                                          TOTAL_STRESS_RATIO_THRESHOLD.isOnPoints )
            self.logger.warning(
                f"{ TOTAL_STRESS_RATIO_THRESHOLD.attributeName } is already on the mesh, it has not been computed by the filter."
            )

        return

    def _computeCriticalPorePressure( self: Self ) -> None:
        """Compute the critical pore pressure and the pressure index."""
        if not isAttributeInObject( self.output, CRITICAL_PORE_PRESSURE.attributeName,
                                    CRITICAL_PORE_PRESSURE.isOnPoints ):
            if self._basicOutput.totalStress is not None:
                self._advancedOutput.criticalPorePressure = fcts.criticalPorePressure(
                    -1.0 * self._basicOutput.totalStress, self.physicalConstants.rockCohesion,
                    self.physicalConstants.frictionAngle )
                self._attributesToCreate.append( CRITICAL_PORE_PRESSURE )
            else:
                mess: str
                mess = f"{ CRITICAL_PORE_PRESSURE.attributeName } has not been computed, geomechanics property { STRESS_TOTAL.attributeName } is missing."
                raise ValueError( mess )
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

        return
