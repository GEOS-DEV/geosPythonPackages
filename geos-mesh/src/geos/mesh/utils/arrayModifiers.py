# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Alexandre Benedicto, Paloma Martinez, Romain Baville
import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from typing import Union, Any
from geos.utils.Logger import getLogger, Logger

from vtk import (  # type: ignore[import-untyped]
    VTK_DOUBLE, VTK_FLOAT, VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG,
)
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkDataSet,
    vtkPointSet,
    vtkCompositeDataSet,
    vtkDataObject,
    vtkDataObjectTreeIterator,
    vtkPointData, 
    vtkCellData,
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
    getArrayInObject,
    isAttributeInObject,
    isAttributeInObjectDataSet,
    isAttributeInObjectMultiBlockDataSet,
    isAttributeGlobal,
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
    - filling partial VTK arrays with values (useful for block merge)
    - creation of new VTK array, empty or with a given data array
    - transfer from VTK point data to VTK cell data
"""


def fillPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    attributeName: str,
    onPoints: bool = False,
    value: Any = np.nan,
    logger: Logger = getLogger( "fillPartialAttributes", True ),
) -> bool:
    """Fill input partial attribute of multiBlockDataSet with the same value for all the components.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): MultiBlockDataSet where to fill the attribute.
        attributeName (str): Attribute name.
        onPoints (bool, optional): Attribute is on Points (True) or on Cells (False).
            Defaults to False.
        value (any, optional): Filling value.
            Defaults to -1 for int VTK arrays, 0 for uint VTK arrays and nan otherwise.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created and filled, False if not.
    """
    #assert isinstance( multiBlockDataSet, vtkMultiBlockDataSet ), "Input mesh has to be inherited from vtkMultiBlockDataSet."
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        logger.error( f"Input mesh has to be inherited from vtkMultiBlockDataSet." )
        return False
    
    #assert not isAttributeGlobal( multiBlockDataSet, attributeName, onPoints ), f"The attribute { attributeName } is already global."
    if isAttributeGlobal( multiBlockDataSet, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already global." )
        return False

    vtkArrayType: int = getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, onPoints )
    infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, onPoints )
    nbComponents: int = infoAttributes[ attributeName ]

    componentNames: tuple[ str, ...] = ()
    if nbComponents > 1:
        componentNames = getComponentNames( multiBlockDataSet, attributeName, onPoints )

    typeMapping: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
    valueType: Any = typeMapping[ vtkArrayType ]
    if np.isnan( value ):
        if vtkArrayType in ( VTK_DOUBLE, VTK_FLOAT ):
            value = valueType( value )
        elif vtkArrayType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG ):
            logger.warning( f"{ attributeName } vtk array type is { valueType }, default value is automatically set to 0." )
            value = valueType( 0 )
        else:
            logger.warning( f"{ attributeName } vtk array type is { valueType }, default value is automatically set to -1." )
            value = valueType( -1 )

    else:
        value = valueType( value )

    values: list[ Any ] = [ value for _ in range( nbComponents ) ]

    # Parse the multiBlockDataSet to create and fill the attribute on blocks where the attribute is not.
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlockDataSet )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        if not isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
            created: bool = createConstantAttributeDataSet( dataSet, values, attributeName, componentNames, onPoints, vtkArrayType, logger )
            if not created:
                return False
                    
        iter.GoToNextItem()

    return True


def fillAllPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    value: Any = np.nan,
    logger: Logger = getLogger( "fillAllPartialAttributes", True ),
) -> bool:
    """Fill all the partial attributes of a multiBlockDataSet with a same value. All components of each attribute are filled with the same value.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): MultiBlockDataSet where to fill the attribute.
        value (any, optional): Filling value.
            Defaults to -1 for int VTK arrays, 0 for uint VTK arrays and nan otherwise.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if attributes were correctly created and filled, False if not.
    """    
    # Parse all attributes, onPoints and onCells
    for onPoints in [ True, False ]:
        infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, onPoints )
        for attributeName in infoAttributes:
            if not isAttributeGlobal( multiBlockDataSet, attributeName, onPoints ):
                filled: bool = fillPartialAttributes( multiBlockDataSet, attributeName, onPoints, value, logger )
                if not filled:
                    return False

    return True


def createEmptyAttribute(
    attributeName: str,
    componentNames: tuple[ str, ...],
    vtkDataType: int,
) -> vtkDataArray:
    """Create an empty attribute.

    Args:
        attributeName (str): Name of the attribute
        componentNames (tuple[str,...]): Name of the components for vectorial attributes.
        vtkDataType (int): Data type.

    Returns:
        bool: True if the attribute was correctly created.
    """
    vtkDataTypeOk: dict = vnp.get_vtk_to_numpy_typemap()
    assert vtkDataType in vtkDataTypeOk, f"Attribute type { vtkDataType } is unknown. The empty attribute { attributeName } has not been created into the mesh."

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
    logger: Logger = getLogger( "createConstantAttribute", True ),
) -> bool:
    """Create a new attribute with a constant value in the object.

    Args:
        object (vtkDataObject): Object (vtkMultiBlockDataSet, vtkDataSet) where to create the attribute.
        values (list[float]): List of values of the attribute for each components.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the array value.
            Warning with int8, uint8 and int64 type of value, the vtk array type corresponding are multiple. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # assert not isAttributeInObject( object, attributeName, onPoints ), f"The attribute { attributeName } is already present in the mesh"
    if isAttributeInObject( object, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already present in the mesh." )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    if isinstance( object, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return createConstantAttributeMultiBlock( object, values, attributeName, componentNames, onPoints, vtkDataType, logger )

    elif isinstance( object, vtkDataSet ):
        return createConstantAttributeDataSet( object, values, attributeName, componentNames, onPoints, vtkDataType, logger )
    
    else:
        logger.error( f"The mesh has to be inherited from a vtkMultiBlockDataSet or a vtkDataSet" )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False


def createConstantAttributeMultiBlock(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    values: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
    logger: Logger = getLogger( "createConstantAttributeMultiBlock", True ),
) -> bool:
    """Create a new attribute with a constant value on every blocks of the multiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): MultiBlockDataSet where to create the attribute.
        values (list[any]): List of values of the attribute for each components.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the given value.
            Warning with int8, uint8 and int64 type of value, the vtk array type associated are multiple. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    #assert isinstance( multiBlockDataSet, vtkMultiBlockDataSet ), "Input mesh has to be inherited from vtkMultiBlockDataSet."
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        logger.error( f"Input mesh has to be inherited from vtkMultiBlockDataSet." )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    #assert not isAttributeInObjectMultiBlockDataSet( multiBlockDataSet, attributeName, onPoints ), f"The attribute { attributeName } is already present in the multiBlockDataSet."
    if isAttributeInObjectMultiBlockDataSet( multiBlockDataSet, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already present in the multiBlockDataSet." )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False

    # Initialize data object tree iterator
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlockDataSet )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        created: bool = createConstantAttributeDataSet( dataSet, values, attributeName, componentNames, onPoints, vtkDataType, logger )
        if not created:
            return False
        
        iter.GoToNextItem()

    return True


def createConstantAttributeDataSet(
    dataSet: vtkDataSet,
    values: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
    logger: Logger = getLogger( "createConstantAttributeDataSet", True ),
) -> bool:
    """Create an attribute with a constant value in the dataSet.

    Args:
        dataSet (vtkDataSet): DataSet where to create the attribute.
        values ( list[any]): List of values of the attribute for each components.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the given value.
            Warning with int8, uint8 and int64 type of value, the vtk array type associated are multiple. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """    
    nbElements: int = ( dataSet.GetNumberOfPoints() if onPoints else dataSet.GetNumberOfCells() )
    nbComponents: int = len( values )
    npArray: npt.NDArray[ Any ]
    if nbComponents > 1:
        npArray = np.array( [ values for _ in range( nbElements ) ] )
    else:
        npArray = np.array( [ values[ 0 ] for _ in range( nbElements ) ] )

    return createAttribute( dataSet, npArray, attributeName, componentNames, onPoints, vtkDataType, logger )


def createAttribute(
    dataSet: vtkDataSet,
    npArray: npt.NDArray[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
    logger: Logger = getLogger( "createAttribute", True ),
) -> bool:
    """Create an attribute and its VTK array from the given array.

    Args:
        dataSet (vtkDataSet): DataSet where to create the attribute.
        npArray (npt.NDArray[any]): Array that contains the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            Defaults to None, the type is given by the type of the given value in the array.
            Warning with int8, uint8 and int64 type of value, the vtk array type associated are multiple. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    #assert isinstance( dataSet, vtkDataSet ), "Input mesh has to be inherited from vtkDataSet."
    if not isinstance( dataSet, vtkDataSet ):
        logger.error( f"Input mesh has to be inherited from vtkDataSet." )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    #assert not isAttributeInObjectDataSet( dataSet, attributeName, onPoints ), f"The attribute { attributeName } is already present in the dataSet."
    if isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already present in the dataSet." )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    data: Union[ vtkPointData, vtkCellData]
    nbElements: int
    if onPoints:
        data = dataSet.GetPointData()
        nbElements = dataSet.GetNumberOfPoints()
    else:
        data = dataSet.GetCellData()
        nbElements = dataSet.GetNumberOfCells()
    
    #assert len( array ) == nbElements, f"The array has to have { nbElements } elements, but have only { len( array ) } elements"
    if len( npArray ) != nbElements:
        logger.error( f"The array has to have { nbElements } elements, but have only { len( npArray ) } elements" )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    createdAttribute: vtkDataArray = vnp.numpy_to_vtk( npArray, deep=True, array_type=vtkDataType )
    createdAttribute.SetName( attributeName )

    nbComponents: int = createdAttribute.GetNumberOfComponents()
    nbNames: int = len( componentNames )
    if nbComponents == 1 and nbNames > 0:
        logger.warning( f"The array has one component, its name is the name of the attribute: { attributeName }, the components names you have enter will not be taking into account." )
    
    if nbComponents > 1:
        if nbNames < nbComponents:
            componentNames = tuple( [ "Component" + str( i ) for i in range( nbComponents ) ] )
            logger.warning( f"Insufficient number of input component names. { attributeName } component names will be set to : Component0, Component1 ..." )
        elif nbNames > nbComponents:
            logger.warning( f"Excessive number of input component names, only the first { nbComponents } names will be used." )

        for i in range( nbComponents ):
            createdAttribute.SetComponentName( i, componentNames[ i ] )

    data.AddArray( createdAttribute )
    data.Modified()

    return True


def copyAttribute(
    objectFrom: vtkMultiBlockDataSet,
    objectTo: vtkMultiBlockDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool = False,
    logger: Logger = getLogger( "copyAttribute", True ),
) -> bool:
    """Copy an attribute from a multiBlockDataSet to another.

    Args:
        objectFrom (vtkMultiBlockDataSet): MultiBlockDataSet from which to copy the attribute.
        objectTo (vtkMultiBlockDataSet): MultiBlockDataSet where to copy the attribute.
        attributeNameFrom (str): Attribute name in objectFrom.
        attributeNameTo (str): Attribute name in objectTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    if not isinstance( objectFrom, vtkMultiBlockDataSet ):
        logger.error( f"ObjectFrom has to be inherited from vtkMultiBlockDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    if not isinstance( objectTo, vtkMultiBlockDataSet ):
        logger.error( f"ObjectTo has to be inherited from vtkMultiBlockDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    if not isAttributeInObjectMultiBlockDataSet( objectFrom, attributeNameFrom, onPoints ):
        logger.error( f"The attribute { attributeNameFrom } is not in the objectFrom." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    elementaryBlockIndexesTo: list[ int ] = getBlockElementIndexesFlatten( objectTo )
    elementaryBlockIndexesFrom: list[ int ] = getBlockElementIndexesFlatten( objectFrom )

    if elementaryBlockIndexesTo != elementaryBlockIndexesFrom:
        logger.error( f"ObjectFrom and objectTo do not have the same block indexes." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    for index in elementaryBlockIndexesTo:
        blockFrom: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( objectFrom, index ) )
        if blockFrom is None:
            logger.error( f"Block { str( index ) } of objectFrom is null." )
            logger.error( f"The attribute { attributeNameFrom } has not been copied." )
            return False

        blockTo: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( objectTo, index ) )
        if blockTo is None:
            logger.error( f"Block { str( index ) } of objectTo is null." )
            logger.error( f"The attribute { attributeNameFrom } has not been copied." )
            return False

        if isAttributeInObjectDataSet( blockFrom, attributeNameFrom, onPoints ):
            copied: bool = copyAttributeDataSet( blockFrom, blockTo, attributeNameFrom, attributeNameTo, onPoints, logger )
            if not copied:
                return False

    return True


def copyAttributeDataSet(
    objectFrom: vtkDataSet,
    objectTo: vtkDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool = False,
    logger: Logger = getLogger( "copyAttributeDataSet", True ),
) -> bool:
    """Copy an attribute from a dataSet to another.

    Args:
        objectFrom (vtkDataSet): DataSet from which to copy the attribute.
        objectTo (vtkDataSet): DataSet where to copy the attribute.
        attributeNameFrom (str): Attribute name in objectFrom.
        attributeNameTo (str): Attribute name in objectTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    if not isinstance( objectFrom, vtkDataSet ):
        logger.error( f"ObjectFrom has to be inherited from vtkDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    if not isinstance( objectTo, vtkDataSet ):
        logger.error( f"ObjectTo has to be inherited from vtkDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    if not isAttributeInObjectDataSet( objectFrom, attributeNameFrom, onPoints ):
        logger.error( f"The attribute { attributeNameFrom } is not in the objectFrom." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    npArray: npt.NDArray[ Any ] = getArrayInObject( objectFrom, attributeNameFrom, onPoints )
    componentNames: tuple[ str, ...] = getComponentNames( objectFrom, attributeNameFrom, onPoints )
    vtkDataType: int = getVtkArrayTypeInObject( objectFrom, attributeNameFrom, onPoints )

    return createAttribute( objectTo, npArray, attributeNameTo, componentNames, onPoints, vtkDataType, logger )


def renameAttribute(
    object: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    attributeName: str,
    newAttributeName: str,
    onPoints: bool,
) -> bool:
    """Rename an attribute.

    Args:
        object (vtkMultiBlockDataSet): Object where the attribute is.
        attributeName (str): Name of the attribute.
        newAttributeName (str): New name of the attribute.
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
        block (vtkDataSet): Input mesh that must be a vtkDataSet
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
        # transfer output to output arrays
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
