# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from geos.mesh.utils.multiblockHelpers import getBlockNameFromIndex, getBlockElementIndexesFlatten
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
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "geosOutput2Ranks" )

    geosBlockExtractor: GeosBlockExtractor = GeosBlockExtractor( multiBlockDataSet, extractFault, extractWell )
    geosBlockExtractor.applyFilter()

    extractedVolume: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.volume

    assert extractedVolume.GetNumberOfBlocks() == 1
    assert getBlockElementIndexesFlatten( extractedVolume ) == [ 2, 3 ]
    assert getBlockNameFromIndex( extractedVolume, 1 ) == "Region"

    if extractFault:
        extractedFault: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.fault
        assert extractedFault.GetNumberOfBlocks() == 1
        assert getBlockElementIndexesFlatten( extractedFault ) == [ 2, 3 ]
        assert getBlockNameFromIndex( extractedFault, 1 ) == "Fault"

    if extractWell:
        extractedWell: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.well
        assert extractedWell.GetNumberOfBlocks() == 2
        assert getBlockElementIndexesFlatten( extractedWell ) == [ 2, 4 ]
        assert getBlockNameFromIndex( extractedWell, 1 ) == "wellRegion1"
        assert getBlockNameFromIndex( extractedWell, 3 ) == "wellRegion2"
