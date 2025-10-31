# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
import logging
import numpy as np

from typing_extensions import Self, Union
import numpy.typing as npt

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkPolyData

from geos.mesh.utils.arrayModifiers import createAttribute
from geos.mesh.utils.arrayHelpers import (
    getArrayInObject,
    getAttributeSet,
    isAttributeInObject,
)
from geos.mesh.utils.genericHelpers import (
    getLocalBasisVectors,
    convertAttributeFromLocalToXYZForOneCell,
)
import geos.geomechanics.processing.geomechanicsCalculatorFunctions as fcts
from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_ROCK_COHESION,
)
from geos.utils.GeosOutputsConstants import (
    ComponentNameEnum,
    GeosMeshOutputsEnum,
    PostProcessingOutputsEnum,
)

__doc__ = """
SurfaceGeomechanics is a VTK filter that allows:
    - Conversion of a set of attributes from local basis to XYZ basis
    - Computation of the shear capacity utilization (SCU)

.. Warning::
    - The computation of the SCU requires the presence of a 'traction' attribute in the input mesh.
    - Conversion from local to XYZ basis is currently only handled for cell attributes.

.. Note::
    Default values for physical constants used in this filter:
        - rock cohesion: 0.0 Pa ( fractured case)
        - friction angle: 10°

Filter input and output types are vtkPolyData.

To use the filter:

.. code-block:: python

    from geos.processing.post_processing.SurfaceGeomechanics import SurfaceGeomechanics

    # filter inputs
    inputMesh: vtkPolyData

    # Optional inputs
    rockCohesion: float   # Pa
    frictionAngle: float  # angle in radian
    speHandler: bool      # defaults to false

    # Instantiate the filter
    sg: SurfaceGeomechanics = SurfaceGeomechanics( inputMesh, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    sg.SetLoggerHandler( yourHandler )

    # [optional] Set rock cohesion and friction angle
    sg.SetRockCohesion( rockCohesion )
    sg.SetFrictionAngle( frictionAngle )

    # Do calculations
    sg.applyFilter()

    # Get output object
    output: vtkPolyData = sg.GetOutputMesh()

    # Get created attribute names
    newAttributeNames: set[str] = sg.GetNewAttributeNames()


.. Note::

    By default, conversion of attributes from local to XYZ basis is performed for the following list: { 'displacementJump' }.
    This list can be modified in different ways:

    - Addition of one or several additional attributes to the set by using the filter function `AddAttributesToConvert`.
    - Replace the list completely with the function `SetAttributesToConvert`.

    Note that the dimension of the attributes to convert must be equal or greater than 3.
"""
loggerTitle: str = "Surface Geomechanics"


class SurfaceGeomechanics:

    def __init__( self: Self, surfacicMesh: vtkPolyData, speHandler: bool = False ) -> None:
        """Vtk filter to compute geomechanical surfacic attributes.

        Input and Output objects are a vtkPolydata with surfaces
        objects with Normals and Tangential attributes.

        Args:
            surfacicMesh (vtkPolyData): The input surfacic mesh.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

        # Input surfacic mesh
        if not surfacicMesh.IsA( "vtkPolyData" ):
            self.logger.error( f"Input surface is expected to be a vtkPolyData, not a {type(surfacicMesh)}." )
        self.inputMesh: vtkPolyData = surfacicMesh
        # Identification of the input surface (logging purpose)
        self.name: Union[ str, None ] = None
        # Output surfacic mesh
        self.outputMesh: vtkPolyData
        # Default attributes to convert from local to XYZ
        self.convertAttributesOn: bool = True
        self.attributesToConvert: set[ str ] = {
            GeosMeshOutputsEnum.DISPLACEMENT_JUMP.attributeName,
        }

        # Attributes are either on points or on cells
        self.attributeOnPoints: bool = False
        # Rock cohesion (Pa)
        self.rockCohesion: float = DEFAULT_ROCK_COHESION
        # Friction angle (rad)
        self.frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD
        # New created attributes names
        self.newAttributeNames: set[ str ] = set()

    def SetLoggerHandler( self: Self, handler: Logger ) -> None:
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

    def SetSurfaceName( self: Self, name: str ) -> None:
        """Set a name for the input surface. For logging purpose only.

        Args:
            name (str): The identifier for the surface.
        """
        self.name = name

    def SetRockCohesion( self: Self, rockCohesion: float ) -> None:
        """Set rock cohesion value. Defaults to 0.0 Pa.

        Args:
            rockCohesion (float): The rock cohesion in Pascal.
        """
        self.rockCohesion = rockCohesion

    def SetFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set friction angle value in radians. Defaults to 10 / 180 * pi rad.

        Args:
            frictionAngle (float): The friction angle in radians.
        """
        self.frictionAngle = frictionAngle

    def ConvertAttributesOn( self: Self ) -> None:
        """Activate the conversion of attributes from local to XYZ basis."""
        self.convertAttributesOn = True

    def ConvertAttributesOff( self: Self ) -> None:
        """Deactivate the conversion of attributes from local to XYZ bais."""
        self.convertAttributesOn = False

    def GetConvertAttributes( self: Self ) -> bool:
        """If convertAttributesOn is True, the set of attributes will be converted from local to XYZ during filter application. Default is True.

        Returns:
            bool: Current state of the attributes conversion request.
        """
        return self.convertAttributesOn

    def GetAttributesToConvert( self: Self ) -> set[ str ]:
        """Get the set of attributes that will be converted from local to XYZ basis.

        Returns:
            set[ str ]: The set of attributes that should be converted.
        """
        return self.attributesToConvert

    def SetAttributesToConvert( self: Self, attributesToConvert: set[ str ] ) -> None:
        """Set the list of attributes that will be converted from local to XYZ basis.

        Args:
            attributesToConvert (set[str]): The set of attributes names that will be converted from local to XYZ basis
        """
        self.attributesToConvert = attributesToConvert
        if len( self.attributesToConvert ) != 0:
            self.ConvertAttributesOn()
        else:
            self.ConvertAttributesOff()
            self.logger.warning( "Empty set of attributes to convert." )

    def AddAttributesToConvert( self: Self, attributeName: Union[ list[ str ], set[ str ] ] ) -> None:
        """Add an attribute to the set of attributes to convert.

        Args:
            attributeName (Union[list[str],set[str]]): List of the attribute array names.
        """
        self.attributesToConvert.update( attributeName )
        self.ConvertAttributesOn()

    def GetNewAttributeNames( self: Self ) -> set[ str ]:
        """Get the set of new attribute names that were created.

        Returns:
            set[str]: The set of new attribute names.
        """
        return self.newAttributeNames

    def applyFilter( self: Self ) -> bool:
        """Compute Geomechanical properties on input surface.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        msg = f"Applying filter {self.logger.name}"
        if self.name is not None:
            msg += f" on surface : {self.name}."
        else:
            msg += "."

        self.logger.info( msg )

        self.outputMesh = vtkPolyData()
        self.outputMesh.ShallowCopy( self.inputMesh )

        # Conversion of attributes from Normal/Tangent basis to xyz basis
        if self.convertAttributesOn:
            self.logger.info( "Conversion of attributes from local to XYZ basis." )
            if not self.convertAttributesFromLocalToXYZBasis():
                self.logger.error( "Error while converting attributes from local to XYZ basis." )
                return False

        # Compute shear capacity utilization
        if not self.computeShearCapacityUtilization():
            self.logger.error( "Error while computing SCU." )
            return False

        self.logger.info( f"Filter {self.logger.name} successfully applied on surface {self.name}." )
        return True

    def convertAttributesFromLocalToXYZBasis( self: Self ) -> bool:
        """Convert attributes from local to XYZ basis.

        Returns:
            bool: True if calculation successfully ended or no attributes, False otherwise.
        """
        # Get the list of attributes to convert and filter
        attributesToConvert: set[ str ] = self.__filterAttributesToConvert()

        if len( attributesToConvert ) == 0:
            self.logger.warning( "No attribute to convert from local to XYZ basis were found." )
            return True

        # Do conversion from local to XYZ for each attribute
        for attrNameLocal in attributesToConvert:
            attrNameXYZ: str = f"{attrNameLocal}_{ComponentNameEnum.XYZ.name}"

            # Skip attribute if it is already in the object
            if isAttributeInObject( self.outputMesh, attrNameXYZ, self.attributeOnPoints ):
                continue

            if self.attributeOnPoints:
                self.logger.error(
                    "This filter can only convert cell attributes from local to XYZ basis, not point attributes." )
            localArray: npt.NDArray[ np.float64 ] = getArrayInObject( self.outputMesh, attrNameLocal,
                                                                      self.attributeOnPoints )

            arrayXYZ: npt.NDArray[ np.float64 ] = self.__computeXYZCoordinates( localArray )

            # Create converted attribute array in dataset
            if createAttribute( self.outputMesh,
                                arrayXYZ,
                                attrNameXYZ,
                                ComponentNameEnum.XYZ.value,
                                onPoints=self.attributeOnPoints,
                                logger=self.logger ):
                self.logger.info( f"Attribute {attrNameXYZ} added to the output mesh." )
                self.newAttributeNames.add( attrNameXYZ )

        return True

    def __filterAttributesToConvert( self: Self ) -> set[ str ]:
        """Filter the set of attribute names if they are vectorial and present.

        Returns:
             set[str]: Set of the attribute names.
        """
        attributesFiltered: set[ str ] = set()

        if len( self.attributesToConvert ) != 0:
            attributeSet: set[ str ] = getAttributeSet( self.outputMesh, False )
            for attrName in self.attributesToConvert:
                if attrName in attributeSet:
                    attr: vtkDataArray = self.outputMesh.GetCellData().GetArray( attrName )
                    if attr.GetNumberOfComponents() > 2:
                        attributesFiltered.add( attrName )
                    else:
                        self.logger.warning(
                            f"Attribute {attrName} filtered out. Dimension of the attribute must be equal or greater than 3."
                        )
                else:
                    self.logger.warning( f"Attribute {attrName} not in the input mesh." )

            if len( attributesFiltered ) == 0:
                self.logger.warning( "All attributes filtered out." )
                self.ConvertAttributesOff()

        return attributesFiltered

    # TODO: Adapt to handle point attributes.
    def __computeXYZCoordinates(
        self: Self,
        attrArray: npt.NDArray[ np.float64 ],
    ) -> npt.NDArray[ np.float64 ]:
        """Compute the XYZ coordinates of a vectorial attribute.

        Args:
            attrArray (npt.NDArray[np.float64]): vector of attribute values

        Returns:
            npt.NDArray[np.float64]: Vector of new coordinates of the attribute.
        """
        attrXYZ: npt.NDArray[ np.float64 ] = np.full_like( attrArray, np.nan )

        # Get all local basis vectors
        localBasis: npt.NDArray[ np.float64 ] = getLocalBasisVectors( self.outputMesh )

        for i, cellAttribute in enumerate( attrArray ):
            if len( cellAttribute ) not in ( 3, 6, 9 ):
                raise ValueError(
                    f"Inconsistent number of components for attribute. Expected 3, 6 or 9 but got { len( cellAttribute.shape ) }."
                )

            # Compute attribute XYZ components
            cellLocalBasis: npt.NDArray[ np.float64 ] = localBasis[ :, i, : ]
            attrXYZ[ i ] = convertAttributeFromLocalToXYZForOneCell( cellAttribute, cellLocalBasis )

        if not np.any( np.isfinite( attrXYZ ) ):
            self.logger.error( "Attribute new coordinate calculation failed." )

        return attrXYZ

    def computeShearCapacityUtilization( self: Self ) -> bool:
        """Compute the shear capacity utilization (SCU) on surface.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        SCUAttributeName: str = PostProcessingOutputsEnum.SCU.attributeName

        if not isAttributeInObject( self.outputMesh, SCUAttributeName, self.attributeOnPoints ):
            # Get the traction to compute the SCU
            tractionAttributeName: str = GeosMeshOutputsEnum.TRACTION.attributeName
            traction: npt.NDArray[ np.float64 ] = getArrayInObject( self.outputMesh, tractionAttributeName,
                                                                    self.attributeOnPoints )

            # Computation of the shear capacity utilization (SCU)
            # TODO: better handling of errors in shearCapacityUtilization
            try:
                scuAttribute: npt.NDArray[ np.float64 ] = fcts.shearCapacityUtilization(
                    traction, self.rockCohesion, self.frictionAngle )
            except AssertionError:
                self.logger.error( f"Failed to compute {SCUAttributeName}." )
                return False

            # Create attribute
            if not createAttribute(
                    self.outputMesh, scuAttribute, SCUAttributeName, (), self.attributeOnPoints, logger=self.logger ):
                self.logger.error( f"Failed to create attribute {SCUAttributeName}." )
                return False
            else:
                self.logger.info( "SCU computed and added to the output mesh." )
                self.newAttributeNames.add( SCUAttributeName )

        return True

    def GetOutputMesh( self: Self ) -> vtkPolyData:
        """Get the output mesh with computed attributes.

        Returns:
            vtkPolyData: The surfacic output mesh.
        """
        return self.outputMesh
