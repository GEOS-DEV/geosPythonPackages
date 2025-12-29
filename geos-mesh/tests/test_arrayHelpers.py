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
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData, vtkFieldData, vtkPointData, vtkCellData

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


@pytest.mark.parametrize(
    "meshFromName, meshToName, piece",
    [
        ( "well", "emptyWell", Piece.CELLS ),  # 1D vtu -> 1D vtu onCells
        ( "well", "emptyWell", Piece.POINTS ),  # 1D vtu -> 1D vtu onPoints
        ( "well", "emptyFracture", Piece.POINTS ),  # 1D vtu -> 2D vtu onCells
        ( "well", "emptypolydata", Piece.POINTS ),  # 1D vtu -> 2D vtp onCells
        ( "well", "emptydataset", Piece.POINTS ),  # 1D vtu -> 3D vtu onCells
        ( "well", "emptymultiblock", Piece.POINTS ),  # 1D vtu -> vtm(3D vtu & 2D vtu) onPoints
        ( "fracture", "emptyFracture", Piece.CELLS ),  # 2D vtu -> 2D vtu onCells
        ( "fracture", "emptyWell", Piece.POINTS ),  # 2D vtu -> 1D vtu onPoints
        ( "fracture", "emptypolydata", Piece.CELLS ),  # 2D vtu -> 2D vtp onCells
        ( "fracture", "emptydataset", Piece.CELLS ),  # 2D vtu -> 3D vtu onCells
        ( "fracture", "emptymultiblock", Piece.CELLS ),  # 2D vtu -> vtm(3D vtu & 2D vtu) onCells
        ( "polydata", "emptypolydata", Piece.CELLS ),  # 2D vtp -> 2D vtp onCells
        ( "polydata", "emptyWell", Piece.POINTS ),  # 2D vtp -> 1D vtu onPoints
        ( "polydata", "emptyFracture", Piece.CELLS ),  # 2D vtp -> 2D vtu onCells
        ( "polydata", "emptydataset", Piece.CELLS ),  # 2D vtp -> 3D vtu onCells
        ( "polydata", "emptymultiblock", Piece.CELLS ),  # 2D vtp -> vtm(3D vtu & 2D vtu) onCells
        ( "dataset", "emptydataset", Piece.CELLS ),  # 3D vtu -> 3D vtu onCells
        ( "dataset", "emptyWell", Piece.POINTS ),  # 3D vtu -> 1D vtu onPoints
        ( "dataset", "emptyFracture", Piece.CELLS ),  # 3D vtu -> 2D vtu onCells
        ( "dataset", "emptypolydata", Piece.CELLS ),  # 3D vtu -> 2D vtp onCells
        ( "dataset", "emptymultiblock", Piece.CELLS ),  # 3D vtu -> vtm(3D vtu & 2D vtu) onCells
        ( "multiblock", "emptymultiblock", Piece.CELLS ),  # vtm( 3D vtu & 2D vtu ) -> vtm( 3D vtu & 2D vtu ) onCells
        ( "multiblock", "emptyWell", Piece.POINTS ),  # vtm(3D vtu & 2D vtu) -> 1D vtu onPoints
        ( "multiblock", "emptyFracture", Piece.CELLS ),  # vtm(3D vtu & 2D vtu) -> 2D vtu onCells
        ( "multiblock", "emptypolydata", Piece.CELLS ),  # vtm(3D vtu & 2D vtu) -> 2D vtp onCells
        ( "multiblock", "emptydataset", Piece.CELLS ),  # vtm(3D vtu & 2D vtu) -> 3D vtu onCells
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
    elementMapComputed: dict[ int,
                              npt.NDArray[ np.int64 ] ] = arrayHelpers.computeElementMapping( meshFrom, meshTo, piece )
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


@pytest.mark.parametrize( "meshName, attributeName, pieceTest", [
    ( "dataset", "CellAttribute", Piece.CELLS ),
    ( "dataset", "PointAttribute", Piece.POINTS ),
    ( "dataset", "NewAttribute", Piece.NONE ),
    ( "multiblockGeosOutput", "ghostRank", Piece.BOTH ),
    ( "multiblockGeosOutput", "TIME", Piece.FIELD ),
] )
def test_getAttributePieceInfo(
    dataSetTest: vtkDataSet,
    meshName: str,
    attributeName: str,
    pieceTest: Piece,
) -> None:
    """Test getting attribute piece information."""
    dataSet: vtkDataSet = dataSetTest( meshName )
    pieceObtained = arrayHelpers.getAttributePieceInfo( dataSet, attributeName )
    assert pieceObtained == pieceTest


def test_getNumpyGlobalIdsArray( dataSetTest: vtkDataSet ) -> None:
    """Test the function getNumpyGlobalIdsArray."""
    dataset: vtkDataSet = dataSetTest( "dataset" )
    for piece in [ Piece.POINTS, Piece.CELLS ]:
        fieldData: vtkPointData | vtkCellData = dataset.GetPointData() if piece == Piece.POINTS else dataset.GetCellData()
        npArrayObtained: npt.NDArray = arrayHelpers.getNumpyGlobalIdsArray( fieldData )
        nbElements: int = fieldData.GetNumberOfTuples()
        npArrayExpected: npt.NDArray = np.array( [ i for i in range( nbElements ) ] )
        assert ( npArrayObtained == npArrayExpected ).all()


def test_getNumpyGlobalIdsArrayTypeError() -> None:
    """Test getNumpyGlobalIdsArray TypeError raises."""
    fieldData: vtkPolyData = vtkPolyData()
    with pytest.raises( TypeError ):
        arrayHelpers.getNumpyGlobalIdsArray( fieldData )


def test_getNumpyGlobalIdsArrayAttributeError() -> None:
    """Test getNumpyGlobalIdsArray AttributeError raises."""
    fieldData: vtkFieldData = vtkFieldData()
    with pytest.raises( AttributeError ):
        arrayHelpers.getNumpyGlobalIdsArray( fieldData )


@pytest.mark.parametrize( "meshName, piece, expectedAttributeSet", [
    ( "dataset", Piece.POINTS, set( [ "GLOBAL_IDS_POINTS", "PointAttribute" ] ) ),
    ( "dataset", Piece.CELLS, set( [ "CELL_MARKERS", "PERM", "PORO", "FAULT", "GLOBAL_IDS_CELLS", "CellAttribute" ] ) ),
    ( "multiblock", Piece.CELLS, set( [ "CELL_MARKERS", "PERM", "PORO", "FAULT", "GLOBAL_IDS_CELLS", "CellAttribute" ] ) ),
])
def test_getAttributeSet(
    dataSetTest: Any,
    meshName: str,
    piece: Piece,
    expectedAttributeSet: set[ str ],
) -> None:
    """Test getAttributeSet function."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    obtainedAttributeSet: set[ str ] = arrayHelpers.getAttributeSet( mesh, piece )
    assert obtainedAttributeSet == expectedAttributeSet


def test_getAttributeSetTypeError() -> None:
    """Test getAttributeSet TypeError raises."""
    mesh: vtkFieldData = vtkFieldData()
    with pytest.raises( TypeError ):
        arrayHelpers.getAttributeSet( mesh, Piece.CELLS )


@pytest.mark.parametrize( "arrayName, sorted, piece, expectedNpArray", [
    ( "PORO", True, Piece.CELLS, np.array( [ 0.20000000298 for _ in range( 1740 ) ], dtype=np.float32 ) ),
    ( "PORO", False, Piece.CELLS, np.array( [ 0.20000000298 for _ in range( 1740 ) ], dtype=np.float32 ) ),
    ( "PointAttribute", False, Piece.POINTS, np.array( [ [ 12.4, 9.7, 10.5 ] for _ in range( 4092 ) ], dtype=np.float64 ) ),
] )
def test_getNumpyArrayByName(
    dataSetTest: vtkDataSet,
    arrayName: str,
    sorted: bool,
    piece: Piece,
    expectedNpArray: npt.NDArray,
) -> None:
    """Test the function getNumpyGlobalIdsArray."""
    dataset: vtkDataSet = dataSetTest( "dataset" )
    fieldData: vtkPointData | vtkCellData = dataset.GetPointData() if piece == Piece.POINTS else dataset.GetCellData()
    obtainedNpArray: npt.NDArray = arrayHelpers.getNumpyArrayByName( fieldData, arrayName, sorted )
    assert ( obtainedNpArray == expectedNpArray ).all()


def test_getNumpyArrayByNameAttributeError( dataSetTest: vtkDataSet ) -> None:
    """Test getNumpyArrayByName AttributeError raises."""
    dataset: vtkDataSet = dataSetTest( "dataset" )
    fieldData: vtkCellData = dataset.GetCellData()
    with pytest.raises( AttributeError ):
        arrayHelpers.getNumpyArrayByName( fieldData, "Attribute" )


@pytest.mark.parametrize( "attributeName, listValues, piece, validValuesTest, invalidValuesTest", [
    ( "GLOBAL_IDS_POINTS", [ 0, 1, 11, -9 ], Piece.POINTS, [ 0, 1, 11 ], [ -9 ] ),
    ( "GLOBAL_IDS_CELLS", [ 0, 1, 11, -9 ], Piece.CELLS, [ 0, 1, 11 ], [ -9 ] ),
] )
def test_checkValidValuesInMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    listValues: list[ Any ],
    piece: Piece,
    validValuesTest: list[ Any ],
    invalidValuesTest: list[ Any ],
) -> None:
    """Test the function checkValidValuesInDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    validValues: list[ Any ]
    invalidValues: list[ Any ]
    validValues, invalidValues = arrayHelpers.checkValidValuesInMultiBlock( multiBlockDataSet, attributeName, listValues, piece )
    assert validValues == validValuesTest
    assert invalidValues == invalidValuesTest


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


@pytest.mark.parametrize( "meshName, attributeName, piece, expected", [
    ( "dataset", "Attribute", Piece.CELLS, False ),
    ( "dataset", "GLOBAL_IDS_CELLS", Piece.CELLS, True ),
    ( "dataset", "GLOBAL_IDS_POINTS", Piece.POINTS, True ),
    ( "multiblockGeosOutput", "TIME", Piece.FIELD, True ),
    ( "multiblockGeosOutput", "ghostRank", Piece.CELLS, True ),
    ( "multiblockGeosOutput", "ghostRank", Piece.POINTS, True ),
] )
def test_isAttributeInObject(
    dataSetTest: Any,
    meshName: str,
    attributeName: str,
    piece: Piece,
    expected: bool,
) -> None:
    """Test the function isAttributeInObject."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    assert arrayHelpers.isAttributeInObject( mesh, attributeName, piece ) == expected


def test_isAttributeInObjectTypeError() -> None:
    """Test isAttributeInObject TypeError raises."""
    mesh: vtkCellData = vtkCellData()
    with pytest.raises( TypeError ):
        arrayHelpers.isAttributeInObject( mesh, "Attribute", Piece.CELLS )


@pytest.mark.parametrize( "attributeName, piece", [
    ( "rockPorosity_referencePorosity", Piece.CELLS ),
    ( "ghostRank", Piece.POINTS ),
    ( "TIME", Piece.FIELD ),
    ( "ghostRank", Piece.BOTH ),
] )
def test_isAttributeInObjectMultiBlockDataSet( dataSetTest: vtkMultiBlockDataSet, attributeName: str,
                                               piece: Piece ) -> None:
    """Test presence of attribute in a multiblock."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )
    obtained: bool = arrayHelpers.isAttributeInObjectMultiBlockDataSet( multiBlockDataset, attributeName, piece )
    assert obtained


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "PointAttribute", Piece.POINTS, True ),
    ( "PORO", Piece.CELLS, True ),
    ( "PORO", Piece.POINTS, False ),
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


@pytest.mark.parametrize( "attributeNames, expected", [
    ( [ "CellAttribute" ], True ),  # Attribute on cells
    ( [ "PointAttribute" ], True ),  # Attribute on points
    ( [ "attribute" ], False ),  # "attribute" is not on the mesh
    ( [ "CellAttribute", "attribute" ], True ),  # "attribute" is not on the mesh
])
def test_hasArray( dataSetTest: vtkDataSet, attributeNames: list[ str ], expected ) -> None:
    """Test the function hasArray."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    assert arrayHelpers.hasArray( mesh, attributeNames ) == expected
