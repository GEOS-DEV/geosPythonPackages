# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import logging
from geos.processing.post_processing.GeosBlockExtractor import GeosBlockExtractor
from geos.processing.post_processing.GeosBlockMerge import GeosBlockMerge
from geos.utils.Logger import ( CountWarningHandler, isHandlerInLogger )
from geos.utils.Errors import VTKError

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

    Raises:
        ChildProcessError: Error during the call of GeosBlockMerge or GeosBlockExtractor filter.
    """
    # Extract blocks
    blockExtractor: GeosBlockExtractor = GeosBlockExtractor( mesh,
                                                             extractFault=extractFault,
                                                             extractWell=extractWell,
                                                             speHandler=True )
    handler: logging.Handler = VTKHandler()
    if not isHandlerInLogger( handler, blockExtractor.logger ):
        blockExtractor.setLoggerHandler( handler )

    try:
        blockExtractor.applyFilter()
    except ( ValueError, TypeError ) as e:
        blockExtractor.logger.error( f"The filter { blockExtractor.logger.name } failed due to: { e }." )
        raise ChildProcessError( f"Error during the processing of: { blockExtractor.logger.name }." )
    except Exception as e:
        mess: str = f"The filter { blockExtractor.logger.name } failed du to: { e }"
        blockExtractor.logger.critical( mess, exc_info=True )
        raise ChildProcessError( f"Critical error during the processing of: { blockExtractor.logger.name }." )

    # Add to the warning counter the number of warning logged with the call of GeosBlockExtractor filter
    warningCounter.addExternalWarningCount( blockExtractor.nbWarnings )

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

    Raises:
        ChildProcessError: Error during the call of GeosBlockMerge filter.
    """
    loggerName = f"GEOS Block Merge for the domain { domainToMerge }"
    mergeBlockFilter: GeosBlockMerge = GeosBlockMerge( mesh, convertSurfaces, True, loggerName )
    handler: logging.Handler = VTKHandler()
    if not isHandlerInLogger( handler, mergeBlockFilter.logger ):
        mergeBlockFilter.setLoggerHandler( handler )

    try:
        mergeBlockFilter.applyFilter()
    except ( ValueError, VTKError ) as e:
        mergeBlockFilter.logger.error( f"The filter { mergeBlockFilter.logger.name } failed due to: { e }" )
        raise ChildProcessError( f"Error during the processing of: { loggerName }." )
    except Exception as e:
        mess: str = f"The filter { mergeBlockFilter.logger.name } failed due to: { e }"
        mergeBlockFilter.logger.critical( mess, exc_info=True )
        raise ChildProcessError( f"Critical error during the processing of: { loggerName }." )

    # Add to the warning counter the number of warning logged with the call of GeosBlockMerge filter
    warningCounter.addExternalWarningCount( mergeBlockFilter.nbWarnings )

    mergedBlocks: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
    mergedBlocks.ShallowCopy( mergeBlockFilter.getOutput() )

    return mergedBlocks
