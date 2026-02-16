# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkPolyData

from geos.mesh.utils.arrayHelpers import getAttributeSet
from geos.mesh.utils.multiblockHelpers import getBlockNameFromIndex, getBlockElementIndexesFlatten
from geos.processing.post_processing.GeosBlockExtractor import GeosBlockExtractor
from geos.processing.post_processing.GeosBlockMerge import GeosBlockMerge
from geos.utils.GeosOutputsConstants import getRockSuffixRenaming
from geos.utils.pieceEnum import Piece


@pytest.mark.parametrize( "extractFault, extractWell, convertFaultToSurface", [
    ( False, False, False ),
    ( True, False, False ),
    ( True, False, True ),
    ( False, True, False ),
    ( True, True, False ),
    ( True, True, True ),
] )
def test_GeosBlockMerge(
    dataSetTest: vtkMultiBlockDataSet,
    extractFault: bool,
    extractWell: bool,
    convertFaultToSurface: bool,
) -> None:
    """Test GeosBlockMerge vtk filter."""
    multiBlockDataSet: vtkMultiBlockDataSet = dataSetTest( "singlePhasePoromechanicsVTKOutput" )

    geosBlockExtractor: GeosBlockExtractor = GeosBlockExtractor( multiBlockDataSet, extractFault, extractWell )
    geosBlockExtractor.applyFilter()

    extractedVolume: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.volume
    geosMergeBlockVolume: GeosBlockMerge = GeosBlockMerge( extractedVolume )
    geosMergeBlockVolume.applyFilter()
    mergedVolume: vtkMultiBlockDataSet = geosMergeBlockVolume.getOutput()
    assert getBlockElementIndexesFlatten( mergedVolume ) == [ 1 ]
    assert getBlockNameFromIndex( mergedVolume, 1 ) == "Region"
    assert geosMergeBlockVolume.phaseNameDict[ "Rock" ] == { "rockPorosity", "rockPerm", "rock" }
    assert geosMergeBlockVolume.phaseNameDict[ "Fluid" ] == { "water" }

    dictAttributesToRenamed: dict[ str, str ] = getRockSuffixRenaming()
    setAttributesMergedVolume: set[ str ] = getAttributeSet( mergedVolume, Piece.CELLS )
    for attribute in dictAttributesToRenamed.values():
        assert attribute in setAttributesMergedVolume

    if extractFault:
        extractedFault: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.fault
        geosMergeBlockFault: GeosBlockMerge = GeosBlockMerge( extractedFault, convertFaultToSurface )
        geosMergeBlockFault.applyFilter()
        mergedFault: vtkMultiBlockDataSet = geosMergeBlockFault.getOutput()
        assert getBlockElementIndexesFlatten( mergedFault ) == [ 1 ]
        assert getBlockNameFromIndex( mergedFault, 1 ) == "Fault"

        if convertFaultToSurface:
            assert isinstance( mergedFault.GetDataSet( 1 ), vtkPolyData )

    if extractWell:
        extractedWell: vtkMultiBlockDataSet = geosBlockExtractor.extractedGeosDomain.well
        geosMergeBlockWell: GeosBlockMerge = GeosBlockMerge( extractedWell )
        geosMergeBlockWell.applyFilter()
        mergedWell: vtkMultiBlockDataSet = geosMergeBlockWell.getOutput()
        assert getBlockElementIndexesFlatten( mergedWell ) == [ 1, 2 ]
        assert getBlockNameFromIndex( mergedWell, 1 ) == "wellRegion1"
        assert getBlockNameFromIndex( mergedWell, 2 ) == "wellRegion2"
