# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Alexandre Benedicto, Paloma Martinez
import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from typing import Union
from vtkmodules.vtkCommonDataModel import ( vtkMultiBlockDataSet, vtkDataSet, vtkPointSet, vtkCompositeDataSet,
                                            vtkDataObject, vtkDataObjectTreeIterator )
from vtkmodules.vtkFiltersCore import vtkArrayRename, vtkCellCenters, vtkPointDataToCellData
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
from geos.mesh.utils.arrayHelpers import (
    getComponentNames,
    getAttributesWithNumberOfComponents,
    getAttributeSet,
    getArrayInObject,
    isAttributeInObject,
)
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten, getBlockFromFlatIndex

__doc__ = """
ArrayModifiers contains utilities to process VTK Arrays objects.

These methods include:
    - filling partial  VTK arrays with nan values (useful for block merge)
    - creation of new VTK array, empty or with a given data array
    - transfer from VTK point data to VTK cell data
"""


def fillPartialAttributes(
    multiBlockMesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    attributeName: str,
    nbComponents: int,
    onPoints: bool = False,
    value: float = np.nan
) -> bool:
    """Fill input partial attribute of multiBlockMesh with values.

    Args:
        multiBlockMesh (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): multiBlock
            mesh where to fill the attribute.
        attributeName (str): attribute name.
        nbComponents (int): number of components.
        onPoints (bool, optional): Attribute is on Points (False) or on Cells (True).
            Defaults to False.
        value (float, optional): value to fill in the partial atribute.
            Defaults to nan.

    Returns:
        bool: True if calculation successfully ended, False otherwise.
    """
    componentNames: tuple[ str, ...] = ()
    if nbComponents > 1:
        componentNames = getComponentNames( multiBlockMesh, attributeName, onPoints )
    values: list[ float ] = [ value for _ in range( nbComponents ) ]
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
    """Copy a cell attribute from objectFrom to objectTo.

    Args:
        objectFrom (vtkMultiBlockDataSet): object from which to copy the attribute.
        objectTo (vtkMultiBlockDataSet): object where to copy the attribute.
        attributNameFrom (str): attribute name in objectFrom.
        attributNameTo (str): attribute name in objectTo.

    Returns:
        bool: True if copy successfully ended, False otherwise
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
    """Copy a cell attribute from objectFrom to objectTo.

    Args:
        objectFrom (vtkDataSet): object from which to copy the attribute.
        objectTo (vtkDataSet): object where to copy the attribute.
        attributNameFrom (str): attribute name in objectFrom.
        attributNameTo (str): attribute name in objectTo.

    Returns:
        bool: True if copy successfully ended, False otherwise
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
        dim: int = 0 if onPoints else 1
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
