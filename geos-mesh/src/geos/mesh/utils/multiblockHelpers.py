# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
from typing import Union
from vtkmodules.vtkCommonDataModel import ( vtkCompositeDataSet, vtkDataObject, vtkDataObjectTreeIterator,
                                            vtkMultiBlockDataSet )
from vtkmodules.vtkFiltersExtraction import vtkExtractBlock

__doc__ = """
Functions to explore VTK multiblock datasets.

Methods include:
    - getters for blocks names and indexes
    - block extractor
"""


def getBlockNames( multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> list[ str ]:
    """Get the name of all blocks of the multiBlockDataSet.

    Args:
        multiBlockDataSet (Union[vtkMultiBlockDataSet, vtkCompositeDataSet]): MultiBlockDataSet with the block names to get.

    Returns:
        list[str]: list of the names of the block in the multiBlockDataSet.
    """
    listBlockNames: list[ str ] = []
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOff()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        listBlockNames.append( iterator.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() ) )
        iterator.GoToNextItem()
    return listBlockNames


def getBlockNameFromIndex( multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ], index: int ) -> str:
    """Get the name of a multiBlockDataSet block with its flat index.

    Args:
        multiBlockDataSet (Union[vtkMultiBlockDataSet, vtkCompositeDataSet]): MultiBlockDataSet with the block to get the name.
        index (int): Flat index of the block to get the name.

    Returns:
        str: name of the block in the tree.
    """
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOff()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        if iterator.GetCurrentFlatIndex() == index:
            return iterator.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() )
        iterator.GoToNextItem()

    raise ValueError( "The block index is not an index of a block in the mesh" )


def getBlockIndexFromName( multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
                           blockName: str ) -> int:
    """Get flat index of a multiBlockDataSet block with its name.

    Args:
        multiBlockDataSet (Union[vtkMultiBlockDataSet, vtkCompositeDataSet]): MultiBlockDataSet with the block to get the index.
        blockName (str): Name of the block to get the flat index.

    Returns:
        int: Flat index of the block if found, -1 otherwise.
    """
    blockIndex: int = -1
    # initialize data object tree iterator
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOff()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        currentBlockName: str = iterator.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() )
        blockIndex = iterator.GetCurrentFlatIndex()
        if currentBlockName == blockName:
            return blockIndex
        iterator.GoToNextItem()
    return -1


def getElementaryCompositeBlockIndexes(
        multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> dict[ str, int ]:
    """Get indexes of composite block of the multiBlockDataSet that contains elementary blocks.

    Args:
        multiBlockDataSet (Union[vtkMultiBlockDataSet, vtkCompositeDataSet]): MultiBlockDataSet.

    Returns:
        dict[str, int]: Dictionary that contains names as keys and flat indices
        as values of the parent composite blocks of elementary blocks.
    """
    # initialize data object tree iterator
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOff()
    iterator.GoToFirstItem()

    dictCompositeBlocks: dict[ str, int ] = {}
    while iterator.GetCurrentDataObject() is not None:
        curIndex: int = iterator.GetCurrentFlatIndex()
        curName: str = iterator.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() )
        curIsComposite = iterator.GetCurrentDataObject().IsA( "vtkMultiBlockDataSet" )
        iterator.GoToNextItem()
        nextIsNotNone = iterator.GetCurrentDataObject() is not None
        if ( curIsComposite and nextIsNotNone
             and ( not iterator.GetCurrentDataObject().IsA( "vtkMultiBlockDataSet" ) ) ):
            dictCompositeBlocks[ curName ] = curIndex

    return dictCompositeBlocks


def getBlockElementIndexesFlatten(
        multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> list[ int ]:
    """Get a flatten list that contains flat indexes of elementary blocks.

    Args:
        multiBlockDataSet (Union[vtkMultiBlockDataSet, vtkCompositeDataSet]): MultiBlockDataSet with the block flat indexes to get.

    Returns:
         list[int]: List of flat indexes.
    """
    return [ i for li in getBlockElementIndexes( multiBlockDataSet ) for i in li ]


def getBlockElementIndexes(
        multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> list[ list[ int ] ]:
    """Get a list of list that contains flat indexes of elementary blocks.

    Each sublist contains the indexes of elementary blocks that belongs to a
    same parent node.

    Args:
        multiBlockDataSet (Union[vtkMultiBlockDataSet, vtkCompositeDataSet]): MultiBlockDataSet with the block indexes to get.

    Returns:
         list[list[int]]: List of list of flat indexes.
    """
    # initialize data object tree iterator
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOff()
    iterator.GoToFirstItem()

    blockElementIndexes: list[ list[ int ] ] = []
    indexes: list[ int ] = []
    while iterator.GetCurrentDataObject() is not None:
        curIndex: int = iterator.GetCurrentFlatIndex()
        if iterator.GetCurrentDataObject().IsA( "vtkMultiBlockDataSet" ):
            # change of parent node, then add the indexes of the previous
            # vtkMultiBlockDataSet if needed
            if len( indexes ) > 0:
                blockElementIndexes.append( indexes )
            # reinitialize the list of indexes of included blocks
            indexes = []
        else:
            indexes.append( curIndex )
        iterator.GoToNextItem()

    # add the indexes of the last vtkMultiBlockDataSet if needed
    if len( indexes ) > 0:
        blockElementIndexes.append( indexes )
    return blockElementIndexes


def getBlockFromFlatIndex( multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
                           blockIndex: int ) -> Union[ None, vtkDataObject ]:
    """Get the block with blockIndex from the vtkMultiBlockDataSet.

    Args:
        multiBlockDataSet (Union[vtkMultiBlockDataSet, vtkCompositeDataSet]): MultiBlockDataSet with the block to get.
        blockIndex (int): The block index og the block to get.

    Returns:
        Union[None, vtkDataObject]: The block with the flat index if it exists, None otherwise
    """
    # initialize data object tree iterator
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOff()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        if iterator.GetCurrentFlatIndex() == blockIndex:
            return iterator.GetCurrentDataObject()
        iterator.GoToNextItem()
    return None


def getBlockFromName( multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
                      blockName: str ) -> Union[ None, vtkDataObject ]:
    """Get the block named blockName from the vtkMultiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): MultiBlockDataSet with the block to get.
        blockName (str): The name of the block to get.

    Returns:
        Union[None, vtkDataObject]: The block name blockName if it exists, None otherwise
    """
    # initialize data object tree iterator
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOff()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        if iterator.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() ) == blockName:
            return iterator.GetCurrentDataObject()
        iterator.GoToNextItem()
    return None


def extractBlock( multiBlockDataSet: vtkMultiBlockDataSet, blockIndex: int ) -> vtkMultiBlockDataSet:
    """Extract the block with index blockIndex from multiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): multiblock dataset from which
            to extract the block
        blockIndex (int): block index to extract

    Returns:
        vtkMultiBlockDataSet: extracted block
    """
    extractBlockfilter: vtkExtractBlock = vtkExtractBlock()
    extractBlockfilter.SetInputData( multiBlockDataSet )
    extractBlockfilter.AddIndex( blockIndex )
    extractBlockfilter.Update()
    extractedBlock: vtkMultiBlockDataSet = extractBlockfilter.GetOutput()
    return extractedBlock
