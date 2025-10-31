# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from typing import Any
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from geos.processing.generic_processing_tools.FillPartialArrays import FillPartialArrays


@pytest.mark.parametrize( "dictAttributesValues", [
    ( {
        "PORO": None
    } ),
    ( {
        "PERM": None
    } ),
    ( {
        "PORO": None,
        "PERM": None
    } ),
    ( {
        "PORO": [ 4 ]
    } ),
    ( {
        "PERM": [ 4, 4, 4 ]
    } ),
    ( {
        "PORO": [ 4 ],
        "PERM": [ 4, 4, 4 ]
    } ),
    ( {
        "PORO": None,
        "PERM": [ 4, 4, 4 ]
    } ),
    ( {
        "PORO": [ 4 ],
        "PERM": None
    } ),
] )
def test_FillPartialArrays(
    dataSetTest: vtkMultiBlockDataSet,
    dictAttributesValues: dict[ str, Any ],
) -> None:
    """Test FillPartialArrays vtk filter."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "multiblock" )

    fillPartialArraysFilter: FillPartialArrays = FillPartialArrays( multiBlockDataSet, dictAttributesValues )
    assert fillPartialArraysFilter.applyFilter()
