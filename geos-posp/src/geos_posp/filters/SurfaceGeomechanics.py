# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import geos.geomechanics.processing.geomechanicsCalculatorFunctions as fcts
import geos.utils.geometryFunctions as geom
import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from geos.utils.algebraFunctions import (
    getAttributeMatrixFromVector,
    getAttributeVectorFromMatrix,
)
from geos.utils.GeosOutputsConstants import (
    ComponentNameEnum,
    GeosMeshOutputsEnum,
    PostProcessingOutputsEnum,
    getAttributeToConvertFromLocalToXYZ,
)
from geos.utils.Logger import Logger, getLogger
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_ROCK_COHESION,
)
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkDoubleArray,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPolyData, )

from geos.mesh.utils.arrayModifiers import createAttribute
from geos.mesh.utils.arrayHelpers import (
    getArrayInObject,
    getAttributeSet,
    isAttributeInObject,
)

__doc__ = """
SurfaceGeomechanics module is a vtk filter that allows to compute Geomechanical
properties on surfaces.

Filter input and output types are vtkPolyData.

To use the filter:

.. code-block:: python

    from filters.SurfaceGeomechanics import SurfaceGeomechanics

    # filter inputs
    logger :Logger
    input :vtkPolyData
    rockCohesion :float
    frictionAngle :float # angle in radian

    # instanciate the filter
    surfaceGeomechanicsFilter :SurfaceGeomechanics = SurfaceGeomechanics()
    # set the logger
    surfaceGeomechanicsFilter.SetLogger(logger)
    # set input data object
    surfaceGeomechanicsFilter.SetInputDataObject(input)
    # set rock cohesion anf friction angle
    surfaceGeomechanicsFilter.SetRockCohesion(rockCohesion)
    surfaceGeomechanicsFilter.SetFrictionAngle(frictionAngle)
    # do calculations
    surfaceGeomechanicsFilter.Update()
    # get output object
    output :vtkPolyData = surfaceGeomechanicsFilter.GetOutputDataObject(0)
    # get created attribute names
    newAttributeNames :set[str] = surfaceGeomechanicsFilter.GetNewAttributeNames()
"""


class SurfaceGeomechanics( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to compute geomechanical surfacic attributes.

        Input and Output objects are a vtkMultiBlockDataSet containing surface
        objects with Normals and Tangential attributes.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkPolyData" )  # type: ignore[no-untyped-call]

        # output surface mesh
        self.m_output: vtkPolyData
        # attributes are either on points or on cells
        self.m_attributeOnPoints: bool = False
        # rock cohesion (Pa)
        self.m_rockCohesion: float = DEFAULT_ROCK_COHESION
        # friction angle (rad)
        self.m_frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD
        # new created attributes names
        self.m_newAttributeNames: set[ str ] = set()

        # logger
        self.m_logger: Logger = getLogger( "Surface Geomechanics Filter" )

    def SetRockCohesion( self: Self, rockCohesion: float ) -> None:
        """Set rock cohesion value.

        Args:
            rockCohesion (float): rock cohesion (Pa)
        """
        self.m_rockCohesion = rockCohesion

    def SetFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set friction angle value.

        Args:
            frictionAngle (float): friction angle (rad)
        """
        self.m_frictionAngle = frictionAngle

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set the logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    def GetNewAttributeNames( self: Self ) -> set[ str ]:
        """Get the set of new attribute names that were created.

        Returns:
            set[str]: set of new attribute names
        """
        return self.m_newAttributeNames

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkPolyData" )
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

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
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
            input = vtkPolyData.GetData( inInfoVec[ 0 ] )
            self.m_output = self.GetOutputData( outInfoVec, 0 )  # type: ignore[no-untyped-call]

            assert input is not None, "Input object is null."
            assert self.m_output is not None, "Output pipeline is null."

            self.m_output.ShallowCopy( input )
            # conversion of vectorial attributes from Normal/Tangent basis to xyz basis
            assert ( self.convertLocalToXYZBasisAttributes() ), "Error while converting Local to XYZ basis attributes"
            # compute shear capacity utilization
            assert self.computeShearCapacityUtilization(), "Error while computing SCU."
            self.Modified()
        except AssertionError as e:
            mess: str = "Surface geomechanics attributes calculation failed due to:"
            self.m_logger.error( mess )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess1: str = "Surface geomechanics attributes calculation failed due to:"
            self.m_logger.critical( mess1 )
            self.m_logger.critical( e, exc_info=True )
            return 0
        mess2: str = "Surface geomechanics attributes were successfully computed."
        self.m_logger.info( mess2 )
        return 1

    def convertLocalToXYZBasisAttributes( self: Self ) -> bool:
        """Convert vectorial property coordinates from Local to canonic basis.

        Returns:
            bool: True if calculation successfully ended, False otherwise
        """
        # look for the list of attributes to convert
        attributesToConvert: set[ str ] = self.getAttributesToConvertFromLocalToXYZ()
        if len( attributesToConvert ) == 0:
            self.m_logger.info( "No attribute to convert from local to XYZ basis were found." )
            return False

        # get local coordinate vectors
        normalTangentVectors: npt.NDArray[ np.float64 ] = self.getNormalTangentsVectors()
        # do conversion for each attribute
        for attributName in attributesToConvert:
            # skip attribute if it is already in the object
            newAttrName: str = attributName + "_" + ComponentNameEnum.XYZ.name
            if isAttributeInObject( self.m_output, newAttrName, False ):
                continue

            attr: vtkDoubleArray = self.m_output.GetCellData().GetArray( attributName )
            assert attr is not None, "Attribute {attributName} is undefined."
            assert attr.GetNumberOfComponents() > 2, ( "Dimension of the attribute " +
                                                       " must be equal or grater than 3." )

            attrArray: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( attr )  # type: ignore[no-untyped-call]
            newAttrArray: npt.NDArray[ np.float64 ] = self.computeNewCoordinates( attrArray, normalTangentVectors,
                                                                                  True )

            # create attribute
            createAttribute(
                self.m_output,
                newAttrArray,
                newAttrName,
                ComponentNameEnum.XYZ.value,
                False,
            )
            self.m_newAttributeNames.add( newAttrName )
        return True

    def convertXYZToLocalBasisAttributes( self: Self ) -> bool:
        """Convert vectorial property coordinates from canonic to local basis.

        Returns:
            bool: True if calculation successfully ended, False otherwise
        """
        # look for the list of attributes to convert
        # empty but to update if needed in the future
        attributesToConvert: set[ str ] = set()
        if len( attributesToConvert ) == 0:
            self.m_logger.info( "No attribute to convert from local to " + "canonic basis were found." )
            return False

        # get local coordinate vectors
        normalTangentVectors: npt.NDArray[ np.float64 ] = self.getNormalTangentsVectors()
        for attributName in attributesToConvert:
            # skip attribute if it is already in the object
            newAttrName: str = ( attributName + "_" + ComponentNameEnum.NORMAL_TANGENTS.name )
            if isAttributeInObject( self.m_output, newAttrName, False ):
                continue
            attr: vtkDoubleArray = self.m_output.GetCellData().GetArray( attributName )
            assert attr is not None, "Attribute {attributName} is undefined."
            assert attr.GetNumberOfComponents() > 2, ( "Dimension of the attribute " +
                                                       " must be equal or grater than 3." )

            attrArray: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( attr )  # type: ignore[no-untyped-call]
            newAttrArray: npt.NDArray[ np.float64 ] = self.computeNewCoordinates( attrArray, normalTangentVectors,
                                                                                  False )

            # create attribute
            createAttribute(
                self.m_output,
                newAttrArray,
                newAttrName,
                ComponentNameEnum.NORMAL_TANGENTS.value,
                False,
            )
            self.m_newAttributeNames.add( newAttrName )
        return True

    def getAttributesToConvertFromLocalToXYZ( self: Self ) -> set[ str ]:
        """Get the list of attributes to convert from local to XYZ basis.

        Returns:
             set[str]: Set of the attribute names.
        """
        return self.filterAttributesToConvert( getAttributeToConvertFromLocalToXYZ() )

    def filterAttributesToConvert( self: Self, attributesToFilter0: set[ str ] ) -> set[ str ]:
        """Filter the set of attribute names if they are vectorial and present.

        Args:
            attributesToFilter0 (set[str]): set of attribute names to filter.

        Returns:
             set[str]: Set of the attribute names.
        """
        attributesFiltered: set[ str ] = set()
        attributeSet: set[ str ] = getAttributeSet( self.m_output, False )
        for attributName in attributesToFilter0:
            if attributName in attributeSet:
                attr: vtkDataArray = self.m_output.GetCellData().GetArray( attributName )
                if attr.GetNumberOfComponents() > 2:
                    attributesFiltered.add( attributName )
        return attributesFiltered

    def computeNewCoordinates(
        self: Self,
        attrArray: npt.NDArray[ np.float64 ],
        normalTangentVectors: npt.NDArray[ np.float64 ],
        fromLocalToYXZ: bool,
    ) -> npt.NDArray[ np.float64 ]:
        """Compute the coordinates of a vectorial attribute.

        Args:
            attrArray (npt.NDArray[np.float64]): vector of attribute values
            normalTangentVectors (npt.NDArray[np.float64]): 3xNx3 local vector
                coordinates
            fromLocalToYXZ (bool): if True, conversion is done from local to XYZ
                basis, otherwise conversion is done from XZY to Local basis.

        Returns:
            npt.NDArray[np.float64]: Vector of new coordinates of the attribute.
        """
        attrArrayNew = np.full_like( attrArray, np.nan )
        # for each cell
        for i in range( attrArray.shape[ 0 ] ):
            # get the change of basis matrix
            localBasis: npt.NDArray[ np.float64 ] = normalTangentVectors[ :, i, : ]
            changeOfBasisMatrix = self.computeChangeOfBasisMatrix( localBasis, fromLocalToYXZ )
            if attrArray.shape[ 1 ] == 3:
                attrArrayNew[ i ] = self.computeNewCoordinatesVector3( attrArray[ i ], changeOfBasisMatrix )
            else:
                attrArrayNew[ i ] = self.computeNewCoordinatesVector6( attrArray[ i ], changeOfBasisMatrix )

        assert np.any( np.isfinite( attrArrayNew ) ), "Attribute new coordinate calculation failed."
        return attrArrayNew

    def computeNewCoordinatesVector3(
        self: Self,
        vector: npt.NDArray[ np.float64 ],
        changeOfBasisMatrix: npt.NDArray[ np.float64 ],
    ) -> npt.NDArray[ np.float64 ]:
        """Compute attribute new coordinates of vector of size 3.

        Args:
            vector (npt.NDArray[np.float64]): input coordinates.
            changeOfBasisMatrix (npt.NDArray[np.float64]): change of basis matrix

        Returns:
            npt.NDArray[np.float64]: new coordinates
        """
        return geom.computeCoordinatesInNewBasis( vector, changeOfBasisMatrix )

    def computeNewCoordinatesVector6(
        self: Self,
        vector: npt.NDArray[ np.float64 ],
        changeOfBasisMatrix: npt.NDArray[ np.float64 ],
    ) -> npt.NDArray[ np.float64 ]:
        """Compute attribute new coordinates of vector of size > 3.

        Args:
            vector (npt.NDArray[np.float64]): input coordinates.
            changeOfBasisMatrix (npt.NDArray[np.float64]): change of basis matrix

        Returns:
            npt.NDArray[np.float64]: new coordinates
        """
        attributeMatrix: npt.NDArray[ np.float64 ] = getAttributeMatrixFromVector( vector )
        attributeMatrixNew: npt.NDArray[ np.float64 ] = np.full_like( attributeMatrix, np.nan )
        # for each column of the matrix
        for j in range( attributeMatrix.shape[ 1 ] ):
            attributeMatrixNew[ :, j ] = geom.computeCoordinatesInNewBasis( attributeMatrix[ :, j ],
                                                                            changeOfBasisMatrix )
        return getAttributeVectorFromMatrix( attributeMatrixNew, vector.size )

    def computeChangeOfBasisMatrix( self: Self, localBasis: npt.NDArray[ np.float64 ],
                                    fromLocalToYXZ: bool ) -> npt.NDArray[ np.float64 ]:
        """Compute the change of basis matrix according to local coordinates.

        Args:
            localBasis (npt.NDArray[np.float64]): local coordinate vectors.
            fromLocalToYXZ (bool): if True, change of basis matrix is from local
                to XYZ bases, otherwise it is from XYZ to local bases.

        Returns:
            npt.NDArray[np.float64]: change of basis matrix.
        """
        P: npt.NDArray[ np.float64 ] = np.transpose( localBasis )
        if fromLocalToYXZ:
            return P
        # inverse the change of basis matrix
        return np.linalg.inv( P ).astype( np.float64 )

    def getNormalTangentsVectors( self: Self ) -> npt.NDArray[ np.float64 ]:
        """Compute the change of basis matrix from Local to XYZ bases.

        Returns:
             npt.NDArray[np.float64]: Nx3 matrix of local vector coordinates.
        """
        # get normal and first tangent components
        normals: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy(
            self.m_output.GetCellData().GetNormals() )  # type: ignore[no-untyped-call]
        assert normals is not None, "Normal attribute was not found."
        tangents1: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy(
            self.m_output.GetCellData().GetTangents() )  # type: ignore[no-untyped-call]
        assert tangents1 is not None, "Tangents attribute was not found."

        # compute second tangential component
        tangents2: npt.NDArray[ np.float64 ] = np.cross( normals, tangents1, axis=1 ).astype( np.float64 )
        assert tangents2 is not None, "Local basis third axis was not computed."

        # put vectors as columns
        return np.array( ( normals, tangents1, tangents2 ) )

    def computeShearCapacityUtilization( self: Self ) -> bool:
        """Compute the shear capacity utilization on surface.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        try:
            SCUAttributeName: str = PostProcessingOutputsEnum.SCU.attributeName
            if not isAttributeInObject( self.m_output, SCUAttributeName, self.m_attributeOnPoints ):
                tractionAttributeName: str = GeosMeshOutputsEnum.TRACTION.attributeName
                traction: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_output, tractionAttributeName,
                                                                        self.m_attributeOnPoints )
                assert traction is not None, ( f"{tractionAttributeName}" + " attribute is undefined." )

                scuAttribute: npt.NDArray[ np.float64 ] = fcts.shearCapacityUtilization(
                    traction, self.m_rockCohesion, self.m_frictionAngle )
                createAttribute(
                    self.m_output,
                    scuAttribute,
                    SCUAttributeName,
                    (),
                    self.m_attributeOnPoints,
                )
                self.m_newAttributeNames.add( SCUAttributeName )

        except AssertionError as e:
            self.m_logger.error( "Shear Capacity Utilization was not computed due to:" )
            self.m_logger.error( str( e ) )
            return False
        return True
