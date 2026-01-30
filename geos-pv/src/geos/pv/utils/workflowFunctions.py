# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
from geos.processing.post_processing.GeosBlockExtractor import GeosBlockExtractor
from geos.processing.post_processing.GeosBlockMerge import GeosBlockMerge
from geos.utils.Logger import CountWarningHandler

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from paraview.detail.loghandler import ( VTKHandler )  # type: ignore[import-not-found]


def doExtractAndMerge(
    mesh: vtkMultiBlockDataSet,
    outputCells: vtkMultiBlockDataSet,
    outputFaults: vtkMultiBlockDataSet,
    outputWells: vtkMultiBlockDataSet,
    extractFault: bool,
    extractWell: bool,
    warningCounter: CountWarningHandler,
) -> None:
    """Apply block extraction and merge.

    Args:
        mesh (vtkMultiBlockDataSet): Mesh to process
        outputCells (vtkMultiBlockDataSet): Output volume mesh
        outputFaults (vtkMultiBlockDataSet): Output surface mesh
        outputWells (vtkMultiBlockDataSet): Output well mesh
        extractFault (bool): True if SurfaceElementRegion needs to be extracted, False otherwise.
        extractWell (bool): True if WellElementRegion needs to be extracted, False otherwise.
        warningCounter (logging.Handler): The plugin Handler to update with the number of warning log during the call of the extract and merge filters.
    """
    # Extract blocks
    blockExtractor: GeosBlockExtractor = GeosBlockExtractor( mesh,
                                                             extractFault=extractFault,
                                                             extractWell=extractWell,
                                                             speHandler=True )
    if len( blockExtractor.logger.handlers ) == 0:
        blockExtractor.setLoggerHandler( VTKHandler() )

    blockExtractor.applyFilter()
    warningCounter.addExternalWarningCount( blockExtractor.counter.warningCount )

    # recover output objects from GeosBlockExtractor filter and merge internal blocks
    volumeBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.volume
    outputCells.ShallowCopy( mergeBlocksFilter( volumeBlockExtracted, warningCounter, False, "Volume" ) )
    outputCells.Modified()

    if extractFault:
        faultBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.fault
        outputFaults.ShallowCopy( mergeBlocksFilter( faultBlockExtracted, warningCounter, True, "Fault" ) )
        outputFaults.Modified()

    if extractWell:
        wellBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.well
        outputWells.ShallowCopy( mergeBlocksFilter( wellBlockExtracted, warningCounter, False, "Well" ) )
        outputWells.Modified()

    return


def mergeBlocksFilter(
    mesh: vtkMultiBlockDataSet,
    warningCounter: CountWarningHandler,
    convertSurfaces: bool = False,
    domainToMerge: str = "Volume",
) -> vtkMultiBlockDataSet:
    """Apply vtk merge block filter on input multi block mesh.

    Args:
        mesh (vtkMultiBlockDataSet): Mesh to merge.
        warningCounter (logging.Handler): The plugin Handler to update with the number of warning log during the call of the extract and merge filters.
        convertSurfaces (bool, optional): True to convert surface from vtkUnstructuredGrid to vtkPolyData.
            Defaults to False.
        domainToMerge (str, optional): The name of the GEOS domain processed.
            Defaults to "Volume".

    Returns:
        vtkMultiBlockDataSet: Mesh composed of internal merged blocks.
    """
    loggerName = f"GEOS Block Merge for the domain { domainToMerge }"
    mergeBlockFilter: GeosBlockMerge = GeosBlockMerge( mesh, convertSurfaces, True, loggerName )
    if len( mergeBlockFilter.logger.handlers ) == 0:
        mergeBlockFilter.setLoggerHandler( VTKHandler() )
    mergeBlockFilter.applyFilter()
    mergedBlocks: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
    mergedBlocks.ShallowCopy( mergeBlockFilter.getOutput() )
    warningCounter.addExternalWarningCount( mergeBlockFilter.counter.warningCount )
    return mergedBlocks
