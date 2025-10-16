# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkUnstructuredGrid
from geos.mesh.utils import multiblockModifiers


@pytest.mark.parametrize( "keepPartialAttributes, nbPointAttributes, nbCellAttributes, nbFieldAttributes", [
    ( False, 0, 16, 1 ),
    ( True, 2, 30, 1 ),
] )
def test_mergeBlocks(
    dataSetTest: vtkMultiBlockDataSet,
    nbPointAttributes: int,
    nbCellAttributes: int,
    nbFieldAttributes: int,
    keepPartialAttributes: bool,
) -> None:
    """Test the merging of a multiblock."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )

    dataset: vtkUnstructuredGrid
    dataset = multiblockModifiers.mergeBlocks( vtkMultiBlockDataSetTest, keepPartialAttributes )

    assert dataset.GetCellData().GetNumberOfArrays(
    ) == nbCellAttributes, f"Expected {nbCellAttributes} cell attributes after the merge, not {dataset.GetCellData().GetNumberOfArrays()}."

    assert dataset.GetPointData().GetNumberOfArrays(
    ) == nbPointAttributes, f"Expected {nbPointAttributes} point attributes after the merge, not {dataset.GetPointData().GetNumberOfArrays()}."

    assert dataset.GetFieldData().GetNumberOfArrays(
    ) == nbFieldAttributes, f"Expected {nbFieldAttributes} field attributes after the merge, not {dataset.GetFieldData().GetNumberOfArrays()}."
