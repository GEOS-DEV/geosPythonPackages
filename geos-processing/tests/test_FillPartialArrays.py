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
        "deltaPressure": None  # On cells
    } ),
    ( {
        "totalDisplacement": None  # On points
    } ),
    ( {
        "deltaPressure": None,
        "totalDisplacement": None
    } ),
    ( {
        "deltaPressure": [ 4 ]
    } ),
    ( {
        "totalDisplacement": [ 4, 4, 4 ]
    } ),
    ( {
        "deltaPressure": [ 4 ],
        "totalDisplacement": [ 4, 4, 4 ]
    } ),
    ( {
        "deltaPressure": None,
        "totalDisplacement": [ 4, 4, 4 ]
    } ),
    ( {
        "deltaPressure": [ 4 ],
        "totalDisplacement": None
    } ),
] )
def test_FillPartialArrays(
    dataSetTest: vtkMultiBlockDataSet,
    dictAttributesValues: dict[ str, Any ],
) -> None:
    """Test FillPartialArrays vtk filter."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "geosOutput2Ranks" )

    fillPartialArraysFilter: FillPartialArrays = FillPartialArrays( multiBlockDataSet, dictAttributesValues )
    fillPartialArraysFilter.applyFilter()


def test_FillPartialArraysRaises( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test the raises of FillPartialArray."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "geosOutput2Ranks" )
    fillPartialArraysFilter: FillPartialArrays

    # Attribute not in the mesh
    with pytest.raises( AttributeError ):
        fillPartialArraysFilter = FillPartialArrays( multiBlockDataSet, { "poro": None } )
        fillPartialArraysFilter.applyFilter()

    # To many value given
    with pytest.raises( ValueError ):
        fillPartialArraysFilter = FillPartialArrays( multiBlockDataSet, { "deltaPressure": [ 4, 4, 4 ] } )
        fillPartialArraysFilter.applyFilter()

    # Not enough value given
    with pytest.raises( ValueError ):
        fillPartialArraysFilter = FillPartialArrays( multiBlockDataSet, { "totalDisplacement": [ 4, 4 ] } )
        fillPartialArraysFilter.applyFilter()
