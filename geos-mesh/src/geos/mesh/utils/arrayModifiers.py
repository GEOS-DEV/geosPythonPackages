# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Alexandre Benedicto, Paloma Martinez, Romain Baville
import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from typing import Union, Any
from vtk import (  # type: ignore[import-untyped]
    VTK_DOUBLE, VTK_FLOAT,
)
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkDataSet,
    vtkPointSet,
    vtkCompositeDataSet,
    vtkDataObject,
    vtkDataObjectTreeIterator,
)
from vtkmodules.vtkFiltersCore import (
    vtkArrayRename,
    vtkCellCenters,
    vtkPointDataToCellData,
)
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkPoints,
)
from geos.mesh.utils.arrayHelpers import (
    getComponentNames,
    getAttributesWithNumberOfComponents,
    getAttributeSet,
    getArrayInObject,
    isAttributeInObject,
    getVtkArrayTypeInObject,
    getVtkArrayTypeInMultiBlock,
)
from geos.mesh.utils.multiblockHelpers import (
    getBlockElementIndexesFlatten,
    getBlockFromFlatIndex,
)

__doc__ = """
ArrayModifiers contains utilities to process VTK Arrays objects.

These methods include:
    - filling partial  VTK arrays with nan values (useful for block merge)
    - creation of new VTK array, empty or with a given data array
    - transfer from VTK point data to VTK cell data
"""


def fillPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    attributeName: str,
    onPoints: bool = False,
    value: Any = np.nan,
) -> bool:
    """Fill input partial attribute of multiBlockDataSet with the same value for all the components.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): multiBlockDataSet where to fill the attribute.
        attributeName (str): attribute name.
        onPoints (bool, optional): Attribute is on Points (True) or on Cells (False).
            Defaults to False.
        value (any, optional): value to fill in the partial atribute.
            Defaults to nan. For int vtk array, default value is automatically set to -1.

    Returns:
        bool: True if calculation successfully ended.
    """
    vtkArrayType: int = getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, onPoints )
    assert vtkArrayType != -1

    infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, onPoints )
    nbComponents: int = infoAttributes[ attributeName ]

    componentNames: tuple[ str, ...] = ()
    if nbComponents > 1:
        componentNames = getComponentNames( multiBlockDataSet, attributeName, onPoints )

    valueType: Any = type( value )
    typeMapping: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
    valueTypeExpected: Any = typeMapping[ vtkArrayType ]
    if valueTypeExpected != valueType:
        if np.isnan( value ):
            if vtkArrayType in ( VTK_DOUBLE, VTK_FLOAT ):
                value = valueTypeExpected( value )
            else:
                print( attributeName + " vtk array type is " + str( valueTypeExpected ) +
                       ", default value is automatically set to -1." )
                value = valueTypeExpected( -1 )

        else:
            print( "The value has the wrong type, it is update to " + str( valueTypeExpected ) + ", the type of the " +
                   attributeName + " array to fill." )
            value = valueTypeExpected( value )

    values: list[ Any ] = [ value for _ in range( nbComponents ) ]

    createConstantAttribute( multiBlockDataSet, values, attributeName, componentNames, onPoints, vtkArrayType )
    multiBlockDataSet.Modified()

    return True


def fillAllPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    value: Any = np.nan,
) -> bool:
    """Fill all the partial attributes of multiBlockDataSet with same value for all attributes and they components.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): multiBlockDataSet where to fill the attribute.
        value (any, optional): value to fill in the partial atribute.
            Defaults to nan. For int vtk array, default value is automatically set to -1.

    Returns:
        bool: True if calculation successfully ended.
    """
    for onPoints in [ True, False ]:
        infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, onPoints )
        for attributeName in infoAttributes:
            fillPartialAttributes( multiBlockDataSet, attributeName, onPoints, value )

    multiBlockDataSet.Modified()

    return True


def createEmptyAttribute(
    attributeName: str,
    componentNames: tuple[ str, ...],
    vtkDataType: int,
) -> vtkDataArray:
    """Create an empty attribute.

    Args:
        attributeName (str): name of the attribute
        componentNames (tuple[str,...]): name of the components for vectorial attributes.
        vtkDataType (int): data type.

    Returns:
        bool: True if the attribute was correctly created.
    """
    vtkDataTypeOk: dict = vnp.get_vtk_to_numpy_typemap()
    if vtkDataType not in vtkDataTypeOk:
        raise ValueError( "Attribute type is unknown." )

    nbComponents: int = len( componentNames )

    createdAttribute: vtkDataArray = vtkDataArray.CreateDataArray( vtkDataType )
    createdAttribute.SetName( attributeName )
    createdAttribute.SetNumberOfComponents( nbComponents )
    if nbComponents > 1:
        for i in range( nbComponents ):
            createdAttribute.SetComponentName( i, componentNames[ i ] )

    return createdAttribute


def createConstantAttribute(
    object: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    values: list[ float ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
) -> bool:
    """Create an attribute with a constant value everywhere if absent.

    Args:
        object (vtkDataObject): object (vtkMultiBlockDataSet, vtkDataSet) where to create the attribute.
        values ( list[float]): list of values of the attribute for each components.
        attributeName (str): name of the attribute.
        componentNames (tuple[str,...], optional): name of the components for vectorial attributes. If one component, give an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the array value.
            Waring with int8, uint8 and int64 type of value, several vtk array type use it by default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG

    Returns:
        bool: True if the attribute was correctly created False if the attribute was already present.
    """
    if isinstance( object, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return createConstantAttributeMultiBlock( object, values, attributeName, componentNames, onPoints, vtkDataType )

    elif isinstance( object, vtkDataSet ):
        listAttributes: set[ str ] = getAttributeSet( object, onPoints )
        if attributeName not in listAttributes:
            return createConstantAttributeDataSet( object, values, attributeName, componentNames, onPoints,
                                                   vtkDataType )
        print( "The attribute was already present in the vtkDataSet." )
        return False
    return False


def createConstantAttributeMultiBlock(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    values: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
) -> bool:
    """Create an attribute with a constant value everywhere if absent.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): vtkMultiBlockDataSet where to create the attribute.
        values (list[any]): list of values of the attribute for each components.
        attributeName (str): name of the attribute.
        componentNames (tuple[str,...], optional): name of the components for vectorial attributes. If one component, give an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the given value.
            Waring with int8, uint8 and int64 type of value, several vtk array type use it by default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG

    Returns:
        bool: True if the attribute was correctly created, False if the attribute was already present.
    """
    # initialize data object tree iterator
    checkCreat: bool = False

    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlockDataSet )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        listAttributes: set[ str ] = getAttributeSet( dataSet, onPoints )
        if attributeName not in listAttributes:
            checkCreat = createConstantAttributeDataSet( dataSet, values, attributeName, componentNames, onPoints,
                                                         vtkDataType )

        iter.GoToNextItem()

    if checkCreat:
        return True
    else:
        print( "The attribute was already present in the vtkMultiBlockDataSet." )
        return False


def createConstantAttributeDataSet(
    dataSet: vtkDataSet,
    values: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
) -> bool:
    """Create an attribute with a constant value everywhere.

    Args:
        dataSet (vtkDataSet): vtkDataSet where to create the attribute.
        values ( list[any]): list of values of the attribute for each components.
        attributeName (str): name of the attribute.
        componentNames (tuple[str,...], optional): name of the components for vectorial attributes. If one component, give an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the given value.
            Waring with int8, uint8 and int64 type of value, several vtk array type use it by default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG

    Returns:
        bool: True if the attribute was correctly created.
    """
    nbElements: int = ( dataSet.GetNumberOfPoints() if onPoints else dataSet.GetNumberOfCells() )

    nbComponents: int = len( values )
    array: npt.NDArray[ Any ]
    if nbComponents > 1:
        array = np.array( [ values for _ in range( nbElements ) ] )
    else:
        array = np.array( [ values[ 0 ] for _ in range( nbElements ) ] )

    return createAttribute( dataSet, array, attributeName, componentNames, onPoints, vtkDataType )


def createAttribute(
    dataSet: vtkDataSet,
    array: npt.NDArray[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
) -> bool:
    """Create an attribute and its VTK array from the given array.

    Args:
        dataSet (vtkDataSet): dataSet where to create the attribute.
        array (npt.NDArray[any]): array that contains the values.
        attributeName (str): name of the attribute.
        componentNames (tuple[str,...], optional): name of the components for vectorial attributes. If one component, give an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the given value in the array.
            Waring with int8, uint8 and int64 type of value, several vtk array type use it. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG

    Returns:
        bool: True if the attribute was correctly created.
    """
    assert isinstance( dataSet, vtkDataSet ), "Attribute can only be created in vtkDataSet object."
    assert not isAttributeInObject( dataSet, attributeName, onPoints ), f"The attribute { attributeName } already exist in the mesh"

    createdAttribute: vtkDataArray = vnp.numpy_to_vtk( array, deep=True, array_type=vtkDataType )
    createdAttribute.SetName( attributeName )

    nbComponents: int = createdAttribute.GetNumberOfComponents()
    if nbComponents > 1:
        nbNames = len( componentNames )

        if nbNames < nbComponents:
            componentNames = tuple( [ "Component" + str( i ) for i in range( nbComponents ) ] )
            print( "Not enough component name enter, component names are set to : Component0, Component1 ..." )
        elif nbNames > nbComponents:
            print( "To many component names enter, the lastest will not be taken into account." )

        for i in range( nbComponents ):
            createdAttribute.SetComponentName( i, componentNames[ i ] )

    if onPoints:
        dataSet.GetPointData().AddArray( createdAttribute )
    else:
        dataSet.GetCellData().AddArray( createdAttribute )

    dataSet.Modified()

    return True


def copyAttribute(
    objectFrom: vtkMultiBlockDataSet,
    objectTo: vtkMultiBlockDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool = False,
) -> bool:
    """Copy an attribute from objectFrom to objectTo.

    Args:
        objectFrom (vtkMultiBlockDataSet): object from which to copy the attribute.
        objectTo (vtkMultiBlockDataSet): object where to copy the attribute.
        attributeNameFrom (str): attribute name in objectFrom.
        attributeNameTo (str): attribute name in objectTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    elementaryBlockIndexesTo: list[ int ] = getBlockElementIndexesFlatten( objectTo )
    elementaryBlockIndexesFrom: list[ int ] = getBlockElementIndexesFlatten( objectFrom )

    assert elementaryBlockIndexesTo == elementaryBlockIndexesFrom, (
        "ObjectFrom " + "and objectTo do not have the same block indexes." )

    for index in elementaryBlockIndexesTo:
        # get block from initial time step object
        blockFrom: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( objectFrom, index ) )
        assert blockFrom is not None, "Block at initial time step is null."

        # get block from current time step object
        blockTo: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( objectTo, index ) )
        assert blockTo is not None, "Block at current time step is null."

        try:
            copyAttributeDataSet( blockFrom, blockTo, attributeNameFrom, attributeNameTo, onPoints )
        except AssertionError:
            # skip attribute if not in block
            continue

    return True


def copyAttributeDataSet(
    objectFrom: vtkDataSet,
    objectTo: vtkDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool = False,
) -> bool:
    """Copy an attribute from objectFrom to objectTo.

    Args:
        objectFrom (vtkDataSet): object from which to copy the attribute.
        objectTo (vtkDataSet): object where to copy the attribute.
        attributeNameFrom (str): attribute name in objectFrom.
        attributeNameTo (str): attribute name in objectTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    # get attribut from initial time step block
    npArray: npt.NDArray[ Any ] = getArrayInObject( objectFrom, attributeNameFrom, onPoints )
    assert npArray is not None

    componentNames: tuple[ str, ...] = getComponentNames( objectFrom, attributeNameFrom, onPoints )
    vtkDataType: int = getVtkArrayTypeInObject( objectFrom, attributeNameFrom, onPoints )

    # copy attribut to current time step block
    createAttribute( objectTo, npArray, attributeNameTo, componentNames, onPoints, vtkDataType )
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
        object (vtkMultiBlockDataSet): object where the attribute is.
        attributeName (str): name of the attribute.
        newAttributeName (str): new name of the attribute.
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
