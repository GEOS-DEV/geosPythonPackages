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
    assert arrayModifiers.fillPartialAttributes( multiBlockDataSetTest,
                                                 attributeName,
                                                 piece=piece,
                                                 listValues=listValues )

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


@pytest.mark.parametrize( "multiBlockDataSetName", [ "multiblock" ] )
def test_FillAllPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    multiBlockDataSetName: str,
) -> None:
    """Test to fill all the partial attributes of a vtkMultiBlockDataSet with a value."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( multiBlockDataSetName )
    assert arrayModifiers.fillAllPartialAttributes( multiBlockDataSetTest )

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


@pytest.mark.parametrize(
    "attributeName, piece",
    [
        # Test to create a new attribute on points and on cells.
        ( "newAttribute", Piece.CELLS ),
        ( "newAttribute", Piece.POINTS ),
    ] )
def test_createConstantAttributeMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    piece: Piece,
) -> None:
    """Test creation of constant attribute in multiblock dataset."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    values: list[ float ] = [ np.nan ]
    assert arrayModifiers.createConstantAttributeMultiBlock( multiBlockDataSetTest, values, attributeName, piece=piece )

    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetTest )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( blockIndex ) )
        data: Union[ vtkPointData, vtkCellData ]
        data = dataSet.GetPointData() if piece == Piece.POINTS else dataSet.GetCellData()

        attributeWellCreated: int = data.HasArray( attributeName )
        assert attributeWellCreated == 1


@pytest.mark.parametrize(
    "listValues, componentNames, componentNamesTest, piece, vtkDataType, vtkDataTypeTest, attributeName",
    [
        # Test attribute names.
        ## Test with a new attributeName on cells and on points.
        ( [ np.float32( 42 ) ], (), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ) ], (), (), Piece.CELLS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test the number of components and their names.
        ( [ np.float32( 42 ) ], ( "X" ), (), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y" ),
          ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ), np.float32( 42 ) ], (),
          ( "Component0", "Component1" ), Piece.POINTS, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test the type of the values.
        ## With numpy scalar type.
        ( [ np.int8( 42 ) ], (), (), Piece.POINTS, None, VTK_SIGNED_CHAR, "newAttribute" ),
        ( [ np.int8( 42 ) ], (), (), Piece.POINTS, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "newAttribute" ),
        ( [ np.int16( 42 ) ], (), (), Piece.POINTS, None, VTK_SHORT, "newAttribute" ),
        ( [ np.int16( 42 ) ], (), (), Piece.POINTS, VTK_SHORT, VTK_SHORT, "newAttribute" ),
        ( [ np.int32( 42 ) ], (), (), Piece.POINTS, None, VTK_INT, "newAttribute" ),
        ( [ np.int32( 42 ) ], (), (), Piece.POINTS, VTK_INT, VTK_INT, "newAttribute" ),
        ( [ np.int64( 42 ) ], (), (), Piece.POINTS, None, VTK_LONG_LONG, "newAttribute" ),
        ( [ np.int64( 42 ) ], (), (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( [ np.uint8( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( [ np.uint8( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( [ np.uint16( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( [ np.uint16( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( [ np.uint32( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_INT, "newAttribute" ),
        ( [ np.uint32( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "newAttribute" ),
        ( [ np.uint64( 42 ) ], (), (), Piece.POINTS, None, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( [ np.uint64( 42 ) ], (), (), Piece.POINTS, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( [ np.float32( 42 ) ], (), (), Piece.POINTS, None, VTK_FLOAT, "newAttribute" ),
        ( [ np.float64( 42 ) ], (), (), Piece.POINTS, None, VTK_DOUBLE, "newAttribute" ),
        ( [ np.float64( 42 ) ], (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
        ## With python scalar type.
        ( [ 42 ], (), (), Piece.POINTS, None, VTK_LONG_LONG, "newAttribute" ),
        ( [ 42 ], (), (), Piece.POINTS, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( [ 42. ], (), (), Piece.POINTS, None, VTK_DOUBLE, "newAttribute" ),
        ( [ 42. ], (), (), Piece.POINTS, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
    ] )
def test_createConstantAttributeDataSet(
    dataSetTest: vtkDataSet,
    listValues: list[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    piece: Piece,
    vtkDataType: Union[ int, Any ],
    vtkDataTypeTest: int,
    attributeName: str,
) -> None:
    """Test constant attribute creation in dataset."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )

    # Create the new constant attribute in the dataSet.
    assert arrayModifiers.createConstantAttributeDataSet( dataSet, listValues, attributeName, componentNames, piece,
                                                          vtkDataType )

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
    assert arrayModifiers.createAttribute( dataSet, npArrayTest, attributeName, componentNames, piece, vtkDataType )

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
    "attributeNameFrom, attributeNameTo, piece",
    [
        # Test with global attributes.
        ( "GLOBAL_IDS_POINTS", "GLOBAL_IDS_POINTS_To", Piece.POINTS ),
        ( "GLOBAL_IDS_CELLS", 'GLOBAL_IDS_CELLS_To', Piece.CELLS ),
        # Test with partial attributes.
        ( "CellAttribute", "CellAttributeTo", Piece.CELLS ),
        ( "PointAttribute", "PointAttributeTo", Piece.POINTS ),
    ] )
def test_copyAttribute(
    dataSetTest: vtkMultiBlockDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    piece: Piece,
) -> None:
    """Test copy of cell attribute from one multiblock to another."""
    multiBlockDataSetFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    multiBlockDataSetTo: vtkMultiBlockDataSet = dataSetTest( "emptymultiblock" )

    # Copy the attribute from the multiBlockDataSetFrom to the multiBlockDataSetTo.
    assert arrayModifiers.copyAttribute( multiBlockDataSetFrom, multiBlockDataSetTo, attributeNameFrom, attributeNameTo,
                                         piece )

    # Parse the two multiBlockDataSet and test if the attribute has been copied.
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetFrom )
    for blockIndex in elementaryBlockIndexes:
        dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetFrom.GetDataSet( blockIndex ) )
        dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTo.GetDataSet( blockIndex ) )
        dataFrom: Union[ vtkPointData, vtkCellData ]
        dataTo: Union[ vtkPointData, vtkCellData ]
        if piece == Piece.POINTS:
            dataFrom = dataSetFrom.GetPointData()
            dataTo = dataSetTo.GetPointData()
        else:
            dataFrom = dataSetFrom.GetCellData()
            dataTo = dataSetTo.GetCellData()

        attributeExistTest: int = dataFrom.HasArray( attributeNameFrom )
        attributeExistCopied: int = dataTo.HasArray( attributeNameTo )
        assert attributeExistCopied == attributeExistTest


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo, piece", [
    ( "CellAttribute", "CellAttributeTo", Piece.CELLS ),
    ( "PointAttribute", "PointAttributeTo", Piece.POINTS ),
] )
def test_copyAttributeDataSet(
    dataSetTest: vtkDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    piece: Piece,
) -> None:
    """Test copy of an attribute from one dataset to another."""
    dataSetFrom: vtkDataSet = dataSetTest( "dataset" )
    dataSetTo: vtkDataSet = dataSetTest( "emptydataset" )

    # Copy the attribute from the dataSetFrom to the dataSetTo.
    assert arrayModifiers.copyAttributeDataSet( dataSetFrom, dataSetTo, attributeNameFrom, attributeNameTo, piece )

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

    assert arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, attributeName, piece )

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
