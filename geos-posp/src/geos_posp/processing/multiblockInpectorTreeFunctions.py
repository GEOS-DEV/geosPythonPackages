# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing import Union, cast

from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataObject,
    vtkDataObjectTreeIterator,
    vtkMultiBlockDataSet,
)

__doc__ = """Functions to explore and process multiblock inspector tree."""


def getBlockName( input: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> str:
    """Get the name of input block.

    If input is a vtkMultiBlockDataSet or vtkCompositeDataSet, returns the name
    of the lowest level unique child block.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block object.

    Returns:
        str: name of the block in the tree.

    """
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( input )
    iter.VisitOnlyLeavesOff()
    iter.GoToFirstItem()
    blockName: str = "Block"
    while iter.GetCurrentDataObject() is not None:
        blockName = iter.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() )
        block: vtkDataObject = iter.GetCurrentDataObject()
        nbBlocks: int = 99
        if isinstance( block, vtkMultiBlockDataSet ):
            block1: vtkMultiBlockDataSet = block
            nbBlocks = block1.GetNumberOfBlocks()

        # stop if multiple children
        if nbBlocks > 1:
            break

        iter.GoToNextItem()
    return blockName


def getBlockNameFromIndex( input: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ], index: int ) -> str:
    """Get the name of a block from input multiblock and block flat index.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block object.
        index (int): flat index of the block to get the name

    Returns:
        str: name of the block in the tree.

    """
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( input )
    iter.VisitOnlyLeavesOff()
    iter.GoToFirstItem()
    blockName: str = "Block"
    while iter.GetCurrentDataObject() is not None:
        blockName = iter.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() )
        if iter.GetCurrentFlatIndex() == index:
            break
        iter.GoToNextItem()
    return blockName


def getBlockIndexFromName( input: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ], name: str ) -> int:
    """Get block flat index from name of node in the vtkMultiBlockDataSet tree.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block object.
        name (str): name of the block to get the index in the tree.

    Returns:
        int: index of the block if found, -1 otherwise.
    """
    blockIndex: int = -1
    # initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( input )
    iter.VisitOnlyLeavesOff()
    iter.GoToFirstItem()
    found: bool = False
    while iter.GetCurrentDataObject() is not None:
        blockName: str = iter.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() )
        blockIndex = iter.GetCurrentFlatIndex()
        if blockName.lower() == name.lower():
            found = True
            break
        iter.GoToNextItem()
    return blockIndex if found else -1


def getElementaryCompositeBlockIndexes( input: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> dict[ str, int ]:
    """Get indexes of composite block that contains elementrary blocks.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block object.

    Returns:
        dict[str, int]: dictionary that contains names as keys and flat indices
        as values of the parent composite blocks of elementary blocks.
    """
    # initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( input )
    iter.VisitOnlyLeavesOff()
    iter.GoToFirstItem()

    elementaryBlockIndexes: dict[ str, int ] = {}
    while iter.GetCurrentDataObject() is not None:
        curIndex: int = iter.GetCurrentFlatIndex()
        curName: str = iter.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() )
        curIsComposite = iter.GetCurrentDataObject().IsA( "vtkMultiBlockDataSet" )
        iter.GoToNextItem()
        nextIsNotNone = iter.GetCurrentDataObject() is not None
        if ( curIsComposite and nextIsNotNone and ( not iter.GetCurrentDataObject().IsA( "vtkMultiBlockDataSet" ) ) ):
            elementaryBlockIndexes[ curName ] = curIndex

    return elementaryBlockIndexes


def getBlockElementIndexesFlatten( input: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> list[ int ]:
    """Get a flatten list that contains flat indexes of elementary blocks.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block object.

    Returns:
         list[int]: list of flat indexes
    """
    return [ i for li in getBlockElementIndexes( input ) for i in li ]


def getBlockElementIndexes( input: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] ) -> list[ list[ int ] ]:
    """Get a list of list that contains flat indexes of elementary blocks.

    Each sublist contains the indexes of elementary blocks that belongs to a
    same parent node.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block object.

    Returns:
         list[list[int]]: list of list of flat indexes
    """
    # initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( input )
    iter.VisitOnlyLeavesOff()
    iter.GoToFirstItem()

    blockElementIndexes: list[ list[ int ] ] = []
    indexes: list[ int ] = []
    while iter.GetCurrentDataObject() is not None:
        curIndex: int = iter.GetCurrentFlatIndex()
        if iter.GetCurrentDataObject().IsA( "vtkMultiBlockDataSet" ):
            # change of parent node, then add the indexes of the previous
            # vtkMultiBlockDataSet if needed
            if len( indexes ) > 0:
                blockElementIndexes += [ indexes ]
            # reinitialize the list of indexes of included blocks
            indexes = []
        else:
            indexes += [ curIndex ]
        iter.GoToNextItem()

    # add the indexes of the last vtkMultiBlockDataSet if needed
    if len( indexes ) > 0:
        blockElementIndexes += [ indexes ]
    return blockElementIndexes


def getBlockFromFlatIndex( multiBlock: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
                           blockIndex: int ) -> vtkDataObject:
    """Get the block with blockIndex from input vtkMultiBlockDataSet.

    Args:
        multiBlock (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block
        blockIndex (int): block index

    Returns:
        vtkMultiBlockDataSet: block if it exists, None otherwise
    """
    block: vtkDataObject
    # initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlock )
    iter.VisitOnlyLeavesOff()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        if iter.GetCurrentFlatIndex() == blockIndex:
            block = iter.GetCurrentDataObject()
            break
        iter.GoToNextItem()
    return block


def getBlockFromName( multiBlock: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ], blockName: str ) -> vtkDataObject:
    """Get the block named blockName from input vtkMultiBlockDataSet.

    Args:
        multiBlock (vtkMultiBlockDataSet | vtkCompositeDataSet): input multi block
        blockName (str): block name

    Returns:
        vtkDataObject: block if it exists, None otherwise
    """
    block: vtkDataObject
    # initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlock )
    iter.VisitOnlyLeavesOff()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        if iter.GetCurrentMetaData().Get( vtkMultiBlockDataSet.NAME() ) == blockName:
            block = vtkMultiBlockDataSet.SafeDownCast( iter.GetCurrentDataObject() )
            break
        iter.GoToNextItem()
    return block
