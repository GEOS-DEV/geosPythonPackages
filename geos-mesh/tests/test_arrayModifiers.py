# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, Any, cast

import numpy as np
import numpy.typing as npt

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkPointData, vtkCellData )

from geos.mesh.utils.arrayHelpers import getAttributesWithNumberOfComponents

from vtk import (  # type: ignore[import-untyped]
    VTK_UNSIGNED_CHAR,
    VTK_UNSIGNED_SHORT,
    VTK_UNSIGNED_INT,
    VTK_UNSIGNED_LONG_LONG,
    VTK_SIGNED_CHAR,
    VTK_SHORT,
    VTK_INT,
    VTK_LONG_LONG,
    VTK_FLOAT,
    VTK_DOUBLE,
    VTK_ID_TYPE,
    VTK_CHAR,
)

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
    "idBlockToFill, attributeName, nbComponentsRef, componentNamesRef, onPoints, value, valueRef, vtkDataTypeRef, valueTypeRef",
    [
        ( 1, "CellAttribute", 3, ( "AX1", "AX2", "AX3" ), False, np.nan, np.nan, VTK_DOUBLE, "float64" ),
        ( 1, "CellAttribute", 3,
          ( "AX1", "AX2", "AX3" ), False, np.float64( 4 ), np.float64( 4 ), VTK_DOUBLE, "float64" ),
        ( 1, "CellAttribute", 3,
          ( "AX1", "AX2", "AX3" ), False, np.int32( 4 ), np.float64( 4 ), VTK_DOUBLE, "float64" ),
        ( 1, "PointAttribute", 3, ( "AX1", "AX2", "AX3" ), True, np.nan, np.nan, VTK_DOUBLE, "float64" ),
        ( 1, "PointAttribute", 3,
          ( "AX1", "AX2", "AX3" ), True, np.float64( 4 ), np.float64( 4 ), VTK_DOUBLE, "float64" ),
        ( 1, "PointAttribute", 3,
          ( "AX1", "AX2", "AX3" ), True, np.int32( 4 ), np.float64( 4 ), VTK_DOUBLE, "float64" ),
        ( 1, "PORO", 1, (), False, np.nan, np.nan, VTK_FLOAT, "float32" ),
        ( 1, "PORO", 1, (), False, np.float32( 4 ), np.float32( 4 ), VTK_FLOAT, "float32" ),
        ( 1, "PORO", 1, (), False, np.int32( 4 ), np.float32( 4 ), VTK_FLOAT, "float32" ),
        ( 1, "FAULT", 1, (), False, np.nan, np.int32( -1 ), VTK_INT, "int32" ),
        ( 1, "FAULT", 1, (), False, np.int32( 4 ), np.int32( 4 ), VTK_INT, "int32" ),
        ( 1, "FAULT", 1, (), False, np.float32( 4 ), np.int32( 4 ), VTK_INT, "int32" ),
        ( 0, "collocated_nodes", 2, ( None, None ), True, np.nan, np.int64( -1 ), VTK_ID_TYPE, "int64" ),
        ( 0, "collocated_nodes", 2, ( None, None ), True, np.int64( 4 ), np.int64( 4 ), VTK_ID_TYPE, "int64" ),
        ( 0, "collocated_nodes", 2, ( None, None ), True, np.int32( 4 ), np.int64( 4 ), VTK_ID_TYPE, "int64" ),
        ( 0, "collocated_nodes", 2, ( None, None ), True, np.float32( 4 ), np.int64( 4 ), VTK_ID_TYPE, "int64" ),
    ] )
def test_fillPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    idBlockToFill: int,
    attributeName: str,
    nbComponentsRef: int,
    componentNamesRef: tuple[ str, ...],
    onPoints: bool,
    value: Any,
    valueRef: Any,
    vtkDataTypeRef: int,
    valueTypeRef: str,
) -> None:
    """Test filling a partial attribute from a multiblock with values."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    arrayModifiers.fillPartialAttributes( multiBlockDataSetTest, attributeName, onPoints, value )

    blockTest: vtkDataSet = cast( vtkDataSet, multiBlockDataSetTest.GetBlock( idBlockToFill ) )
    dataTest: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if onPoints:
        nbElements = blockTest.GetNumberOfPoints()
        dataTest = blockTest.GetPointData()
    else:
        nbElements = blockTest.GetNumberOfCells()
        dataTest = blockTest.GetCellData()

    attributeFillTest: vtkDataArray = dataTest.GetArray( attributeName )
    nbComponentsTest: int = attributeFillTest.GetNumberOfComponents()
    assert nbComponentsTest == nbComponentsRef

    npArrayFillRef: npt.NDArray[ Any ]
    if nbComponentsRef > 1:
        componentNamesTest: tuple[ str, ...] = tuple(
            attributeFillTest.GetComponentName( i ) for i in range( nbComponentsRef ) )
        assert componentNamesTest == componentNamesRef

    npArrayFillRef = np.full( ( nbElements, nbComponentsRef ), valueRef )

    npArrayFillTest: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeFillTest )
    assert npArrayFillTest.dtype == valueTypeRef

    if np.isnan( valueRef ):
        assert np.isnan( npArrayFillRef ).all()
    else:
        assert ( npArrayFillTest == npArrayFillRef ).all()

    vtkDataTypeTest: int = attributeFillTest.GetDataType()
    assert vtkDataTypeTest == vtkDataTypeRef


@pytest.mark.parametrize( "value", [
    ( np.nan ),
    ( np.int32( 42 ) ),
    ( np.int64( 42 ) ),
    ( np.float32( 42 ) ),
    ( np.float64( 42 ) ),
] )
def test_FillAllPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    value: Any,
) -> None:
    """Test to fill all the partial attributes of a vtkMultiBlockDataSet with a value."""
    multiBlockDataSetRef: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    arrayModifiers.fillAllPartialAttributes( multiBlockDataSetTest, value )

    nbBlock = multiBlockDataSetRef.GetNumberOfBlocks()
    for idBlock in range( nbBlock ):
        datasetTest: vtkDataSet = cast( vtkDataSet, multiBlockDataSetTest.GetBlock( idBlock ) )
        for onPoints in [ True, False ]:
            infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSetRef, onPoints )
            dataTest: Union[ vtkPointData, vtkCellData ]
            dataTest = datasetTest.GetPointData() if onPoints else datasetTest.GetCellData()

            for attributeName in infoAttributes:
                attributeTest: int = dataTest.HasArray( attributeName )
                assert attributeTest == 1


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


@pytest.mark.parametrize( "attributeName, onPoints", [
    ( "newAttribute", False ),
    ( "newAttribute", True ),
    ( "PORO", True ), # Partial attribute on cells already exist
    ( "GLOBAL_IDS_CELLS", True ), # Global attribute on cells already exist
] )
def test_createConstantAttributeMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onPoints: bool,
) -> None:
    """Test creation of constant attribute in multiblock dataset."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    values: list[ float ] = [ np.nan ]
    assert arrayModifiers.createConstantAttributeMultiBlock( multiBlockDataSetTest, values, attributeName, onPoints=onPoints )

    nbBlock = multiBlockDataSetTest.GetNumberOfBlocks()
    for idBlock in range( nbBlock ):
        datasetTest: vtkDataSet = cast( vtkDataSet, multiBlockDataSetTest.GetBlock( idBlock ) )
        dataTest: Union[ vtkPointData, vtkCellData ]
        if onPoints:
            dataTest = datasetTest.GetPointData()
        else:
            dataTest = datasetTest.GetCellData()

        attributeTest: int = dataTest.HasArray( attributeName )
        assert attributeTest == 1


@pytest.mark.parametrize( "listValues, componentNames, componentNamesTest, onPoints, vtkDataType, vtkDataTypeTest, attributeName", [
    # Test attribute names. 
    ## Test with an attributeName already existing on cells data.
    ( [ np.float32( 42 ) ], (), (), True, VTK_FLOAT, VTK_FLOAT, "PORO" ),
    ## Test with a new attributeName on cells and on points.
    ( [ np.float32( 42 ) ], (), (), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
    ( [ np.float32( 42 ) ], (), (), False, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
    # Test the number of components and their names.
    ( [ np.float32( 42 ) ], ( "X" ), (), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
    ( [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
    ( [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
    ( [ np.float32( 42 ), np.float32( 42 ) ], (), ( "Component0", "Component1" ), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
    # Test the type of the values.
    ## With numpy scalar type.
    ( [ np.int8( 42 ) ], (), (), True, None, VTK_SIGNED_CHAR, "newAttribute" ),
    ( [ np.int8( 42 ) ], (), (), True, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "newAttribute" ),
    ( [ np.int16( 42 ) ], (), (), True, None, VTK_SHORT, "newAttribute" ),
    ( [ np.int16( 42 ) ], (), (), True, VTK_SHORT, VTK_SHORT, "newAttribute" ),
    ( [ np.int32( 42 ) ], (), (), True, None, VTK_INT, "newAttribute" ),
    ( [ np.int32( 42 ) ], (), (), True, VTK_INT, VTK_INT, "newAttribute" ),
    ( [ np.int64( 42 ) ], (), (), True, None, VTK_LONG_LONG, "newAttribute" ),
    ( [ np.int64( 42 ) ], (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
    ( [ np.uint8( 42 ) ], (), (), True, None, VTK_UNSIGNED_CHAR, "newAttribute" ),
    ( [ np.uint8( 42 ) ], (), (), True, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "newAttribute" ),
    ( [ np.uint16( 42 ) ], (), (), True, None, VTK_UNSIGNED_SHORT, "newAttribute" ),
    ( [ np.uint16( 42 ) ], (), (), True, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "newAttribute" ),
    ( [ np.uint32( 42 ) ], (), (), True, None, VTK_UNSIGNED_INT, "newAttribute" ),
    ( [ np.uint32( 42 ) ], (), (), True, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "newAttribute" ),
    ( [ np.uint64( 42 ) ], (), (), True, None, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
    ( [ np.uint64( 42 ) ], (), (), True, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
    ( [ np.float32( 42 ) ], (), (), True, None, VTK_FLOAT, "newAttribute" ),
    ( [ np.float64( 42 ) ], (), (), True, None, VTK_DOUBLE, "newAttribute" ),
    ( [ np.float64( 42 ) ], (), (), True, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
    ## With python scalar type.
    ( [ 42 ], (), (), True, None, VTK_LONG_LONG, "newAttribute" ),
    ( [ 42 ], (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
    ( [ 42. ], (), (), True, None, VTK_DOUBLE, "newAttribute" ),
    ( [ 42. ], (), (), True, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
] )
def test_createConstantAttributeDataSet(
    dataSetTest: vtkDataSet,
    listValues: list[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    onPoints: bool,
    vtkDataType: Union[ int, Any ],
    vtkDataTypeTest: int,
    attributeName: str,
) -> None:
    """Test constant attribute creation in dataset."""
    # Get the dataSet from a vtu.
    dataSet: vtkDataSet = dataSetTest( "dataset" )

    # Create the new constant attribute in the dataSet.
    assert arrayModifiers.createConstantAttributeDataSet( dataSet, listValues, attributeName, componentNames, onPoints, vtkDataType )

    # Get the new attribute to check its properties.
    data: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if onPoints:
        data = dataSet.GetPointData()
        nbElements = dataSet.GetNumberOfPoints()
    else:
        data = dataSet.GetCellData()
        nbElements = dataSet.GetNumberOfCells()
    createdAttribute: vtkDataArray = data.GetArray( attributeName )

    # Test the number of components and their names if multiple.
    nbComponentsTest: int = len( listValues )
    nbComponentsCreated: int = createdAttribute.GetNumberOfComponents()
    assert nbComponentsCreated == nbComponentsTest
    if nbComponentsTest > 1:
        componentNamesCreated: tuple[ str, ...] = tuple(
            createdAttribute.GetComponentName( i ) for i in range( nbComponentsCreated ) )
        assert componentNamesCreated, componentNamesTest

    # Test values and their types.
    ## Create the constant array test from values in the list values.
    npArrayTest: npt.NDArray[ Any ]
    if len( listValues ) > 1:
        npArrayTest = np.array( [ listValues for _ in range( nbElements ) ] )
    else:
        npArrayTest = np.array( [ listValues[ 0 ] for _ in range( nbElements ) ] )

    npArrayCreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( createdAttribute )
    assert ( npArrayCreated == npArrayTest ).all()
    assert npArrayCreated.dtype == npArrayTest.dtype

    vtkDataTypeCreated: int = createdAttribute.GetDataType()
    assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize( "componentNames, componentNamesTest, onPoints, vtkDataType, vtkDataTypeTest, valueType, attributeName", [
    # Test attribute names. 
    ## Test with an attributeName already existing on cells data.
    ( (), (), True, VTK_FLOAT, VTK_FLOAT, "float32", "PORO" ),
    ## Test with a new attributeName on cells and on points.
    ( (), (), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
    ( (), (), False, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
    # Test the number of components and their names.
    ( ( "X" ), (), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
    ( (), ( "Component0", "Component1" ), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
    # Test the type of the values.
    ## With numpy scalar type.
    ( (), (), True, None, VTK_SIGNED_CHAR, "int8", "newAttribute" ),
    ( (), (), True, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "int8", "newAttribute" ),
    ( (), (), True, None, VTK_SHORT, "int16", "newAttribute" ),
    ( (), (), True, VTK_SHORT, VTK_SHORT, "int16", "newAttribute" ),
    ( (), (), True, None, VTK_INT, "int32", "newAttribute" ),
    ( (), (), True, VTK_INT, VTK_INT, "int32", "newAttribute" ),
    ( (), (), True, None, VTK_LONG_LONG, "int64", "newAttribute" ),
    ( (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64", "newAttribute" ),
    ( (), (), True, None, VTK_UNSIGNED_CHAR, "uint8", "newAttribute" ),
    ( (), (), True, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "uint8", "newAttribute" ),
    ( (), (), True, None, VTK_UNSIGNED_SHORT, "uint16", "newAttribute" ),
    ( (), (), True, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "uint16", "newAttribute" ),
    ( (), (), True, None, VTK_UNSIGNED_INT, "uint32", "newAttribute" ),
    ( (), (), True, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "uint32", "newAttribute" ),
    ( (), (), True, None, VTK_UNSIGNED_LONG_LONG, "uint64", "newAttribute" ),
    ( (), (), True, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "uint64", "newAttribute" ),
    ( (), (), True, None, VTK_FLOAT, "float32", "newAttribute" ),
    ( (), (), True, None, VTK_DOUBLE, "float64", "newAttribute" ),
    ( (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float64", "newAttribute" ),
    ## With python scalar type.
    ( (), (), True, None, VTK_LONG_LONG, "int", "newAttribute" ),
    ( (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "int", "newAttribute" ),
    ( (), (), True, None, VTK_DOUBLE, "float", "newAttribute" ),
    ( (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float", "newAttribute" ),
] )
def test_createAttribute(
    dataSetTest: vtkDataSet,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    onPoints: bool,
    vtkDataType: int,
    vtkDataTypeTest: int,
    valueType: str,
    attributeName: str,
) -> None:
    """Test creation of dataset in dataset from given array."""
    # Get the dataSet from a vtu.
    dataSet: vtkDataSet = dataSetTest( "dataset" )

    # Get a array with random values of a given type.
    nbComponentsTest: int = 1 if len( componentNamesTest ) == 0 else len( componentNamesTest )
    nbElementsTest: int = dataSet.GetNumberOfPoints() if onPoints else dataSet.GetNumberOfCells()
    npArrayTest: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( nbComponentsTest, nbElementsTest, valueType )

    # Create the new attribute in the dataSet.
    assert arrayModifiers.createAttribute( dataSet, npArrayTest, attributeName, componentNames, onPoints, vtkDataType )

    # Get the new attribute to check its properties.
    data: Union[ vtkPointData, vtkCellData ]
    data = dataSet.GetPointData() if onPoints else dataSet.GetCellData()
    createdAttribute: vtkDataArray = data.GetArray( attributeName )

    # Test the number of components and their names if multiple.
    nbComponentsCreated: int = createdAttribute.GetNumberOfComponents()
    assert nbComponentsCreated == nbComponentsTest
    if nbComponentsTest > 1:
        componentsNamesCreated: tuple[ str, ...] = tuple(
            createdAttribute.GetComponentName( i ) for i in range( nbComponentsCreated ) )
        assert componentsNamesCreated == componentNamesTest

    # Test values and their types.
    npArrayCreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( createdAttribute )
    assert ( npArrayCreated == npArrayTest ).all()
    assert npArrayCreated.dtype == npArrayTest.dtype

    vtkDataTypeCreated: int = createdAttribute.GetDataType()
    assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo, onPoints, idBlock", [
    ( "PORO", "POROTo", False, 0 ),
    ( "CellAttribute", "CellAttributeTo", False, 0 ),
    ( "FAULT", "FAULTTo", False, 0 ),
    ( "PointAttribute", "PointAttributeTo", True, 0 ),
    ( "collocated_nodes", "collocated_nodesTo", True, 1 ),
] )
def test_copyAttribute( dataSetTest: vtkMultiBlockDataSet, attributeNameFrom: str, attributeNameTo: str, onPoints: bool,
                        idBlock: int ) -> None:
    """Test copy of cell attribute from one multiblock to another."""
    objectFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    objectTo: vtkMultiBlockDataSet = dataSetTest( "emptymultiblock" )

    arrayModifiers.copyAttribute( objectFrom, objectTo, attributeNameFrom, attributeNameTo, onPoints )

    blockFrom: vtkDataSet = cast( vtkDataSet, objectFrom.GetBlock( idBlock ) )
    blockTo: vtkDataSet = cast( vtkDataSet, objectTo.GetBlock( idBlock ) )

    dataFrom: Union[ vtkPointData, vtkCellData ]
    dataTo: Union[ vtkPointData, vtkCellData ]
    if onPoints:
        dataFrom = blockFrom.GetPointData()
        dataTo = blockTo.GetPointData()
    else:
        dataFrom = blockFrom.GetCellData()
        dataTo = blockTo.GetCellData()

    attributeFrom: vtkDataArray = dataFrom.GetArray( attributeNameFrom )
    attributeTo: vtkDataArray = dataTo.GetArray( attributeNameTo )

    nbComponentsFrom: int = attributeFrom.GetNumberOfComponents()
    nbComponentsTo: int = attributeTo.GetNumberOfComponents()
    assert nbComponentsFrom == nbComponentsTo

    if nbComponentsFrom > 1:
        componentsNamesFrom: tuple[ str, ...] = tuple(
            attributeFrom.GetComponentName( i ) for i in range( nbComponentsFrom ) )
        componentsNamesTo: tuple[ str,
                                  ...] = tuple( attributeTo.GetComponentName( i ) for i in range( nbComponentsTo ) )
        assert componentsNamesFrom == componentsNamesTo

    npArrayFrom: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeFrom )
    npArrayTo: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeTo )
    assert ( npArrayFrom == npArrayTo ).all()
    assert npArrayFrom.dtype == npArrayTo.dtype

    vtkDataTypeFrom: int = attributeFrom.GetDataType()
    vtkDataTypeTo: int = attributeTo.GetDataType()
    assert vtkDataTypeFrom == vtkDataTypeTo


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo, onPoints", [
    ( "CellAttribute", "CellAttributeTo", False ),
    ( "PointAttribute", "PointAttributeTo", True ),
] )
def test_copyAttributeDataSet( dataSetTest: vtkDataSet, attributeNameFrom: str, attributeNameTo: str,
                               onPoints: bool ) -> None:
    """Test copy of an attribute from one dataset to another."""
    objectFrom: vtkDataSet = dataSetTest( "dataset" )
    objectTo: vtkDataSet = dataSetTest( "emptydataset" )

    arrayModifiers.copyAttributeDataSet( objectFrom, objectTo, attributeNameFrom, attributeNameTo, onPoints )

    dataFrom: Union[ vtkPointData, vtkCellData ]
    dataTo: Union[ vtkPointData, vtkCellData ]
    if onPoints:
        dataFrom = objectFrom.GetPointData()
        dataTo = objectTo.GetPointData()
    else:
        dataFrom = objectFrom.GetCellData()
        dataTo = objectTo.GetCellData()

    attributeFrom: vtkDataArray = dataFrom.GetArray( attributeNameFrom )
    attributeTo: vtkDataArray = dataTo.GetArray( attributeNameTo )

    nbComponentsFrom: int = attributeFrom.GetNumberOfComponents()
    nbComponentsTo: int = attributeTo.GetNumberOfComponents()
    assert nbComponentsFrom == nbComponentsTo

    if nbComponentsFrom > 1:
        componentsNamesFrom: tuple[ str, ...] = tuple(
            attributeFrom.GetComponentName( i ) for i in range( nbComponentsFrom ) )
        componentsNamesTo: tuple[ str,
                                  ...] = tuple( attributeTo.GetComponentName( i ) for i in range( nbComponentsTo ) )
        assert componentsNamesFrom == componentsNamesTo

    vtkDataTypeFrom: int = attributeFrom.GetDataType()
    vtkDataTypeTo: int = attributeTo.GetDataType()
    assert vtkDataTypeFrom == vtkDataTypeTo

    npArrayFrom: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeFrom )
    npArrayTo: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeTo )
    assert ( npArrayFrom == npArrayTo ).all()
    assert npArrayFrom.dtype == npArrayTo.dtype


@pytest.mark.parametrize( "attributeName, onPoints", [
    ( "CellAttribute", False ),
    ( "PointAttribute", True ),
] )
def test_renameAttributeMultiblock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onPoints: bool,
) -> None:
    """Test renaming attribute in a multiblock dataset."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute(
        vtkMultiBlockDataSetTest,
        attributeName,
        newAttributeName,
        onPoints,
    )
    block: vtkDataSet = cast( vtkDataSet, vtkMultiBlockDataSetTest.GetBlock( 0 ) )
    data: Union[ vtkPointData, vtkCellData ]
    if onPoints:
        data = block.GetPointData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1

    else:
        data = block.GetCellData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1


@pytest.mark.parametrize( "attributeName, onPoints", [ ( "CellAttribute", False ), ( "PointAttribute", True ) ] )
def test_renameAttributeDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    onPoints: bool,
) -> None:
    """Test renaming an attribute in a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute( object=vtkDataSetTest,
                                    attributeName=attributeName,
                                    newAttributeName=newAttributeName,
                                    onPoints=onPoints )
    if onPoints:
        assert vtkDataSetTest.GetPointData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetPointData().HasArray( newAttributeName ) == 1

    else:
        assert vtkDataSetTest.GetCellData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetCellData().HasArray( newAttributeName ) == 1
