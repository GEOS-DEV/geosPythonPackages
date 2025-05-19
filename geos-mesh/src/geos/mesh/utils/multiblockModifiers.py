# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing import Union, cast

from vtkmodules.vtkCommonDataModel import ( vtkCompositeDataSet, vtkDataObjectTreeIterator, vtkMultiBlockDataSet,
                                            vtkUnstructuredGrid )
from vtkmodules.vtkFiltersCore import vtkAppendDataSets
from geos.mesh.utils.arrayModifiers import fillAllPartialAttributes

__doc__ = """Function to process VTK multiblock datasets. """


# TODO : fix function for keepPartialAttributes = True
def mergeBlocks(
    input: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    keepPartialAttributes: bool = False,
) -> vtkUnstructuredGrid:
    """Merge all blocks of a multi block mesh.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet ): composite
            object to merge blocks
        keepPartialAttributes (bool): if True, keep partial attributes after merge.

            Defaults to False.

    Returns:
        vtkUnstructuredGrid: merged block object

    """
    if keepPartialAttributes:
        fillAllPartialAttributes( input, False )
        fillAllPartialAttributes( input, True )

    af = vtkAppendDataSets()
    af.MergePointsOn()
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( input )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        block: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( iter.GetCurrentDataObject() )
        af.AddInputData( block )
        iter.GoToNextItem()
    af.Update()
    return af.GetOutputDataObject( 0 )
