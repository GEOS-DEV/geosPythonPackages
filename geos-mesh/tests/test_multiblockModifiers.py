# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkUnstructuredGrid
from geos.mesh.utils import multiblockModifiers


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
    dataset: vtkUnstructuredGrid = multiblockModifiers.mergeBlocks( vtkMultiBlockDataSetTest, keepPartialAttributes )

    assert dataset.GetCellData().GetNumberOfArrays() == len( expected_cell_attributes )
    for c_attribute in expected_cell_attributes:
        assert dataset.GetCellData().HasArray( c_attribute )

    assert dataset.GetPointData().GetNumberOfArrays() == len( expected_point_attributes )
    for p_attribute in expected_point_attributes:
        assert dataset.GetPointData().HasArray( p_attribute )