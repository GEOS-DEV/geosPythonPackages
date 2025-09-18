# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
from typing import Union
from vtkmodules.vtkCommonDataModel import ( vtkCompositeDataSet, vtkDataObjectTreeIterator, vtkMultiBlockDataSet,
                                            vtkUnstructuredGrid )
from vtkmodules.vtkFiltersCore import vtkAppendDataSets
from geos.mesh.utils.arrayModifiers import fillAllPartialAttributes
from geos.utils.Logger import getLogger, Logger

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
        bool: True if the mesh was correctly merged. False otherwise
        vtkUnstructuredGrid: Merged dataset if success, empty dataset otherwise.

    .. Note::
        Default filling values:
            - 0 for uint data.
            - -1 for int data.
            - nan for float data.

    .. Warning:: This function will not work properly if there are duplicated cell IDs in the different blocks of the input mesh.

    """
    if logger is None:
        logger = getLogger( "mergeBlocks", True )

    outputMesh = vtkUnstructuredGrid()

    if not inputMesh.IsA( "vtkMultiBlockDataSet" ) and not inputMesh.IsA( "vtkCompositeDataSet" ):
        logger.error(
            "The input mesh should be either a vtkMultiBlockDataSet or a vtkCompositeDataSet. Cannot proceed with the block merge."
        )
        return False, outputMesh

    # Fill the partial attributes with default values to keep them during the merge.
    if keepPartialAttributes and not fillAllPartialAttributes( inputMesh, logger ):
        logger.error( "Failed to fill partial attributes. Cannot proceed with the block merge." )
        return False, outputMesh

    af: vtkAppendDataSets = vtkAppendDataSets()
    af.MergePointsOn()
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( inputMesh )
    iterator.VisitOnlyLeavesOn()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        block: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( iterator.GetCurrentDataObject() )
        af.AddInputData( block )
        iterator.GoToNextItem()
    af.Update()

    outputMesh.ShallowCopy( af.GetOutputDataObject( 0 ) )

    return True, outputMesh
