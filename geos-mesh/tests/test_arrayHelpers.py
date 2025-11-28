# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator, attr-defined"
import pytest
from typing import Tuple, Union, Any

import numpy as np
import numpy.typing as npt

import vtkmodules.util.numpy_support as vnp
import pandas as pd  # type: ignore[import-untyped]
from vtkmodules.vtkCommonCore import vtkDoubleArray
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData

from geos.mesh.utils import arrayHelpers

from geos.utils.pieceEnum import Piece


@pytest.mark.parametrize( "meshName, cellDimExpected", [
    ( "dataset", { 3 } ),
    ( "fracture", { 2 } ),
    ( "well", { 1 } ),
    ( "meshGeosExtractBlockTmp", { 3, 2, 1 } ),
] )
def test_getCellDimension(
    dataSetTest: vtkDataSet,
    meshName: str,
    cellDimExpected: set[ int ],
) -> None:
    """Test getting the different cells dimension in a mesh."""
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshName )
    cellDimObtained: set[ int ] = arrayHelpers.getCellDimension( mesh )
    assert cellDimObtained == cellDimExpected


@pytest.mark.parametrize( "meshFromName, meshToName, piece", [
    ( "multiblock", "emptymultiblock", Piece.CELLS ),
    ( "multiblock", "emptyFracture", Piece.CELLS ),
    ( "dataset", "emptyFracture", Piece.CELLS ),
    ( "dataset", "emptypolydata", Piece.CELLS ),
    ( "fracture", "emptyFracture", Piece.POINTS ),
    ( "fracture", "emptyFracture", Piece.CELLS ),
    ( "fracture", "emptymultiblock", Piece.CELLS ),
    ( "polydata", "emptypolydata", Piece.CELLS ),
] )
def test_computeElementMapping(
    dataSetTest: vtkDataSet,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshFromName: str,
    meshToName: str,
    piece: Piece,
) -> None:
    """Test getting the map between two meshes element."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    elementMapComputed: dict[ int, npt.NDArray[ np.int64 ] ] = arrayHelpers.computeElementMapping(
        meshFrom, meshTo, piece )
    elementMapTest: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( meshFromName, meshToName, piece )

    keysComputed: list[ int ] = list( elementMapComputed.keys() )
    keysTest: list[ int ] = list( elementMapTest.keys() )
    assert keysComputed == keysTest

    for key in keysTest:
        assert np.all( elementMapComputed[ key ] == elementMapTest[ key ] )


@pytest.mark.parametrize( "piece, expected", [ ( Piece.POINTS, {
    'GLOBAL_IDS_POINTS': 1,
    'collocated_nodes': 2,
    'PointAttribute': 3,
} ), ( Piece.CELLS, {
    'CELL_MARKERS': 1,
    'PERM': 3,
    'PORO': 1,
    'FAULT': 1,
    'GLOBAL_IDS_CELLS': 1,
    'CellAttribute': 3,
} ) ] )
def test_getAttributeFromMultiBlockDataSet( dataSetTest: vtkMultiBlockDataSet, piece: Piece,
                                            expected: dict[ str, int ] ) -> None:
    """Test getting attribute list as dict from multiblock."""
    multiBlockTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    attributes: dict[ str, int ] = arrayHelpers.getAttributesFromMultiBlockDataSet( multiBlockTest, piece )

    assert attributes == expected


@pytest.mark.parametrize( "attributeName, pieceTest", [
    ( "CellAttribute", Piece.CELLS ),
    ( "PointAttribute", Piece.POINTS ),
    ( "NewAttribute", Piece.NONE ),
] )
def test_getAttributePieceInfo(
    dataSetTest: vtkDataSet,
    attributeName: str,
    pieceTest: Piece,
) -> None:
    """Test getting attribute piece information."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )
    pieceObtained = arrayHelpers.getAttributePieceInfo( dataSet, attributeName )
    assert pieceObtained == pieceTest


@pytest.mark.parametrize( "attributeName, listValues, piece, validValuesTest, invalidValuesTest", [
    ( "PointAttribute", [ [ 12.4, 9.7, 10.5 ], [ 0, 0, 0 ] ], Piece.POINTS, [ [ 12.4, 9.7, 10.5 ] ], [ [ 0, 0, 0 ] ] ),
    ( "CellAttribute", [ [ 24.8, 19.4, 21 ], [ 0, 0, 0 ] ], Piece.CELLS, [ [ 24.8, 19.4, 21 ] ], [ [ 0, 0, 0 ] ] ),
    ( "FAULT", [ 0, 100, 101, 2 ], Piece.CELLS, [ 0, 100, 101 ], [ 2 ] ),
] )
def test_checkValidValuesInDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    listValues: list[ Any ],
    piece: Piece,
    validValuesTest: list[ Any ],
    invalidValuesTest: list[ Any ],
) -> None:
    """Test the function checkValidValuesInDataSet."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )
    validValues: list[ Any ]
    invalidValues: list[ Any ]
    validValues, invalidValues = arrayHelpers.checkValidValuesInDataSet( dataSet, attributeName, listValues, piece )
    assert validValues == validValuesTest
    assert invalidValues == invalidValuesTest


@pytest.mark.parametrize( "piece, expected", [ ( Piece.POINTS, {
    'GLOBAL_IDS_POINTS': 1,
    'PointAttribute': 3,
} ), ( Piece.CELLS, {
    'CELL_MARKERS': 1,
    'PERM': 3,
    'PORO': 1,
    'FAULT': 1,
    'GLOBAL_IDS_CELLS': 1,
    'CellAttribute': 3,
} ) ] )
def test_getAttributesFromDataSet( dataSetTest: vtkDataSet, piece: Piece, expected: dict[ str, int ] ) -> None:
    """Test getting attribute list as dict from dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    attributes: dict[ str, int ] = arrayHelpers.getAttributesFromDataSet( vtkDataSetTest, piece )
    assert attributes == expected


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PORO", Piece.CELLS, 1 ),
    ( "PORO", Piece.POINTS, 0 ),
] )
def test_isAttributeInObjectMultiBlockDataSet( dataSetTest: vtkMultiBlockDataSet, attributeName: str, piece: Piece,
                                               expected: dict[ str, int ] ) -> None:
    """Test presence of attribute in a multiblock."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: bool = arrayHelpers.isAttributeInObjectMultiBlockDataSet( multiBlockDataset, attributeName, piece )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PORO", Piece.CELLS, 1 ),
    ( "PORO", Piece.POINTS, 0 ),
] )
def test_isAttributeInObjectDataSet( dataSetTest: vtkDataSet, attributeName: str, piece: Piece,
                                     expected: bool ) -> None:
    """Test presence of attribute in a dataset."""
    vtkDataset: vtkDataSet = dataSetTest( "dataset" )
    obtained: bool = arrayHelpers.isAttributeInObjectDataSet( vtkDataset, attributeName, piece )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PORO", Piece.CELLS, False ),
    ( "GLOBAL_IDS_POINTS", Piece.POINTS, True ),
] )
def test_isAttributeGlobal(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    piece: Piece,
    expected: bool,
) -> None:
    """Test if the attribute is global or partial."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: bool = arrayHelpers.isAttributeGlobal( multiBlockDataset, attributeName, piece )
    assert obtained == expected


@pytest.mark.parametrize( "arrayExpected, piece", [
    ( "PORO", Piece.CELLS ),
    ( "PERM", Piece.CELLS ),
    ( "PointAttribute", Piece.POINTS ),
],
                          indirect=[ "arrayExpected" ] )
def test_getArrayInObject( request: pytest.FixtureRequest, arrayExpected: npt.NDArray[ np.float64 ],
                           dataSetTest: vtkDataSet, piece: Piece ) -> None:
    """Test getting numpy array of an attribute from dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    params = request.node.callspec.params
    attributeName: str = params[ "arrayExpected" ]

    obtained: npt.NDArray[ np.float64 ] = arrayHelpers.getArrayInObject( vtkDataSetTest, attributeName, piece )
    expected: npt.NDArray[ np.float64 ] = arrayExpected

    assert ( obtained == expected ).all()


@pytest.mark.parametrize( "attributeName, vtkDataType, piece", [
    ( "CellAttribute", 11, Piece.CELLS ),
    ( "PointAttribute", 11, Piece.POINTS ),
    ( "collocated_nodes", 12, Piece.POINTS ),
] )
def test_getVtkArrayTypeInMultiBlock( dataSetTest: vtkMultiBlockDataSet, attributeName: str, vtkDataType: int,
                                      piece: Piece ) -> None:
    """Test getting the type of the vtk array of an attribute from multiBlockDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )

    vtkDataTypeTest: int = arrayHelpers.getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, piece )

    assert ( vtkDataTypeTest == vtkDataType )


@pytest.mark.parametrize( "attributeName, piece", [
    ( "CellAttribute", Piece.CELLS ),
    ( "PointAttribute", Piece.POINTS ),
] )
def test_getVtkArrayTypeInObject( dataSetTest: vtkDataSet, attributeName: str, piece: Piece ) -> None:
    """Test getting the type of the vtk array of an attribute from dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )

    obtained: int = arrayHelpers.getVtkArrayTypeInObject( vtkDataSetTest, attributeName, piece )
    expected: int = 11

    assert ( obtained == expected )


@pytest.mark.parametrize( "arrayExpected, piece", [
    ( "PORO", Piece.CELLS ),
    ( "PointAttribute", Piece.POINTS ),
],
                          indirect=[ "arrayExpected" ] )
def test_getVtkArrayInObject( request: pytest.FixtureRequest, arrayExpected: npt.NDArray[ np.float64 ],
                              dataSetTest: vtkDataSet, piece: Piece ) -> None:
    """Test getting Vtk Array from a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    params = request.node.callspec.params
    attributeName: str = params[ 'arrayExpected' ]

    obtained: vtkDoubleArray = arrayHelpers.getVtkArrayInObject( vtkDataSetTest, attributeName, piece )
    obtained_as_np: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( obtained )

    assert ( obtained_as_np == arrayExpected ).all()


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PORO", Piece.CELLS, 1 ),
    ( "PERM", Piece.CELLS, 3 ),
    ( "PointAttribute", Piece.POINTS, 3 ),
] )
def test_getNumberOfComponentsDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    piece: Piece,
    expected: int,
) -> None:
    """Test getting the number of components of an attribute from a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    obtained: int = arrayHelpers.getNumberOfComponentsDataSet( vtkDataSetTest, attributeName, piece )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PORO", Piece.CELLS, 1 ),
    ( "PERM", Piece.CELLS, 3 ),
    ( "PointAttribute", Piece.POINTS, 3 ),
] )
def test_getNumberOfComponentsMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    piece: Piece,
    expected: int,
) -> None:
    """Test getting the number of components of an attribute from a multiblock."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: int = arrayHelpers.getNumberOfComponentsMultiBlock( vtkMultiBlockDataSetTest, attributeName, piece )

    assert obtained == expected


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PERM", Piece.CELLS, ( "AX1", "AX2", "AX3" ) ),
    ( "PORO", Piece.CELLS, () ),
] )
def test_getComponentNamesDataSet( dataSetTest: vtkDataSet, attributeName: str, piece: Piece,
                                   expected: tuple[ str, ...] ) -> None:
    """Test getting the component names of an attribute from a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    obtained: tuple[ str, ...] = arrayHelpers.getComponentNamesDataSet( vtkDataSetTest, attributeName, piece )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PERM", Piece.CELLS, ( "AX1", "AX2", "AX3" ) ),
    ( "PORO", Piece.CELLS, () ),
] )
def test_getComponentNamesMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    piece: Piece,
    expected: tuple[ str, ...],
) -> None:
    """Test getting the component names of an attribute from a multiblock."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: tuple[ str, ...] = arrayHelpers.getComponentNamesMultiBlock( vtkMultiBlockDataSetTest, attributeName,
                                                                           piece )
    assert obtained == expected


@pytest.mark.parametrize( "attributeNames, piece, expected_columns", [
    ( ( "collocated_nodes", ), Piece.POINTS, ( "collocated_nodes_0", "collocated_nodes_1" ) ),
] )
def test_getAttributeValuesAsDF( dataSetTest: vtkPolyData, attributeNames: Tuple[ str, ...], piece: Piece,
                                 expected_columns: Tuple[ str, ...] ) -> None:
    """Test getting an attribute from a polydata as a dataframe."""
    polydataset: vtkPolyData = vtkPolyData.SafeDownCast( dataSetTest( "polydata" ) )
    data: pd.DataFrame = arrayHelpers.getAttributeValuesAsDF( polydataset, attributeNames, piece )

    obtained_columns = data.columns.values.tolist()
    assert obtained_columns == list( expected_columns )
