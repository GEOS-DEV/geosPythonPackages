# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator, attr-defined"
import pytest
from typing import Tuple

import numpy as np
import numpy.typing as npt

import vtkmodules.util.numpy_support as vnp
import pandas as pd  # type: ignore[import-untyped]
from vtkmodules.vtkCommonCore import vtkDoubleArray
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData

from geos.mesh.utils import helpers as vtkHelpers


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
    attributes: dict[ str, int ] = vtkHelpers.getAttributesFromMultiBlockDataSet( multiBlockTest, onpoints )

    assert attributes == expected


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
    attributes: dict[ str, int ] = vtkHelpers.getAttributesFromDataSet( vtkDataSetTest, onpoints )
    assert attributes == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PORO", True, 0 ),
] )
def test_isAttributeInObjectMultiBlockDataSet( dataSetTest: vtkMultiBlockDataSet, attributeName: str, onpoints: bool,
                                               expected: dict[ str, int ] ) -> None:
    """Test presence of attribute in a multiblock."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    obtained: bool = vtkHelpers.isAttributeInObjectMultiBlockDataSet( multiBlockDataset, attributeName, onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PORO", True, 0 ),
] )
def test_isAttributeInObjectDataSet( dataSetTest: vtkDataSet, attributeName: str, onpoints: bool,
                                     expected: bool ) -> None:
    """Test presence of attribute in a dataset."""
    vtkDataset: vtkDataSet = dataSetTest( "dataset" )
    obtained: bool = vtkHelpers.isAttributeInObjectDataSet( vtkDataset, attributeName, onpoints )
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

    obtained: npt.NDArray[ np.float64 ] = vtkHelpers.getArrayInObject( vtkDataSetTest, attributeName, onpoints )
    expected: npt.NDArray[ np.float64 ] = arrayExpected

    assert ( obtained == expected ).all()


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

    obtained: vtkDoubleArray = vtkHelpers.getVtkArrayInObject( vtkDataSetTest, attributeName, onpoints )
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
    obtained: int = vtkHelpers.getNumberOfComponentsDataSet( vtkDataSetTest, attributeName, onpoints )
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
    obtained: int = vtkHelpers.getNumberOfComponentsMultiBlock( vtkMultiBlockDataSetTest, attributeName, onpoints )

    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PERM", False, ( "AX1", "AX2", "AX3" ) ),
    ( "PORO", False, () ),
] )
def test_getComponentNamesDataSet( dataSetTest: vtkDataSet, attributeName: str, onpoints: bool,
                                   expected: tuple[ str, ...] ) -> None:
    """Test getting the component names of an attribute from a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    obtained: tuple[ str, ...] = vtkHelpers.getComponentNamesDataSet( vtkDataSetTest, attributeName, onpoints )
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
    obtained: tuple[ str, ...] = vtkHelpers.getComponentNamesMultiBlock( vtkMultiBlockDataSetTest, attributeName,
                                                                         onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeNames, expected_columns", [
    ( ( "CellAttribute1", ), ( "CellAttribute1_0", "CellAttribute1_1", "CellAttribute1_2" ) ),
    ( (
        "CellAttribute1",
        "CellAttribute2",
    ), ( "CellAttribute2", "CellAttribute1_0", "CellAttribute1_1", "CellAttribute1_2" ) ),
] )
def test_getAttributeValuesAsDF( dataSetTest: vtkPolyData, attributeNames: Tuple[ str, ...],
                                 expected_columns: Tuple[ str, ...] ) -> None:
    """Test getting an attribute from a polydata as a dataframe."""
    polydataset: vtkPolyData = dataSetTest( "polydata" )
    data: pd.DataFrame = vtkHelpers.getAttributeValuesAsDF( polydataset, attributeNames )

    obtained_columns = data.columns.values.tolist()
    assert obtained_columns == list( expected_columns )
