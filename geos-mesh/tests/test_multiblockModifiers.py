# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkUnstructuredGrid
from geos.mesh.utils import multiblockModifiers


@pytest.mark.parametrize( "keepPartialAttributes, nb_pt_attributes, nb_cell_attributes, nb_field_attributes", [
    ( False, 0, 16, 1 ),
    ( True, 2, 30, 1 ),
] )
def test_mergeBlocks(
    dataSetTest: vtkMultiBlockDataSet,
    nb_pt_attributes: int,
    nb_cell_attributes: int,
    nb_field_attributes: int,
    keepPartialAttributes: bool,
) -> None:
    """Test the merging of a multiblock."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )

    success: bool
    dataset: vtkUnstructuredGrid
    success, dataset = multiblockModifiers.mergeBlocks( vtkMultiBlockDataSetTest, keepPartialAttributes )

    assert success

    assert dataset.GetCellData().GetNumberOfArrays(
    ) == nb_cell_attributes, f"Expected {nb_cell_attributes} cell attributes after the merge, not {dataset.GetCellData().GetNumberOfArrays()}."

    assert dataset.GetPointData().GetNumberOfArrays(
    ) == nb_pt_attributes, f"Expected {nb_pt_attributes} point attributes after the merge, not {dataset.GetPointData().GetNumberOfArrays()}."

    assert dataset.GetFieldData().GetNumberOfArrays(
    ) == nb_field_attributes, f"Expected {nb_field_attributes} field attributes after the merge, not {dataset.GetFieldData().GetNumberOfArrays()}."
