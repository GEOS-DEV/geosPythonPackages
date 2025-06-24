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

from vtk import (  # type: ignore[import-untyped]
    VTK_CHAR, VTK_DOUBLE, VTK_FLOAT, VTK_INT, VTK_UNSIGNED_INT,
)

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

        iter.GoToNextItem()


@pytest.mark.parametrize( "values, onpoints, elementSize", [
    ( ( 42, 58, -103 ), True, 4092 ),
    ( ( -42, -58, 103 ), False, 1740 ),
] )
def test_createConstantAttributeDataSet(
    dataSetTest: vtkDataSet,
    values: list[ float ],
    elementSize: int,
    onpoints: bool,
) -> None:
    """Test constant attribute creation in dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    componentNames: Tuple[ str, str, str ] = ( "XX", "YY", "ZZ" )
    attributeName: str = "newAttributedataset"
    arrayModifiers.createConstantAttributeDataSet( vtkDataSetTest, values, attributeName, componentNames, onpoints )

    data: Union[ vtkPointData, vtkCellData ]
    if onpoints:
        data = vtkDataSetTest.GetPointData()

    else:
        data = vtkDataSetTest.GetCellData()

    createdAttribute: vtkDoubleArray = data.GetArray( attributeName )
    cnames: Tuple[ str, ...] = tuple( createdAttribute.GetComponentName( i ) for i in range( 3 ) )

    assert ( vnp.vtk_to_numpy( createdAttribute ) == np.full( ( elementSize, 3 ), fill_value=values ) ).all()
    assert cnames == componentNames


@pytest.mark.parametrize( "onpoints, arrayTest, arrayExpected, arrayTypeTest", [
    ( True, 4092, "random_4092", VTK_DOUBLE ),
    ( False, 1740, "random_1740", VTK_DOUBLE ),
],
                          indirect=[ "arrayTest", "arrayExpected" ] )
def test_createAttribute(
    dataSetTest: vtkDataSet,
    arrayTest: npt.NDArray[ any ],
    arrayExpected: npt.NDArray[ any ],
    onpoints: bool,
    arrayTypeTest: int,
) -> None:
    """Test creation of dataset in dataset from given array."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    componentNames: tuple[ str, str, str ] = ( "XX", "YY", "ZZ" )
    attributeName: str = "AttributeName"

    arrayModifiers.createAttribute( vtkDataSetTest, arrayTest, attributeName, componentNames, onpoints, arrayTypeTest )

    data: Union[ vtkPointData, vtkCellData ]
    if onpoints:
        data = vtkDataSetTest.GetPointData()
    else:
        data = vtkDataSetTest.GetCellData()

    createdAttribute: vtkDataArray = data.GetArray( attributeName )
    cnames: Tuple[ str, ...] = tuple( createdAttribute.GetComponentName( i ) for i in range( 3 ) )
    arrayTypeObtained: int = createdAttribute.GetDataType()

    assert ( vnp.vtk_to_numpy( createdAttribute ) == arrayExpected ).all()
    assert cnames == componentNames
    assert arrayTypeTest == arrayTypeObtained


@pytest.mark.parametrize( "attributeFrom, attributeTo, onPoint, idBlock", [
    ( "PORO", "POROTo", False, 0 ),
    ( "CellAttribute", "CellAttributeTo", False, 0 ),
    ( "FAULT", "FAULTTo", False, 0 ),
    ( "PointAttribute", "PointAttributeTo", True, 0 ),
    ( "collocated_nodes", "collocated_nodesTo", True, 1 ),
] )
def test_copyAttribute( dataSetTest: vtkMultiBlockDataSet, attributeFrom:str, attributeTo: str, onPoint: bool, idBlock: int ) -> None:
    """Test copy of cell attribute from one multiblock to another."""
    objectFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    objectTo: vtkMultiBlockDataSet = dataSetTest( "emptymultiblock" )

    arrayModifiers.copyAttribute( objectFrom, objectTo, attributeFrom, attributeTo, onPoint )

    blockIndex: int = idBlock
    blockFrom: vtkDataSet = cast( vtkDataSet, objectFrom.GetBlock( blockIndex ) )
    blockTo: vtkDataSet = cast( vtkDataSet, objectTo.GetBlock( blockIndex ) )

    if onPoint:
        arrayFrom: npt.NDArray[ any ] = vnp.vtk_to_numpy( blockFrom.GetPointData().GetArray( attributeFrom ) )
        arrayTo: npt.NDArray[ any ] = vnp.vtk_to_numpy( blockTo.GetPointData().GetArray( attributeTo ) )

        typeArrayFrom: int = blockFrom.GetPointData().GetArray( attributeFrom ).GetDataType()
        typeArrayTo: int = blockTo.GetPointData().GetArray( attributeTo ).GetDataType()
    
    else:
        arrayFrom: npt.NDArray[ any ] = vnp.vtk_to_numpy( blockFrom.GetCellData().GetArray( attributeFrom ) )
        arrayTo: npt.NDArray[ any ] = vnp.vtk_to_numpy( blockTo.GetCellData().GetArray( attributeTo ) )

        typeArrayFrom: int = blockFrom.GetCellData().GetArray( attributeFrom ).GetDataType()
        typeArrayTo: int = blockTo.GetCellData().GetArray( attributeTo ).GetDataType()

    assert ( arrayFrom == arrayTo ).all()
    assert ( typeArrayFrom == typeArrayTo )


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo, onPoint", [
    ( "CellAttribute", "CellAttributeTo", False ),
    ( "PointAttribute", "PointAttributeTo", True ),
] )
def test_copyAttributeDataSet( dataSetTest: vtkDataSet, attributeNameFrom:str, attributeNameTo: str, onPoint: bool ) -> None:
    """Test copy of an attribute from one dataset to another."""
    objectFrom: vtkDataSet = dataSetTest( "dataset" )
    objectTo: vtkDataSet = dataSetTest( "emptydataset" )

    arrayModifiers.copyAttributeDataSet( objectFrom, objectTo, attributeNameFrom, attributeNameTo, onPoint )

    if onPoint:
        arrayFrom: npt.NDArray[ any ] = vnp.vtk_to_numpy( objectFrom.GetPointData().GetArray( attributeNameFrom ) )
        arrayTo: npt.NDArray[ any ] = vnp.vtk_to_numpy( objectTo.GetPointData().GetArray( attributeNameTo ) )

        typeArrayFrom: int = objectFrom.GetPointData().GetArray( attributeNameFrom ).GetDataType()
        typeArrayTo: int = objectTo.GetPointData().GetArray( attributeNameTo ).GetDataType()
    else:
        arrayFrom: npt.NDArray[ any ] = vnp.vtk_to_numpy( objectFrom.GetCellData().GetArray( attributeNameFrom ) )
        arrayTo: npt.NDArray[ any ] = vnp.vtk_to_numpy( objectTo.GetCellData().GetArray( attributeNameTo ) )

        typeArrayFrom: int = objectFrom.GetCellData().GetArray( attributeNameFrom ).GetDataType()
        typeArrayTo: int = objectTo.GetCellData().GetArray( attributeNameTo ).GetDataType()

    assert ( arrayFrom == arrayTo ).all()
    assert ( typeArrayFrom == typeArrayTo )


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
