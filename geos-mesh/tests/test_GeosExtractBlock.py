# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from geos.mesh.processing.GeosBlockExtractor import GeosBlockExtractor


@pytest.mark.parametrize( "extractFaults, extractWells", [
    ( False, False ),
    ( True, False ),
    ( False, True ),
    ( True, True ),
] )
def test_GeosExtractBlock(
    dataSetTest: vtkMultiBlockDataSet,
    extractFaults: bool,
    extractWells: bool,
) -> None:
    """Test GeosExtractBlock vtk filter."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "meshGeosExtractBlockTmp" )

    filter: GeosBlockExtractor = GeosBlockExtractor( multiBlockDataSet, extractFaults, extractWells )
    assert filter.applyFilter()

    extractVolume: vtkMultiBlockDataSet = filter.getOutput( 0 )
    extractFault: vtkMultiBlockDataSet = filter.getOutput( 1 )
    extractWell: vtkMultiBlockDataSet = filter.getOutput( 2 )

    assert extractVolume.GetNumberOfBlocks() == 2

    if extractFaults:
        assert extractFault.GetNumberOfBlocks() == 2

    if extractWells:
        assert extractWell.GetNumberOfBlocks() == 1
