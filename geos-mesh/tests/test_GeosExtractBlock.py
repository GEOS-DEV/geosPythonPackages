# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from geos.mesh.processing.GeosBlockExtractor import GeosBlockExtractor


@pytest.mark.parametrize( "extractFault, extractWell", [
    ( False, False ),
    ( True, False ),
    ( False, True ),
    ( True, True ),
] )
def test_GeosExtractBlock(
    dataSetTest: vtkMultiBlockDataSet,
    extractFault: bool,
    extractWell: bool,
) -> None:
    """Test GeosExtractBlock vtk filter."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "meshGeosExtractBlockTmp" )

    filter: GeosBlockExtractor = GeosBlockExtractor( multiBlockDataSet, extractFault, extractWell )
    filter.applyFilter()

    extractedVolume: vtkMultiBlockDataSet = filter.extractedGeosDomain.volume
    extractedFault: vtkMultiBlockDataSet = filter.extractedGeosDomain.fault
    extractedWell: vtkMultiBlockDataSet = filter.extractedGeosDomain.well

    assert extractedVolume.GetNumberOfBlocks() == 2

    if extractFault:
        assert extractedFault.GetNumberOfBlocks() == 2

    if extractWell:
        assert extractedWell.GetNumberOfBlocks() == 1
