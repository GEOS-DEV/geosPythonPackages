# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, Tuple, cast

import numpy as np
import numpy.typing as npt

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonCore import vtkDataArray, vtkDoubleArray
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkDataObjectTreeIterator, vtkPointData,
                                            vtkCellData )

from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataWriter, vtkXMLUnstructuredGridWriter

from vtk import (  # type: ignore[import-untyped]
    VTK_CHAR, VTK_DOUBLE, VTK_FLOAT, VTK_INT, VTK_UNSIGNED_INT, VTK_LONG_LONG, VTK_ID_TYPE,
)

# Information :
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


@pytest.mark.parametrize( "attributeName, nbComponents, onpoints, value_test", [
    ( "CellAttribute", 3, False, np.nan ),
    ( "PointAttribute", 3, True, np.nan ),
    ( "CELL_MARKERS", 1, False, np.nan ),
    ( "PORO", 1, False, np.nan ),
    ( "CellAttribute", 3, False, 2. ),
    ( "PointAttribute", 3, True, 2. ),
    ( "CELL_MARKERS", 1, False, 2. ),
    ( "PORO", 1, False, 2. ),
] )
def test_fillPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    nbComponents: int,
    onpoints: bool,
    value_test: float,
) -> None:
    """Test filling a partial attribute from a multiblock with values."""
    vtkMultiBlockDataSetTestRef: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    arrayModifiers.fillPartialAttributes( vtkMultiBlockDataSetTest,
                                          attributeName,
                                          nbComponents,
                                          onPoints=onpoints,
                                          value=value_test )

    nbBlock: int = vtkMultiBlockDataSetTestRef.GetNumberOfBlocks()
    for block_id in range( nbBlock ):
        datasetRef: vtkDataSet = cast( vtkDataSet, vtkMultiBlockDataSetTestRef.GetBlock( block_id ) )
        dataset: vtkDataSet = cast( vtkDataSet, vtkMultiBlockDataSetTest.GetBlock( block_id ) )
        expected_array: npt.NDArray[ np.float64 ]
        array: npt.NDArray[ np.float64 ]
        if onpoints:
            array = vnp.vtk_to_numpy( dataset.GetPointData().GetArray( attributeName ) )
            if block_id == 0:
                expected_array = vnp.vtk_to_numpy( datasetRef.GetPointData().GetArray( attributeName ) )
            else:
                expected_array = np.array( [ [ value_test for i in range( nbComponents ) ] for _ in range( 212 ) ] )
        else:
            array = vnp.vtk_to_numpy( dataset.GetCellData().GetArray( attributeName ) )
            if block_id == 0:
                expected_array = vnp.vtk_to_numpy( datasetRef.GetCellData().GetArray( attributeName ) )
            else:
                expected_array = np.array( [ [ value_test for i in range( nbComponents ) ] for _ in range( 156 ) ] )

        if block_id == 0:
            assert ( array == expected_array ).all()
        else:
            if np.isnan( value_test ):
                assert np.all( np.isnan( array ) == np.isnan( expected_array ) )
            else:
                assert ( array == expected_array ).all()



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


@pytest.mark.parametrize( "onpoints, elementSize", [
    ( False, ( 1740, 156 ) ),
    ( True, ( 4092, 212 ) ),
] )
def test_createConstantAttributeMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    onpoints: bool,
    elementSize: Tuple[ int, ...],
) -> None:
    """Test creation of constant attribute in multiblock dataset."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    attributeName: str = "testAttributemultiblock"
    values: tuple[ float, float, float ] = ( 12.4, 10, 40.0 )
    componentNames: tuple[ str, str, str ] = ( "X", "Y", "Z" )
    arrayModifiers.createConstantAttributeMultiBlock( vtkMultiBlockDataSetTest, values, attributeName, componentNames,
                                                      onpoints )

    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( vtkMultiBlockDataSetTest )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataset: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        data: Union[ vtkPointData, vtkCellData ]
        if onpoints:
            data = dataset.GetPointData()
        else:
            data = dataset.GetCellData()
        createdAttribute: vtkDoubleArray = data.GetArray( attributeName )
        cnames: Tuple[ str, ...] = tuple( createdAttribute.GetComponentName( i ) for i in range( 3 ) )

        assert ( vnp.vtk_to_numpy( createdAttribute ) == np.full( ( elementSize[ iter.GetCurrentFlatIndex() - 1 ], 3 ),
                                                                  fill_value=values ) ).all()
        assert cnames == componentNames
        assert ( vnp.vtk_to_numpy( createdAttribute ).dtype == "float64" )

        iter.GoToNextItem()


@pytest.mark.parametrize( "values, componentNames, componentNamesTest, onPoints, vtkArrayType, vtkArrayTypeTest, valueType", [ 
    ( [ np.float32( 42 ) ], (), (), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ) ], (), (), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ) ], (), (), True, None, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ) ], (), (), False, None, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], (), ( "Component0", "Component1" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], (), ( "Component0", "Component1" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], (), ( "Component0", "Component1" ), True, None, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], (), ( "Component0", "Component1" ), False, None, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_FLOAT, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_FLOAT, "float32" ),
    ( [ np.float32( 42 ), np.float32( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_FLOAT, "float32" ),
    ( [ np.float64( 42 ) ], (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ) ], (), (), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ) ], (), (), True, None, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ) ], (), (), False, None, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], (), ( "Component0", "Component1" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], (), ( "Component0", "Component1" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], (), ( "Component0", "Component1" ), True, None, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], (), ( "Component0", "Component1" ), False, None, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
    ( [ np.float64( 42 ), np.float64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_DOUBLE, VTK_DOUBLE, "float64" ),
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
    ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), True, None, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], (), ( "Component0", "Component1" ), False, None, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), True, None, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y" ), ( "X", "Y" ), False, None, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_ID_TYPE, VTK_ID_TYPE, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, VTK_LONG_LONG, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), True, None, VTK_LONG_LONG, "int64" ),
    ( [ np.int64( 42 ), np.int64( 22 ) ], ( "X", "Y", "Z" ), ( "X", "Y" ), False, None, VTK_LONG_LONG, "int64" ),
] )
def test_createConstantAttributeDataSet(
    dataSetTest: vtkDataSet,
    values: list[ any ],
    componentNames: Tuple[ str, ... ],
    componentNamesTest: Tuple[ str, ... ],
    onPoints: bool,
    vtkArrayType: Union[ int, any ],
    vtkArrayTypeTest: int,
    valueType: str,
) -> None:
    """Test constant attribute creation in dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    attributeName: str = "newAttributedataset"
    arrayModifiers.createConstantAttributeDataSet( vtkDataSetTest, values, attributeName, componentNames, onPoints, vtkArrayType )

    data: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if onPoints:
        data = vtkDataSetTest.GetPointData()
        nbElements = vtkDataSetTest.GetNumberOfPoints()
    else:
        data = vtkDataSetTest.GetCellData()
        nbElements = vtkDataSetTest.GetNumberOfCells()

    createdAttribute: vtkDataArray = data.GetArray( attributeName )

    nbComponents: int = len( values )
    nbComponentsCreated: int = createdAttribute.GetNumberOfComponents()
    assert nbComponents == nbComponentsCreated

    npArray: npt.NDArray[ any ]
    if nbComponents > 1:
        componentNamesCreated: Tuple[ str, ...] = tuple( createdAttribute.GetComponentName( i ) for i in range( nbComponents ) )
        assert componentNamesTest == componentNamesCreated
        npArray = np.array( [ [ val for val in values  ] for _ in range( nbElements ) ] )
    else:
        npArray = np.array( [ values[ 0 ] for _ in range( nbElements ) ] )

    npArraycreated: npt.NDArray[ any ] = vnp.vtk_to_numpy( createdAttribute )
    assert ( npArray == npArraycreated ).all()
    assert valueType == npArraycreated.dtype

    vtkArrayTypeCreated: int = createdAttribute.GetDataType()
    assert vtkArrayTypeTest == vtkArrayTypeCreated


@pytest.mark.parametrize( "componentNames, componentNamesTest, onPoints, vtkArrayType, vtkArrayTypeTest, valueType", [
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
    getArrayWithSpeTypeValue: npt.NDArray[ any ],
    componentNames: tuple[ str, ... ],
    componentNamesTest: tuple[ str, ... ],
    onPoints: bool,
    vtkArrayType: int,
    vtkArrayTypeTest: int,
    valueType: str,
) -> None:
    """Test creation of dataset in dataset from given array."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    attributeName: str = "AttributeName"
    nbComponents: int = ( 1 if len( componentNamesTest ) == 0 else len( componentNamesTest ) )
    nbElements: int = ( vtkDataSetTest.GetNumberOfPoints() if onPoints else vtkDataSetTest.GetNumberOfCells() )
    npArray: npt.NDArray[ any ] = getArrayWithSpeTypeValue( nbComponents, nbElements, valueType )
    arrayModifiers.createAttribute( vtkDataSetTest, npArray, attributeName, componentNames, onPoints, vtkArrayType )

    data: Union[ vtkPointData, vtkCellData ]
    if onPoints:
        data = vtkDataSetTest.GetPointData()
    else:
        data = vtkDataSetTest.GetCellData()

    createdAttribute: vtkDataArray = data.GetArray( attributeName )

    nbComponentsCreated: int = createdAttribute.GetNumberOfComponents()
    assert nbComponents == nbComponentsCreated

    if nbComponents > 1:
        componentsNamesCreated: Tuple[ str, ...] = tuple( createdAttribute.GetComponentName( i ) for i in range( nbComponents ) )
        assert componentNamesTest == componentsNamesCreated
    
    npArraycreated: npt.NDArray[ any ] = vnp.vtk_to_numpy( createdAttribute )
    assert ( npArray == npArraycreated ).all()
    assert valueType == npArraycreated.dtype

    vtkArrayTypeCreated: int = createdAttribute.GetDataType()
    assert vtkArrayTypeTest == vtkArrayTypeCreated


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo, onPoints, idBlock", [
    ( "PORO", "POROTo", False, 0 ),
    ( "CellAttribute", "CellAttributeTo", False, 0 ),
    ( "FAULT", "FAULTTo", False, 0 ),
    ( "PointAttribute", "PointAttributeTo", True, 0 ),
    ( "collocated_nodes", "collocated_nodesTo", True, 1 ),
] )
def test_copyAttribute( dataSetTest: vtkMultiBlockDataSet, attributeNameFrom:str, attributeNameTo: str, onPoints: bool, idBlock: int ) -> None:
    """Test copy of cell attribute from one multiblock to another."""
    objectFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    objectTo: vtkMultiBlockDataSet = dataSetTest( "emptymultiblock" )

    arrayModifiers.copyAttribute( objectFrom, objectTo, attributeNameFrom, attributeNameTo, onPoints )

    blockIndex: int = idBlock
    blockFrom: vtkDataSet = cast( vtkDataSet, objectFrom.GetBlock( blockIndex ) )
    blockTo: vtkDataSet = cast( vtkDataSet, objectTo.GetBlock( blockIndex ) )

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
        componentsNamesFrom: Tuple[ str, ...] = tuple( attributeFrom.GetComponentName( i ) for i in range( nbComponentsFrom ) )
        componentsNamesTo: Tuple[ str, ...] = tuple( attributeTo.GetComponentName( i ) for i in range( nbComponentsTo ) )
        assert componentsNamesFrom == componentsNamesTo

    npArrayFrom: npt.NDArray[ any ] = vnp.vtk_to_numpy( attributeFrom )
    npArrayTo: npt.NDArray[ any ] = vnp.vtk_to_numpy(  attributeTo )
    assert ( npArrayFrom == npArrayTo ).all()
    assert npArrayFrom.dtype == npArrayTo.dtype

    vtkArrayTypeFrom: int = attributeFrom.GetDataType()
    vtkArrayTypeTo: int = attributeTo.GetDataType()
    assert vtkArrayTypeFrom == vtkArrayTypeTo


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo, onPoints", [
    ( "CellAttribute", "CellAttributeTo", False ),
    ( "PointAttribute", "PointAttributeTo", True ),
] )
def test_copyAttributeDataSet( dataSetTest: vtkDataSet, attributeNameFrom:str, attributeNameTo: str, onPoints: bool ) -> None:
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
        componentsNamesFrom: Tuple[ str, ...] = tuple( attributeFrom.GetComponentName( i ) for i in range( nbComponentsFrom ) )
        componentsNamesTo: Tuple[ str, ...] = tuple( attributeTo.GetComponentName( i ) for i in range( nbComponentsTo ) )
        assert componentsNamesFrom == componentsNamesTo

    vtkArrayTypeFrom: int = attributeFrom.GetDataType()
    vtkArrayTypeTo: int = attributeTo.GetDataType()
    assert vtkArrayTypeFrom == vtkArrayTypeTo

    npArrayFrom: npt.NDArray[ any ] = vnp.vtk_to_numpy( attributeFrom )
    npArrayTo: npt.NDArray[ any ] = vnp.vtk_to_numpy(  attributeTo )
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
