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
    VTK_CHAR, VTK_DOUBLE, VTK_FLOAT, VTK_INT, VTK_UNSIGNED_INT, VTK_LONG_LONG, VTK_ID_TYPE,
)

# Informations :
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
        assert componentNamesRef == componentNamesTest

        npArrayFillRef = np.array( [ [ valueRef for _ in range( nbComponentsRef ) ] for _ in range( nbElements ) ] )
    else:
        npArrayFillRef = np.array( [ valueRef for _ in range( nbElements ) ] )

    npArrayFillTest: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeFillTest )
    assert valueTypeRef == npArrayFillTest.dtype

    if np.isnan( valueRef ):
        assert np.isnan( npArrayFillRef ).all()
    else:
        assert ( npArrayFillRef == npArrayFillTest ).all()

    vtkDataTypeTest: int = attributeFillTest.GetDataType()
    assert vtkDataTypeRef == vtkDataTypeTest


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
    MultiBlockDataSetRef: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    MultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    arrayModifiers.fillAllPartialAttributes( MultiBlockDataSetTest, value )

    nbBlock = MultiBlockDataSetRef.GetNumberOfBlocks()
    for idBlock in range( nbBlock ):
        datasetTest: vtkDataSet = cast( vtkDataSet, MultiBlockDataSetTest.GetBlock( idBlock ) )
        for onPoints in [ True, False ]:
            infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( MultiBlockDataSetRef, onPoints )
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


@pytest.mark.parametrize( "attributeName, isNewOnBlock, onPoints", [
    ( "newAttribute", ( True, True ), False ),
    ( "newAttribute", ( True, True ), True ),
    ( "PORO", ( True, True ), True ),
    ( "PORO", ( False, True ), False ),
    ( "PointAttribute", ( False, True ), True ),
    ( "PointAttribute", ( True, True ), False ),
    ( "collocated_nodes", ( True, False ), True ),
    ( "collocated_nodes", ( True, True ), False ),
] )
def test_createConstantAttributeMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    isNewOnBlock: tuple[ bool, ...],
    onPoints: bool,
) -> None:
    """Test creation of constant attribute in multiblock dataset."""
    MultiBlockDataSetRef: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    MultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    values: list[ float ] = [ np.nan ]
    arrayModifiers.createConstantAttributeMultiBlock( MultiBlockDataSetTest, values, attributeName, onPoints=onPoints )

    nbBlock = MultiBlockDataSetRef.GetNumberOfBlocks()
    for idBlock in range( nbBlock ):
        datasetRef: vtkDataSet = cast( vtkDataSet, MultiBlockDataSetRef.GetBlock( idBlock ) )
        datasetTest: vtkDataSet = cast( vtkDataSet, MultiBlockDataSetTest.GetBlock( idBlock ) )
        dataRef: Union[ vtkPointData, vtkCellData ]
        dataTest: Union[ vtkPointData, vtkCellData ]
        if onPoints:
            dataRef = datasetRef.GetPointData()
            dataTest = datasetTest.GetPointData()
        else:
            dataRef = datasetRef.GetCellData()
            dataTest = datasetTest.GetCellData()

        attributeRef: int = dataRef.HasArray( attributeName )
        attributeTest: int = dataTest.HasArray( attributeName )
        if isNewOnBlock[ idBlock ]:
            assert attributeRef != attributeTest
        else:
            assert attributeRef == attributeTest


@pytest.mark.parametrize(
    "values, componentNames, componentNamesTest, onPoints, vtkDataType, vtkDataTypeTest, valueType", [
        ( [ np.float32( 42 ) ], (), (), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ) ], (), (), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ) ], (), (), True, None, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ) ], (), (), False, None, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], (),
          ( "Component0", "Component1" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], (),
          ( "Component0", "Component1" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], (),
          ( "Component0", "Component1" ), True, None, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], (),
          ( "Component0", "Component1" ), False, None, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_FLOAT, "float32" ),
        ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_FLOAT, "float32" ),
        ( [ np.float64( 42 ) ], (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ) ], (), (), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ) ], (), (), True, None, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ) ], (), (), False, None, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], (),
          ( "Component0", "Component1" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], (),
          ( "Component0", "Component1" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], (),
          ( "Component0", "Component1" ), True, None, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], (),
          ( "Component0", "Component1" ), False, None, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ),
          ( "X", "Y" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_DOUBLE, "float64" ),
        ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_DOUBLE, "float64" ),
        ( [ np.int32( 42 ) ], (), (), True, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ) ], (), (), False, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ) ], (), (), True, None, VTK_INT, "int32" ),
        ( [ np.int32( 42 ) ], (), (), False, None, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], (), ( "Component0", "Component1" ), True, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], (), ( "Component0", "Component1" ), False, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], (), ( "Component0", "Component1" ), True, None, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], (), ( "Component0", "Component1" ), False, None, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_INT, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_INT, "int32" ),
        ( [ np.int32( 42 ), np.int32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_INT, "int32" ),
        ( [ np.int64( 42 ) ], (), (), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ) ], (), (), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ) ], (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ) ], (), (), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ) ], (), (), True, None, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ) ], (), (), False, None, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], (),
          ( "Component0", "Component1" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], (),
          ( "Component0", "Component1" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], (),
          ( "Component0", "Component1" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], (),
          ( "Component0", "Component1" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), True, None, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), False, None, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ),
          ( "X", "Y" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_LONG_LONG, "int64" ),
        ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_LONG_LONG, "int64" ),
    ] )
def test_createConstantAttributeDataSet(
    dataSetTest: vtkDataSet,
    values: list[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    onPoints: bool,
    vtkDataType: Union[ int, Any ],
    vtkDataTypeTest: int,
    valueType: str,
) -> None:
    """Test constant attribute creation in dataset."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )
    attributeName: str = "newAttributedataset"
    arrayModifiers.createConstantAttributeDataSet( dataSet, values, attributeName, componentNames, onPoints,
                                                   vtkDataType )

    data: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if onPoints:
        data = dataSet.GetPointData()
        nbElements = dataSet.GetNumberOfPoints()
    else:
        data = dataSet.GetCellData()
        nbElements = dataSet.GetNumberOfCells()

    createdAttribute: vtkDataArray = data.GetArray( attributeName )

    nbComponents: int = len( values )
    nbComponentsCreated: int = createdAttribute.GetNumberOfComponents()
    assert nbComponents == nbComponentsCreated

    npArray: npt.NDArray[ Any ]
    if nbComponents > 1:
        componentNamesCreated: tuple[ str, ...] = tuple(
            createdAttribute.GetComponentName( i ) for i in range( nbComponents ) )
        assert componentNamesTest == componentNamesCreated

        npArray = np.array( [ values for _ in range( nbElements ) ] )
    else:
        npArray = np.array( [ values[ 0 ] for _ in range( nbElements ) ] )

    npArraycreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( createdAttribute )
    assert ( npArray == npArraycreated ).all()
    assert valueType == npArraycreated.dtype

    vtkDataTypeCreated: int = createdAttribute.GetDataType()
    assert vtkDataTypeTest == vtkDataTypeCreated


@pytest.mark.parametrize( "componentNames, componentNamesTest, onPoints, vtkDataType, vtkDataTypeTest, valueType", [
    ( (), (), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( (), (), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( (), (), True, None, VTK_FLOAT, "float32" ),
    ( (), (), False, None, VTK_FLOAT, "float32" ),
    ( (), ( "Component0", "Component1" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( (), ( "Component0", "Component1" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( (), ( "Component0", "Component1" ), True, None, VTK_FLOAT, "float32" ),
    ( (), ( "Component0", "Component1" ), False, None, VTK_FLOAT, "float32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_FLOAT, "float32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_FLOAT, "float32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_FLOAT, "float32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_FLOAT, "float32" ),
    ( (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( (), (), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( (), (), True, None, VTK_DOUBLE, "float64" ),
    ( (), (), False, None, VTK_DOUBLE, "float64" ),
    ( (), ( "Component0", "Component1" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( (), ( "Component0", "Component1" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( (), ( "Component0", "Component1" ), True, None, VTK_DOUBLE, "float64" ),
    ( (), ( "Component0", "Component1" ), False, None, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_DOUBLE, "float64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_DOUBLE, "float64" ),
    ( (), (), True, VTK_INT, VTK_INT, "int32" ),
    ( (), (), False, VTK_INT, VTK_INT, "int32" ),
    ( (), (), True, None, VTK_INT, "int32" ),
    ( (), (), False, None, VTK_INT, "int32" ),
    ( (), ( "Component0", "Component1" ), True, VTK_INT, VTK_INT, "int32" ),
    ( (), ( "Component0", "Component1" ), False, VTK_INT, VTK_INT, "int32" ),
    ( (), ( "Component0", "Component1" ), True, None, VTK_INT, "int32" ),
    ( (), ( "Component0", "Component1" ), False, None, VTK_INT, "int32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, VTK_INT, VTK_INT, "int32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, VTK_INT, VTK_INT, "int32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_INT, "int32" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_INT, "int32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_INT, VTK_INT, "int32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_INT, VTK_INT, "int32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_INT, "int32" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_INT, "int32" ),
    ( (), (), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( (), (), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( (), (), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( (), (), True, None, VTK_LONG_LONG, "int64" ),
    ( (), (), False, None, VTK_LONG_LONG, "int64" ),
    ( (), ( "Component0", "Component1" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( (), ( "Component0", "Component1" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( (), ( "Component0", "Component1" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( (), ( "Component0", "Component1" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( (), ( "Component0", "Component1" ), True, None, VTK_LONG_LONG, "int64" ),
    ( (), ( "Component0", "Component1" ), False, None, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_LONG_LONG, "int64" ),
    ( ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_LONG_LONG, "int64" ),
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
) -> None:
    """Test creation of dataset in dataset from given array."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )
    attributeName: str = "AttributeName"

    nbComponents: int = ( 1 if len( componentNamesTest ) == 0 else len( componentNamesTest ) )
    nbElements: int = ( dataSet.GetNumberOfPoints() if onPoints else dataSet.GetNumberOfCells() )

    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( nbComponents, nbElements, valueType )
    arrayModifiers.createAttribute( dataSet, npArray, attributeName, componentNames, onPoints, vtkDataType )

    data: Union[ vtkPointData, vtkCellData ]
    data = dataSet.GetPointData() if onPoints else dataSet.GetCellData()

    createdAttribute: vtkDataArray = data.GetArray( attributeName )
    nbComponentsCreated: int = createdAttribute.GetNumberOfComponents()
    assert nbComponents == nbComponentsCreated
    if nbComponents > 1:
        componentsNamesCreated: tuple[ str, ...] = tuple(
            createdAttribute.GetComponentName( i ) for i in range( nbComponents ) )
        assert componentNamesTest == componentsNamesCreated

    npArraycreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( createdAttribute )
    assert ( npArray == npArraycreated ).all()
    assert valueType == npArraycreated.dtype

    vtkDataTypeCreated: int = createdAttribute.GetDataType()
    assert vtkDataTypeTest == vtkDataTypeCreated


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


@pytest.mark.parametrize( "attributeName, onpoints", [
    ( "CellAttribute", False ),
    ( "PointAttribute", True ),
] )
def test_renameAttributeMultiblock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onpoints: bool,
) -> None:
    """Test renaming attribute in a multiblock dataset."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute(
        vtkMultiBlockDataSetTest,
        attributeName,
        newAttributeName,
        onpoints,
    )
    block: vtkDataSet = cast( vtkDataSet, vtkMultiBlockDataSetTest.GetBlock( 0 ) )
    data: Union[ vtkPointData, vtkCellData ]
    if onpoints:
        data = block.GetPointData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1

    else:
        data = block.GetCellData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1


@pytest.mark.parametrize( "attributeName, onpoints", [ ( "CellAttribute", False ), ( "PointAttribute", True ) ] )
def test_renameAttributeDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    onpoints: bool,
) -> None:
    """Test renaming an attribute in a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute( object=vtkDataSetTest,
                                    attributeName=attributeName,
                                    newAttributeName=newAttributeName,
                                    onPoints=onpoints )
    if onpoints:
        assert vtkDataSetTest.GetPointData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetPointData().HasArray( newAttributeName ) == 1

    else:
        assert vtkDataSetTest.GetCellData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetCellData().HasArray( newAttributeName ) == 1
