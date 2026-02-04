# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez, Jacques Franc
from typing import Union
import logging

from vtkmodules.vtkCommonDataModel import ( vtkCompositeDataSet, vtkDataObjectTreeIterator, vtkMultiBlockDataSet,
                                            vtkUnstructuredGrid, vtkDataSet )
from packaging.version import Version
from vtkmodules.vtkCommonCore import vtkLogger
from geos.utils.Errors import VTKError

# TODO: remove this condition when all codes are adapted for VTK newest version.
import vtk
if Version( vtk.__version__ ) >= Version( "9.5" ):
    from vtkmodules.vtkFiltersParallel import vtkMergeBlocks
else:
    from vtkmodules.vtkFiltersCore import vtkAppendDataSets

from geos.mesh.utils.arrayModifiers import fillAllPartialAttributes
from geos.utils.Logger import ( getLogger, Logger, VTKCaptureLog, RegexExceptionFilter )

__doc__ = """Contains a method to merge blocks of a VTK multiblock dataset."""


def mergeBlocks(
    inputMesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    keepPartialAttributes: bool = False,
    logger: Union[ Logger, None ] = None,
) -> vtkUnstructuredGrid:
    """Merge all blocks of a multiblock dataset mesh with the possibility of keeping all partial attributes present in the initial mesh.

    Args:
        inputMesh (vtkMultiBlockDataSet | vtkCompositeDataSet ): The input multiblock dataset to merge.
        keepPartialAttributes (bool): If False (default), only global attributes are kept during the merge. If True, partial attributes are filled with default values and kept in the output mesh.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        vtkUnstructuredGrid: Merged dataset or input mesh if it's already a single block.

    Raises:
        geos.utils.VTKError (): Error raised during call of VTK function

    .. Note::
        Default filling values:
            - 0 for uint data.
            - -1 for int data.
            - nan for float data.

    .. Warning:: This function will not work properly if there are duplicated cell IDs in the different blocks of the input mesh.

    """
    vtkErrorLogger: Logger
    if logger is None:
        vtkErrorLogger = getLogger( "Merge blocks", True )
    else:
        vtkErrorLogger = logging.getLogger( f"{ logger.name } vtkError Logger" )
        vtkErrorLogger.setLevel( logging.INFO )
        vtkErrorLogger.addHandler( logger.handlers[ 0 ] )
        vtkErrorLogger.propagate = False

    vtkLogger.SetStderrVerbosity( vtkLogger.VERBOSITY_ERROR )
    vtkErrorLogger.addFilter( RegexExceptionFilter() )  # will raise VTKError if captured VTK Error

    # Fill the partial attributes with default values to keep them during the merge.
    if keepPartialAttributes:
        fillAllPartialAttributes( inputMesh, logger )

    outputMesh: vtkUnstructuredGrid

    if Version( vtk.__version__ ) >= Version( "9.5" ):
        filter: vtkMergeBlocks = vtkMergeBlocks()
        filter.SetInputData( inputMesh )
        filter.Update()

        outputMesh = filter.GetOutputDataObject( 0 )

    else:
        if inputMesh.IsA( "vtkDataSet" ):
            vtkErrorLogger.warning( "Input mesh is already a single block." )
            outputMesh = vtkUnstructuredGrid.SafeDownCast( inputMesh )
        else:

            with VTKCaptureLog() as captured_log:

                af: vtkAppendDataSets = vtkAppendDataSets()
                af.MergePointsOn()
                iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
                iterator.SetDataSet( inputMesh )
                iterator.VisitOnlyLeavesOn()
                iterator.GoToFirstItem()
                while iterator.GetCurrentDataObject() is not None:
                    block: vtkDataSet = vtkDataSet.SafeDownCast( iterator.GetCurrentDataObject() )
                    af.AddInputData( block )
                    iterator.GoToNextItem()
                af.Update()
                captured_log.seek( 0 )
                captured = captured_log.read().decode()

            if captured != "":
                vtkErrorLogger.error( captured.strip() )
                # raise VTKError( captured.strip() )
                # pass

            outputMesh = af.GetOutputDataObject( 0 )

            if outputMesh is None:
                raise VTKError( "Something went wrong in VTK" )

    return outputMesh
