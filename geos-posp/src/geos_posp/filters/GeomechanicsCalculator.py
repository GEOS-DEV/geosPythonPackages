# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Union

import geos.geomechanics.processing.geomechanicsCalculatorFunctions as fcts
import numpy as np
import numpy.typing as npt
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
    from geos_posp.filters.GeomechanicsCalculator import GeomechanicsCalculator

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

    # instanciate the filter
    geomechanicsCalculatorFilter :GeomechanicsCalculator = GeomechanicsCalculator()

    # set filter attributes
    # set logger
    geomechanicsCalculatorFilter.SetLogger(logger)
    # set input object
    geomechanicsCalculatorFilter.SetInputDataObject(input)
    # set computeAdvancedOutputsOn or computeAdvancedOutputsOff to compute or
    # not advanced outputs...
    geomechanicsCalculatorFilter.computeAdvancedOutputsOn()
    # set oter parameters
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

TYPE_ERROR_MESSAGE = ( "Input object must by either a vtkPointSet or a vtkUntructuredGrid." )
UNDEFINED_ATTRIBUTE_MESSAGE = " attribute is undefined."


class GeomechanicsCalculator( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """VTK Filter to perform Geomechanical output computation.

        Input object is either a vtkPointSet or a vtkUntructuredGrid.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkDataSet" )  # type: ignore[no-untyped-call]

        self.m_output: Union[ vtkPointSet, vtkUnstructuredGrid ]

        # additional parameters
        self.m_computeAdvancedOutputs: bool = False
        self.m_grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.m_specificDensity: float = WATER_DENSITY
        self.m_rockCohesion: float = DEFAULT_ROCK_COHESION
        self.m_frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        # computation results
        self.m_elasticModuliComputed: bool = False
        self.m_biotCoefficientComputed: bool = False
        self.m_compressibilityComputed: bool = False
        self.m_effectiveStressComputed: bool = False
        self.m_totalStressComputed: bool = False
        self.m_effectiveStressRatioOedComputed: bool = False

        # will compute resuls if m_ready is True (updated by initFilter method)
        self.m_ready: bool = False
        # attributes are either on points or on cells
        self.m_attributeOnPoints: bool = False
        # elastic moduli are either bulk and Shear moduli (m_computeYoungPoisson=True)
        # or young Modulus and poisson's ratio (m_computeYoungPoisson=False)
        self.m_computeYoungPoisson: bool = True

        # set m_logger
        self.m_logger: Logger = getLogger( "Geomechanics calculator" )

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkDataSet" )
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()  # noqa: F841
        outInfo = outInfoVec.GetInformationObject( 0 )  # noqa: F841
        return 1

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
        inData = self.GetInputData( inInfoVec, 0, 0 )  # type: ignore[no-untyped-call]
        outData = self.GetOutputData( outInfoVec, 0 )  # type: ignore[no-untyped-call]
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore

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
        try:
            input: vtkDataSet = vtkDataSet.GetData( inInfoVec[ 0 ] )
            assert input is not None, "Input object is null."

            # initialize output objects
            self.m_output = self.GetOutputData( outInfoVec, 0 )  # type: ignore[no-untyped-call]
            assert self.m_output is not None, "Output object is null."
            self.m_output.ShallowCopy( input )

            # check the input and update self.m_ready, m_attributeOnPoints and m_computeBulkAndShear
            self.initFilter()
            if not self.m_ready:
                mess: str = ( "Mandatory properties are missing to compute geomechanical outputs:" )
                mess += ( f"Either {PostProcessingOutputsEnum.YOUNG_MODULUS.attributeName} "
                          f"and {PostProcessingOutputsEnum.POISSON_RATIO.attributeName} or "
                          f"{GeosMeshOutputsEnum.BULK_MODULUS.attributeName} and "
                          f"{GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName} must be "
                          f"present in the data as well as the "
                          f"{GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName} attribute." )
                self.m_logger.error( mess )
                return 0

            self.computeBasicOutputs()
            if self.m_computeAdvancedOutputs:
                self.computeAdvancedOutputs()

        except AssertionError as e:
            mess1: str = "Geomechanical attribute calculation failed due to:"
            self.m_logger.error( mess1 )
            self.m_logger.error( str( e ) )
            return 0
        except Exception as e:
            mess2: str = "Geomechanical attribut calculation failed due to:"
            self.m_logger.critical( mess2 )
            self.m_logger.critical( e, exc_info=True )
            return 0
        return 1

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set the logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger
        self.Modified()

    def computeAdvancedOutputsOn( self: Self ) -> None:
        """Activate advanced outputs calculation."""
        self.m_computeAdvancedOutputs = True
        self.Modified()

    def computeAdvancedOutputsOff( self: Self ) -> None:
        """Deactivate advanced outputs calculation."""
        self.m_computeAdvancedOutputs = False
        self.Modified()

    def SetGrainBulkModulus( self: Self, grainBulkModulus: float ) -> None:
        """Set the grain bulk modulus.

        Args:
            grainBulkModulus (float): grain bulk modulus
        """
        self.m_grainBulkModulus = grainBulkModulus
        self.Modified()

    def SetSpecificDensity( self: Self, specificDensity: float ) -> None:
        """Set the specific density.

        Args:
            specificDensity (float): pecific density
        """
        self.m_specificDensity = specificDensity
        self.Modified()

    def SetRockCohesion( self: Self, rockCohesion: float ) -> None:
        """Set the rock cohesion.

        Args:
            rockCohesion (float): rock cohesion
        """
        self.m_rockCohesion = rockCohesion
        self.Modified()

    def SetFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set the friction angle.

        Args:
            frictionAngle (float): friction angle (rad)
        """
        self.m_frictionAngle = frictionAngle
        self.Modified()

    def getOutputType( self: Self ) -> str:
        """Get output object type.

        Returns:
            str: type of output object.
        """
        output: vtkDataSet = self.GetOutputDataObject( 0 )
        assert output is not None, "Output is null."
        return output.GetClassName()

    def resetDefaultValues( self: Self ) -> None:
        """Reset filter parameters to the default values."""
        self.m_computeAdvancedOutputs = False
        self.m_grainBulkModulus = DEFAULT_GRAIN_BULK_MODULUS
        self.m_specificDensity = WATER_DENSITY
        self.m_rockCohesion = DEFAULT_ROCK_COHESION
        self.m_frictionAngle = DEFAULT_FRICTION_ANGLE_RAD

        self.m_elasticModuliComputed = False
        self.m_biotCoefficientComputed = False
        self.m_compressibilityComputed = False
        self.m_effectiveStressComputed = False
        self.m_totalStressComputed = False
        self.m_effectiveStressRatioOedComputed = False
        self.m_ready = False
        self.Modified()

    def initFilter( self: Self ) -> None:
        """Check that mandatory attributes are present in the data set.

        Determine if attributes are on cells or on Points.
        Set self.m_ready = True if all data is ok, False otherwise
        """
        # check attributes are on cells, or on points otherwise
        attributeOnPoints: bool = False
        attributeOnCells: bool = self.checkMandatoryAttributes( False )
        if not attributeOnCells:
            attributeOnPoints = self.checkMandatoryAttributes( True )

        self.m_ready = attributeOnPoints or attributeOnCells
        self.m_attributeOnPoints = attributeOnPoints

    def checkMandatoryAttributes( self: Self, onPoints: bool ) -> bool:
        """Check that mandatory attributes are present in the mesh.

        The mesh must contains either the young Modulus and Poisson's ratio
        (m_computeYoungPoisson=False) or the bulk and shear moduli
        (m_computeYoungPoisson=True)

        Args:
            onPoints (bool): attributes are on points (True) or on cells (False)

        Returns:
            bool: True if all needed attributes are present, False otherwise
        """
        youngModulusAttributeName: str = ( PostProcessingOutputsEnum.YOUNG_MODULUS.attributeName )
        poissonRatioAttributeName: str = ( PostProcessingOutputsEnum.POISSON_RATIO.attributeName )
        bulkModulusAttributeName: str = GeosMeshOutputsEnum.BULK_MODULUS.attributeName
        shearModulusAttributeName: str = GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName
        effectiveStressAttributeName: str = ( GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName )

        self.m_computeYoungPoisson = not isAttributeInObject( self.m_output, youngModulusAttributeName,
                                                              onPoints ) or not isAttributeInObject(
                                                                  self.m_output, poissonRatioAttributeName, onPoints )

        # if none of elastic moduli is present, return False
        if self.m_computeYoungPoisson and (
                not isAttributeInObject( self.m_output, bulkModulusAttributeName, onPoints )
                or not isAttributeInObject( self.m_output, shearModulusAttributeName, onPoints ) ):
            return False

        # check effective Stress is present
        ret: bool = isAttributeInObject( self.m_output, effectiveStressAttributeName, onPoints )
        return ret

    def computeBasicOutputs( self: Self ) -> bool:
        """Compute basic geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not self.m_ready:
            return False

        try:
            self.m_elasticModuliComputed = self.computeElasticModulus()
            if not self.m_elasticModuliComputed:
                mess: str = ( "Geomechanical outputs cannot be computed without elastic moduli." )
                self.m_logger.error( mess )
                return False

            self.m_biotCoefficientComputed = self.computeBiotCoefficient()
            if not self.m_biotCoefficientComputed:
                mess2: str = ( "Total stress, elastic strain, and advanced geomechanical " +
                               "outputs cannot be computed without Biot coefficient." )
                self.m_logger.warning( mess2 )

            self.m_compressibilityComputed = self.computeCompressibilityCoefficient()

            self.m_effectiveStressComputed = self.computeRealEffectiveStressRatio()
            if not self.m_effectiveStressComputed:
                mess3: str = ( "Total stress, elastic strain, and advanced geomechanical " +
                               "outputs cannot be computed without effective stress." )
                self.m_logger.warning( mess3 )

            specificGravityComputed: bool = self.computeSpecificGravity()

            # TODO: deactivate lithostatic stress calculation until right formula
            litostaticStressComputed: bool = True  # self.computeLitostaticStress()

            elasticStrainComputed: bool = False
            if self.m_effectiveStressComputed:
                if self.m_biotCoefficientComputed:
                    self.m_totalStressComputed = self.computeTotalStresses()
                if self.m_elasticModuliComputed:
                    elasticStrainComputed = self.computeElasticStrain()

            reservoirStressPathOedComputed: bool = False
            if self.m_elasticModuliComputed:
                # oedometric DRSP (effective stress ratio in oedometric conditions)
                self.m_effectiveStressRatioOedComputed = ( self.computeEffectiveStressRatioOed() )

                if self.m_biotCoefficientComputed:
                    reservoirStressPathOedComputed = ( self.computeReservoirStressPathOed() )

            reservoirStressPathRealComputed: bool = False
            if self.m_totalStressComputed:
                reservoirStressPathRealComputed = self.computeReservoirStressPathReal()

            if ( self.m_elasticModuliComputed and self.m_biotCoefficientComputed and self.m_compressibilityComputed
                 and self.m_effectiveStressComputed and specificGravityComputed and elasticStrainComputed
                 and litostaticStressComputed and self.m_totalStressComputed and self.m_effectiveStressRatioOedComputed
                 and reservoirStressPathRealComputed and reservoirStressPathRealComputed
                 and reservoirStressPathOedComputed and reservoirStressPathRealComputed ):
                mess4: str = ( "All geomechanical basic outputs were successfully computed." )
                self.m_logger.info( mess4 )
            else:
                mess5: str = "Some geomechanical basic outputs were not computed."
                self.m_logger.warning( mess5 )

        except AssertionError as e:
            mess6: str = ( "Some of the geomechanical basic outputs were " + "not computed due to:" )
            self.m_logger.error( mess6 )
            self.m_logger.error( str( e ) )
            return False
        except Exception as e:
            mess7: str = ( "Some of the geomechanical basic outputs were " + "not computed due to:" )
            self.m_logger.critical( mess7 )
            self.m_logger.critical( e, exc_info=True )
            return False
        return True

    def computeAdvancedOutputs( self: Self ) -> bool:
        """Compute advanced geomechanical outputs.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        if not self.m_ready:
            return False

        try:
            fractureIndexesComputed: bool = False
            criticalPorePressure: bool = False
            if self.m_totalStressComputed:
                fractureIndexesComputed = self.computeCriticalTotalStressRatio()
                criticalPorePressure = self.computeCriticalPorePressure()

            if ( self.m_effectiveStressRatioOedComputed and fractureIndexesComputed and criticalPorePressure ):
                mess: str = ( "All geomechanical advanced outputs were " + "successfully computed." )
                self.m_logger.info( mess )
            else:
                mess0: str = ( "Some geomechanical advanced outputs were " + "not computed." )
                self.m_logger.warning( mess0 )

        except AssertionError as e:
            mess1: str = ( "Some of the geomechanical basic outputs were " + "not computed due to:" )
            self.m_logger.error( mess1 )
            self.m_logger.error( str( e ) )
            return False
        except Exception as e:
            mess2: str = ( "Some of the geomechanical advanced outputs " + "were not computed due to:" )
            self.m_logger.critical( mess2 )
            self.m_logger.critical( e, exc_info=True )
            return False
        return True

    def computeElasticModulus( self: Self ) -> bool:
        """Compute elastic moduli.

        Young modulus and the poisson ratio computed from shear and bulk moduli
        if needed.

        Returns:
            bool: True if elastic moduli are already present or if calculation
            successfully ended, False otherwise.
        """
        if self.m_computeYoungPoisson:
            return self.computeElasticModulusFromBulkShear()
        return self.computeElasticModulusFromYoungPoisson()

    def computeElasticModulusFromBulkShear( self: Self ) -> bool:
        """Compute Young modulus Poisson's ratio from bulk and shear moduli.

        Returns:
            bool: True if calculation successfully ended, False otherwise
        """
        youngModulusAttributeName: str = ( PostProcessingOutputsEnum.YOUNG_MODULUS.attributeName )
        poissonRatioAttributeName: str = ( PostProcessingOutputsEnum.POISSON_RATIO.attributeName )
        bulkModulusAttributeName: str = GeosMeshOutputsEnum.BULK_MODULUS.attributeName
        shearModulusAttributeName: str = GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName

        ret: bool = True
        bulkModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, bulkModulusAttributeName,
                                                                   self.m_attributeOnPoints )

        shearModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, shearModulusAttributeName,
                                                                    self.m_attributeOnPoints )
        try:
            assert bulkModulus is not None, ( f"{bulkModulusAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
            assert shearModulus is not None, ( f"{shearModulusAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
        except AssertionError as e:
            self.m_logger.error( "Elastic moduli were not computed due to:" )
            self.m_logger.error( str( e ) )
            return False

        try:
            youngModulus: npt.NDArray[ np.float64 ] = fcts.youngModulus( bulkModulus, shearModulus )
            # assert np.any(youngModulus < 0), ("Young modulus yields negative " +
            #     "values. Check Bulk and Shear modulus values.")
            createAttribute(
                self.m_output,
                youngModulus,
                youngModulusAttributeName,
                (),
                self.m_attributeOnPoints,
            )
        except AssertionError as e:
            self.m_logger.error( "Young modulus was not computed due to:" )
            self.m_logger.error( str( e ) )
            ret = False

        try:
            poissonRatio: npt.NDArray[ np.float64 ] = fcts.poissonRatio( bulkModulus, shearModulus )
            # assert np.any(poissonRatio < 0), ("Poisson ratio yields negative " +
            #     "values. Check Bulk and Shear modulus values.")
            createAttribute(
                self.m_output,
                poissonRatio,
                poissonRatioAttributeName,
                (),
                self.m_attributeOnPoints,
            )
        except AssertionError as e:
            self.m_logger.error( "Poisson's ratio was not computed due to:" )
            self.m_logger.error( str( e ) )
            ret = False

        return ret

    def computeElasticModulusFromYoungPoisson( self: Self ) -> bool:
        """Compute bulk modulus from Young Modulus and Poisson's ratio.

        Returns:
            bool: True if bulk modulus was wuccessfully computed, False otherwise
        """
        try:
            youngModulusAttributeName: str = ( PostProcessingOutputsEnum.YOUNG_MODULUS.attributeName )
            poissonRatioAttributeName: str = ( PostProcessingOutputsEnum.POISSON_RATIO.attributeName )
            bulkModulusAttributeName: str = ( GeosMeshOutputsEnum.BULK_MODULUS.attributeName )
            if not isAttributeInObject( self.m_output, bulkModulusAttributeName, self.m_attributeOnPoints ):
                youngModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, youngModulusAttributeName,
                                                                            self.m_attributeOnPoints )
                poissonRatio: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, poissonRatioAttributeName,
                                                                            self.m_attributeOnPoints )

                assert youngModulus is not None, ( f"{youngModulusAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert poissonRatio is not None, ( f"{poissonRatioAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                bulkModulus: npt.NDArray[ np.float64 ] = fcts.bulkModulus( youngModulus, poissonRatio )
                # assert np.any(bulkModulus < 0), ("Bulk modulus yields negative " +
                #     "values. Check Young modulus and Poisson ratio values.")
                ret: bool = createAttribute(
                    self.m_output,
                    bulkModulus,
                    bulkModulusAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
                return ret

        except AssertionError as e:
            self.m_logger.error( "Bulk modulus was not computed due to:" )
            self.m_logger.error( str( e ) )
            return False
        return True

    def computeBiotCoefficient( self: Self ) -> bool:
        """Compute Biot coefficient from default and grain bulk modulus.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        biotCoefficientAttributeName: str = ( PostProcessingOutputsEnum.BIOT_COEFFICIENT.attributeName )
        if not isAttributeInObject( self.m_output, biotCoefficientAttributeName, self.m_attributeOnPoints ):
            bulkModulusAttributeName: str = ( GeosMeshOutputsEnum.BULK_MODULUS.attributeName )
            bulkModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, bulkModulusAttributeName,
                                                                       self.m_attributeOnPoints )
            try:
                assert bulkModulus is not None, ( f"{bulkModulusAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )

                biotCoefficient: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( self.m_grainBulkModulus,
                                                                                   bulkModulus )
                createAttribute(
                    self.m_output,
                    biotCoefficient,
                    biotCoefficientAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Biot coefficient was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

    def computeCompressibilityCoefficient( self: Self ) -> bool:
        """Compute compressibility coefficient from simulation outputs.

        Compressibility coefficient is computed from Poisson's ratio, bulk
        modulus, Biot coefficient and Porosity.

        Returns:
            bool: True if the attribute is correctly created, False otherwise.
        """
        compressibilityAttributeName: str = ( PostProcessingOutputsEnum.COMPRESSIBILITY.attributeName )
        bulkModulusAttributeName: str = GeosMeshOutputsEnum.BULK_MODULUS.attributeName
        bulkModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, bulkModulusAttributeName,
                                                                   self.m_attributeOnPoints )
        porosityAttributeName: str = GeosMeshOutputsEnum.POROSITY.attributeName
        porosity: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, porosityAttributeName,
                                                                self.m_attributeOnPoints )
        porosityInitialAttributeName: str = ( GeosMeshOutputsEnum.POROSITY_INI.attributeName )
        porosityInitial: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, porosityInitialAttributeName,
                                                                       self.m_attributeOnPoints )
        if not isAttributeInObject( self.m_output, compressibilityAttributeName, self.m_attributeOnPoints ):
            poissonRatioAttributeName: str = ( PostProcessingOutputsEnum.POISSON_RATIO.attributeName )
            poissonRatio: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, poissonRatioAttributeName,
                                                                        self.m_attributeOnPoints )
            biotCoefficientAttributeName: str = ( PostProcessingOutputsEnum.BIOT_COEFFICIENT.attributeName )
            biotCoefficient: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, biotCoefficientAttributeName,
                                                                           self.m_attributeOnPoints )

            try:
                assert poissonRatio is not None, ( f"{poissonRatioAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert bulkModulus is not None, ( f"{bulkModulusAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert biotCoefficient is not None, ( f"{biotCoefficientAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert porosity is not None, ( f"{porosityAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )

                compressibility: npt.NDArray[ np.float64 ] = fcts.compressibility( poissonRatio, bulkModulus,
                                                                                   biotCoefficient, porosity )
                createAttribute(
                    self.m_output,
                    compressibility,
                    compressibilityAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Compressibility was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        # oedometric compressibility
        compressibilityOedAttributeName: str = ( PostProcessingOutputsEnum.COMPRESSIBILITY_OED.attributeName )
        if not isAttributeInObject( self.m_output, compressibilityOedAttributeName, self.m_attributeOnPoints ):
            shearModulusAttributeName: str = ( GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName )
            shearModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, shearModulusAttributeName,
                                                                        self.m_attributeOnPoints )
            try:
                assert poissonRatio is not None, ( f"{poissonRatioAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert bulkModulus is not None, ( f"{bulkModulusAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert porosityInitial is not None, ( f"{porosityInitialAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                compressibilityOed: npt.NDArray[ np.float64 ] = fcts.compressibilityOed(
                    bulkModulus, shearModulus, porosityInitial )
                createAttribute(
                    self.m_output,
                    compressibilityOed,
                    compressibilityOedAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Oedometric Compressibility was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        # real compressibility
        compressibilityRealAttributeName: str = ( PostProcessingOutputsEnum.COMPRESSIBILITY_REAL.attributeName )
        if not isAttributeInObject( self.m_output, compressibilityRealAttributeName, self.m_attributeOnPoints ):
            deltaPressureAttributeName: str = ( GeosMeshOutputsEnum.DELTA_PRESSURE.attributeName )
            deltaPressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, deltaPressureAttributeName,
                                                                         self.m_attributeOnPoints )
            try:
                assert deltaPressure is not None, ( f"{deltaPressureAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert porosityInitial is not None, ( f"{porosityInitialAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert porosity is not None, ( f"{porosityAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )
                compressibilityReal: npt.NDArray[ np.float64 ] = fcts.compressibilityReal(
                    deltaPressure, porosity, porosityInitial )
                createAttribute(
                    self.m_output,
                    compressibilityReal,
                    compressibilityRealAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Real compressibility was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

    def computeSpecificGravity( self: Self ) -> bool:
        """Create Specific gravity attribute.

        Specific gravity is computed from rock density attribute and specific
        density input.

        Returns:
            bool: True if the attribute is correctly created, False otherwise.
        """
        densityAttributeName: str = GeosMeshOutputsEnum.ROCK_DENSITY.attributeName
        density: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, densityAttributeName,
                                                               self.m_attributeOnPoints )
        specificGravityAttributeName: str = ( PostProcessingOutputsEnum.SPECIFIC_GRAVITY.attributeName )
        if not isAttributeInObject( self.m_output, specificGravityAttributeName, self.m_attributeOnPoints ):
            try:
                assert density is not None, ( f"{densityAttributeName} " + UNDEFINED_ATTRIBUTE_MESSAGE )

                specificGravity: npt.NDArray[ np.float64 ] = fcts.specificGravity( density, self.m_specificDensity )
                createAttribute(
                    self.m_output,
                    specificGravity,
                    specificGravityAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Specific gravity was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

    def computeRealEffectiveStressRatio( self: Self ) -> bool:
        """Compute effective stress ratio.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # test if effective stress is in the table
        if not isAttributeInObject(
                self.m_output,
                GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName,
                self.m_attributeOnPoints,
        ):
            self.m_logger.error( "Effective stress is not in input data." )
            return False

        # real effective stress ratio
        return self.computeStressRatioReal(
            GeosMeshOutputsEnum.STRESS_EFFECTIVE,
            PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_REAL,
        )

    def computeTotalStresses( self: Self ) -> bool:
        """Compute total stress total stress ratio.

        Total stress is computed at the initial and current time steps.
        total stress ratio is computed at current time step only.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        # compute total stress at initial time step
        totalStressT0AttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL.attributeName )
        if not isAttributeInObject( self.m_output, totalStressT0AttributeName, self.m_attributeOnPoints ):
            self.computeTotalStressInitial()

        # compute total stress at current time step
        totalStressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL.attributeName )
        if not isAttributeInObject( self.m_output, totalStressAttributeName, self.m_attributeOnPoints ):
            try:
                effectiveStressAttributeName: str = ( GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName )
                effectiveStress: npt.NDArray[ np.float64 ] = getArrayInObject(
                    self.m_output,
                    effectiveStressAttributeName,
                    self.m_attributeOnPoints,
                )
                assert effectiveStress is not None, ( f"{effectiveStressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
                pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, pressureAttributeName,
                                                                        self.m_attributeOnPoints )
                assert pressure is not None, ( f"{pressureAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                biotCoefficientAttributeName: str = ( PostProcessingOutputsEnum.BIOT_COEFFICIENT.attributeName )
                biotCoefficient: npt.NDArray[ np.float64 ] = getArrayInObject(
                    self.m_output,
                    biotCoefficientAttributeName,
                    self.m_attributeOnPoints,
                )
                assert biotCoefficient is not None, ( f"{biotCoefficientAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                self.doComputeTotalStress( effectiveStress, pressure, biotCoefficient, totalStressAttributeName )
                self.computeStressRatioReal(
                    PostProcessingOutputsEnum.STRESS_TOTAL,
                    PostProcessingOutputsEnum.STRESS_TOTAL_RATIO_REAL,
                )

            except AssertionError as e:
                self.m_logger.error( "Total stress at current time step was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

    def computeTotalStressInitial( self: Self ) -> bool:
        """Compute total stress at initial time step.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        try:

            # compute elastic moduli at initial time step
            bulkModulusT0: npt.NDArray[ np.float64 ]

            bulkModulusT0AttributeName: str = ( PostProcessingOutputsEnum.BULK_MODULUS_INITIAL.attributeName )
            youngModulusT0AttributeName: str = ( PostProcessingOutputsEnum.YOUNG_MODULUS_INITIAL.attributeName )
            poissonRatioT0AttributeName: str = ( PostProcessingOutputsEnum.POISSON_RATIO_INITIAL.attributeName )
            # get bulk modulus at initial time step
            if isAttributeInObject( self.m_output, bulkModulusT0AttributeName, self.m_attributeOnPoints ):

                bulkModulusT0 = getArrayInObject( self.m_output, bulkModulusT0AttributeName, self.m_attributeOnPoints )
            # or compute it from Young and Poisson if not an attribute
            elif isAttributeInObject( self.m_output, youngModulusT0AttributeName,
                                      self.m_attributeOnPoints ) and isAttributeInObject(
                                          self.m_output, poissonRatioT0AttributeName, self.m_attributeOnPoints ):

                youngModulusT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output,
                                                                              youngModulusT0AttributeName,
                                                                              self.m_attributeOnPoints )
                poissonRatioT0: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output,
                                                                              poissonRatioT0AttributeName,
                                                                              self.m_attributeOnPoints )
                assert poissonRatioT0 is not None, "Poisson's ratio is undefined."
                assert youngModulusT0 is not None, "Young modulus is undefined."
                bulkModulusT0 = fcts.bulkModulus( youngModulusT0, poissonRatioT0 )
            else:
                raise AssertionError( "Elastic moduli at initial time are absent." )

            assert ( bulkModulusT0 is not None ), "Bulk modulus at initial time step is undefined."

            # compute Biot at initial time step
            biotCoefficientT0: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( self.m_grainBulkModulus,
                                                                                 bulkModulusT0 )
            assert ( biotCoefficientT0 is not None ), "Biot coefficient at initial time step is undefined."

            # compute total stress at initial time step
            # get effective stress attribute
            effectiveStressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL.attributeName )
            effectiveStress: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, effectiveStressAttributeName,
                                                                           self.m_attributeOnPoints )
            assert effectiveStress is not None, ( f"{effectiveStressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

            # get pressure attribute
            pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
            pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, pressureAttributeName,
                                                                    self.m_attributeOnPoints )
            pressureT0: npt.NDArray[ np.float64 ]
            # case pressureT0 is None, total stress = effective stress
            # (managed by doComputeTotalStress function)
            if pressure is not None:
                # get delta pressure to recompute pressure at initial time step (pressureTo)
                deltaPressureAttributeName: str = ( GeosMeshOutputsEnum.DELTA_PRESSURE.attributeName )
                deltaPressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, deltaPressureAttributeName,
                                                                             self.m_attributeOnPoints )
                assert deltaPressure is not None, ( f"{deltaPressureAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                pressureT0 = pressure - deltaPressure

            totalStressT0AttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL.attributeName )
            return self.doComputeTotalStress(
                effectiveStress,
                pressureT0,
                biotCoefficientT0,
                totalStressT0AttributeName,
            )

        except AssertionError as e:
            self.m_logger.error( "Total stress at initial time step was not computed due to:" )
            self.m_logger.error( str( e ) )
            return False

    def doComputeTotalStress(
        self: Self,
        effectiveStress: npt.NDArray[ np.float64 ],
        pressure: Union[ npt.NDArray[ np.float64 ], None ],
        biotCoefficient: npt.NDArray[ np.float64 ],
        totalStressAttributeName: str,
    ) -> bool:
        """Compute total stress from effective stress and pressure.

        Args:
            effectiveStress (npt.NDArray[np.float64]): effective stress
            pressure (npt.NDArray[np.float64] | None): pressure
            biotCoefficient (npt.NDArray[np.float64]): biot coefficient
            totalStressAttributeName (str): total stress attribute name

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        totalStress: npt.NDArray[ np.float64 ]
        # if pressure data is missing, total stress equals effective stress
        if pressure is None:
            # copy effective stress data
            totalStress = np.copy( effectiveStress )
            mess: str = ( "Pressure attribute is undefined, " + "total stress will be equal to effective stress." )
            self.m_logger.warning( mess )
        else:
            if np.isnan( pressure ).any():
                mess0: str = ( "Some cells do not have pressure data, " +
                               "total stress will be equal to effective stress." )
                self.m_logger.warning( mess0 )

            # replace nan values by 0.
            pressure[ np.isnan( pressure ) ] = 0.0
            totalStress = fcts.totalStress( effectiveStress, biotCoefficient, pressure )

        # create total stress attribute
        assert totalStress is not None, "Total stress data is null."
        createAttribute(
            self.m_output,
            totalStress,
            totalStressAttributeName,
            ComponentNameEnum.XYZ.value,
            self.m_attributeOnPoints,
        )
        return True

    def computeLitostaticStress( self: Self ) -> bool:
        """Compute lithostatic stress.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        litostaticStressAttributeName: str = ( PostProcessingOutputsEnum.LITHOSTATIC_STRESS.attributeName )
        if not isAttributeInObject( self.m_output, litostaticStressAttributeName, self.m_attributeOnPoints ):

            densityAttributeName: str = GeosMeshOutputsEnum.ROCK_DENSITY.attributeName
            density: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, densityAttributeName,
                                                                   self.m_attributeOnPoints )
            try:
                depth: npt.NDArray[ np.float64 ] = self.computeDepthAlongLine(
                ) if self.m_attributeOnPoints else self.computeDepthInMesh()
                assert depth is not None, "Depth is undefined."
                assert density is not None, ( f"{densityAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                litostaticStress = fcts.lithostaticStress( depth, density, GRAVITY )
                createAttribute(
                    self.m_output,
                    litostaticStress,
                    litostaticStressAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Lithostatic stress was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

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
        """Get z coordinates from self.m_output.

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
        elasticStrainAttributeName: str = ( PostProcessingOutputsEnum.STRAIN_ELASTIC.attributeName )
        if not isAttributeInObject( self.m_output, elasticStrainAttributeName, self.m_attributeOnPoints ):
            effectiveStressAttributeName: str = ( GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName )
            effectiveStress: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, effectiveStressAttributeName,
                                                                           self.m_attributeOnPoints )

            effectiveStressIniAttributeName: str = ( PostProcessingOutputsEnum.STRESS_EFFECTIVE_INITIAL.attributeName )
            effectiveStressIni: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output,
                                                                              effectiveStressIniAttributeName,
                                                                              self.m_attributeOnPoints )

            bulkModulusAttributeName: str = ( GeosMeshOutputsEnum.BULK_MODULUS.attributeName )
            bulkModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, bulkModulusAttributeName,
                                                                       self.m_attributeOnPoints )

            shearModulusAttributeName: str = ( GeosMeshOutputsEnum.SHEAR_MODULUS.attributeName )
            shearModulus: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, shearModulusAttributeName,
                                                                        self.m_attributeOnPoints )

            try:
                assert effectiveStress is not None, ( f"{effectiveStressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert effectiveStressIni is not None, ( f"{effectiveStressIniAttributeName}" +
                                                         UNDEFINED_ATTRIBUTE_MESSAGE )
                assert bulkModulus is not None, ( f"{bulkModulusAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert shearModulus is not None, ( f"{shearModulusAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                deltaEffectiveStress = effectiveStress - effectiveStressIni
                elasticStrain: npt.NDArray[ np.float64 ] = ( fcts.elasticStrainFromBulkShear(
                    deltaEffectiveStress, bulkModulus, shearModulus ) )
                createAttribute(
                    self.m_output,
                    elasticStrain,
                    elasticStrainAttributeName,
                    ComponentNameEnum.XYZ.value,
                    self.m_attributeOnPoints,
                )

            except AssertionError as e:
                self.m_logger.error( "Elastic strain was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False
        return True

    def computeReservoirStressPathReal( self: Self ) -> bool:
        """Compute reservoir stress paths.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        RSPrealAttributeName: str = PostProcessingOutputsEnum.RSP_REAL.attributeName
        if not isAttributeInObject( self.m_output, RSPrealAttributeName, self.m_attributeOnPoints ):
            # real RSP
            try:
                # total stress at current and initial time steps
                totalStressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL.attributeName )
                totalStress: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, totalStressAttributeName,
                                                                           self.m_attributeOnPoints )

                totalStressT0AttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL_INITIAL.attributeName )
                totalStressIni: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, totalStressT0AttributeName,
                                                                              self.m_attributeOnPoints )

                deltaPressureAttributeName: str = ( GeosMeshOutputsEnum.DELTA_PRESSURE.attributeName )
                deltaPressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, deltaPressureAttributeName,
                                                                             self.m_attributeOnPoints )

                assert totalStress is not None, ( f"{totalStressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert totalStressIni is not None, ( f"{totalStressT0AttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert deltaPressure is not None, ( f"{deltaPressureAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                # create delta stress attribute for QC
                deltaTotalStressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL_DELTA.attributeName )
                deltaStress: npt.NDArray[ np.float64 ] = totalStress - totalStressIni
                componentNames: tuple[ str, ...] = getComponentNames( self.m_output, totalStressAttributeName,
                                                                      self.m_attributeOnPoints )
                assert deltaStress is not None, ( f"{deltaTotalStressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                createAttribute(
                    self.m_output,
                    deltaStress,
                    deltaTotalStressAttributeName,
                    componentNames,
                    self.m_attributeOnPoints,
                )

                RSPreal: npt.NDArray[ np.float64 ] = fcts.reservoirStressPathReal( deltaStress, deltaPressure )
                assert RSPreal is not None, ( f"{RSPrealAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                createAttribute(
                    self.m_output,
                    RSPreal,
                    RSPrealAttributeName,
                    componentNames,
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Reservoir stress path in real conditions was " + "not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

    def computeReservoirStressPathOed( self: Self ) -> bool:
        """Compute Reservoir Stress Path in oedometric conditions.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        RSPOedAttributeName: str = PostProcessingOutputsEnum.RSP_OED.attributeName
        if not isAttributeInObject( self.m_output, RSPOedAttributeName, self.m_attributeOnPoints ):

            poissonRatioAttributeName: str = ( PostProcessingOutputsEnum.POISSON_RATIO.attributeName )
            poissonRatio: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, poissonRatioAttributeName,
                                                                        self.m_attributeOnPoints )

            biotCoefficientAttributeName: str = ( PostProcessingOutputsEnum.BIOT_COEFFICIENT.attributeName )
            biotCoefficient: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, biotCoefficientAttributeName,
                                                                           self.m_attributeOnPoints )

            try:
                assert poissonRatio is not None, ( f"{poissonRatioAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )
                assert biotCoefficient is not None, ( f"{biotCoefficientAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                RSPoed: npt.NDArray[ np.float64 ] = fcts.reservoirStressPathOed( biotCoefficient, poissonRatio )
                createAttribute(
                    self.m_output,
                    RSPoed,
                    RSPOedAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Oedometric RSP was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

    def computeStressRatioReal( self: Self, inputAttribute: AttributeEnum, outputAttribute: AttributeEnum ) -> bool:
        """Compute the ratio between horizontal and vertical effective stress.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        stressRatioRealAttributeName = outputAttribute.attributeName
        if not isAttributeInObject( self.m_output, stressRatioRealAttributeName, self.m_attributeOnPoints ):
            try:
                stressAttributeName: str = inputAttribute.attributeName
                stress: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, stressAttributeName,
                                                                      self.m_attributeOnPoints )
                assert stress is not None, ( f"{stressAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                verticalStress: npt.NDArray[ np.float64 ] = stress[ :, 2 ]
                # keep the minimum of the 2 horizontal components
                horizontalStress: npt.NDArray[ np.float64 ] = np.min( stress[ :, :2 ], axis=1 )

                stressRatioReal: npt.NDArray[ np.float64 ] = fcts.stressRatio( horizontalStress, verticalStress )
                createAttribute(
                    self.m_output,
                    stressRatioReal,
                    stressRatioRealAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( f"{outputAttribute.attributeName} was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False

        return True

    def computeEffectiveStressRatioOed( self: Self ) -> bool:
        """Compute the effective stress ratio in oedometric conditions.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        effectiveStressRatioOedAttributeName: str = (
            PostProcessingOutputsEnum.STRESS_EFFECTIVE_RATIO_OED.attributeName )
        if not isAttributeInObject(
                self.m_output,
                effectiveStressRatioOedAttributeName,
                self.m_attributeOnPoints,
        ):
            poissonRatioAttributeName: str = ( PostProcessingOutputsEnum.POISSON_RATIO.attributeName )
            poissonRatio: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, poissonRatioAttributeName,
                                                                        self.m_attributeOnPoints )

            try:
                assert poissonRatio is not None, ( f"{poissonRatioAttributeName}" + UNDEFINED_ATTRIBUTE_MESSAGE )

                effectiveStressRatioOed: npt.NDArray[ np.float64 ] = ( fcts.deviatoricStressPathOed( poissonRatio ) )
                createAttribute(
                    self.m_output,
                    effectiveStressRatioOed,
                    effectiveStressRatioOedAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
            except AssertionError as e:
                self.m_logger.error( "Oedometric effective stress ratio was not computed due to:" )
                self.m_logger.error( str( e ) )
                return False
        return True

    def computeCriticalTotalStressRatio( self: Self ) -> bool:
        """Compute fracture index and fracture threshold.

        Returns:
            bool: return True if calculation successfully ended, False otherwise.
        """
        ret: bool = True

        fractureIndexAttributeName = ( PostProcessingOutputsEnum.CRITICAL_TOTAL_STRESS_RATIO.attributeName )
        if not isAttributeInObject( self.m_output, fractureIndexAttributeName, self.m_attributeOnPoints ):

            stressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL.attributeName )
            stress: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, stressAttributeName,
                                                                  self.m_attributeOnPoints )

            pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
            pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, pressureAttributeName,
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
                    self.m_output,
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
                    self.m_output,
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
        if not isAttributeInObject( self.m_output, criticalPorePressureAttributeName, self.m_attributeOnPoints ):

            stressAttributeName: str = ( PostProcessingOutputsEnum.STRESS_TOTAL.attributeName )
            stress: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, stressAttributeName,
                                                                  self.m_attributeOnPoints )

            pressureAttributeName: str = GeosMeshOutputsEnum.PRESSURE.attributeName
            pressure: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, pressureAttributeName,
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
                    self.m_output,
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
                    self.m_output,
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
            return self.m_output.GetPoints()  # type: ignore[no-any-return]
        else:
            # Find cell centers
            filter = vtkCellCenters()
            filter.SetInputDataObject( self.m_output )
            filter.Update()
            return filter.GetOutput().GetPoints()  # type: ignore[no-any-return]
