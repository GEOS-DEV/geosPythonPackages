# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file


from geos.processing.post_processing.GeosBlockExtractor import GeosBlockExtractor
from geos.processing.post_processing.GeosBlockMerge import GeosBlockMerge

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from paraview.detail.loghandler import ( VTKHandler ) # type: ignore[import-not-found]


def doExtractAndMerge(
    mesh: vtkMultiBlockDataSet,
    outputCells: vtkMultiBlockDataSet,
    outputFaults: vtkMultiBlockDataSet,
    outputWells: vtkMultiBlockDataSet,
    extractFault: bool,
    extractWell: bool,
) -> None:
    """Apply block extraction and merge.

    Args:
        mesh (vtkMultiBlockDataSet): Mesh to process.
        outputCells (vtkMultiBlockDataSet): Output volume mesh.
        outputFaults (vtkMultiBlockDataSet): Output surface mesh.
        outputWells (vtkMultiBlockDataSet): Output well mesh.
    """
    # Extract blocks
    blockExtractor: GeosBlockExtractor = GeosBlockExtractor( mesh, extractFault=extractFault, extractWell=extractWell, speHandler=True )
    if not blockExtractor.logger.hasHandlers():
        blockExtractor.setLoggerHandler( VTKHandler() )
    blockExtractor.applyFilter()

    # recover output objects from GeosBlockExtractor filter and merge internal blocks
    volumeBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.volume
    outputCells.ShallowCopy( mergeBlocksFilter( volumeBlockExtracted, False ) )
    outputCells.Modified()

    if extractFault:
        faultBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.fault
        outputFaults.ShallowCopy( mergeBlocksFilter( faultBlockExtracted, True ) )
        outputFaults.Modified()

    if extractWell:
        wellBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.well
        outputWells.ShallowCopy( mergeBlocksFilter( wellBlockExtracted, False ) )
        outputWells.Modified()

    return

def mergeBlocksFilter( mesh: vtkMultiBlockDataSet,
                        convertSurfaces: bool = False, ) -> vtkMultiBlockDataSet:
    """Apply vtk merge block filter on input multi block mesh.

    Args:
        mesh (vtkMultiBlockDataSet): Mesh to merge.
        convertSurfaces (bool, optional): True to convert surface from vtkUnstructuredGrid to vtkPolyData.
            Defaults to False.

    Returns:
        vtkMultiBlockDataSet: Mesh composed of internal merged blocks.
    """
    mergeBlockFilter: GeosBlockMerge = GeosBlockMerge( mesh, convertSurfaces, True )
    if not mergeBlockFilter.logger.hasHandlers():
        mergeBlockFilter.setLoggerHandler( VTKHandler() )
    mergeBlockFilter.applyFilter()
    mergedBlocks: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
    mergedBlocks.ShallowCopy( mergeBlockFilter.getOutput() )
    return mergedBlocks
