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
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkDataObjectTreeIterator,
                                            vtkPointData, vtkCellData, vtkUnstructuredGrid )

from vtk import (  # type: ignore[import-untyped]
    VTK_CHAR, VTK_DOUBLE, VTK_FLOAT, VTK_INT, VTK_UNSIGNED_INT,
)

from geos.mesh.utils import filters as vtkFilters


@pytest.mark.parametrize( "attributeName, onpoints", [ ( "CellAttribute", False ), ( "PointAttribute", True ) ] )
def test_fillPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onpoints: bool,
) -> None:
    """Test filling a partial attribute from a multiblock with nan values."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    vtkFilters.fillPartialAttributes( vtkMultiBlockDataSetTest, attributeName, nbComponents=3, onPoints=onpoints )

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
        assert data.HasArray( attributeName ) == 1

        iter.GoToNextItem()


@pytest.mark.parametrize( "onpoints, expectedArrays", [
    ( True, ( "PointAttribute", "collocated_nodes" ) ),
    ( False, ( "CELL_MARKERS", "CellAttribute", "FAULT", "PERM", "PORO" ) ),
] )
def test_fillAllPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    onpoints: bool,
    expectedArrays: tuple[ str, ...],
) -> None:
    """Test filling all partial attributes from a multiblock with nan values."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    vtkFilters.fillAllPartialAttributes( vtkMultiBlockDataSetTest, onpoints )

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

        for attribute in expectedArrays:
            assert data.HasArray( attribute ) == 1

        iter.GoToNextItem()


# TODO: Add test for keepPartialAttributes = True when function fixed
@pytest.mark.parametrize(
    "keepPartialAttributes, expected_point_attributes, expected_cell_attributes",
    [
        ( False, ( "GLOBAL_IDS_POINTS", ), ( "GLOBAL_IDS_CELLS", ) ),
        # ( True, ( "GLOBAL_IDS_POINTS",  ), ( "GLOBAL_IDS_CELLS", "CELL_MARKERS", "FAULT", "PERM", "PORO" ) ),
    ] )
def test_mergeBlocks(
    dataSetTest: vtkMultiBlockDataSet,
    expected_point_attributes: tuple[ str, ...],
    expected_cell_attributes: tuple[ str, ...],
    keepPartialAttributes: bool,
) -> None:
    """Test the merging of a multiblock."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    dataset: vtkUnstructuredGrid = vtkFilters.mergeBlocks( vtkMultiBlockDataSetTest, keepPartialAttributes )

    assert dataset.GetCellData().GetNumberOfArrays() == len( expected_cell_attributes )
    for c_attribute in expected_cell_attributes:
        assert dataset.GetCellData().HasArray( c_attribute )

    assert dataset.GetPointData().GetNumberOfArrays() == len( expected_point_attributes )
    for p_attribute in expected_point_attributes:
        assert dataset.GetPointData().HasArray( p_attribute )


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
    newAttr: vtkDataArray = vtkFilters.createEmptyAttribute( attributeName, componentNames, dataType )

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
    vtkFilters.createConstantAttributeMultiBlock( vtkMultiBlockDataSetTest, values, attributeName, componentNames,
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
    vtkFilters.createConstantAttributeDataSet( vtkDataSetTest, values, attributeName, componentNames, onpoints )

    data: Union[ vtkPointData, vtkCellData ]
    if onpoints:
        data = vtkDataSetTest.GetPointData()

    else:
        data = vtkDataSetTest.GetCellData()

    createdAttribute: vtkDoubleArray = data.GetArray( attributeName )
    cnames: Tuple[ str, ...] = tuple( createdAttribute.GetComponentName( i ) for i in range( 3 ) )

    assert ( vnp.vtk_to_numpy( createdAttribute ) == np.full( ( elementSize, 3 ), fill_value=values ) ).all()
    assert cnames == componentNames


@pytest.mark.parametrize( "onpoints, arrayTest, arrayExpected", [
    ( True, 4092, "random_4092" ),
    ( False, 1740, "random_1740" ),
],
                          indirect=[ "arrayTest", "arrayExpected" ] )
def test_createAttribute(
    dataSetTest: vtkDataSet,
    arrayTest: npt.NDArray[ np.float64 ],
    arrayExpected: npt.NDArray[ np.float64 ],
    onpoints: bool,
) -> None:
    """Test creation of dataset in dataset from given array."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    componentNames: tuple[ str, str, str ] = ( "XX", "YY", "ZZ" )
    attributeName: str = "AttributeName"

    vtkFilters.createAttribute( vtkDataSetTest, arrayTest, attributeName, componentNames, onpoints )

    data: Union[ vtkPointData, vtkCellData ]
    if onpoints:
        data = vtkDataSetTest.GetPointData()
    else:
        data = vtkDataSetTest.GetCellData()

    createdAttribute: vtkDoubleArray = data.GetArray( attributeName )
    cnames: Tuple[ str, ...] = tuple( createdAttribute.GetComponentName( i ) for i in range( 3 ) )

    assert ( vnp.vtk_to_numpy( createdAttribute ) == arrayExpected ).all()
    assert cnames == componentNames


def test_copyAttribute( dataSetTest: vtkMultiBlockDataSet ) -> None:
    """Test copy of cell attribute from one multiblock to another."""
    objectFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    objectTo: vtkMultiBlockDataSet = dataSetTest( "multiblock" )

    attributeFrom: str = "CellAttribute"
    attributeTo: str = "CellAttributeTO"

    vtkFilters.copyAttribute( objectFrom, objectTo, attributeFrom, attributeTo )

    blockIndex: int = 0
    blockFrom: vtkDataSet = cast( vtkDataSet, objectFrom.GetBlock( blockIndex ) )
    blockTo: vtkDataSet = cast( vtkDataSet, objectTo.GetBlock( blockIndex ) )

    arrayFrom: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( blockFrom.GetCellData().GetArray( attributeFrom ) )
    arrayTo: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( blockTo.GetCellData().GetArray( attributeTo ) )

    assert ( arrayFrom == arrayTo ).all()


def test_copyAttributeDataSet( dataSetTest: vtkDataSet, ) -> None:
    """Test copy of cell attribute from one dataset to another."""
    objectFrom: vtkDataSet = dataSetTest( "dataset" )
    objectTo: vtkDataSet = dataSetTest( "dataset" )

    attributNameFrom = "CellAttribute"
    attributNameTo = "COPYATTRIBUTETO"

    vtkFilters.copyAttributeDataSet( objectFrom, objectTo, attributNameFrom, attributNameTo )

    arrayFrom: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( objectFrom.GetCellData().GetArray( attributNameFrom ) )
    arrayTo: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( objectTo.GetCellData().GetArray( attributNameTo ) )

    assert ( arrayFrom == arrayTo ).all()


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
    vtkFilters.renameAttribute(
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
    vtkFilters.renameAttribute( object=vtkDataSetTest,
                                attributeName=attributeName,
                                newAttributeName=newAttributeName,
                                onPoints=onpoints )
    if onpoints:
        assert vtkDataSetTest.GetPointData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetPointData().HasArray( newAttributeName ) == 1

    else:
        assert vtkDataSetTest.GetCellData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetCellData().HasArray( newAttributeName ) == 1
