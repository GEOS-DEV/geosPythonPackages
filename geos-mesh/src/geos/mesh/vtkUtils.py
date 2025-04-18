# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing import Union, cast

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import vtkmodules.util.numpy_support as vnp
from vtk import (  # type: ignore[import-untyped]
    VTK_CHAR, VTK_DOUBLE, VTK_FLOAT, VTK_INT, VTK_UNSIGNED_INT,
)
from vtkmodules.vtkCommonCore import (
    vtkCharArray,
    vtkDataArray,
    vtkDoubleArray,
    vtkFloatArray,
    vtkIntArray,
    vtkPoints,
    vtkUnsignedIntArray,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCellData,
    vtkCompositeDataSet,
    vtkDataObject,
    vtkDataObjectTreeIterator,
    vtkDataSet,
    vtkMultiBlockDataSet,
    vtkPlane,
    vtkPointData,
    vtkPointSet,
    vtkPolyData,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkFiltersCore import (
    vtk3DLinearGridPlaneCutter,
    vtkAppendDataSets,
    vtkArrayRename,
    vtkCellCenters,
    vtkPointDataToCellData,
)
from vtkmodules.vtkFiltersExtraction import vtkExtractBlock

from geos.mesh.multiblockInspectorTreeFunctions import (
    getBlockElementIndexesFlatten,
    getBlockFromFlatIndex,
)

__doc__ = """ Utilities to process vtk objects. """


def getAttributeSet( object: Union[ vtkMultiBlockDataSet, vtkDataSet ], onPoints: bool ) -> set[ str ]:
    """Get the set of all attributes from an object on points or on cells.

    Args:
        object (Any): object where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on
            cells.

    Returns:
        set[str]: set of attribute names present in input object.
    """
    attributes: dict[ str, int ]
    if isinstance( object, vtkMultiBlockDataSet ):
        attributes = getAttributesFromMultiBlockDataSet( object, onPoints )
    elif isinstance( object, vtkDataSet ):
        attributes = getAttributesFromDataSet( object, onPoints )
    else:
        raise TypeError( "Input object must be a vtkDataSet or vtkMultiBlockDataSet." )

    assert attributes is not None, "Attribute list is undefined."

    return set( attributes.keys() ) if attributes is not None else set()


def getAttributesWithNumberOfComponents(
    object: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet, vtkDataObject ],
    onPoints: bool,
) -> dict[ str, int ]:
    """Get the dictionnary of all attributes from object on points or cells.

    Args:
        object (Any): object where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on
            cells.

    Returns:
        dict[str, int]: dictionnary where keys are the names of the attributes
            and values the number of components.

    """
    attributes: dict[ str, int ]
    if isinstance( object, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        attributes = getAttributesFromMultiBlockDataSet( object, onPoints )
    elif isinstance( object, vtkDataSet ):
        attributes = getAttributesFromDataSet( object, onPoints )
    else:
        raise TypeError( "Input object must be a vtkDataSet or vtkMultiBlockDataSet." )
    return attributes


def getAttributesFromMultiBlockDataSet( object: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
                                        onPoints: bool ) -> dict[ str, int ]:
    """Get the dictionnary of all attributes of object on points or on cells.

    Args:
        object (vtkMultiBlockDataSet | vtkCompositeDataSet): object where to find
            the attributes.
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        dict[str, int]: Dictionnary of the names of the attributes as keys, and
            number of components as values.

    """
    attributes: dict[ str, int ] = {}
    # initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( object )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        blockAttributes: dict[ str, int ] = getAttributesFromDataSet( dataSet, onPoints )
        for attributeName, nbComponents in blockAttributes.items():
            if attributeName not in attributes:
                attributes[ attributeName ] = nbComponents

        iter.GoToNextItem()
    return attributes


def getAttributesFromDataSet( object: vtkDataSet, onPoints: bool ) -> dict[ str, int ]:
    """Get the dictionnary of all attributes of a vtkDataSet on points or cells.

    Args:
        object (vtkDataSet): object where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        dict[str, int]: List of the names of the attributes.
    """
    attributes: dict[ str, int ] = {}
    data: Union[ vtkPointData, vtkCellData ]
    sup: str = ""
    if onPoints:
        data = object.GetPointData()
        sup = "Point"
    else:
        data = object.GetCellData()
        sup = "Cell"
    assert data is not None, f"{sup} data was not recovered."

    nbAttributes = data.GetNumberOfArrays()
    for i in range( nbAttributes ):
        attributeName = data.GetArrayName( i )
        attribute = data.GetArray( attributeName )
        assert attribute is not None, f"Attribut {attributeName} is null"
        nbComponents = attribute.GetNumberOfComponents()
        attributes[ attributeName ] = nbComponents
    return attributes


def isAttributeInObject( object: Union[ vtkMultiBlockDataSet, vtkDataSet ], attributeName: str,
                         onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        object (vtkMultiBlockDataSet | vtkDataSet): input object
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise
    """
    if isinstance( object, vtkMultiBlockDataSet ):
        return isAttributeInObjectMultiBlockDataSet( object, attributeName, onPoints )
    elif isinstance( object, vtkDataSet ):
        return isAttributeInObjectDataSet( object, attributeName, onPoints )
    else:
        raise TypeError( "Input object must be a vtkDataSet or vtkMultiBlockDataSet." )


def isAttributeInObjectMultiBlockDataSet( object: vtkMultiBlockDataSet, attributeName: str, onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        object (vtkMultiBlockDataSet): input multiblock object
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise
    """
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( object )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        if isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
            return True
        iter.GoToNextItem()
    return False


def isAttributeInObjectDataSet( object: vtkDataSet, attributeName: str, onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        object (vtkDataSet): input object
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise
    """
    data: Union[ vtkPointData, vtkCellData ]
    sup: str = ""
    if onPoints:
        data = object.GetPointData()
        sup = "Point"
    else:
        data = object.GetCellData()
        sup = "Cell"
    assert data is not None, f"{sup} data was not recovered."
    return bool( data.HasArray( attributeName ) )


def getArrayInObject( object: vtkDataSet, attributeName: str, onPoints: bool ) -> npt.NDArray[ np.float64 ]:
    """Return the numpy array corresponding to input attribute name in table.

    Args:
        object (PointSet or UnstructuredGrid): input object
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        ArrayLike[float]: the array corresponding to input attribute name.
    """
    array: vtkDoubleArray = getVtkArrayInObject( object, attributeName, onPoints )
    nparray: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( array )  # type: ignore[no-untyped-call]
    return nparray


def getVtkArrayInObject( object: vtkDataSet, attributeName: str, onPoints: bool ) -> vtkDoubleArray:
    """Return the array corresponding to input attribute name in table.

    Args:
        object (PointSet or UnstructuredGrid): input object
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        vtkDoubleArray: the vtk array corresponding to input attribute name.
    """
    assert isAttributeInObject( object, attributeName, onPoints ), f"{attributeName} is not in input object."
    return object.GetPointData().GetArray( attributeName ) if onPoints else object.GetCellData().GetArray(
        attributeName )


def getNumberOfComponents(
    dataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet ],
    attributeName: str,
    onPoints: bool,
) -> int:
    """Get the number of components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataSet):
            dataSet where the attribute is.
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        int: number of components.
    """
    if isinstance( dataSet, vtkDataSet ):
        return getNumberOfComponentsDataSet( dataSet, attributeName, onPoints )
    elif isinstance( dataSet, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return getNumberOfComponentsMultiBlock( dataSet, attributeName, onPoints )
    else:
        raise AssertionError( "Object type is not managed." )


def getNumberOfComponentsDataSet( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> int:
    """Get the number of components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkDataSet): dataSet where the attribute is.
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        int: number of components.
    """
    array: vtkDoubleArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
    return array.GetNumberOfComponents()


def getNumberOfComponentsMultiBlock(
    dataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    attributeName: str,
    onPoints: bool,
) -> int:
    """Get the number of components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): multi block data Set where the attribute is.
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        int: number of components.
    """
    elementraryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( dataSet )
    for blockIndex in elementraryBlockIndexes:
        block: vtkDataSet = cast( vtkDataSet, getBlockFromFlatIndex( dataSet, blockIndex ) )
        if isAttributeInObject( block, attributeName, onPoints ):
            array: vtkDoubleArray = getVtkArrayInObject( block, attributeName, onPoints )
            return array.GetNumberOfComponents()
    return 0


def getComponentNames(
    dataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet, vtkDataObject ],
    attributeName: str,
    onPoints: bool,
) -> tuple[ str, ...]:
    """Get the name of the components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkDataSet | vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): dataSet
            where the attribute is.
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        tuple[str,...]: names of the components.

    """
    if isinstance( dataSet, vtkDataSet ):
        return getComponentNamesDataSet( dataSet, attributeName, onPoints )
    elif isinstance( dataSet, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return getComponentNamesMultiBlock( dataSet, attributeName, onPoints )
    else:
        raise AssertionError( "Object type is not managed." )


def getComponentNamesDataSet( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> tuple[ str, ...]:
    """Get the name of the components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkDataSet): dataSet where the attribute is.
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        tuple[str,...]: names of the components.

    """
    array: vtkDoubleArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
    componentNames: list[ str ] = []
    if array.GetNumberOfComponents() > 1:
        componentNames += [ array.GetComponentName( i ) for i in range( array.GetNumberOfComponents() ) ]
    return tuple( componentNames )


def getComponentNamesMultiBlock(
    dataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    attributeName: str,
    onPoints: bool,
) -> tuple[ str, ...]:
    """Get the name of the components of attribute in MultiBlockDataSet.

    Args:
        dataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): dataSet where the
            attribute is.
        attributeName (str): name of the attribute
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        tuple[str,...]: names of the components.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( dataSet )
    for blockIndex in elementaryBlockIndexes:
        block: vtkDataSet = cast( vtkDataSet, getBlockFromFlatIndex( dataSet, blockIndex ) )
        if isAttributeInObject( block, attributeName, onPoints ):
            return getComponentNamesDataSet( block, attributeName, onPoints )
    return ()


def fillPartialAttributes(
    multiBlockMesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    attributeName: str,
    nbComponents: int,
    onPoints: bool = False,
) -> bool:
    """Fill input partial attribute of multiBlockMesh with nan values.

    Args:
        multiBlockMesh (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): multiBlock
            mesh where to fill the attribute
        attributeName (str): attribute name
        nbComponents (int): number of components
        onPoints (bool, optional): Attribute is on Points (False) or
            on Cells.

            Defaults to False.

    Returns:
        bool: True if calculation successfully ended, False otherwise
    """
    componentNames: tuple[ str, ...] = ()
    if nbComponents > 1:
        componentNames = getComponentNames( multiBlockMesh, attributeName, onPoints )
    values: list[ float ] = [ np.nan for _ in range( nbComponents ) ]
    createConstantAttribute( multiBlockMesh, values, attributeName, componentNames, onPoints )
    multiBlockMesh.Modified()
    return True


def fillAllPartialAttributes(
    multiBlockMesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    onPoints: bool = False,
) -> bool:
    """Fill all the partial attributes of multiBlockMesh with nan values.

    Args:
        multiBlockMesh (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject):
            multiBlockMesh where to fill the attribute
        onPoints (bool, optional): Attribute is on Points (False) or
            on Cells.

            Defaults to False.

    Returns:
        bool: True if calculation successfully ended, False otherwise
    """
    attributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockMesh, onPoints )
    for attributeName, nbComponents in attributes.items():
        fillPartialAttributes( multiBlockMesh, attributeName, nbComponents, onPoints )
    multiBlockMesh.Modified()
    return True


def getAttributeValuesAsDF( surface: vtkPolyData, attributeNames: tuple[ str, ...] ) -> pd.DataFrame:
    """Get attribute values from input surface.

    Args:
        surface (vtkPolyData): mesh where to get attribute values
        attributeNames (tuple[str,...]): tuple of attribute names to get the values.

    Returns:
        pd.DataFrame: DataFrame containing property names as columns.

    """
    nbRows: int = surface.GetNumberOfCells()
    data: pd.DataFrame = pd.DataFrame( np.full( ( nbRows, len( attributeNames ) ), np.nan ), columns=attributeNames )
    for attributeName in attributeNames:
        if not isAttributeInObject( surface, attributeName, False ):
            print( f"WARNING: Attribute {attributeName} is not in the mesh." )
            continue
        array: npt.NDArray[ np.float64 ] = getArrayInObject( surface, attributeName, False )

        if len( array.shape ) > 1:
            for i in range( array.shape[ 1 ] ):
                data[ attributeName + f"_{i}" ] = array[ :, i ]
            data.drop(
                columns=[
                    attributeName,
                ],
                inplace=True,
            )
        else:
            data[ attributeName ] = array
    return data


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


def createEmptyAttribute(
    attributeName: str,
    componentNames: tuple[ str, ...],
    dataType: int,
) -> vtkDataArray:
    """Create an empty attribute.

    Args:
        attributeName (str): name of the attribute
        componentNames (tuple[str,...]): name of the components for vectorial
            attributes
        dataType (int): data type.

    Returns:
        bool: True if the attribute was correctly created
    """
    # create empty array
    newAttr: vtkDataArray
    if dataType == VTK_DOUBLE:
        newAttr = vtkDoubleArray()
    elif dataType == VTK_FLOAT:
        newAttr = vtkFloatArray()
    elif dataType == VTK_INT:
        newAttr = vtkIntArray()
    elif dataType == VTK_UNSIGNED_INT:
        newAttr = vtkUnsignedIntArray()
    elif dataType == VTK_CHAR:
        newAttr = vtkCharArray()
    else:
        raise ValueError( "Attribute type is unknown." )

    newAttr.SetName( attributeName )
    newAttr.SetNumberOfComponents( len( componentNames ) )
    if len( componentNames ) > 1:
        for i in range( len( componentNames ) ):
            newAttr.SetComponentName( i, componentNames[ i ] )

    return newAttr


def createConstantAttribute(
    object: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    values: list[ float ],
    attributeName: str,
    componentNames: tuple[ str, ...],
    onPoints: bool,
) -> bool:
    """Create an attribute with a constant value everywhere if absent.

    Args:
        object (vtkDataObject): object (vtkMultiBlockDataSet, vtkDataSet)
            where to create the attribute
        values ( list[float]): list of values of the attribute for each components
        attributeName (str): name of the attribute
        componentNames (tuple[str,...]): name of the components for vectorial
            attributes
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        bool: True if the attribute was correctly created
    """
    if isinstance( object, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return createConstantAttributeMultiBlock( object, values, attributeName, componentNames, onPoints )
    elif isinstance( object, vtkDataSet ):
        listAttributes: set[ str ] = getAttributeSet( object, onPoints )
        if attributeName not in listAttributes:
            return createConstantAttributeDataSet( object, values, attributeName, componentNames, onPoints )
        return True
    return False


def createConstantAttributeMultiBlock(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    values: list[ float ],
    attributeName: str,
    componentNames: tuple[ str, ...],
    onPoints: bool,
) -> bool:
    """Create an attribute with a constant value everywhere if absent.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): vtkMultiBlockDataSet
            where to create the attribute
        values (list[float]): list of values of the attribute for each components
        attributeName (str): name of the attribute
        componentNames (tuple[str,...]): name of the components for vectorial
            attributes
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        bool: True if the attribute was correctly created
    """
    # initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlockDataSet )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        listAttributes: set[ str ] = getAttributeSet( dataSet, onPoints )
        if attributeName not in listAttributes:
            createConstantAttributeDataSet( dataSet, values, attributeName, componentNames, onPoints )
        iter.GoToNextItem()
    return True


def createConstantAttributeDataSet(
    dataSet: vtkDataSet,
    values: list[ float ],
    attributeName: str,
    componentNames: tuple[ str, ...],
    onPoints: bool,
) -> bool:
    """Create an attribute with a constant value everywhere.

    Args:
        dataSet (vtkDataSet): vtkDataSet where to create the attribute
        values ( list[float]): list of values of the attribute for each components
        attributeName (str): name of the attribute
        componentNames (tuple[str,...]): name of the components for vectorial
            attributes
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        bool: True if the attribute was correctly created
    """
    nbElements: int = ( dataSet.GetNumberOfPoints() if onPoints else dataSet.GetNumberOfCells() )
    nbComponents: int = len( values )
    array: npt.NDArray[ np.float64 ] = np.ones( ( nbElements, nbComponents ) )
    for i, val in enumerate( values ):
        array[ :, i ] *= val
    createAttribute( dataSet, array, attributeName, componentNames, onPoints )
    return True


def createAttribute(
    dataSet: vtkDataSet,
    array: npt.NDArray[ np.float64 ],
    attributeName: str,
    componentNames: tuple[ str, ...],
    onPoints: bool,
) -> bool:
    """Create an attribute from the given array.

    Args:
        dataSet (vtkDataSet): dataSet where to create the attribute
        array (npt.NDArray[np.float64]): array that contains the values
        attributeName (str): name of the attribute
        componentNames (tuple[str,...]): name of the components for vectorial
            attributes
        onPoints (bool): True if attributes are on points, False if they are
            on cells.

    Returns:
        bool: True if the attribute was correctly created
    """
    assert isinstance( dataSet, vtkDataSet ), "Attribute can only be created in vtkDataSet object."

    newAttr: vtkDataArray = vnp.numpy_to_vtk( array, deep=True, array_type=VTK_DOUBLE )
    newAttr.SetName( attributeName )

    nbComponents: int = newAttr.GetNumberOfComponents()
    if nbComponents > 1:
        for i in range( nbComponents ):
            newAttr.SetComponentName( i, componentNames[ i ] )

    if onPoints:
        dataSet.GetPointData().AddArray( newAttr )
    else:
        dataSet.GetCellData().AddArray( newAttr )
    dataSet.Modified()
    return True


def copyAttribute(
    objectFrom: vtkMultiBlockDataSet,
    objectTo: vtkMultiBlockDataSet,
    attributNameFrom: str,
    attributNameTo: str,
) -> bool:
    """Copy an attribute from objectFrom to objectTo.

    Args:
        objectFrom (vtkMultiBlockDataSet): object from which to copy the attribute.
        objectTo (vtkMultiBlockDataSet): object where to copy the attribute.
        attributNameFrom (str): attribute name in objectFrom.
        attributNameTo (str): attribute name in objectTo.

    Returns:
        bool: True if copy sussfully ended, False otherwise
    """
    elementaryBlockIndexesTo: list[ int ] = getBlockElementIndexesFlatten( objectTo )
    elementaryBlockIndexesFrom: list[ int ] = getBlockElementIndexesFlatten( objectFrom )

    assert elementaryBlockIndexesTo == elementaryBlockIndexesFrom, (
        "ObjectFrom " + "and objectTo do not have the same block indexes." )

    for index in elementaryBlockIndexesTo:
        # get block from initial time step object
        blockT0: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( objectFrom, index ) )
        assert blockT0 is not None, "Block at initial time step is null."

        # get block from current time step object
        block: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( objectTo, index ) )
        assert block is not None, "Block at current time step is null."
        try:
            copyAttributeDataSet( blockT0, block, attributNameFrom, attributNameTo )
        except AssertionError:
            # skip attribute if not in block
            continue
    return True


def copyAttributeDataSet(
    objectFrom: vtkDataSet,
    objectTo: vtkDataSet,
    attributNameFrom: str,
    attributNameTo: str,
) -> bool:
    """Copy an attribute from objectFrom to objectTo.

    Args:
        objectFrom (vtkDataSet): object from which to copy the attribute.
        objectTo (vtkDataSet): object where to copy the attribute.
        attributNameFrom (str): attribute name in objectFrom.
        attributNameTo (str): attribute name in objectTo.

    Returns:
        bool: True if copy sussfully ended, False otherwise
    """
    # get attribut from initial time step block
    npArray: npt.NDArray[ np.float64 ] = getArrayInObject( objectFrom, attributNameFrom, False )
    assert npArray is not None
    componentNames: tuple[ str, ...] = getComponentNames( objectFrom, attributNameFrom, False )
    # copy attribut to current time step block
    createAttribute( objectTo, npArray, attributNameTo, componentNames, False )
    objectTo.Modified()
    return True


def renameAttribute(
    object: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    attributeName: str,
    newAttributeName: str,
    onPoints: bool,
) -> bool:
    """Rename an attribute.

    Args:
        object (vtkMultiBlockDataSet): object where the attribute is
        attributeName (str): name of the attribute
        newAttributeName (str): new name of the attribute
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if renaming operation successfully ended.
    """
    if isAttributeInObject( object, attributeName, onPoints ):
        dim: int = int( onPoints )
        filter = vtkArrayRename()
        filter.SetInputData( object )
        filter.SetArrayName( dim, attributeName, newAttributeName )
        filter.Update()
        object.ShallowCopy( filter.GetOutput() )
    else:
        return False
    return True


def createCellCenterAttribute( mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ], cellCenterAttributeName: str ) -> bool:
    """Create elementCenter attribute if it does not exist.

    Args:
        mesh (vtkMultiBlockDataSet | vtkDataSet): input mesh
        cellCenterAttributeName (str): Name of the attribute

    Raises:
        TypeError: Raised if input mesh is not a vtkMultiBlockDataSet or a
        vtkDataSet.

    Returns:
        bool: True if calculation successfully ended, False otherwise.
    """
    ret: int = 1
    if isinstance( mesh, vtkMultiBlockDataSet ):
        # initialize data object tree iterator
        iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
        iter.SetDataSet( mesh )
        iter.VisitOnlyLeavesOn()
        iter.GoToFirstItem()
        while iter.GetCurrentDataObject() is not None:
            block: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
            ret *= int( doCreateCellCenterAttribute( block, cellCenterAttributeName ) )
            iter.GoToNextItem()
    elif isinstance( mesh, vtkDataSet ):
        ret = int( doCreateCellCenterAttribute( mesh, cellCenterAttributeName ) )
    else:
        raise TypeError( "Input object must be a vtkDataSet or vtkMultiBlockDataSet." )
    return bool( ret )


def doCreateCellCenterAttribute( block: vtkDataSet, cellCenterAttributeName: str ) -> bool:
    """Create elementCenter attribute in a vtkDataSet if it does not exist.

    Args:
        block (vtkDataSet): input mesh that must be a vtkDataSet
        cellCenterAttributeName (str): Name of the attribute

    Returns:
        bool: True if calculation successfully ended, False otherwise.
    """
    if not isAttributeInObject( block, cellCenterAttributeName, False ):
        # apply ElementCenter filter
        filter: vtkCellCenters = vtkCellCenters()
        filter.SetInputData( block )
        filter.Update()
        output: vtkPointSet = filter.GetOutputDataObject( 0 )
        assert output is not None, "vtkCellCenters output is null."
        # transfer output to ouput arrays
        centers: vtkPoints = output.GetPoints()
        assert centers is not None, "Center are undefined."
        centerCoords: vtkDataArray = centers.GetData()
        assert centers is not None, "Center coordinates are undefined."
        centerCoords.SetName( cellCenterAttributeName )
        block.GetCellData().AddArray( centerCoords )
        block.Modified()
    return True


def computeCellCenterCoordinates( mesh: vtkDataSet ) -> vtkDataArray:
    """Get the coordinates of Cell center.

    Args:
        mesh (vtkDataSet): input surface

    Returns:
        vtkPoints: cell center coordinates
    """
    assert mesh is not None, "Surface is undefined."
    filter: vtkCellCenters = vtkCellCenters()
    filter.SetInputDataObject( mesh )
    filter.Update()
    output: vtkUnstructuredGrid = filter.GetOutputDataObject( 0 )
    assert output is not None, "Cell center output is undefined."
    pts: vtkPoints = output.GetPoints()
    assert pts is not None, "Cell center points are undefined."
    return pts.GetData()


def extractSurfaceFromElevation( mesh: vtkUnstructuredGrid, elevation: float ) -> vtkPolyData:
    """Extract surface at a constant elevation from a mesh.

    Args:
        mesh (vtkUnstructuredGrid): input mesh
        elevation (float): elevation at which to extract the surface

    Returns:
        vtkPolyData: output surface
    """
    assert mesh is not None, "Input mesh is undefined."
    assert isinstance( mesh, vtkUnstructuredGrid ), "Wrong object type"

    bounds: tuple[ float, float, float, float, float, float ] = mesh.GetBounds()
    ooX: float = ( bounds[ 0 ] + bounds[ 1 ] ) / 2.0
    ooY: float = ( bounds[ 2 ] + bounds[ 3 ] ) / 2.0

    # check plane z coordinates against mesh bounds
    assert ( elevation <= bounds[ 5 ] ) and ( elevation >= bounds[ 4 ] ), "Plane is out of input mesh bounds."

    plane: vtkPlane = vtkPlane()
    plane.SetNormal( 0.0, 0.0, 1.0 )
    plane.SetOrigin( ooX, ooY, elevation )

    cutter = vtk3DLinearGridPlaneCutter()
    cutter.SetInputDataObject( mesh )
    cutter.SetPlane( plane )
    cutter.SetInterpolateAttributes( True )
    cutter.Update()
    return cutter.GetOutputDataObject( 0 )


def transferPointDataToCellData( mesh: vtkPointSet ) -> vtkPointSet:
    """Transfer point data to cell data.

    Args:
        mesh (vtkPointSet): Input mesh.

    Returns:
        vtkPointSet: Output mesh where point data were transferred to cells.

    """
    filter = vtkPointDataToCellData()
    filter.SetInputDataObject( mesh )
    filter.SetProcessAllArrays( True )
    filter.Update()
    return filter.GetOutputDataObject( 0 )


def getBounds(
        input: Union[ vtkUnstructuredGrid,
                      vtkMultiBlockDataSet ] ) -> tuple[ float, float, float, float, float, float ]:
    """Get bounds of either single of composite data set.

    Args:
        input (Union[vtkUnstructuredGrid, vtkMultiBlockDataSet]): input mesh

    Returns:
        tuple[float, float, float, float, float, float]: tuple containing
            bounds (xmin, xmax, ymin, ymax, zmin, zmax)

    """
    if isinstance( input, vtkMultiBlockDataSet ):
        return getMultiBlockBounds( input )
    else:
        return getMonoBlockBounds( input )


def getMonoBlockBounds( input: vtkUnstructuredGrid, ) -> tuple[ float, float, float, float, float, float ]:
    """Get boundary box extrema coordinates for a vtkUnstructuredGrid.

    Args:
        input (vtkMultiBlockDataSet): input single block mesh

    Returns:
        tuple[float, float, float, float, float, float]: tuple containing
            bounds (xmin, xmax, ymin, ymax, zmin, zmax)

    """
    return input.GetBounds()


def getMultiBlockBounds( input: vtkMultiBlockDataSet, ) -> tuple[ float, float, float, float, float, float ]:
    """Get boundary box extrema coordinates for a vtkMultiBlockDataSet.

    Args:
        input (vtkMultiBlockDataSet): input multiblock mesh

    Returns:
        tuple[float, float, float, float, float, float]: bounds.

    """
    xmin, ymin, zmin = 3 * [ np.inf ]
    xmax, ymax, zmax = 3 * [ -1.0 * np.inf ]
    blockIndexes: list[ int ] = getBlockElementIndexesFlatten( input )
    for blockIndex in blockIndexes:
        block0: vtkDataObject = getBlockFromFlatIndex( input, blockIndex )
        assert block0 is not None, "Mesh is undefined."
        block: vtkDataSet = vtkDataSet.SafeDownCast( block0 )
        bounds: tuple[ float, float, float, float, float, float ] = block.GetBounds()
        xmin = bounds[ 0 ] if bounds[ 0 ] < xmin else xmin
        xmax = bounds[ 1 ] if bounds[ 1 ] > xmax else xmax
        ymin = bounds[ 2 ] if bounds[ 2 ] < ymin else ymin
        ymax = bounds[ 3 ] if bounds[ 3 ] > ymax else ymax
        zmin = bounds[ 4 ] if bounds[ 4 ] < zmin else zmin
        zmax = bounds[ 5 ] if bounds[ 5 ] > zmax else zmax
    return xmin, xmax, ymin, ymax, zmin, zmax
