# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from geos.mesh.utils.multiblockHelpers import getBlockNameFromIndex
from geos.processing.post_processing.GeosBlockExtractor import GeosBlockExtractor


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

    geosBlockExtractor: GeosBlockExtractor = GeosBlockExtractor( multiBlockDataSet, extractFault, extractWell )
    geosBlockExtractor.applyFilter()

    extractedVolume: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.volume
    extractedFault: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.fault
    extractedWell: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.well

    assert extractedVolume.GetNumberOfBlocks() == 2
    assert getBlockNameFromIndex( extractedVolume, 1 ) == "domain"
    assert getBlockNameFromIndex( extractedVolume, 2 ) == "emptyDomain"

    if extractFault:
        assert extractedFault.GetNumberOfBlocks() == 2
        assert getBlockNameFromIndex( extractedFault, 1 ) == "fracture"
        assert getBlockNameFromIndex( extractedFault, 2 ) == "emptyFracture"

    if extractWell:
        assert extractedWell.GetNumberOfBlocks() == 1
        assert getBlockNameFromIndex( extractedWell, 1 ) == "well"
