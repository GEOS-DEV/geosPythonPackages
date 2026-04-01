# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, Any

import numpy as np
import numpy.typing as npt

from vtkmodules.util.numpy_support import vtk_to_numpy, get_vtk_to_numpy_typemap
from vtkmodules.vtkCommonCore import ( vtkDataArray, VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG,
                                       VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG, VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT,
                                       VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE, VTK_FLOAT, VTK_DOUBLE )
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPointData, vtkCellData

from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten
from geos.mesh.utils.arrayHelpers import isAttributeInObject
from geos.mesh.utils import arrayModifiers
from geos.utils.pieceEnum import Piece

# Information :
# https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/numpy_support.py
# https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/vtkConstants.py
#     vtk array type       int   numpy type
# VTK_CHAR               = 2  = np.int8
# VTK_SIGNED_CHAR        = 15 = np.int8
# VTK_SHORT              = 4  = np.int16
# VTK_INT                = 6  = np.int32
# VTK_BIT                = 1  = np.uint8
# VTK_UNSIGNED_CHAR      = 3  = np.uint8
# VTK_UNSIGNED_SHORT     = 5  = np.uint16
# VTK_UNSIGNED_INT       = 7  = np.uint32
# VTK_UNSIGNED_LONG_LONG = 17 = np.uint64
# VTK_LONG               = 8  = LONG_TYPE_CODE ( int32 | int64 )
# VTK_UNSIGNED_LONG      = 9  = ULONG_TYPE_CODE ( uint32 | uint64 )
# VTK_FLOAT              = 10 = np.float32
# VTK_DOUBLE             = 11 = np.float64
# VTK_ID_TYPE            = 12 = ID_TYPE_CODE ( int32 | int64 )

#     vtk array type       int  IdType  numpy type
# VTK_LONG_LONG          = 16 = 2 = np.int64


@pytest.mark.parametrize(
    "idBlock, attributeName, nbComponentsTest, componentNamesTest, piece, listValues, listValuesTest, vtkDataTypeTest",
    [
        # Filled attributes with the default value
        ## Attributes with one component on point and on cell
        ( 4, "mass", 1, (), Piece.CELLS, None, [ np.float64( np.nan ) ], VTK_DOUBLE ),
        ( 4, "mass", 1, (), Piece.POINTS, None, [ np.float64( np.nan ) ], VTK_DOUBLE ),
        ## Attributes with multiple components on point and on cell
        ( 4, "permeability", 3,
          ( None, None, None ), Piece.CELLS, None, [ np.float64(
              np.nan ), np.float64( np.nan ), np.float64( np.nan ) ], VTK_DOUBLE ),
        ( 4, "totalDisplacement", 3, ( None, None, None ), Piece.POINTS, None,
          [ np.float64( np.nan ), np.float64( np.nan ),
            np.float64( np.nan ) ], VTK_DOUBLE ),
        ## Attributes with other types
        ( 4, "ghostRank", 1, (), Piece.POINTS, None, [ np.int32( -1 ) ], VTK_INT ),
        ( 4, "localToGlobalMap", 1, (), Piece.POINTS, None, [ np.int64( -1 ) ], VTK_LONG_LONG ),
        # Filled attributes with a specified value
        ( 4, "ghostRank", 1, (), Piece.POINTS, [ np.int32( 4 ) ], [ np.int32( 4 ) ], VTK_INT ),
        ( 4, "mass", 1, (), Piece.POINTS, [ np.float64( 4 ) ], [ np.float64( 4 ) ], VTK_DOUBLE ),
        ( 4, "localToGlobalMap", 1, (), Piece.POINTS, [ np.int64( 4 ) ], [ np.int64( 4 ) ], VTK_LONG_LONG ),
        ( 4, "totalDisplacement", 3, ( None, None, None ), Piece.POINTS, [
            np.float64( 4 ), np.float64( 4 ), np.float64( 4 )
        ], [ np.float64( 4 ), np.float64( 4 ), np.float64( 4 ) ], VTK_DOUBLE ),
        # Filled attributes with a specified value of wrong type
        ( 4, "ghostRank", 1, (), Piece.POINTS, [ 4 ], [ np.int32( 4 ) ], VTK_INT ),
        ( 4, "ghostRank", 1, (), Piece.POINTS, [ 4. ], [ np.int32( 4 ) ], VTK_INT ),
        ( 4, "ghostRank", 1, (), Piece.POINTS, [ np.int64( 4 ) ], [ np.int32( 4 ) ], VTK_INT ),
        ( 4, "ghostRank", 1, (), Piece.POINTS, [ np.float32( 4 ) ], [ np.int32( 4 ) ], VTK_INT ),
        ( 4, "ghostRank", 1, (), Piece.POINTS, [ np.float64( 4 ) ], [ np.int32( 4 ) ], VTK_INT ),
    ] )
def test_fillPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    idBlock: int,
    attributeName: str,
    nbComponentsTest: int,
    componentNamesTest: tuple[ str, ...],
    piece: Piece,
    listValues: Union[ list[ Any ], None ],
    listValuesTest: list[ Any ],
    vtkDataTypeTest: int,
) -> None:
    """Test filling a partial attribute from a multiblock with values."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "extractAndMergeVolumeWell1" )
    # Fill the attribute in the multiBlockDataSet.
    arrayModifiers.fillPartialAttributes( multiBlockDataSetTest, attributeName, piece=piece, listValues=listValues )

    # Get the dataSet where the attribute has been filled.
    dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( idBlock ) )

    # Get the filled attribute.
    data: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if piece == Piece.POINTS:
        nbElements = dataSet.GetNumberOfPoints()
        data = dataSet.GetPointData()
    else:
        nbElements = dataSet.GetNumberOfCells()
        data = dataSet.GetCellData()
    attributeFilled: vtkDataArray = data.GetArray( attributeName )

    # Test the number of components and their names if multiple.
    nbComponentsFilled: int = attributeFilled.GetNumberOfComponents()
    assert nbComponentsFilled == nbComponentsTest
    if nbComponentsTest > 1:
        componentNamesFilled: tuple[ str, ...] = tuple(
            attributeFilled.GetComponentName( i ) for i in range( nbComponentsFilled ) )
        assert componentNamesFilled == componentNamesTest

    # Test values and their types.
    ## Create the constant array test from the value.
    npArrayTest: npt.NDArray[ Any ]
    if nbComponentsTest > 1:
        npArrayTest = np.array( [ listValuesTest for _ in range( nbElements ) ] )
    else:
        npArrayTest = np.array( [ listValuesTest[ 0 ] for _ in range( nbElements ) ] )

    npArrayFilled: npt.NDArray[ Any ] = vtk_to_numpy( attributeFilled )
    assert npArrayFilled.dtype == npArrayTest.dtype
    if listValues is None and vtkDataTypeTest in ( VTK_FLOAT, VTK_DOUBLE ):
        assert np.isnan( npArrayFilled ).all()
    else:
        assert ( npArrayFilled == npArrayTest ).all()

    vtkDataTypeFilled: int = attributeFilled.GetDataType()
    assert vtkDataTypeFilled == vtkDataTypeTest


def test_fillPartialAttributesTypeError( dataSetTest: vtkDataSet, ) -> None:
    """Test the raises TypeError for the function fillPartialAttributes with a wrong mesh type."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    with pytest.raises( TypeError ):
        arrayModifiers.fillPartialAttributes( mesh, "mass" )


def test_fillPartialAttributesValueError( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test the raises ValueError for the function fillPartialAttributes with too many values for the attribute."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "extractAndMergeVolumeWell1" )
    with pytest.raises( ValueError ):
        arrayModifiers.fillPartialAttributes( mesh, "mass", listValues=[ 42, 42 ] )


@pytest.mark.parametrize(
    "attributeName",
    [
        ( "newAttribute" ),  # The attribute is not in the mesh
        ( "elementCenter" ),  # The attribute is already global
    ] )
def test_fillPartialAttributesAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
) -> None:
    """Test the raises AttributeError for the function fillPartialAttributes."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "extractAndMergeVolumeWell1" )
    with pytest.raises( AttributeError ):
        arrayModifiers.fillPartialAttributes( mesh, attributeName )


def test_FillAllPartialAttributes( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test to fill all the partial attributes of a vtkMultiBlockDataSet."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "extractAndMergeVolumeWell1" )
    arrayModifiers.fillAllPartialAttributes( multiBlockDataSetTest )

    dataSet1: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( 2 ) )
    dataSet2: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( 4 ) )
    assert dataSet1.GetCellData().GetNumberOfArrays() == dataSet2.GetCellData().GetNumberOfArrays()
    assert dataSet1.GetPointData().GetNumberOfArrays() == dataSet2.GetPointData().GetNumberOfArrays()


def test_fillAllPartialAttributesTypeError( dataSetTest: vtkDataSet, ) -> None:
    """Test the raises TypeError for the function fillAllPartialAttributes with a wrong mesh type."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    with pytest.raises( TypeError ):
        arrayModifiers.fillAllPartialAttributes( mesh )


@pytest.mark.parametrize( "attributeName, dataType, expectedDatatypeArray", [
    ( "test_double", VTK_DOUBLE, "vtkDoubleArray" ),
    ( "test_float", VTK_FLOAT, "vtkFloatArray" ),
    ( "test_int", VTK_INT, "vtkIntArray" ),
    ( "test_unsigned_int", VTK_UNSIGNED_INT, "vtkUnsignedIntArray" ),
    ( "test_char", VTK_CHAR, "vtkCharArray" ),
] )
def test_createEmptyAttribute(
    attributeName: str,
    dataType: int,
    expectedDatatypeArray: vtkDataArray,
) -> None:
    """Test empty attribute creation."""
    componentNames: tuple[ str, str, str ] = ( "d1", "d2", "d3" )
    newAttr: vtkDataArray = arrayModifiers.createEmptyAttribute( attributeName, componentNames, dataType )

    assert newAttr.GetNumberOfComponents() == len( componentNames )
    for ax in range( 3 ):
        assert newAttr.GetComponentName( ax ) == componentNames[ ax ]
    assert newAttr.IsA( str( expectedDatatypeArray ) )


def test_createEmptyAttributeValueError() -> None:
    """Test the raises ValueError for the function createEmptyAttribute with a wrong vtkDataType."""
    with pytest.raises( ValueError ):
        arrayModifiers.createEmptyAttribute( "newAttribute", (), 64 )


@pytest.mark.parametrize(
    "meshName, listValues, componentNames, componentNamesTest, piece, vtkDataType, vtkDataTypeTest, attributeName",
    [
        # Test mesh types.
        ( "extractAndMergeVolume", [ np.float32( 42 ) ], (), (), Piece.CELLS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "2Ranks", [ np.float32( 42 ) ], (), (), Piece.CELLS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "2Ranks", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test with an attribute name that exist on the opposite piece.
        ( "extractAndMergeVolume", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "elementVolume" ),
        ( "geosOutput2Ranks", [ np.float32( 42 ) ], (),
          (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "deltaPressure" ),  # Partial
        ( "2Ranks", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "deltaPressure" ),  # Global
        # Test the number of components and their names.
        ( "extractAndMergeVolume", [ np.float32( 42 ) ], ( "X" ),
          (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y" ),
          ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.float32( 42 ), np.float32( 42 ) ], (),
          ( "Component0", "Component1" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test the type of the values.
        ## With numpy scalar type.
        ( "extractAndMergeVolume", [ np.int8( 42 ) ], (), (), Piece.POINTS, None, VTK_SIGNED_CHAR, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.int8( 42 ) ], (),
          (), Piece.POINTS, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.int16( 42 ) ], (), (), Piece.POINTS, None, VTK_SHORT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.int16( 42 ) ], (), (), Piece.POINTS, VTK_SHORT, VTK_SHORT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.int32( 42 ) ], (), (), Piece.POINTS, None, VTK_INT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.int32( 42 ) ], (), (), Piece.POINTS, VTK_INT, VTK_INT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.int64( 42 ) ], (), (), Piece.POINTS, None, VTK_LONG_LONG, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.int64( 42 ) ], (),
          (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint8( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint8( 42 ) ], (),
          (), Piece.POINTS, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint16( 42 ) ], (),
          (), Piece.POINTS, None, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint16( 42 ) ], (),
          (), Piece.POINTS, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint32( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_INT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint32( 42 ) ], (),
          (), Piece.POINTS, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint64( 42 ) ], (),
          (), Piece.POINTS, None, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.uint64( 42 ) ], (),
          (), Piece.POINTS, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.float32( 42 ) ], (), (), Piece.POINTS, None, VTK_FLOAT, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.float64( 42 ) ], (), (), Piece.POINTS, None, VTK_DOUBLE, "newAttribute" ),
        ( "extractAndMergeVolume", [ np.float64( 42 ) ], (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
        ## With python scalar type.
        ( "extractAndMergeVolume", [ 42 ], (), (), Piece.POINTS, None, VTK_LONG_LONG, "newAttribute" ),
        ( "extractAndMergeVolume", [ 42 ], (), (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( "extractAndMergeVolume", [ 42. ], (), (), Piece.POINTS, None, VTK_DOUBLE, "newAttribute" ),
        ( "extractAndMergeVolume", [ 42. ], (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
    ] )
def test_createConstantAttribute(
    dataSetTest: Any,
    meshName: str,
    listValues: list[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    piece: Piece,
    vtkDataType: Union[ int, Any ],
    vtkDataTypeTest: int,
    attributeName: str,
) -> None:
    """Test constant attribute creation."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )

    # Create the new constant attribute in the mesh.
    arrayModifiers.createConstantAttribute( mesh, listValues, attributeName, componentNames, piece, vtkDataType )

    listDataSet: list[ vtkDataSet ] = []
    if isinstance( mesh, vtkDataSet ):
        listDataSet.append( mesh )
    else:
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for blockIndex in elementaryBlockIndexes:
            listDataSet.append( vtkDataSet.SafeDownCast( mesh.GetDataSet( blockIndex ) ) )

    for dataSet in listDataSet:
        # Get the created attribute.
        data: Union[ vtkPointData, vtkCellData ]
        nbElements: int
        if piece == Piece.POINTS:
            data = dataSet.GetPointData()
            nbElements = dataSet.GetNumberOfPoints()
        else:
            data = dataSet.GetCellData()
            nbElements = dataSet.GetNumberOfCells()
        attributeCreated: vtkDataArray = data.GetArray( attributeName )

        # Test the number of components and their names if multiple.
        nbComponentsTest: int = len( listValues )
        nbComponentsCreated: int = attributeCreated.GetNumberOfComponents()
        assert nbComponentsCreated == nbComponentsTest
        if nbComponentsTest > 1:
            componentNamesCreated: tuple[ str, ...] = tuple(
                attributeCreated.GetComponentName( i ) for i in range( nbComponentsCreated ) )
            assert componentNamesCreated, componentNamesTest

        # Test values and their types.
        ## Create the constant array test from values in the list values.
        npArrayTest: npt.NDArray[ Any ]
        if len( listValues ) > 1:
            npArrayTest = np.array( [ listValues for _ in range( nbElements ) ] )
        else:
            npArrayTest = np.array( [ listValues[ 0 ] for _ in range( nbElements ) ] )

        npArrayCreated: npt.NDArray[ Any ] = vtk_to_numpy( attributeCreated )
        assert npArrayCreated.dtype == npArrayTest.dtype
        assert ( npArrayCreated == npArrayTest ).all()

        vtkDataTypeCreated: int = attributeCreated.GetDataType()
        assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize(
    "meshName, listValues, vtkDataType",
    [
        ( "extractAndMergeVolume", [ np.int32( 42 ), np.int64( 42 )
                                    ], VTK_DOUBLE ),  # All the values in the listValues are not the same
        ( "extractAndMergeVolume", [ np.int32( 42 )
                                    ], VTK_DOUBLE ),  # The type of the value is not coherent with the vtkDataType
        ( "other", [ np.int64( 42 ) ], VTK_DOUBLE ),  # The type of the mesh is wrong
    ] )
def test_createConstantAttributeRaiseTypeError(
    dataSetTest: vtkDataSet,
    meshName: str,
    listValues: list[ Any ],
    vtkDataType: int,
) -> None:
    """Test the raises TypeError for the function createConstantAttribute."""
    mesh: vtkCellData | vtkDataSet = vtkCellData() if meshName == "other" else dataSetTest( meshName )
    with pytest.raises( TypeError ):
        arrayModifiers.createConstantAttribute( mesh, listValues, "newAttribute", vtkDataType=vtkDataType )


def test_createConstantAttributeRaiseValueErrorVTKDataType( dataSetTest: vtkDataSet, ) -> None:
    """Test the raises ValueError for the function createConstantAttribute with wrong values for the vtk data type."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    with pytest.raises( ValueError ):
        arrayModifiers.createConstantAttribute( mesh, [ np.int32( 42 ) ], "newAttribute", vtkDataType=64 )


def test_createConstantAttributeRaiseValueErrorPiece( dataSetTest: vtkDataSet, ) -> None:
    """Test the raises ValueError for the function createConstantAttribute with wrong values for the piece."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    with pytest.raises( ValueError ):
        arrayModifiers.createConstantAttribute( mesh, [ np.int32( 42 ) ], "newAttribute", piece=Piece.BOTH )


@pytest.mark.parametrize(
    "meshName, attributeName",
    [
        ( "geosOutput2Ranks", "mass" ),  # Partial
        ( "2Ranks", "mass" ),  # Global
        ( "extractAndMergeVolume", "mass" ),
    ] )
def test_createConstantAttributeRaiseAttributeError(
    dataSetTest: Any,
    meshName: str,
    attributeName: str,
) -> None:
    """Test the raises ValueError for the function createConstantAttribute with a wrong AttributeName."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    with pytest.raises( AttributeError ):
        arrayModifiers.createConstantAttribute( mesh, [ np.int32( 42 ) ], attributeName )


@pytest.mark.parametrize(
    "componentNames, componentNamesTest, piece, vtkDataType, vtkDataTypeTest, valueType, attributeName",
    [
        # Test attribute names.
        ## Test with a new attributeName on cells and on points.
        ( (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( (), (), Piece.CELLS, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ## Test with an attributeName already existing on opposite piece.
        ( (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "float64", "averageStrain" ),
        ( (), (), Piece.CELLS, VTK_DOUBLE, VTK_DOUBLE, "float64", "totalDisplacement" ),
        # Test the number of components and their names.
        ( ( "X" ), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( ( "X", "Y" ), ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( ( "X", "Y", "Z" ), ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( (), ( "Component0", "Component1" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        # Test the type of the values.
        ## With numpy scalar type.
        ( (), (), Piece.POINTS, None, VTK_SIGNED_CHAR, "int8", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "int8", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_SHORT, "int16", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_SHORT, VTK_SHORT, "int16", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_INT, "int32", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_INT, VTK_INT, "int32", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_LONG_LONG, "int64", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "int64", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_UNSIGNED_CHAR, "uint8", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "uint8", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_UNSIGNED_SHORT, "uint16", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "uint16", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_UNSIGNED_INT, "uint32", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "uint32", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_UNSIGNED_LONG_LONG, "uint64", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "uint64", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_FLOAT, "float32", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_DOUBLE, "float64", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "float64", "newAttribute" ),
        ## With python scalar type.
        ( (), (), Piece.POINTS, None, VTK_LONG_LONG, "int", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "int", "newAttribute" ),
        ( (), (), Piece.POINTS, None, VTK_DOUBLE, "float", "newAttribute" ),
        ( (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "float", "newAttribute" ),
    ] )
def test_createAttribute(
    dataSetTest: vtkDataSet,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    piece: Piece,
    vtkDataType: int,
    vtkDataTypeTest: int,
    valueType: str,
    attributeName: str,
) -> None:
    """Test creation of dataset in dataset from given array."""
    dataSet: vtkDataSet = dataSetTest( "extractAndMergeVolume" )

    # Get a array with random values of a given type.
    nbElements: int = dataSet.GetNumberOfPoints() if piece == Piece.POINTS else dataSet.GetNumberOfCells()
    nbComponentsTest: int = 1 if len( componentNamesTest ) == 0 else len( componentNamesTest )
    npArrayTest: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( nbComponentsTest, nbElements, valueType )

    # Create the new attribute in the dataSet.
    arrayModifiers.createAttribute( dataSet, npArrayTest, attributeName, componentNames, piece, vtkDataType )

    # Get the created attribute.
    data: Union[ vtkPointData, vtkCellData ]
    data = dataSet.GetPointData() if piece == Piece.POINTS else dataSet.GetCellData()
    attributeCreated: vtkDataArray = data.GetArray( attributeName )

    # Test the number of components and their names if multiple.
    nbComponentsCreated: int = attributeCreated.GetNumberOfComponents()
    assert nbComponentsCreated == nbComponentsTest
    if nbComponentsTest > 1:
        componentsNamesCreated: tuple[ str, ...] = tuple(
            attributeCreated.GetComponentName( i ) for i in range( nbComponentsCreated ) )
        assert componentsNamesCreated == componentNamesTest

    # Test values and their types.
    npArrayCreated: npt.NDArray[ Any ] = vtk_to_numpy( attributeCreated )
    assert npArrayCreated.dtype == npArrayTest.dtype
    assert ( npArrayCreated == npArrayTest ).all()

    vtkDataTypeCreated: int = attributeCreated.GetDataType()
    assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize(
    "meshName, arrayType",
    [
        ( "2Ranks", "float64" ),  # The input mesh has the wrong type
        ( "extractAndMergeVolume", "int32" ),  # The input array has the wrong type (should be float64)
    ] )
def test_createAttributeRaiseTypeError(
    dataSetTest: Any,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    meshName: str,
    arrayType: str,
) -> None:
    """Test the raises TypeError for the function createAttribute."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, 1, arrayType )
    with pytest.raises( TypeError ):
        arrayModifiers.createAttribute( mesh, npArray, "newAttribute", vtkDataType=VTK_DOUBLE )


@pytest.mark.parametrize(
    "vtkDataType, nbElements",
    [
        ( 64, 1740 ),  # The vtkDataType does not exist
        ( VTK_DOUBLE, 1741 ),  # The number of element of the array is wrong
    ] )
def test_createAttributeRaiseValueError(
    dataSetTest: vtkDataSet,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    vtkDataType: int,
    nbElements: int,
) -> None:
    """Test the raises ValueError for the function createAttribute."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, nbElements, "float64" )
    with pytest.raises( ValueError ):
        arrayModifiers.createAttribute( mesh, npArray, "newAttribute", vtkDataType=vtkDataType )


def test_createAttributeRaiseAttributeError(
    dataSetTest: vtkDataSet,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
) -> None:
    """Test the raises AttributeError for the function createAttribute with a wrong attribute name."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, 1740, "float64" )
    with pytest.raises( AttributeError ):
        arrayModifiers.createAttribute( mesh, npArray, "mass" )


@pytest.mark.parametrize(
    "meshFromName, meshToName, attributeNameFrom, attributeNameTo, piece",
    [
        # Test the attribute to copy
        ## on dataset
        ( "extractAndMergeVolume", "extractAndMergeVolume", "mass", "newAttribute", Piece.CELLS ),
        ( "extractAndMergeVolume", "extractAndMergeVolume", "mass", "newAttributes", Piece.POINTS ),
        ## on multiblock (global)
        ( "2Ranks", "2Ranks", "mass", 'newAttribute', Piece.CELLS ),
        ( "2Ranks", "2Ranks", "mass", "newAttribute", Piece.POINTS ),
        ## on multiblock (partial)
        ( "extractAndMergeVolumeWell1", "extractAndMergeVolumeWell1", "mass", "newAttribute", Piece.CELLS ),
        ( "extractAndMergeVolumeWell1", "extractAndMergeVolumeWell1", "mass", "newAttribute", Piece.POINTS ),
        # Test the copy attribute name that is a name of an attribute on the other piece.
        ## on dataset
        ( "extractAndMergeVolume", "extractAndMergeVolume", "mass", "externalForce", Piece.CELLS ),
        ( "extractAndMergeVolume", "extractAndMergeVolume", "mass", "deltaPressure", Piece.POINTS ),
        ## on multiblock (global)
        ( "2Ranks", "2Ranks", "mass", "externalForce", Piece.CELLS ),
        ( "2Ranks", "2Ranks", "mass", "deltaPressure", Piece.POINTS ),
        ## on multiblock (partial)
        ( "extractAndMergeVolumeWell1", "extractAndMergeVolumeWell1", "mass", "externalForce", Piece.CELLS ),
        ( "extractAndMergeVolumeWell1", "extractAndMergeVolumeWell1", "mass", "deltaPressure", Piece.POINTS ),
    ] )
def test_copyAttribute(
    dataSetTest: Any,
    meshFromName: str,
    meshToName: str,
    attributeNameFrom: str,
    attributeNameTo: str,
    piece: Piece,
) -> None:
    """Test copy of cell attribute from one multiblock to another."""
    meshFrom: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshFromName )
    meshTo: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshToName )

    # Copy the attribute from the meshFrom to the meshTo.
    arrayModifiers.copyAttribute( meshFrom, meshTo, attributeNameFrom, attributeNameTo, piece )

    listDataSets: list[ list[ vtkDataSet ] ] = []
    if isinstance( meshFrom, vtkDataSet ):
        listDataSets.append( [ meshFrom, meshTo ] )
    else:
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( meshFrom )
        for blockIndex in elementaryBlockIndexes:
            dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( blockIndex ) )
            if isAttributeInObject( dataSetFrom, attributeNameFrom, piece ):
                listDataSets.append( [ dataSetFrom, vtkDataSet.SafeDownCast( meshTo.GetDataSet( blockIndex ) ) ] )

    for dataSetFrom, dataSetTo in listDataSets:
        # Get the tested attribute and its copy.
        dataFrom: Union[ vtkPointData, vtkCellData ]
        dataTo: Union[ vtkPointData, vtkCellData ]
        if piece == Piece.POINTS:
            dataFrom = dataSetFrom.GetPointData()
            dataTo = dataSetTo.GetPointData()
        else:
            dataFrom = dataSetFrom.GetCellData()
            dataTo = dataSetTo.GetCellData()
        attributeTest: vtkDataArray = dataFrom.GetArray( attributeNameFrom )
        attributeCopied: vtkDataArray = dataTo.GetArray( attributeNameTo )

        # Test the number of components and their names if multiple.
        nbComponentsTest: int = attributeTest.GetNumberOfComponents()
        nbComponentsCopied: int = attributeCopied.GetNumberOfComponents()
        assert nbComponentsCopied == nbComponentsTest
        if nbComponentsTest > 1:
            componentsNamesTest: tuple[ str, ...] = tuple(
                attributeTest.GetComponentName( i ) for i in range( nbComponentsTest ) )
            componentsNamesCopied: tuple[ str, ...] = tuple(
                attributeCopied.GetComponentName( i ) for i in range( nbComponentsCopied ) )
            assert componentsNamesCopied == componentsNamesTest

        # Test values and their types.
        npArrayTest: npt.NDArray[ Any ] = vtk_to_numpy( attributeTest )
        npArrayCopied: npt.NDArray[ Any ] = vtk_to_numpy( attributeCopied )
        assert npArrayCopied.dtype == npArrayTest.dtype
        assert ( npArrayCopied == npArrayTest ).all()

        vtkDataTypeTest: int = attributeTest.GetDataType()
        vtkDataTypeCopied: int = attributeCopied.GetDataType()
        assert vtkDataTypeCopied == vtkDataTypeTest


@pytest.mark.parametrize(
    "meshNameFrom, meshNameTo",
    [
        ( "extractAndMergeVolume", "other" ),  # The mesh To is not a vtkDataSet or a vtkMultiBlockDataSet
        ( "other", "extractAndMergeVolume" ),  # The mesh From is not a vtkDataSet or a vtkMultiBlockDataSet
        ( "extractAndMergeVolume", "2Ranks" ),  # The two meshes do not have the same type
    ] )
def test_copyAttributeTypeError(
    dataSetTest: Any,
    meshNameFrom: str,
    meshNameTo: str,
) -> None:
    """Test the raises TypeError for the function copyAttribute."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    meshFrom = vtkCellData() if meshNameFrom == "other" else dataSetTest( meshNameFrom )
    meshTo = vtkCellData() if meshNameTo == "other" else dataSetTest( meshNameTo )
    with pytest.raises( TypeError ):
        arrayModifiers.copyAttribute( meshFrom, meshTo, "mass", "mass" )


@pytest.mark.parametrize(
    "meshNameFrom, meshNameTo, piece",
    [
        ( "extractAndMergeVolume", "extractAndMergeVolume", Piece.BOTH ),  # The piece is wrong
        ( "extractAndMergeVolume", "extractAndMergeFault", Piece.CELLS ),  # Two meshes with different cells dimension
        ( "extractAndMergeVolume", "extractAndMergeWell1", Piece.CELLS ),  # Two meshes with different number of cells
        ( "extractAndMergeVolume", "extractAndMergeFault", Piece.POINTS ),  # Two meshes with different number of points
        ( "2Ranks", "4Ranks", Piece.CELLS ),  # Two meshes with different blocks indexation
        ( "extractAndMergeVolume", "extractAndMergeVolume4Ranks",
          Piece.CELLS ),  # Two meshes with different element indexation
    ] )
def test_copyAttributeValueError(
    dataSetTest: Any,
    meshNameFrom: str,
    meshNameTo: str,
    piece: Piece,
) -> None:
    """Test the raises ValueError for the function copyAttribute."""
    meshFrom: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshNameFrom )
    meshTo: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshNameTo )
    with pytest.raises( ValueError ):
        arrayModifiers.copyAttribute( meshFrom, meshTo, "mass", "newAttribute", piece=piece )


@pytest.mark.parametrize(
    "meshNameFrom, meshNameTo, attributeNameFrom, attributeNameTo",
    [
        # The copy attribute name is already an attribute on the mesh to
        ( "extractAndMergeVolume", "extractAndMergeVolume", "mass", "mass" ),
        ( "geosOutput2Ranks", "geosOutput2Ranks", "mass", "mass" ),
        ( "geosOutput2Ranks", "geosOutput2Ranks", "mass", "ghostRank" ),
        # The attribute to copy is not in the mesh From
        ( "extractAndMergeVolume", "extractAndMergeVolume", "newAttribute", "newAttribute" ),
        ( "geosOutput2Ranks", "geosOutput2Ranks", "newAttribute", "newAttribute" ),
    ] )
def test_copyAttributeAttributeError(
    dataSetTest: Any,
    meshNameFrom: str,
    meshNameTo: str,
    attributeNameFrom: str,
    attributeNameTo: str,
) -> None:
    """Test the raises AttributeError for the function copyAttribute."""
    meshFrom: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshNameFrom )
    meshTo: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshNameTo )
    with pytest.raises( AttributeError ):
        arrayModifiers.copyAttribute( meshFrom, meshTo, attributeNameFrom, attributeNameTo )


@pytest.mark.parametrize(
    "meshFromName, meshToName, piece",
    [
        ( "vtu1D", "vtu1D", Piece.CELLS ),  # 1D vtu -> 1D vtu onCells
        ( "vtu1D", "vtu1D", Piece.POINTS ),  # 1D vtu -> 1D vtu onPoints
        ( "vtu1D", "vtu2D", Piece.CELLS ),  # 1D vtu -> 2D vtu onCells
        ( "vtu1D", "vtu2D", Piece.POINTS ),  # 1D vtu -> 2D vtu onPoints
        ( "vtu1D", "vtu3D", Piece.CELLS ),  # 1D vtu -> 3D vtu onCells
        ( "vtu1D", "vtu3D", Piece.POINTS ),  # 1D vtu -> 3D vtu onPoints
        ( "vtu1D", "vtm", Piece.CELLS ),  # 1D vtu -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtu1D", "vtm", Piece.POINTS ),  # 1D vtu -> vtm( 1D, 2D & 3D vtu ) onPoints
        ( "vtu2D", "vtu2D", Piece.CELLS ),  # 2D vtu -> 2D vtu onCells
        ( "vtu2D", "vtu2D", Piece.POINTS ),  # 2D vtu -> 2D vtu onPoints
        ( "vtu2D", "vtu1D", Piece.CELLS ),  # 2D vtu -> 1D vtu onCells
        ( "vtu2D", "vtu1D", Piece.POINTS ),  # 2D vtu -> 1D vtu onPoints
        ( "vtu2D", "vtu3D", Piece.CELLS ),  # 2D vtu -> 3D vtu onCells
        ( "vtu2D", "vtu3D", Piece.POINTS ),  # 2D vtu -> 3D vtu onPoints
        ( "vtu2D", "vtm", Piece.CELLS ),  # 2D vtu -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtu2D", "vtm", Piece.POINTS ),  # 2D vtu -> vtm( 1D, 2D & 3D vtu ) onPoints
        ( "vtu3D", "vtu3D", Piece.CELLS ),  # 3D vtu -> 3D vtu onCells
        ( "vtu3D", "vtu3D", Piece.POINTS ),  # 3D vtu -> 3D vtu onPoints
        ( "vtu3D", "vtu1D", Piece.CELLS ),  # 3D vtu -> 1D vtu onCells
        ( "vtu3D", "vtu1D", Piece.POINTS ),  # 3D vtu -> 1D vtu onPoints
        ( "vtu3D", "vtu2D", Piece.CELLS ),  # 3D vtu -> 2D vtu onCells
        ( "vtu3D", "vtu2D", Piece.POINTS ),  # 3D vtu -> 2D vtu onPoints
        ( "vtu3D", "vtm", Piece.CELLS ),  # 3D vtu -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtu3D", "vtm", Piece.POINTS ),  # 3D vtu -> vtm( 1D, 2D & 3D vtu ) onPoints
        ( "vtm", "vtm", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtm", "vtm", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> vtm( 1D, 2D & 3D vtu ) onPoints
        ( "vtm", "vtu1D", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> 1D vtu onCells
        ( "vtm", "vtu1D", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> 1D vtu onPoints
        ( "vtm", "vtu2D", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> 2D vtu onCells
        ( "vtm", "vtu2D", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> 2D vtu onPoints
        ( "vtm", "vtu3D", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> 3D vtu onCells
        ( "vtm", "vtu3D", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> 3D vtu onPoints
    ] )
def test_transferAttributeWithElementMapMeshesType(
    internMeshTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshFromName: str,
    meshToName: str,
    piece: Piece,
) -> None:
    """Test to transfer attributes from the source mesh to the final mesh using a map of points/cells.

    The transfer between meshes with different type is tested.
    """
    meshFrom: Union[ vtkMultiBlockDataSet, vtkDataSet ] = internMeshTest( meshFromName )
    meshTo: Union[ vtkMultiBlockDataSet, vtkDataSet ] = internMeshTest( meshToName )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( meshFromName, meshToName, piece )

    # Create a constant attribute to transfer on the mesh from
    arrayModifiers.createConstantAttribute( meshFrom, [ 42 ], "attributeToTransfer", piece=piece )

    arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, "attributeToTransfer", piece )
    for flatIdDataSetTo in elementMap:
        dataTo: Union[ vtkPointData, vtkCellData ]
        if isinstance( meshTo, vtkDataSet ):
            dataTo = meshTo.GetPointData() if piece == Piece.POINTS else meshTo.GetCellData()
        elif isinstance( meshTo, vtkMultiBlockDataSet ):
            dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( meshTo.GetDataSet( flatIdDataSetTo ) )
            dataTo = dataSetTo.GetPointData() if piece == Piece.POINTS else dataSetTo.GetCellData()

        arrayTo: npt.NDArray[ Any ] = vtk_to_numpy( dataTo.GetArray( "attributeToTransfer" ) )
        for idElementTo in range( len( arrayTo ) ):
            idElementFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 1 ] )
            if idElementFrom == -1:
                assert arrayTo[ idElementTo ] == -1

            else:
                dataFrom: Union[ vtkPointData, vtkCellData ]
                if isinstance( meshFrom, vtkDataSet ):
                    dataFrom = meshFrom.GetPointData() if piece == Piece.POINTS else meshFrom.GetCellData()
                elif isinstance( meshFrom, vtkMultiBlockDataSet ):
                    flatIdDataSetFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 0 ] )
                    dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( flatIdDataSetFrom ) )
                    dataFrom = dataSetFrom.GetPointData() if piece == Piece.POINTS else dataSetFrom.GetCellData()

                arrayFrom: npt.NDArray[ Any ] = vtk_to_numpy( dataFrom.GetArray( "attributeToTransfer" ) )
                assert np.all( arrayTo[ idElementTo ] == arrayFrom[ idElementFrom ] )


@pytest.mark.parametrize( "vtkDataType, nbValues", [
    ( VTK_FLOAT, 3 ),
    ( VTK_FLOAT, 1 ),
    ( VTK_DOUBLE, 1 ),
    ( VTK_CHAR, 1 ),
    ( VTK_SIGNED_CHAR, 1 ),
    ( VTK_SHORT, 1 ),
    ( VTK_LONG, 1 ),
    ( VTK_INT, 1 ),
    ( VTK_LONG_LONG, 1 ),
    ( VTK_ID_TYPE, 1 ),
    ( VTK_BIT, 1 ),
    ( VTK_UNSIGNED_CHAR, 1 ),
    ( VTK_UNSIGNED_SHORT, 1 ),
    ( VTK_UNSIGNED_LONG, 1 ),
    ( VTK_UNSIGNED_INT, 1 ),
    ( VTK_UNSIGNED_LONG_LONG, 1 ),
] )
def test_transferAttributeWithElementMapValueType(
    internMeshTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    vtkDataType: int,
    nbValues: int,
) -> None:
    """Test to transfer attributes from the source mesh to the final mesh using a map of cells.

    The transfer of attribute with different type and number of value is tested.
    """
    meshFrom: Union[ vtkMultiBlockDataSet, vtkDataSet ] = internMeshTest( "vtu3D" )
    meshTo: Union[ vtkMultiBlockDataSet, vtkDataSet ] = internMeshTest( "vtu2D" )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "vtu3D", "vtu2D", Piece.CELLS )

    # Get the default value set by the function depending of the type of the value for the test
    defaultValue: Any
    if vtkDataType in ( VTK_FLOAT, VTK_DOUBLE ):
        defaultValue = np.nan
    elif vtkDataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ):
        defaultValue = -1
    elif vtkDataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT,
                          VTK_UNSIGNED_LONG_LONG ):
        defaultValue = 0

    # Create the attribute to transfer on the meshFrom
    typeMapping: dict[ int, type ] = get_vtk_to_numpy_typemap()
    valueType: type = typeMapping[ vtkDataType ]
    value: list[ Any ] = [ valueType( 42 ) ] * nbValues
    defaultValue = valueType( defaultValue )
    if nbValues > 1:
        defaultValue = [ defaultValue ] * nbValues
    arrayModifiers.createConstantAttribute( meshFrom, value, "attributeToTransfer" )

    # Transfer the attribute
    arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, "attributeToTransfer", Piece.CELLS )

    # Test the transfer of the attribute
    for flatIdDataSetTo in elementMap:
        dataTo: vtkCellData = meshTo.GetCellData()
        arrayTo: npt.NDArray[ Any ] = vtk_to_numpy( dataTo.GetArray( "attributeToTransfer" ) )
        for idElementTo in range( len( arrayTo ) ):
            idElementFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 1 ] )
            if idElementFrom == -1:
                if np.isnan( defaultValue ).all():
                    assert np.isnan( arrayTo[ idElementTo ] ).all()
                else:
                    assert np.all( arrayTo[ idElementTo ] == defaultValue )

            else:
                dataFrom: vtkCellData = meshFrom.GetCellData()
                arrayFrom: npt.NDArray[ Any ] = vtk_to_numpy( dataFrom.GetArray( "attributeToTransfer" ) )
                assert np.all( arrayTo[ idElementTo ] == arrayFrom[ idElementFrom ] )


@pytest.mark.parametrize(
    "meshNameFrom, meshNameTo",
    [
        ( "extractAndMergeVolume", "other" ),  # The mesh To is not a vtkDataSet or a vtkMultiBlockDataSet
        ( "other", "extractAndMergeVolume" ),  # The mesh From is not a vtkDataSet or a vtkMultiBlockDataSet
        ( "other", "other" ),  # The two meshes are not vtkDataSet or vtkMultiBlockDataSet
    ] )
def test_transferAttributeWithElementMapTypeError(
    dataSetTest: Any,
    meshNameFrom: str,
    meshNameTo: str,
) -> None:
    """Test the raises TypeError for the function transferAttributeWithElementMap."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    meshFrom = vtkCellData() if meshNameFrom == "other" else dataSetTest( meshNameFrom )
    meshTo = vtkCellData() if meshNameTo == "other" else dataSetTest( meshNameTo )

    with pytest.raises( TypeError ):
        arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, {}, "mass", Piece.CELLS )


@pytest.mark.parametrize(
    "meshNameFrom, meshNameTo, attributeName",
    [
        # Issues with the mesh From
        ( "extractAndMergeVolumeWell1", "extractAndMergeVolume", "mass" ),  # The attribute is partial in the mesh From
        ( "extractAndMergeVolume", "extractAndMergeVolume", "newAttribute" ),  # The attribute is not in the mesh From
        # Issues with the mesh To
        ( "extractAndMergeVolume", "extractAndMergeVolume", "mass"
         ),  # The attribute is already in the mesh to (dataset)
        ( "extractAndMergeVolume", "extractAndMergeVolumeWell1",
          "mass" ),  # The attribute is already in the mesh to (partial)
        ( "extractAndMergeVolume", "2Ranks", "mass" ),  # The attribute is already in the mesh to (global)
    ] )
def test_transferAttributeWithElementMapAttributeError(
    dataSetTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshNameFrom: str,
    meshNameTo: str,
    attributeName: str,
) -> None:
    """Test the raises AttributeError for the function transferAttributeWithElementMap with an attribute already in the mesh to."""
    meshFrom: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshNameFrom )
    meshTo: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshNameTo )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( meshNameFrom, meshNameTo, Piece.CELLS )
    with pytest.raises( AttributeError ):
        arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, attributeName, Piece.CELLS )


@pytest.mark.parametrize(
    "meshNameTo, meshNameToMap, flatIdDataSetTo, piece",
    [
        ( "vtu1D", "vtu1D", 0, Piece.BOTH ),  # The piece is wrong.
        ( "vtu1D", "vtu1D", 1, Piece.CELLS ),  # The flatIdDataSetTo is wrong.
        ( "vtu1D", "vtu2D", 0, Piece.CELLS ),  # The map is wrong.
    ] )
def test_transferAttributeWithElementMapValueError(
    internMeshTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshNameTo: str,
    meshNameToMap: str,
    flatIdDataSetTo: int,
    piece: Piece,
) -> None:
    """Test the raises ValueError for the function transferAttributeWithElementMap."""
    meshFrom: vtkDataSet = internMeshTest( "vtu1D" )
    arrayModifiers.createConstantAttribute( meshFrom, [ 4 ], "attributeToTransfer" )  # Create the attribute to transfer
    meshTo: vtkDataSet = internMeshTest( meshNameTo )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "vtu1D", meshNameToMap, Piece.CELLS )
    with pytest.raises( ValueError ):
        arrayModifiers.transferAttributeWithElementMap( meshFrom,
                                                        meshTo,
                                                        elementMap,
                                                        "attributeToTransfer",
                                                        piece,
                                                        flatIdDataSetTo=flatIdDataSetTo )


@pytest.mark.parametrize( "attributeName, piece", [
    ( "mass", Piece.CELLS ),
    ( "mass", Piece.POINTS ),
] )
def test_renameAttributeMultiblock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    piece: Piece,
) -> None:
    """Test renaming attribute in a multiblock dataset."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "2Ranks" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute(
        vtkMultiBlockDataSetTest,
        attributeName,
        newAttributeName,
        piece,
    )

    blockIds = getBlockElementIndexesFlatten( vtkMultiBlockDataSetTest )
    for blockId in blockIds:
        block: vtkDataSet = vtkDataSet.SafeDownCast( vtkMultiBlockDataSetTest.GetDataSet( blockId ) )
        data: Union[ vtkPointData, vtkCellData ]
        if piece == Piece.POINTS:
            data = block.GetPointData()
            assert data.HasArray( attributeName ) == 0
            assert data.HasArray( newAttributeName ) == 1

        else:
            data = block.GetCellData()
            assert data.HasArray( attributeName ) == 0
            assert data.HasArray( newAttributeName ) == 1


@pytest.mark.parametrize( "attributeName, piece", [
    ( "mass", Piece.CELLS ),
    ( "mass", Piece.POINTS ),
] )
def test_renameAttributeDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    piece: Piece,
) -> None:
    """Test renaming an attribute in a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute( object=vtkDataSetTest,
                                    attributeName=attributeName,
                                    newAttributeName=newAttributeName,
                                    piece=piece )
    if piece == Piece.POINTS:
        assert vtkDataSetTest.GetPointData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetPointData().HasArray( newAttributeName ) == 1

    else:
        assert vtkDataSetTest.GetCellData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetCellData().HasArray( newAttributeName ) == 1


def test_renameAttributeTypeError() -> None:
    """Test the raises TypeError for the function renameAttribute with the mesh to with a wrong type."""
    with pytest.raises( TypeError ):
        arrayModifiers.renameAttribute( False, "PORO", "newName", Piece.CELLS )


@pytest.mark.parametrize(
    "attributeName, newName",
    [
        ( "newName", "newName" ),  # The attribute is not in the mesh.
        ( "mass", "mass" ),  # The new name is already an attribute in the mesh.
    ] )
def test_renameAttributeAttributeError(
    dataSetTest: vtkDataSet,
    attributeName: str,
    newName: str,
) -> None:
    """Test the raises AttributeError for the function renameAttribute."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    with pytest.raises( AttributeError ):
        arrayModifiers.renameAttribute( mesh, attributeName, newName, Piece.CELLS )
