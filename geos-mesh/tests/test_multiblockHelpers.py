# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from geos.mesh.utils import multiblockHelpers


@pytest.mark.parametrize( "meshName,listBlockNamesTest", [
    ( "geosOutput2Ranks", [ 'mesh1', 'Level0', 'CellElementRegion', 'Region', 'rank_0', 'rank_1', 'WellElementRegion', 'wellRegion1', 'rank_0', 'wellRegion2', 'rank_0', 'SurfaceElementRegion', 'Fault', 'rank_0', 'rank_1' ] ),
    ( "extractAndMergeVolumeWell1", [ 'Volume', 'Volume', 'Wells', 'Well1' ] ),
    ( "2Ranks", [ 'mesh1', 'Level0', 'CellElementRegion', 'Region', 'rank_0', 'rank_1' ] ),
] )
def test_getBlockNames(
    dataSetTest: vtkMultiBlockDataSet,
    meshName: str,
    listBlockNamesTest: list[ str ],
) -> None:
    """Test getting the name of all blocks in a multiBlockDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( meshName )
    listBlockName: list[ str ] = multiblockHelpers.getBlockNames( multiBlockDataSet )
    assert listBlockName == listBlockNamesTest


@pytest.mark.parametrize( "idBlock, blockNameTest", [
    ( 1, "mesh1" ),
    ( 2, "Level0" ),
    ( 3, "CellElementRegion" ),
    ( 4, "Region" ),
    ( 5, "rank_0" ),
    ( 6, "rank_1" ),
] )
def test_getBlockNameFromIndex(
    dataSetTest: vtkMultiBlockDataSet,
    idBlock: int,
    blockNameTest: str,
) -> None:
    """Test getting the name of the block with the idBlock index."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "2Ranks" )
    blockName: str = multiblockHelpers.getBlockNameFromIndex( multiBlockDataSet, idBlock )
    assert blockName == blockNameTest


@pytest.mark.parametrize( "idBlockTest, blockName", [
    ( 1, "mesh1" ),
    ( 2, "Level0" ),
    ( 3, "CellElementRegion" ),
    ( 4, "Region" ),
    ( 5, "rank_0" ),
    ( 6, "rank_1" ),
] )
def test_getBlockIndexFromName(
    dataSetTest: vtkMultiBlockDataSet,
    idBlockTest: int,
    blockName: str,
) -> None:
    """Test getting the flat index of a block with its name."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "geosOutput2Ranks" )
    idBlock: str = multiblockHelpers.getBlockIndexFromName( multiBlockDataSet, blockName )
    assert idBlock == idBlockTest


@pytest.mark.parametrize( "meshName, dictCompositeBlocksTest", [
    ( "geosOutput2Ranks", {'Region': 4, 'wellRegion1': 8, 'wellRegion2': 10, 'Fault': 13 } ),
    ( "extractAndMergeVolumeWell1", {'Volume': 1, 'Wells': 3 } ),
] )
def test_getElementaryCompositeBlockIndexes(
    dataSetTest: vtkMultiBlockDataSet,
    meshName: str,
    dictCompositeBlocksTest: dict[ str, int ],
) -> None:
    """Test getting the name of all blocks in a multiBlockDataSet."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( meshName )
    dictCompositeBlocks: dict[ str, int ] = multiblockHelpers.getElementaryCompositeBlockIndexes( multiBlockDataSet )
    assert dictCompositeBlocks == dictCompositeBlocksTest


@pytest.mark.parametrize( "meshName, blockElementFlatIndexesTest", [
    ( "geosOutput2Ranks", [ 5, 6, 9, 11, 14, 15 ] ),
    ( "extractAndMergeVolumeWell1", [ 2, 4 ] ),
] )
def test_getBlockElementIndexesFlatten(
    dataSetTest: vtkMultiBlockDataSet,
    meshName: str,
    blockElementFlatIndexesTest: list[ int ],
) -> None:
    """Test getting  a flatten list that contains flat indexes of elementary blocks."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( meshName )
    blockElementFlatIndexes: list[ int ] = multiblockHelpers.getBlockElementIndexesFlatten( multiBlockDataSet )
    assert blockElementFlatIndexes == blockElementFlatIndexesTest


@pytest.mark.parametrize( "meshName, blockElementIndexesTest", [
    ( "geosOutput2Ranks", [ [ 5, 6 ], [ 9 ], [ 11 ], [ 14, 15 ] ] ),
    ( "extractAndMergeVolumeWell1", [ [ 2 ], [ 4 ] ] ),
] )
def test_getBlockElementIndexes(
    dataSetTest: vtkMultiBlockDataSet,
    meshName: str,
    blockElementIndexesTest: list[ list[ int ] ],
) -> None:
    """Test getting a list of list that contains flat indexes of elementary blocks."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( meshName )
    blockElementIndexes: list[ list[ int ] ] = multiblockHelpers.getBlockElementIndexes( multiBlockDataSet )
    assert blockElementIndexes == blockElementIndexesTest
