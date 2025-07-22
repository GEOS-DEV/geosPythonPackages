# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Alexandre Benedicto, Paloma Martinez, Romain Baville
import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from typing import Union, Any
from geos.utils.Logger import getLogger, Logger

from vtk import (  # type: ignore[import-untyped]
    VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG,
    VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE,
    VTK_FLOAT, VTK_DOUBLE,
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
    getComponentNamesDataSet,
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
        value (any, optional): Filling value. It is better to use numpy scalar type for the values.
            Defaults to -1 for int VTK arrays, 0 for uint VTK arrays and nan for float VTK arrays.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created and filled, False if not.
    """
    # Check if the input mesh is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        logger.error( f"Input mesh has to be inherited from vtkMultiBlockDataSet." )
        return False
    
    # Check if the attribute is partial.
    if isAttributeGlobal( multiBlockDataSet, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already global." )
        return False

    # Get information of the attribute to fill.
    vtkDataType: int = getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, onPoints )
    infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, onPoints )
    nbComponents: int = infoAttributes[ attributeName ]
    componentNames: tuple[ str, ...] = ()
    if nbComponents > 1:
        componentNames = getComponentNames( multiBlockDataSet, attributeName, onPoints )

    # Set the default value depending of the type of the attribute to fill
    if np.isnan( value ):
        typeMapping: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
        valueType: type = typeMapping[ vtkDataType ]
        # Default value for float types is nan.
        if vtkDataType in ( VTK_FLOAT, VTK_DOUBLE ):
            value = valueType( value )
            logger.warning( f"{ attributeName } vtk data type is { vtkDataType } cooresponding to { value.dtype } numpy type, default value is automatically set to nan." )
        # Default value for int types is -1.
        elif vtkDataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ) :
            value = valueType( -1 )
            logger.warning( f"{ attributeName } vtk data type is { vtkDataType } cooresponding to { value.dtype } numpy type, default value is automatically set to -1." )
        # Default value for uint types is 0.
        elif vtkDataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG ):
            value = valueType( 0 )
            logger.warning( f"{ attributeName } vtk data type is { vtkDataType } cooresponding to { value.dtype } numpy type, default value is automatically set to 0." )
        else:
            logger.error( f"The type of the attribute { attributeName } is not compatible with the function.")
            return False

    values: list[ Any ] = [ value for _ in range( nbComponents ) ]

    # Parse the multiBlockDataSet to create and fill the attribute on blocks where it is not.
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlockDataSet )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        if not isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
            if not createConstantAttributeDataSet( dataSet, values, attributeName, componentNames, onPoints, vtkDataType, logger ):
                return False
                    
        iter.GoToNextItem()

    return True


def fillAllPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    logger: Logger = getLogger( "fillAllPartialAttributes", True ),
) -> bool:
    """Fill all partial attributes of a multiBlockDataSet with the default value.
    All components of each attributes are filled with the same value.
    Depending of the type of the attribute, the default value is different:
        - 0 for uint types (VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG).
        - -1 for int types (VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE).
        - nan for float types (VTK_FLOAT, VTK_DOUBLE).

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): MultiBlockDataSet where to fill attributes.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if attributes were correctly created and filled, False if not.
    """    
    # Parse all partial attributes, onPoints and onCells to fill them.
    for onPoints in [ True, False ]:
        infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, onPoints )
        for attributeName in infoAttributes:
            if not isAttributeGlobal( multiBlockDataSet, attributeName, onPoints ):
                if not fillPartialAttributes( multiBlockDataSet, attributeName, onPoints, logger=logger ):
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
    # Check if the vtk data type is correct.
    vtkNumpyTypeMap: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
    assert vtkDataType in vtkNumpyTypeMap, f"Attribute type { vtkDataType } is unknown. The empty attribute { attributeName } has not been created into the mesh."

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
    listValues: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
    logger: Logger = getLogger( "createConstantAttribute", True ),
) -> bool:
    """Create a new attribute with a constant value in the object.

    Args:
        object (vtkDataObject): Object (vtkMultiBlockDataSet, vtkDataSet) where to create the attribute.
        listValues (list[any]): List of values of the attribute for each components. It is better to use numpy scalar type for the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            If None the vtk data type is given by the type of the values.
            Else, the values are converted to the corresponding numpy type.
            Defaults to None.
            Warning with int8, uint8 and int64 type of value, the vtk data type corresponding are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """    
    if isinstance( object, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return createConstantAttributeMultiBlock( object, listValues, attributeName, componentNames, onPoints, vtkDataType, logger )

    elif isinstance( object, vtkDataSet ):
        return createConstantAttributeDataSet( object, listValues, attributeName, componentNames, onPoints, vtkDataType, logger )
    
    else:
        logger.error( f"The mesh has to be inherited from a vtkMultiBlockDataSet or a vtkDataSet" )
        logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
        return False


def createConstantAttributeMultiBlock(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    listValues: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
    logger: Logger = getLogger( "createConstantAttributeMultiBlock", True ),
) -> bool:
    """Create a new attribute with a constant value per component on every blocks of the multiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): MultiBlockDataSet where to create the attribute.
        listValues (list[any]): List of values of the attribute for each components. It is better to use numpy scalar type for the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            If None the vtk data type is given by the type of the values.
            Else, values type have to correspond to the type of the vtk data, check https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/numpy_support.py for more information.
            Defaults to None.
            Warning with int8, uint8 and int64 type of value, the vtk data type corresponding are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # Check if the input mesh is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        logger.error( f"Input mesh has to be inherited from vtkMultiBlockDataSet." )
        logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
        return False
    
    # Check if the attribute already exist in the input mesh.
    if isAttributeInObjectMultiBlockDataSet( multiBlockDataSet, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already present in the multiBlockDataSet." )
        logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
        return False

    # Check if an attribute with the same name exist on the opposite piece (points or cells) on the input mesh.
    oppositePiece: bool = not onPoints
    oppositePieceName: str = "points" if oppositePiece else "cells"
    if isAttributeInObjectMultiBlockDataSet( multiBlockDataSet, attributeName, oppositePiece ):
        oppositePieceState: str = "global" if isAttributeGlobal( multiBlockDataSet, attributeName, oppositePiece ) else "partial"
        logger.warning( f"A { oppositePieceState } attribute with the same name ({ attributeName }) is already present in the multiBlockDataSet but on { oppositePieceName }." )
    
    # Parse the multiBlockDataSet to create the constant attribute on each blocks.
    iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iter.SetDataSet( multiBlockDataSet )
    iter.VisitOnlyLeavesOn()
    iter.GoToFirstItem()
    while iter.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iter.GetCurrentDataObject() )
        if not createConstantAttributeDataSet( dataSet, listValues, attributeName, componentNames, onPoints, vtkDataType, logger ):
            return False
        
        iter.GoToNextItem()

    return True


def createConstantAttributeDataSet(
    dataSet: vtkDataSet,
    listValues: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, Any ] = None,
    logger: Logger = getLogger( "createConstantAttributeDataSet", True ),
) -> bool:
    """Create an attribute with a constant value per component in the dataSet.

    Args:
        dataSet (vtkDataSet): DataSet where to create the attribute.
        listValues (list[any]): List of values of the attribute for each components. It is better to use numpy scalar type for the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            If None the vtk data type is given by the type of the values of listValues.
            Else, values type have to correspond to the type of the vtk data, check https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/numpy_support.py for more information.
            Defaults to None.
            Warning with int8, uint8 and int64 type of value, the vtk data type corresponding are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # Check if all the values of listValues have the same type.
    valueType: type = type( listValues[ 0 ] )
    for value in listValues:
        valueTypeTest: type = type( value )
        if valueType != valueTypeTest:
            logger.error( f"All values in the list of values have not the same type." )
            logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
            return False
    
    # Convert int and float type into numpy scalar type.
    if valueType in ( int, float ):
        npType: type = type( np.array( listValues )[ 0 ] )
        logger.warning( f"During the creation of the constant attribute { attributeName }, values will be converted from { valueType } to { npType }." )
        logger.warning( f"To avoid any issue with the conversion use directly numpy scalar type for the values" )
        valueType = npType
    
    # Check the coherency between the given value type and the vtk array type if it exist.
    valueType = valueType().dtype
    if vtkDataType is not None:
        vtkNumpyTypeMap: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
        if vtkDataType not in vtkNumpyTypeMap:
            logger.error( f"The vtk data type { vtkDataType } is unknown." )
            logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
            return False
        npArrayTypeFromVtk: type = vtkNumpyTypeMap[ vtkDataType ]().dtype
        if npArrayTypeFromVtk != valueType:
            logger.error( f"Values type { valueType } is not coherent with the type of array created ({ npArrayTypeFromVtk }) from the given vtkDataType." )
            logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
            return False

    # Create the numpy array constant per component.
    nbComponents: int = len( listValues )
    nbElements: int = ( dataSet.GetNumberOfPoints() if onPoints else dataSet.GetNumberOfCells() )
    npArray: npt.NDArray[ Any ]
    if nbComponents > 1:
        npArray = np.array( [ listValues for _ in range( nbElements ) ], valueType )
    else:
        npArray = np.array( [ listValues[ 0 ] for _ in range( nbElements ) ], valueType )

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
    """Create an attribute from the given numpy array.

    Args:
        dataSet (vtkDataSet): DataSet where to create the attribute.
        npArray (npt.NDArray[any]): Array that contains the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union(any, int), optional): Vtk data type of the attribute to create.
            If None the vtk data type is given by the type of the numpy array.
            Else, numpy array type have to correspond to the type of the vtk data, check https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/numpy_support.py for more information.
            Defaults to None.
            Warning with int8, uint8 and int64 type of value, the vtk data type corresponding are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # Check if the input mesh is inherited from vtkDataSet.
    if not isinstance( dataSet, vtkDataSet ):
        logger.error( f"Input mesh has to be inherited from vtkDataSet." )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    # Check if the attribute already exist in the input mesh.
    if isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already present in the dataSet." )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    # Check the coherency between the given array type and the vtk array type if it exist.
    if vtkDataType is not None:
        vtkNumpyTypeMap: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
        if vtkDataType not in vtkNumpyTypeMap:
            logger.error( f"The vtk data type { vtkDataType } is unknown." )
            logger.error( f"The attribute { attributeName } has not been created into the mesh." )
            return False
        npArrayTypeFromVtk: type = vtkNumpyTypeMap[ vtkDataType ]().dtype        
        npArrayTypeFromInput: type = npArray.dtype
        if npArrayTypeFromVtk != npArrayTypeFromInput:
            logger.error( f"The numpy array type { npArrayTypeFromInput } is not coherent with the type of array created ({ npArrayTypeFromVtk }) from the given vtkDataType." )
            logger.error( f"The attribute { attributeName } has not been created into the mesh." )
            return False

    data: Union[ vtkPointData, vtkCellData]
    nbElements: int
    oppositePieceName: str
    if onPoints:
        data = dataSet.GetPointData()
        nbElements = dataSet.GetNumberOfPoints()
        oppositePieceName = "cells"
    else:
        data = dataSet.GetCellData()
        nbElements = dataSet.GetNumberOfCells()
        oppositePieceName = "points"
    
    # Check if the input array has the good size.
    if len( npArray ) != nbElements:
        logger.error( f"The array has to have { nbElements } elements, but have only { len( npArray ) } elements" )
        logger.error( f"The attribute { attributeName } has not been created into the mesh." )
        return False
    
    # Check if an attribute with the same name exist on the opposite piece (points or cells).
    oppositePiece: bool = not onPoints
    if isAttributeInObjectDataSet( dataSet, attributeName, oppositePiece ):
        logger.warning( f"An attribute with the same name ({ attributeName }) is already present in the dataSet but on { oppositePieceName }." )
    
    # Convert the numpy array int a vtkDataArray.
    createdAttribute: vtkDataArray = vnp.numpy_to_vtk( npArray, deep=True, array_type=vtkDataType )
    createdAttribute.SetName( attributeName )

    nbComponents: int = createdAttribute.GetNumberOfComponents()
    nbNames: int = len( componentNames )
    if nbComponents == 1 and nbNames > 0:
        logger.warning( f"The array has one component and no name, the components names you have enter will not be taking into account." )
    
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
    multiBlockDataSetFrom: vtkMultiBlockDataSet,
    multiBlockDataSetTo: vtkMultiBlockDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool = False,
    logger: Logger = getLogger( "copyAttribute", True ),
) -> bool:
    """Copy an attribute from a multiBlockDataSet to a similare one on the same piece. 

    Args:
        multiBlockDataSetFrom (vtkMultiBlockDataSet): MultiBlockDataSet from which to copy the attribute.
        multiBlockDataSetTo (vtkMultiBlockDataSet): MultiBlockDataSet where to copy the attribute.
        attributeNameFrom (str): Attribute name in multiBlockDataSetFrom.
        attributeNameTo (str): Attribute name in multiBlockDataSetTo. It will be a new attribute of multiBlockDataSetTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    # Check if the multiBlockDataSetFrom is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSetFrom, vtkMultiBlockDataSet ):
        logger.error( f"multiBlockDataSetFrom has to be inherited from vtkMultiBlockDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False

    # Check if the multiBlockDataSetTo is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSetTo, vtkMultiBlockDataSet ):
        logger.error( f"multiBlockDataSetTo has to be inherited from vtkMultiBlockDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Check if the attribute exist in the multiBlockDataSetFrom.
    if not isAttributeInObjectMultiBlockDataSet( multiBlockDataSetFrom, attributeNameFrom, onPoints ):
        logger.error( f"The attribute { attributeNameFrom } is not in the multiBlockDataSetFrom." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Check if the attribute already exist in the multiBlockDataSetTo.
    if isAttributeInObjectMultiBlockDataSet( multiBlockDataSetTo, attributeNameTo, onPoints ):
        logger.error( f"The attribute { attributeNameTo } is already in the multiBlockDataSetTo." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Check if the two multiBlockDataSets are similare.
    elementaryBlockIndexesTo: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetTo )
    elementaryBlockIndexesFrom: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetFrom )
    if elementaryBlockIndexesTo != elementaryBlockIndexesFrom:
        logger.error( f"multiBlockDataSetFrom and multiBlockDataSetTo do not have the same block indexes." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Parse blocks of the two mesh to copy the attribute.
    for idBlock in elementaryBlockIndexesTo:
        dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( multiBlockDataSetFrom, idBlock ) )
        if dataSetFrom is None:
            logger.error( f"Block { blockId } of multiBlockDataSetFrom is null." )
            logger.error( f"The attribute { attributeNameFrom } has not been copied." )
            return False

        dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( multiBlockDataSetTo, idBlock ) )
        if dataSetTo is None:
            logger.error( f"Block { blockId } of multiBlockDataSetTo is null." )
            logger.error( f"The attribute { attributeNameFrom } has not been copied." )
            return False

        if isAttributeInObjectDataSet( dataSetFrom, attributeNameFrom, onPoints ):
            if not copyAttributeDataSet( dataSetFrom, dataSetTo, attributeNameFrom, attributeNameTo, onPoints, logger ):
                return False

    return True


def copyAttributeDataSet(
    dataSetFrom: vtkDataSet,
    dataSetTo: vtkDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool = False,
    logger: Logger = getLogger( "copyAttributeDataSet", True ),
) -> bool:
    """Copy an attribute from a dataSet to a similare one on the same piece. 

    Args:
        dataSetFrom (vtkDataSet): DataSet from which to copy the attribute.
        dataSetTo (vtkDataSet): DataSet where to copy the attribute.
        attributeNameFrom (str): Attribute name in dataSetFrom.
        attributeNameTo (str): Attribute name in dataSetTo. It will be a new attribute of dataSetTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        logger (Logger, optional): A logger to manage the output messages.
            Defaults to an internal logger.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    # Check if the dataSetFrom is inherited from vtkDataSet.
    if not isinstance( dataSetFrom, vtkDataSet ):
        logger.error( f"dataSetFrom has to be inherited from vtkDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Check if the dataSetTo is inherited from vtkDataSet.
    if not isinstance( dataSetTo, vtkDataSet ):
        logger.error( f"dataSetTo has to be inherited from vtkDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Check if the attribute exist in the dataSetFrom.
    if not isAttributeInObjectDataSet( dataSetFrom, attributeNameFrom, onPoints ):
        logger.error( f"The attribute { attributeNameFrom } is not in the dataSetFrom." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Check if the attribute already exist in the dataSetTo.
    if isAttributeInObjectDataSet( dataSetTo, attributeNameTo, onPoints ):
        logger.error( f"The attribute { attributeNameTo } is already in the dataSetTo." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False
    
    # Get the properties of the attribute to copied.
    npArray: npt.NDArray[ Any ] = getArrayInObject( dataSetFrom, attributeNameFrom, onPoints )
    componentNames: tuple[ str, ...] = getComponentNamesDataSet( dataSetFrom, attributeNameFrom, onPoints )
    vtkArrayType: int = getVtkArrayTypeInObject( dataSetFrom, attributeNameFrom, onPoints )

    return createAttribute( dataSetTo, npArray, attributeNameTo, componentNames, onPoints, vtkArrayType, logger )


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
