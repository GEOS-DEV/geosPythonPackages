# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
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
from geos.mesh.utils.arrayModifiers import createConstantAttribute


@pytest.mark.parametrize( "onpoints, expected", [ ( True, {
    'GLOBAL_IDS_POINTS': 1,
    'collocated_nodes': 2,
    'PointAttribute': 3
} ), ( False, {
    'CELL_MARKERS': 1,
    'PERM': 3,
    'PORO': 1,
    'FAULT': 1,
    'GLOBAL_IDS_CELLS': 1,
    'CellAttribute': 3
} ) ] )
def test_getAttributeFromMultiBlockDataSet( dataSetTest: vtkMultiBlockDataSet, onpoints: bool,
                                            expected: dict[ str, int ] ) -> None:
    """Test getting attribute list as dict from multiblock."""
    multiBlockTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    attributes: dict[ str, int ] = arrayHelpers.getAttributesFromMultiBlockDataSet( multiBlockTest, onpoints )

    assert attributes == expected


@pytest.mark.parametrize( "attributeName, onPointsTest, onBothTest", [
    ( "CellAttribute", False, False ),
    ( "PointAttribute", True, False ),
    ( "NewAttribute", None, False ),
    ( "NewAttribute", True, True ),
] )
def test_getAttributePieceInfo(
    dataSetTest: vtkDataSet,
    attributeName: str,
    onPointsTest: Union[ None, bool ],
    onBothTest: bool,
) -> None:
    """Test getting attribute piece information."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )
    if onBothTest:  # Create a case with an attribute with the same name on points and on cells.
        createConstantAttribute( dataSet, [ 42. ], attributeName, onPoints=True )
        createConstantAttribute( dataSet, [ 42. ], attributeName, onPoints=False )
    onPoints: Union[ None, bool ]
    onBoth: bool
    onPoints, onBoth = arrayHelpers.getAttributePieceInfo( dataSet, attributeName )
    assert onPoints == onPointsTest
    assert onBoth == onBothTest


@pytest.mark.parametrize( "attributeName, listValues, onPoints, validValuesTest, invalidValuesTest", [
    ( "PointAttribute", [ [ 12.4, 9.7, 10.5 ], [ 0, 0, 0 ] ], True, [ [ 12.4, 9.7, 10.5 ] ], [ [ 0, 0, 0 ] ] ),
    ( "CellAttribute", [ [ 24.8, 19.4, 21 ], [ 0, 0, 0 ] ], False, [ [ 24.8, 19.4, 21 ] ], [ [ 0, 0, 0 ] ] ),
    ( "FAULT", [ 0, 100, 101, 2 ], False, [ 0, 100, 101 ], [ 2 ] ),
] )
def test_checkValidValuesInDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    listValues: list[ Any ],
    onPoints: bool,
    validValuesTest: list[ Any ],
    invalidValuesTest: list[ Any ],
) -> None:
    """Test the function checkValidValuesInDataSet."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )
    validValues: list[ Any ]
    invalidValues: list[ Any ]
    validValues, invalidValues = arrayHelpers.checkValidValuesInDataSet( dataSet, attributeName, listValues, onPoints )
    assert validValues == validValuesTest
    assert invalidValues == invalidValuesTest


@pytest.mark.parametrize( "onpoints, expected", [ ( True, {
    'GLOBAL_IDS_POINTS': 1,
    'PointAttribute': 3,
} ), ( False, {
    'CELL_MARKERS': 1,
    'PERM': 3,
    'PORO': 1,
    'FAULT': 1,
    'GLOBAL_IDS_CELLS': 1,
    'CellAttribute': 3
} ) ] )
def test_getAttributesFromDataSet( dataSetTest: vtkDataSet, onpoints: bool, expected: dict[ str, int ] ) -> None:
    """Test getting attribute list as dict from dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    attributes: dict[ str, int ] = arrayHelpers.getAttributesFromDataSet( vtkDataSetTest, onpoints )
    assert attributes == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PORO", True, 0 ),
] )
def test_isAttributeInObjectMultiBlockDataSet( dataSetTest: vtkMultiBlockDataSet, attributeName: str, onpoints: bool,
                                               expected: dict[ str, int ] ) -> None:
    """Test presence of attribute in a multiblock."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: bool = arrayHelpers.isAttributeInObjectMultiBlockDataSet( multiBlockDataset, attributeName, onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PORO", True, 0 ),
] )
def test_isAttributeInObjectDataSet( dataSetTest: vtkDataSet, attributeName: str, onpoints: bool,
                                     expected: bool ) -> None:
    """Test presence of attribute in a dataset."""
    vtkDataset: vtkDataSet = dataSetTest( "dataset" )
    obtained: bool = arrayHelpers.isAttributeInObjectDataSet( vtkDataset, attributeName, onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, False ),
    ( "GLOBAL_IDS_POINTS", True, True ),
] )
def test_isAttributeGlobal(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onpoints: bool,
    expected: bool,
) -> None:
    """Test if the attribute is global or partial."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: bool = arrayHelpers.isAttributeGlobal( multiBlockDataset, attributeName, onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "arrayExpected, onpoints", [
    ( "PORO", False ),
    ( "PERM", False ),
    ( "PointAttribute", True ),
],
                          indirect=[ "arrayExpected" ] )
def test_getArrayInObject( request: pytest.FixtureRequest, arrayExpected: npt.NDArray[ np.float64 ],
                           dataSetTest: vtkDataSet, onpoints: bool ) -> None:
    """Test getting numpy array of an attribute from dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    params = request.node.callspec.params
    attributeName: str = params[ "arrayExpected" ]

    obtained: npt.NDArray[ np.float64 ] = arrayHelpers.getArrayInObject( vtkDataSetTest, attributeName, onpoints )
    expected: npt.NDArray[ np.float64 ] = arrayExpected

    assert ( obtained == expected ).all()


@pytest.mark.parametrize( "attributeName, vtkDataType, onPoints", [
    ( "CellAttribute", 11, False ),
    ( "PointAttribute", 11, True ),
    ( "collocated_nodes", 12, True ),
] )
def test_getVtkArrayTypeInMultiBlock( dataSetTest: vtkMultiBlockDataSet, attributeName: str, vtkDataType: int,
                                      onPoints: bool ) -> None:
    """Test getting the type of the vtk array of an attribute from multiBlockDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )

    vtkDataTypeTest: int = arrayHelpers.getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, onPoints )

    assert ( vtkDataTypeTest == vtkDataType )


@pytest.mark.parametrize( "attributeName, onPoints", [
    ( "CellAttribute", False ),
    ( "PointAttribute", True ),
] )
def test_getVtkArrayTypeInObject( dataSetTest: vtkDataSet, attributeName: str, onPoints: bool ) -> None:
    """Test getting the type of the vtk array of an attribute from dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )

    obtained: int = arrayHelpers.getVtkArrayTypeInObject( vtkDataSetTest, attributeName, onPoints )
    expected: int = 11

    assert ( obtained == expected )


@pytest.mark.parametrize( "arrayExpected, onpoints", [
    ( "PORO", False ),
    ( "PointAttribute", True ),
],
                          indirect=[ "arrayExpected" ] )
def test_getVtkArrayInObject( request: pytest.FixtureRequest, arrayExpected: npt.NDArray[ np.float64 ],
                              dataSetTest: vtkDataSet, onpoints: bool ) -> None:
    """Test getting Vtk Array from a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    params = request.node.callspec.params
    attributeName: str = params[ 'arrayExpected' ]

    obtained: vtkDoubleArray = arrayHelpers.getVtkArrayInObject( vtkDataSetTest, attributeName, onpoints )
    obtained_as_np: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( obtained )

    assert ( obtained_as_np == arrayExpected ).all()


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PERM", False, 3 ),
    ( "PointAttribute", True, 3 ),
] )
def test_getNumberOfComponentsDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    onpoints: bool,
    expected: int,
) -> None:
    """Test getting the number of components of an attribute from a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    obtained: int = arrayHelpers.getNumberOfComponentsDataSet( vtkDataSetTest, attributeName, onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PERM", False, 3 ),
    ( "PointAttribute", True, 3 ),
] )
def test_getNumberOfComponentsMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onpoints: bool,
    expected: int,
) -> None:
    """Test getting the number of components of an attribute from a multiblock."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: int = arrayHelpers.getNumberOfComponentsMultiBlock( vtkMultiBlockDataSetTest, attributeName, onpoints )

    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PERM", False, ( "AX1", "AX2", "AX3" ) ),
    ( "PORO", False, () ),
] )
def test_getComponentNamesDataSet( dataSetTest: vtkDataSet, attributeName: str, onpoints: bool,
                                   expected: tuple[ str, ...] ) -> None:
    """Test getting the component names of an attribute from a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    obtained: tuple[ str, ...] = arrayHelpers.getComponentNamesDataSet( vtkDataSetTest, attributeName, onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PERM", False, ( "AX1", "AX2", "AX3" ) ),
    ( "PORO", False, () ),
] )
def test_getComponentNamesMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onpoints: bool,
    expected: tuple[ str, ...],
) -> None:
    """Test getting the component names of an attribute from a multiblock."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: tuple[ str, ...] = arrayHelpers.getComponentNamesMultiBlock( vtkMultiBlockDataSetTest, attributeName,
                                                                           onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeNames, onPoints, expected_columns", [
    ( ( "collocated_nodes", ), True, ( "collocated_nodes_0", "collocated_nodes_1" ) ),
] )
def test_getAttributeValuesAsDF( dataSetTest: vtkPolyData, attributeNames: Tuple[ str, ...],
                                 onPoints: bool, expected_columns: Tuple[ str, ...] ) -> None:
    """Test getting an attribute from a polydata as a dataframe."""
    polydataset: vtkPolyData = vtkPolyData.SafeDownCast( dataSetTest( "polydata" ) )
    data: pd.DataFrame = arrayHelpers.getAttributeValuesAsDF( polydataset, attributeNames, onPoints )

    obtained_columns = data.columns.values.tolist()
    assert obtained_columns == list( expected_columns )
