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

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkPointData, vtkCellData )

from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten
from geos.mesh.utils.arrayHelpers import isAttributeInObject

from vtk import (  # type: ignore[import-untyped]
    VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG, VTK_CHAR, VTK_SIGNED_CHAR,
    VTK_SHORT, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE, VTK_FLOAT, VTK_DOUBLE,
)
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

from geos.mesh.utils import arrayModifiers


@pytest.mark.parametrize(
    "idBlock, attributeName, nbComponentsTest, componentNamesTest, piece, listValues, listValuesTest, vtkDataTypeTest",
    [
        # Test fill an attribute on point and on cell.
        ( 3, "PointAttribute", 3, ( "AX1", "AX2", "AX3" ), Piece.POINTS, None,
          [ np.float64( np.nan ), np.float64( np.nan ),
            np.float64( np.nan ) ], VTK_DOUBLE ),
        ( 3, "CellAttribute", 3, ( "AX1", "AX2", "AX3" ), Piece.CELLS, None,
          [ np.float64( np.nan ), np.float64( np.nan ),
            np.float64( np.nan ) ], VTK_DOUBLE ),
        # Test fill attributes with different number of component with or without component names.
        ( 3, "PORO", 1, (), Piece.CELLS, None, [ np.float32( np.nan ) ], VTK_FLOAT ),
        ( 1, "collocated_nodes", 2,
          ( None, None ), Piece.POINTS, None, [ np.int64( -1 ), np.int64( -1 ) ], VTK_ID_TYPE ),
        # Test fill an attribute with different type of value.
        ( 3, "FAULT", 1, (), Piece.CELLS, None, [ np.int32( -1 ) ], VTK_INT ),
        ( 3, "FAULT", 1, (), Piece.CELLS, [ 4 ], [ np.int32( 4 ) ], VTK_INT ),
        ( 3, "PORO", 1, (), Piece.CELLS, [ 4 ], [ np.float32( 4 ) ], VTK_FLOAT ),
        ( 1, "collocated_nodes", 2,
          ( None, None ), Piece.POINTS, [ 4, 4 ], [ np.int64( 4 ), np.int64( 4 ) ], VTK_ID_TYPE ),
        ( 3, "CellAttribute", 3, ( "AX1", "AX2", "AX3" ), Piece.CELLS, [ 4, 4, 4 ],
          [ np.float64( 4 ), np.float64( 4 ), np.float64( 4 ) ], VTK_DOUBLE ),
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
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
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

    npArrayFilled: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeFilled )
    assert npArrayFilled.dtype == npArrayTest.dtype
    if listValues is None and vtkDataTypeTest in ( VTK_FLOAT, VTK_DOUBLE ):
        assert np.isnan( npArrayFilled ).all()
    else:
        assert ( npArrayFilled == npArrayTest ).all()

    vtkDataTypeFilled: int = attributeFilled.GetDataType()
    assert vtkDataTypeFilled == vtkDataTypeTest


def test_fillPartialAttributesTypeError( dataSetTest: vtkDataSet, ) -> None:
    """Test the raises TypeError for the function fillPartialAttributes with a wrong mesh type."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( TypeError ):
        arrayModifiers.fillPartialAttributes( mesh, "PORO" )


def test_fillPartialAttributesValueError( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test the raises ValueError for the function fillPartialAttributes with too many values for the attribute."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    with pytest.raises( ValueError ):
        arrayModifiers.fillPartialAttributes( mesh, "PORO", listValues=[ 42, 42 ] )


@pytest.mark.parametrize(
    "attributeName",
    [
        ( "newAttribute" ),  # The attribute is not in the mesh
        ( "GLOBAL_IDS_CELLS" ),  # The attribute is already global
    ] )
def test_fillPartialAttributesAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
) -> None:
    """Test the raises AttributeError for the function fillPartialAttributes."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    with pytest.raises( AttributeError ):
        arrayModifiers.fillPartialAttributes( mesh, attributeName )


def test_FillAllPartialAttributes( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test to fill all the partial attributes of a vtkMultiBlockDataSet with a value."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    arrayModifiers.fillAllPartialAttributes( multiBlockDataSetTest )

    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetTest )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( blockIndex ) )
        attributeExist: int
        for attributeNameOnPoint in [ "PointAttribute", "collocated_nodes" ]:
            attributeExist = dataSet.GetPointData().HasArray( attributeNameOnPoint )
            assert attributeExist == 1
        for attributeNameOnCell in [ "CELL_MARKERS", "CellAttribute", "FAULT", "PERM", "PORO" ]:
            attributeExist = dataSet.GetCellData().HasArray( attributeNameOnCell )
            assert attributeExist == 1


def test_fillAllPartialAttributesTypeError( dataSetTest: vtkDataSet, ) -> None:
    """Test the raises TypeError for the function fillAllPartialAttributes with a wrong mesh type."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
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
        ( "dataset", [ np.float32( 42 ) ], (), (), Piece.CELLS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "dataset", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "multiblock", [ np.float32( 42 ) ], (), (), Piece.CELLS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "multiblock", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test with an attribute name that exist on the opposite piece.
        ( "dataset", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "PORO" ),
        ( "multiblock", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "PORO" ),  # Partial
        ( "multiblock", [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "GLOBAL_IDS_CELLS" ),  # Global
        # Test the number of components and their names.
        ( "dataset", [ np.float32( 42 ) ], ( "X" ), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "dataset", [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y" ),
          ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "dataset", [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( "dataset", [ np.float32( 42 ), np.float32( 42 ) ], (),
          ( "Component0", "Component1" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test the type of the values.
        ## With numpy scalar type.
        ( "dataset", [ np.int8( 42 ) ], (), (), Piece.POINTS, None, VTK_SIGNED_CHAR, "newAttribute" ),
        ( "dataset", [ np.int8( 42 ) ], (), (), Piece.POINTS, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "newAttribute" ),
        ( "dataset", [ np.int16( 42 ) ], (), (), Piece.POINTS, None, VTK_SHORT, "newAttribute" ),
        ( "dataset", [ np.int16( 42 ) ], (), (), Piece.POINTS, VTK_SHORT, VTK_SHORT, "newAttribute" ),
        ( "dataset", [ np.int32( 42 ) ], (), (), Piece.POINTS, None, VTK_INT, "newAttribute" ),
        ( "dataset", [ np.int32( 42 ) ], (), (), Piece.POINTS, VTK_INT, VTK_INT, "newAttribute" ),
        ( "dataset", [ np.int64( 42 ) ], (), (), Piece.POINTS, None, VTK_LONG_LONG, "newAttribute" ),
        ( "dataset", [ np.int64( 42 ) ], (), (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( "dataset", [ np.uint8( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( "dataset", [ np.uint8( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( "dataset", [ np.uint16( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( "dataset", [ np.uint16( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( "dataset", [ np.uint32( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_INT, "newAttribute" ),
        ( "dataset", [ np.uint32( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "newAttribute" ),
        ( "dataset", [ np.uint64( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( "dataset", [ np.uint64( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( "dataset", [ np.float32( 42 ) ], (), (), Piece.POINTS, None, VTK_FLOAT, "newAttribute" ),
        ( "dataset", [ np.float64( 42 ) ], (), (), Piece.POINTS, None, VTK_DOUBLE, "newAttribute" ),
        ( "dataset", [ np.float64( 42 ) ], (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
        ## With python scalar type.
        ( "dataset", [ 42 ], (), (), Piece.POINTS, None, VTK_LONG_LONG, "newAttribute" ),
        ( "dataset", [ 42 ], (), (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( "dataset", [ 42. ], (), (), Piece.POINTS, None, VTK_DOUBLE, "newAttribute" ),
        ( "dataset", [ 42. ], (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
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

        npArrayCreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeCreated )
        assert npArrayCreated.dtype == npArrayTest.dtype
        assert ( npArrayCreated == npArrayTest ).all()

        vtkDataTypeCreated: int = attributeCreated.GetDataType()
        assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize(
    "meshName, listValues, vtkDataType",
    [
        ( "dataset", [ np.int32( 42 ), np.int64( 42 ) ], VTK_DOUBLE ),  # All the values in the listValues are not the same
        ( "dataset", [ np.int32( 42 ) ], VTK_DOUBLE ),  # The type of the value is not coherent with the vtkDataType
        ( "other", [ np.int64( 42 ) ], VTK_DOUBLE ),  # The type of the mesh is wrong
    ] )
def test_createConstantAttributeRaiseTypeError(
    dataSetTest: vtkDataSet,
    meshName: str,
    listValues: list[ Any ],
    vtkDataType: int,
) -> None:
    """Test the raises TypeError for the function createConstantAttribute."""
    mesh: vtkCellData | vtkDataSet
    if meshName == "other":
        mesh = vtkCellData()
    else:
        mesh = dataSetTest( meshName )
    with pytest.raises( TypeError ):
        arrayModifiers.createConstantAttribute( mesh, listValues, "newAttribute", vtkDataType=vtkDataType )


def test_createConstantAttributeRaiseValueError( dataSetTest: vtkDataSet, ) -> None:
    """Test the raises ValueError for the function createConstantAttribute with wrong values."""
    mesh: vtkDataSet = dataSetTest( "dataset" )

    # Wrong vtk type
    with pytest.raises( ValueError ):
        arrayModifiers.createConstantAttribute( mesh, [ np.int32( 42 ) ], "newAttribute", vtkDataType=64 )

    # Wrong piece
    with pytest.raises( ValueError ):
        arrayModifiers.createConstantAttribute( mesh, [ np.int32( 42 ) ], "newAttribute", piece=Piece.BOTH )


@pytest.mark.parametrize("meshName, attributeName",
    [
        ( "multiblock", "PORO" ),  # Partial
        ( "multiblock", "GLOBAL_IDS_CELLS" ),  # Global
        ( "dataset", "PORO" ),
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
        ( (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "float64", "CellAttribute" ),
        ( (), (), Piece.CELLS, VTK_DOUBLE, VTK_DOUBLE, "float64", "PointAttribute" ),
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
    dataSet: vtkDataSet = dataSetTest( "dataset" )

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
    npArrayCreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeCreated )
    assert npArrayCreated.dtype == npArrayTest.dtype
    assert ( npArrayCreated == npArrayTest ).all()

    vtkDataTypeCreated: int = attributeCreated.GetDataType()
    assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize(
    "meshName, arrayType",
    [
        ( "multiblock", "float64" ),  # The input mesh has the wrong type
        ( "dataset", "int32" ),  # The input array has the wrong type (should be float64)
    ] )
def test_createAttributeRaiseTypeError(
    dataSetTest: Any,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    meshName: str,
    arrayType: str,
) -> None:
    """Test the raises TypeError for the function createAttribute."""
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshName )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, 1, arrayType )
    attributeName: str = "NewAttribute"
    with pytest.raises( TypeError ):
        arrayModifiers.createAttribute( mesh, npArray, attributeName, vtkDataType=VTK_DOUBLE )


@pytest.mark.parametrize(
    "vtkDataType, nbElements",
    [
        ( 64, 1740 ),  # The vtkDataType does not exist
        ( VTK_DOUBLE, 1741 ),  # The number of element of the array is wrong
    ] )
def test_createAttributeRaiseValueError(
    dataSetTest: Any,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    vtkDataType: int,
    nbElements: int,
) -> None:
    """Test the raises ValueError for the function createAttribute."""
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( "dataset" )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, nbElements, "float64" )
    with pytest.raises( ValueError ):
        arrayModifiers.createAttribute( mesh, npArray, "newAttribute", vtkDataType=vtkDataType )


def test_createAttributeRaiseAttributeError(
    dataSetTest: Any,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
) -> None:
    """Test the raises AttributeError for the function createAttribute with a wrong attribute name."""
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( "dataset" )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, 1740, "float64" )
    with pytest.raises( AttributeError ):
        arrayModifiers.createAttribute( mesh, npArray, "PORO" )


@pytest.mark.parametrize(
    "meshFromName, meshToName, attributeNameFrom, attributeNameTo, piece",
    [
        # Test multiblock.
        ## Test with global attributes.
        ( "multiblock", "emptymultiblock", "GLOBAL_IDS_POINTS", "newAttribute", Piece.POINTS ),
        ( "multiblock", "emptymultiblock","GLOBAL_IDS_CELLS", 'newAttribute', Piece.CELLS ),
        ## Test with partial attributes.
        ( "multiblock", "emptymultiblock","CellAttribute", "newAttribute", Piece.CELLS ),
        ( "multiblock", "emptymultiblock","PointAttribute", "newAttribute", Piece.POINTS ),
        # Test dataset.
        ( "dataset", "emptydataset","CellAttribute", "newAttribute", Piece.CELLS ),
        ( "dataset", "emptydataset","PointAttribute", "newAttributes", Piece.POINTS ),
        # Test attribute names. The copy attribute name is a name of an attribute on the other piece.
        ( "multiblock", "multiblock", "GLOBAL_IDS_POINTS", "GLOBAL_IDS_CELLS", Piece.POINTS ),
        ( "multiblock", "multiblock","CellAttribute", "PointAttribute", Piece.CELLS ),
        ( "dataset", "dataset","CellAttribute", "PointAttribute", Piece.CELLS ),
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
    meshFrom: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshFromName )
    meshTo: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshToName )

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
        npArrayTest: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeTest )
        npArrayCopied: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeCopied )
        assert npArrayCopied.dtype == npArrayTest.dtype
        assert ( npArrayCopied == npArrayTest ).all()

        vtkDataTypeTest: int = attributeTest.GetDataType()
        vtkDataTypeCopied: int = attributeCopied.GetDataType()
        assert vtkDataTypeCopied == vtkDataTypeTest


@pytest.mark.parametrize( "meshNameFrom, meshNameTo", [
    ( "dataset", "other" ),
    ( "other", "emptydataset" ),
    ( "dataset", "emptymultiblock" ),
    ( "multiblock", "emptydataset" ),
] )
def test_copyAttributeTypeError(
    dataSetTest: Any,
    meshNameFrom: str,
    meshNameTo: str,
) -> None:
    """Test the raises TypeError for the function copyAttribute."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    if meshNameFrom == "other":
        meshFrom = vtkCellData()
    else:
        meshFrom= dataSetTest( meshNameFrom )

    if meshNameTo == "other":
        meshTo = vtkCellData()
    else:
        meshTo = dataSetTest( meshNameTo )

    with pytest.raises( TypeError ):
        arrayModifiers.copyAttribute( meshFrom, meshTo, "PORO", "PORO" )


# TODO: Create two meshes similar but with two different element indexation
@pytest.mark.parametrize( "meshNameFrom, meshNameTo, piece", [
    ( "dataset", "emptydataset", Piece.BOTH ),  # The piece is wrong
    ( "dataset", "well", Piece.CELLS ),  # Two meshes with different cells dimension
    ( "multiblock", "multiblockGeosOutput", Piece.CELLS ),  # Two meshes with different blocks indexation
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
        arrayModifiers.copyAttribute( meshFrom, meshTo, "GLOBAL_IDS_CELLS", "newAttribute", piece=piece )


@pytest.mark.parametrize( "meshNameFrom, meshNameTo, attributeNameFrom, attributeNameTo", [
    # The copy attribute name is already an attribute on the mesh to
    ( "dataset", "dataset", "PORO", "PORO" ),
    ( "multiblock", "multiblock", "PORO", "PORO" ),
    ( "multiblock", "multiblock", "PORO", "GLOBAL_IDS_CELLS" ),
    # The attribute to copy is not in the mesh From
    # ( "dataset", "emptydataset", "newAttribute", "newAttribute" ),  TODO: activate when the PR 223 is merged
    ( "multiblock", "emptymultiblock", "newAttribute", "newAttribute" ),
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


@pytest.mark.parametrize( "meshFromName, meshToName, attributeName, piece, defaultValueTest", [
    ( "fracture", "emptyFracture", "collocated_nodes", Piece.POINTS, [ -1, -1 ] ),
    ( "multiblock", "emptyFracture", "FAULT", Piece.CELLS, -1 ),
    ( "multiblock", "emptymultiblock", "FAULT", Piece.CELLS, -1 ),
    ( "dataset", "emptymultiblock", "FAULT", Piece.CELLS, -1 ),
    ( "dataset", "emptydataset", "FAULT", Piece.CELLS, -1 ),
] )
def test_transferAttributeWithElementMap(
    dataSetTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshFromName: str,
    meshToName: str,
    attributeName: str,
    piece: Piece,
    defaultValueTest: Any,
) -> None:
    """Test to transfer attributes from the source mesh to the final mesh using a map of points/cells."""
    meshFrom: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshFromName )
    if isinstance( meshFrom, vtkMultiBlockDataSet ):
        arrayModifiers.fillAllPartialAttributes( meshFrom )

    meshTo: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshToName )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( meshFromName, meshToName, piece )

    arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, attributeName, piece )

    for flatIdDataSetTo in elementMap:
        dataTo: Union[ vtkPointData, vtkCellData ]
        if isinstance( meshTo, vtkDataSet ):
            dataTo = meshTo.GetPointData() if piece == Piece.POINTS else meshTo.GetCellData()
        elif isinstance( meshTo, vtkMultiBlockDataSet ):
            dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( meshTo.GetDataSet( flatIdDataSetTo ) )
            dataTo = dataSetTo.GetPointData() if piece == Piece.POINTS else dataSetTo.GetCellData()

        arrayTo: npt.NDArray[ Any ] = vnp.vtk_to_numpy( dataTo.GetArray( attributeName ) )
        for idElementTo in range( len( arrayTo ) ):
            idElementFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 1 ] )
            if idElementFrom == -1:
                assert arrayTo[ idElementTo ] == defaultValueTest

            else:
                dataFrom: Union[ vtkPointData, vtkCellData ]
                if isinstance( meshFrom, vtkDataSet ):
                    dataFrom = meshFrom.GetPointData() if piece == Piece.POINTS else meshFrom.GetCellData()
                elif isinstance( meshFrom, vtkMultiBlockDataSet ):
                    flatIdDataSetFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 0 ] )
                    dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( flatIdDataSetFrom ) )
                    dataFrom = dataSetFrom.GetPointData() if piece == Piece.POINTS else dataSetFrom.GetCellData()

                arrayFrom: npt.NDArray[ Any ] = vnp.vtk_to_numpy( dataFrom.GetArray( attributeName ) )
                assert np.all( arrayTo[ idElementTo ] == arrayFrom[ idElementFrom ] )


@pytest.mark.parametrize( "meshNameFrom, meshNameTo", [
    ( "dataset", "other" ),
    ( "other", "emptydataset" ),
    ( "other", "other" ),
] )
def test_transferAttributeWithElementMapTypeError(
    dataSetTest: Any,
    meshNameFrom: str,
    meshNameTo: str,
) -> None:
    """Test the raises TypeError for the function transferAttributeWithElementMap."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCellData ]
    if meshNameFrom == "other":
        meshFrom = vtkCellData()
    else:
        meshFrom= dataSetTest( meshNameFrom )

    if meshNameTo == "other":
        meshTo = vtkCellData()
    else:
        meshTo = dataSetTest( meshNameTo )

    with pytest.raises( TypeError ):
        arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, {}, "GLOBAL_IDS_CELLS", Piece.CELLS )


@pytest.mark.parametrize( "meshNameFrom, meshNameTo, attributeName", [
    ( "multiblock", "emptymultiblock", "PORO" ),  # The attribute is partial in the mesh From
    ( "dataset", "emptydataset", "newAttribute" ),  # The attribute is not in the mesh From
    ( "dataset", "emptydataset", "GLOBAL_IDS_CELLS" ),  # The attribute is already in the mesh to
    ( "multiblock", "emptymultiblock", "GLOBAL_IDS_CELLS" ),  # The attribute is already in the mesh to
] )
def test_transferAttributeWithElementMapAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
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


@pytest.mark.parametrize( "meshNameTo, meshNameToMap, flatIdDataSetTo, piece", [
    ( "emptyFracture", "emptyFracture", 0, Piece.BOTH ),  # The piece is wrong.
    ( "emptyFracture", "emptyFracture", 1, Piece.CELLS ),  # The flatIdDataSetTo is wrong.
    ( "emptyFracture", "emptymultiblock", 0, Piece.CELLS ),  # The map is wrong.
] )
def test_transferAttributeWithElementMapValueError(
    dataSetTest: vtkDataSet,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshNameTo: str,
    meshNameToMap: str,
    flatIdDataSetTo: int,
    piece: Piece,
) -> None:
    """Test the raises ValueError for the function transferAttributeWithElementMap."""
    meshFrom: vtkDataSet = dataSetTest( "dataset" )
    meshTo: vtkDataSet = dataSetTest( meshNameTo )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "dataset", meshNameToMap, False )
    with pytest.raises( ValueError ):
        arrayModifiers.transferAttributeWithElementMap( meshFrom,
                                                                 meshTo,
                                                                 elementMap,
                                                                 "FAULT",
                                                                 piece,
                                                                 flatIdDataSetTo=flatIdDataSetTo )


@pytest.mark.parametrize( "attributeName, piece", [
    ( "CellAttribute", Piece.CELLS ),
    ( "PointAttribute", Piece.POINTS ),
] )
def test_renameAttributeMultiblock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    piece: Piece,
) -> None:
    """Test renaming attribute in a multiblock dataset."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute(
        vtkMultiBlockDataSetTest,
        attributeName,
        newAttributeName,
        piece,
    )
    block: vtkDataSet = vtkDataSet.SafeDownCast( vtkMultiBlockDataSetTest.GetDataSet( 1 ) )
    data: Union[ vtkPointData, vtkCellData ]
    if piece == Piece.POINTS:
        data = block.GetPointData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1

    else:
        data = block.GetCellData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1


@pytest.mark.parametrize( "attributeName, piece", [ ( "CellAttribute", Piece.CELLS ),
                                                    ( "PointAttribute", Piece.POINTS ) ] )
def test_renameAttributeDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    piece: Piece,
) -> None:
    """Test renaming an attribute in a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
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
        ( "PORO", "PORO" ),  # The new name is already an attribute in the mesh.
    ] )
def test_renameAttributeAttributeError(
    dataSetTest: vtkDataSet,
    attributeName: str,
    newName: str,
) -> None:
    """Test the raises AttributeError for the function renameAttribute."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( AttributeError ):
        arrayModifiers.renameAttribute( mesh, attributeName, newName, Piece.CELLS )
