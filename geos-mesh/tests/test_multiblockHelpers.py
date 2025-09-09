# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, cast
from vtkmodules.vtkCommonDataModel import ( vtkCompositeDataSet, vtkDataObject, vtkDataObjectTreeIterator,
                                            vtkMultiBlockDataSet )

from geos.mesh.utils import multiblockHelpers


@pytest.mark.parametrize( "listBlockNamesTest", [
    ( [ "main", "Fracture", "fracture" ] ),
] )
def test_getBlockNames(
    dataSetTest: vtkMultiBlockDataSet,
    listBlockNamesTest: list[ str ],
) -> None:
    """Test getting the name of all blocks in a multiBlockDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    listBlockName: list[ str ] = multiblockHelpers.getBlockNames( multiBlockDataSet )
    assert listBlockName == listBlockNamesTest


@pytest.mark.parametrize( "idBlock, blockNameTest", [
    ( 1, "main" ),
    ( 2, "Fracture" ),
    ( 3, "fracture" ),
] )
def test_getBlockNameFromIndex(
    dataSetTest: vtkMultiBlockDataSet,
    idBlock: int,
    blockNameTest: str,
) -> None:
    """Test getting the name of the block with the idBlock index."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    blockName: str = multiblockHelpers.getBlockNameFromIndex( multiBlockDataSet, idBlock )
    assert blockName == blockNameTest


@pytest.mark.parametrize( "idBlockTest, blockName", [
    ( 1, "main" ),
    ( 2, "Fracture" ),
    ( 3, "fracture" ),
    ( -1, "NotABlock" ),
] )
def test_getBlockIndexFromName(
    dataSetTest: vtkMultiBlockDataSet,
    idBlockTest: int,
    blockName: str,
) -> None:
    """Test getting the flat index of a block with its name."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    idBlock: str = multiblockHelpers.getBlockIndexFromName( multiBlockDataSet, blockName )
    assert idBlock == idBlockTest


@pytest.mark.parametrize( "dictCompositeBlocksTest", [
    ( { "Fracture": 2 } ),
] )
def test_getElementaryCompositeBlockIndexes(
    dataSetTest: vtkMultiBlockDataSet,
    dictCompositeBlocksTest: dict[ str, int ],
) -> None:
    """Test getting the name of all blocks in a multiBlockDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    dictCompositeBlocks: dict[ str, int ] = multiblockHelpers.getElementaryCompositeBlockIndexes( multiBlockDataSet )
    assert dictCompositeBlocks == dictCompositeBlocksTest


@pytest.mark.parametrize( "blockElementFlatIndexesTest", [
    ( [ 1 ,  3 ] ),
] )
def test_getBlockElementIndexesFlatten(
    dataSetTest: vtkMultiBlockDataSet,
    blockElementFlatIndexesTest: list[ int ],
) -> None:
    """Test getting  a flatten list that contains flat indexes of elementary blocks."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    blockElementFlatIndexes: list[ int ] = multiblockHelpers.getBlockElementIndexesFlatten( multiBlockDataSet )
    assert blockElementFlatIndexes == blockElementFlatIndexesTest


@pytest.mark.parametrize( "blockElementIndexesTest", [
    ( [ [ 1 ], [ 3 ] ] ),
] )
def test_getBlockElementIndexes(
    dataSetTest: vtkMultiBlockDataSet,
    blockElementIndexesTest: list[ list[ int ] ],
) -> None:
    """Test getting a list of list that contains flat indexes of elementary blocks."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    blockElementIndexes: list[ list[ int ] ] = multiblockHelpers.getBlockElementIndexes( multiBlockDataSet )
    assert blockElementIndexes == blockElementIndexesTest

