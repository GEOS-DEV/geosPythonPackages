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
    VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE, VTK_FLOAT, VTK_DOUBLE,
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
    getVtkDataTypeInObject,
    getNumberOfComponentsMultiBlock,
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
    listValues: Union[ list[ Any ], None ] = None,
    logger: Union[ Logger, None ] = None,
) -> bool:
    """Fill input partial attribute of multiBlockDataSet with a constant value per component.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): MultiBlockDataSet where to fill the attribute.
        attributeName (str): Attribute name.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        listValues (list[Any], optional): List of filling value for each component.
            Defaults to None, the filling value is for all components:
            -1 for int VTK arrays.
            0 for uint VTK arrays.
            nan for float VTK arrays.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if the attribute was correctly created and filled, False if not.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "fillPartialAttributes", True )

    # Check if the input mesh is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        logger.error( "Input mesh has to be inherited from vtkMultiBlockDataSet." )
        return False

    # Check if the attribute is partial.
    if isAttributeGlobal( multiBlockDataSet, attributeName, onPoints ):
        logger.error( f"The attribute { attributeName } is already global." )
        return False

    # Get information of the attribute to fill.
    vtkDataType: int = getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, onPoints )
    nbComponents: int = getNumberOfComponentsMultiBlock( multiBlockDataSet, attributeName, onPoints )
    componentNames: tuple[ str, ...] = ()
    if nbComponents > 1:
        componentNames = getComponentNames( multiBlockDataSet, attributeName, onPoints )

    typeMapping: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
    valueType: type = typeMapping[ vtkDataType ]
    # Set the default value depending of the type of the attribute to fill
    if listValues is None:
        defaultValue: Any
        logger.warning( f"The attribute { attributeName } is filled with the default value for each component." )
        # Default value for float types is nan.
        if vtkDataType in ( VTK_FLOAT, VTK_DOUBLE ):
            defaultValue = valueType( np.nan )
            logger.warning(
                f"{ attributeName } vtk data type is { vtkDataType } corresponding to { defaultValue.dtype } numpy type, default value is automatically set to nan."
            )
        # Default value for int types is -1.
        elif vtkDataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ):
            defaultValue = valueType( -1 )
            logger.warning(
                f"{ attributeName } vtk data type is { vtkDataType } corresponding to { defaultValue.dtype } numpy type, default value is automatically set to -1."
            )
        # Default value for uint types is 0.
        elif vtkDataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT,
                              VTK_UNSIGNED_LONG_LONG ):
            defaultValue = valueType( 0 )
            logger.warning(
                f"{ attributeName } vtk data type is { vtkDataType } corresponding to { defaultValue.dtype } numpy type, default value is automatically set to 0."
            )
        else:
            logger.error( f"The type of the attribute { attributeName } is not compatible with the function." )
            return False

        listValues = [ defaultValue ] * nbComponents

    else:
        if len( listValues ) != nbComponents:
            return False

        for idValue in range( nbComponents ):
            value: Any = listValues[ idValue ]
            if type( value ) is not valueType:
                listValues[ idValue ] = valueType( listValues[ idValue ] )
                logger.warning(
                    f"The filling value { value } for the attribute { attributeName } has not the correct type, it is convert to the numpy scalar type { valueType().dtype }."
                )

    # Parse the multiBlockDataSet to create and fill the attribute on blocks where it is not.
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOn()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iterator.GetCurrentDataObject() )
        if not isAttributeInObjectDataSet( dataSet, attributeName, onPoints ) and \
           not createConstantAttributeDataSet( dataSet, listValues, attributeName, componentNames, onPoints, vtkDataType, logger ):
            return False

        iterator.GoToNextItem()

    return True


def fillAllPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    logger: Union[ Logger, None ] = None,
) -> bool:
    """Fill all partial attributes of a multiBlockDataSet with the default value. All components of each attributes are filled with the same value. Depending of the type of the attribute, the default value is different 0, -1 and nan for respectively uint, int and float vtk type.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): MultiBlockDataSet where to fill attributes.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if attributes were correctly created and filled, False if not.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "fillAllPartialAttributes", True )

    # Parse all partial attributes, onPoints and onCells to fill them.
    for onPoints in [ True, False ]:
        infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, onPoints )
        for attributeName in infoAttributes:
            if not isAttributeGlobal( multiBlockDataSet, attributeName, onPoints ) and \
               not fillPartialAttributes( multiBlockDataSet, attributeName, onPoints=onPoints, logger=logger ):
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
        vtkDataArray: The empty attribute.
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
    vtkDataType: Union[ int, None ] = None,
    logger: Union[ Logger, None ] = None,
) -> bool:
    """Create a new attribute with a constant value in the object.

    Args:
        object (vtkDataObject): Object (vtkMultiBlockDataSet, vtkDataSet) where to create the attribute.
        listValues (list[Any]): List of values of the attribute for each components. It is recommended to use numpy scalar type for the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union[int, None], optional): Vtk data type of the attribute to create.
            Defaults to None, the vtk data type is given by the type of the values.

            Warning with int8, uint8 and int64 type of value, the corresponding vtk data type are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "createConstantAttribute", True )

    # Deals with multiBlocksDataSets.
    if isinstance( object, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return createConstantAttributeMultiBlock( object, listValues, attributeName, componentNames, onPoints,
                                                  vtkDataType, logger )

    # Deals with dataSets.
    elif isinstance( object, vtkDataSet ):
        return createConstantAttributeDataSet( object, listValues, attributeName, componentNames, onPoints, vtkDataType,
                                               logger )

    else:
        logger.error( "The mesh has to be inherited from a vtkMultiBlockDataSet or a vtkDataSet" )
        logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
        return False


def createConstantAttributeMultiBlock(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    listValues: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, None ] = None,
    logger: Union[ Logger, None ] = None,
) -> bool:
    """Create a new attribute with a constant value per component on every block of the multiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): MultiBlockDataSet where to create the attribute.
        listValues (list[Any]): List of values of the attribute for each components. It is recommended to use numpy scalar type for the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union[int, None], optional): Vtk data type of the attribute to create.
            Defaults to None, the vtk data type is given by the type of the values.

            Warning with int8, uint8 and int64 type of value, the corresponding vtk data type are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "createConstantAttributeMultiBlock", True )

    # Check if the input mesh is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        logger.error( "Input mesh has to be inherited from vtkMultiBlockDataSet." )
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
        oppositePieceState: str = "global" if isAttributeGlobal( multiBlockDataSet, attributeName,
                                                                 oppositePiece ) else "partial"
        logger.warning(
            f"A { oppositePieceState } attribute with the same name ({ attributeName }) is already present in the multiBlockDataSet but on { oppositePieceName }."
        )

    # Parse the multiBlockDataSet to create the constant attribute on each blocks.
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( multiBlockDataSet )
    iterator.VisitOnlyLeavesOn()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iterator.GetCurrentDataObject() )
        if not createConstantAttributeDataSet( dataSet, listValues, attributeName, componentNames, onPoints,
                                               vtkDataType, logger ):
            return False

        iterator.GoToNextItem()

    return True


def createConstantAttributeDataSet(
    dataSet: vtkDataSet,
    listValues: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    onPoints: bool = False,
    vtkDataType: Union[ int, None ] = None,
    logger: Union[ Logger, None ] = None,
) -> bool:
    """Create an attribute with a constant value per component in the dataSet.

    Args:
        dataSet (vtkDataSet): DataSet where to create the attribute.
        listValues (list[Any]): List of values of the attribute for each components. It is recommended to use numpy scalar type for the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union[int, None], optional): Vtk data type of the attribute to create.
            Defaults to None, the vtk data type is given by the type of the values.

            Warning with int8, uint8 and int64 type of value, the corresponding vtk data type are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "createConstantAttributeDataSet", True )

    # Check if all the values of listValues have the same type.
    valueType: type = type( listValues[ 0 ] )
    for value in listValues:
        valueTypeTest: type = type( value )
        if valueType != valueTypeTest:
            logger.error( "All values in the list of values don't have the same type." )
            logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
            return False

    # Convert int and float type into numpy scalar type.
    if valueType in ( int, float ):
        npType: type = type( np.array( listValues )[ 0 ] )
        logger.warning(
            f"During the creation of the constant attribute { attributeName }, values have been converted from { valueType } to { npType }."
        )
        logger.warning( "To avoid any issue with the conversion, please use directly numpy scalar type for the values" )
        valueType = npType

    # Check the consistency between the given value type and the vtk array type if it exists.
    valueType = valueType().dtype
    if vtkDataType is not None:
        vtkNumpyTypeMap: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
        if vtkDataType not in vtkNumpyTypeMap:
            logger.error( f"The vtk data type { vtkDataType } is unknown." )
            logger.error( f"The constant attribute { attributeName } has not been created into the mesh." )
            return False
        npArrayTypeFromVtk: npt.DTypeLike = vtkNumpyTypeMap[ vtkDataType ]().dtype
        if npArrayTypeFromVtk != valueType:
            logger.error(
                f"Values type { valueType } is not coherent with the type of array created ({ npArrayTypeFromVtk }) from the given vtkDataType."
            )
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
    vtkDataType: Union[ int, None ] = None,
    logger: Union[ Logger, None ] = None,
) -> bool:
    """Create an attribute from the given numpy array.

    Args:
        dataSet (vtkDataSet): DataSet where to create the attribute.
        npArray (NDArray[Any]): Array that contains the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        vtkDataType (Union[int, None], optional): Vtk data type of the attribute to create.
            Defaults to None, the vtk data type is given by the type of the array.

            Warning with int8, uint8 and int64 type, the corresponding vtk data type are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if the attribute was correctly created, False if it was not created.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "createAttribute", True )

    # Check if the input mesh is inherited from vtkDataSet.
    if not isinstance( dataSet, vtkDataSet ):
        logger.error( "Input mesh has to be inherited from vtkDataSet." )  # type: ignore[unreachable]
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
        npArrayTypeFromVtk: npt.DTypeLike = vtkNumpyTypeMap[ vtkDataType ]().dtype
        npArrayTypeFromInput: npt.DTypeLike = npArray.dtype
        if npArrayTypeFromVtk != npArrayTypeFromInput:
            logger.error(
                f"The numpy array type { npArrayTypeFromInput } is not coherent with the type of array created ({ npArrayTypeFromVtk }) from the given vtkDataType."
            )
            logger.error( f"The attribute { attributeName } has not been created into the mesh." )
            return False

    data: Union[ vtkPointData, vtkCellData ]
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
        logger.warning(
            f"An attribute with the same name ({ attributeName }) is already present in the dataSet but on { oppositePieceName }."
        )

    # Convert the numpy array int a vtkDataArray.
    createdAttribute: vtkDataArray = vnp.numpy_to_vtk( npArray, deep=True, array_type=vtkDataType )
    createdAttribute.SetName( attributeName )

    nbComponents: int = createdAttribute.GetNumberOfComponents()
    nbNames: int = len( componentNames )
    if nbComponents == 1 and nbNames > 0:
        logger.warning(
            "The array has one component and no name, the components names you have enter will not be taking into account."
        )

    if nbComponents > 1:
        if nbNames < nbComponents:
            componentNames = tuple( [ "Component" + str( i ) for i in range( nbComponents ) ] )
            logger.warning(
                f"Insufficient number of input component names. { attributeName } component names will be set to : Component0, Component1 ..."
            )
        elif nbNames > nbComponents:
            logger.warning(
                f"Excessive number of input component names, only the first { nbComponents } names will be used." )

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
    logger: Union[ Logger, None ] = None,
) -> bool:
    """Copy an attribute from a multiBlockDataSet to a similar one on the same piece.

    Args:
        multiBlockDataSetFrom (vtkMultiBlockDataSet): MultiBlockDataSet from which to copy the attribute.
        multiBlockDataSetTo (vtkMultiBlockDataSet): MultiBlockDataSet where to copy the attribute.
        attributeNameFrom (str): Attribute name in multiBlockDataSetFrom.
        attributeNameTo (str): Attribute name in multiBlockDataSetTo. It will be a new attribute of multiBlockDataSetTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "copyAttribute", True )

    # Check if the multiBlockDataSetFrom is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSetFrom, vtkMultiBlockDataSet ):
        logger.error(  # type: ignore[unreachable]
            "multiBlockDataSetFrom has to be inherited from vtkMultiBlockDataSet." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False

    # Check if the multiBlockDataSetTo is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSetTo, vtkMultiBlockDataSet ):
        logger.error(  # type: ignore[unreachable]
            "multiBlockDataSetTo has to be inherited from vtkMultiBlockDataSet." )
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

    # Check if the two multiBlockDataSets are similar.
    elementaryBlockIndexesTo: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetTo )
    elementaryBlockIndexesFrom: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetFrom )
    if elementaryBlockIndexesTo != elementaryBlockIndexesFrom:
        logger.error( "multiBlockDataSetFrom and multiBlockDataSetTo do not have the same block indexes." )
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False

    # Parse blocks of the two mesh to copy the attribute.
    for idBlock in elementaryBlockIndexesTo:
        dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( multiBlockDataSetFrom, idBlock ) )
        if dataSetFrom is None:
            logger.error( f"Block { idBlock } of multiBlockDataSetFrom is null." )  # type: ignore[unreachable]
            logger.error( f"The attribute { attributeNameFrom } has not been copied." )
            return False

        dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( multiBlockDataSetTo, idBlock ) )
        if dataSetTo is None:
            logger.error( f"Block { idBlock } of multiBlockDataSetTo is null." )  # type: ignore[unreachable]
            logger.error( f"The attribute { attributeNameFrom } has not been copied." )
            return False

        if isAttributeInObjectDataSet( dataSetFrom, attributeNameFrom, onPoints ) and \
        not copyAttributeDataSet( dataSetFrom, dataSetTo, attributeNameFrom, attributeNameTo, onPoints, logger ):
            return False

    return True


def copyAttributeDataSet(
    dataSetFrom: vtkDataSet,
    dataSetTo: vtkDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool = False,
    logger: Union[ Logger, Any ] = None,
) -> bool:
    """Copy an attribute from a dataSet to a similar one on the same piece.

    Args:
        dataSetFrom (vtkDataSet): DataSet from which to copy the attribute.
        dataSetTo (vtkDataSet): DataSet where to copy the attribute.
        attributeNameFrom (str): Attribute name in dataSetFrom.
        attributeNameTo (str): Attribute name in dataSetTo. It will be a new attribute of dataSetTo.
        onPoints (bool, optional): True if attributes are on points, False if they are on cells.
            Defaults to False.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if copy successfully ended, False otherwise.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "copyAttributeDataSet", True )

    # Check if the dataSetFrom is inherited from vtkDataSet.
    if not isinstance( dataSetFrom, vtkDataSet ):
        logger.error( "dataSetFrom has to be inherited from vtkDataSet." )  # type: ignore[unreachable]
        logger.error( f"The attribute { attributeNameFrom } has not been copied." )
        return False

    # Check if the dataSetTo is inherited from vtkDataSet.
    if not isinstance( dataSetTo, vtkDataSet ):
        logger.error( "dataSetTo has to be inherited from vtkDataSet." )  # type: ignore[unreachable]
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

    npArray: npt.NDArray[ Any ] = getArrayInObject( dataSetFrom, attributeNameFrom, onPoints )
    componentNames: tuple[ str, ...] = getComponentNamesDataSet( dataSetFrom, attributeNameFrom, onPoints )
    vtkArrayType: int = getVtkArrayTypeInObject( dataSetFrom, attributeNameFrom, onPoints )

    return createAttribute( dataSetTo, npArray, attributeNameTo, componentNames, onPoints, vtkArrayType, logger )


def transferAttributeToDataSetWithElementMap(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    dataSetTo: vtkDataSet,
    dictElementMap: dict[ int, npt.NDArray[ np.int64] ],
    attributeName: str,
    onPoints: bool,
    flatIdDataSetTo: int = 0,
    logger: Union[ Logger, Any ] = None,
) -> bool:
    """Transfer attributes from the meshFrom to the dataSetTo using a mapping.

    If meshFrom is a vtkDataSet, the flat index (flatIdDataSetFrom) is set to 0.
    dataSetTo is considered as block of vtkMultiblockDataSet, if not the flat index (flatIdDataSetTo) is set to 0.

    The map used to transfer the attribute is a dictionary where:
        - The keys is the flat index of the dataSetTo (flatIdDataSetTo).
        - The item is an array of size (nb elements in dataSetTo, 2).
    
    If an element (idElementTo) of the dataSetTo (flatIdDataSetTo) is mapped with no element of the meshFrom:
        - dictElementMap[flatIdDataSetTo][idElementTo] = [-1, -1].
        - The value of the attribute for this element depends of the type of the value of the attribute (0 for unit, -1 for int, nan for float).

    If an element (idElementTo) of the dataSetTo (flatIdDataSetTo) is mapped with an element (idElementFrom) of one of the meshFrom's dataset (flatIdDataSetFrom):
        - dictElementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom].
        - The value of the attribute for this element is the value of the element (idElementFrom) of the meshFrom on on the dataSetFrom (flatIdDataSetFrom).

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the attribute to transfer.
        dataSetTo (vtkDataSet): The mesh where to transfer the attribute.
        dictElementMap (dict[int, npt.NDArray[np.int64]]): The elementMap.
        attributeName (str): The name of the attribute to transfer.
        onPoints (bool): True if the attribute is on points, False if it is on cells.
        flatIdDataSetTo (int, Optional): The flat index of the dataSetTo.
            Defaults to 0.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if transfer successfully ended.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "transferAttributeToDataSetWithElementMap", True )

    if flatIdDataSetTo not in dictElementMap.keys():
        logger.error( f"The map is incomplete, there is no data for the dataSetTo (flat index { flatIdDataSetTo })." )
        return False
    
    nbElementsTo: int = dataSetTo.GetNumberOfPoints() if onPoints else dataSetTo.GetNumberOfCells()
    if len( dictElementMap[ flatIdDataSetTo ] ) != nbElementsTo:
        logger.error( f"The map is wrong, there is { nbElementsTo } elements in the the dataSetTo (flat index { flatIdDataSetTo })\
                      but { len( dictElementMap[ flatIdDataSetTo ] ) } elements in the map." )
        return False

    componentNames: tuple[ str, ...] = getComponentNames( meshFrom, attributeName, onPoints )
    nbComponents: int = len( componentNames )

    vtkDataType: int = getVtkDataTypeInObject( meshFrom, attributeName, onPoints )
    defaultValue: Any
    if vtkDataType in ( VTK_FLOAT, VTK_DOUBLE ):
        defaultValue = np.nan
    elif vtkDataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ):
        defaultValue = -1
    elif vtkDataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT,
                            VTK_UNSIGNED_LONG_LONG ):
        defaultValue = 0

    typeMapping: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
    valueType: type = typeMapping[ vtkDataType ]

    arrayTo: npt.NDArray[ Any ]
    if nbComponents > 1:
        defaultValue = [ defaultValue ] * nbComponents
        arrayTo = np.full( ( nbElementsTo, nbComponents ), defaultValue, dtype=valueType )
    else:
        arrayTo = np.array( [ defaultValue for _ in range( nbElementsTo ) ], dtype=valueType )

    for idElementTo in range( nbElementsTo ):
        valueToTransfer: Any = defaultValue
        idElementFrom: int = dictElementMap[ flatIdDataSetTo ][ idElementTo ][ 1 ]
        if idElementFrom != -1:
            flatIdDataSetFrom = dictElementMap[ flatIdDataSetTo ][ idElementTo ][ 0 ]
            dataFrom: Union[ vtkPointData, vtkCellData ]
            if isinstance( meshFrom, vtkDataSet ):
                dataFrom = meshFrom.GetPointData() if onPoints else  meshFrom.GetCellData()
            elif isinstance( meshFrom, vtkMultiBlockDataSet ):
                dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( flatIdDataSetFrom ) )
                dataFrom = dataSetFrom.GetPointData() if onPoints else  dataSetFrom.GetCellData()
            arrayFrom: npt.NDArray[ Any ] = vnp.vtk_to_numpy( dataFrom.GetArray( attributeName ) )
            valueToTransfer = arrayFrom[ idElementFrom ]
        arrayTo[ idElementTo ] = valueToTransfer

    return createAttribute( dataSetTo,
                            arrayTo,
                            attributeName,
                            componentNames,
                            onPoints=onPoints,
                            vtkDataType=vtkDataType,
                            logger=logger )


def transferAttributeWithElementMap(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    dictElementMap: dict[ int, npt.NDArray[ np.int64] ],
    attributeName: str,
    onPoints: bool,
    logger: Union[ Logger, Any ] = None,
) -> bool:
    """Transfer attributes from the meshFrom to the meshTo using a mapping.

    If meshFrom is a vtkDataSet, the flat index (flatIdDataSetFrom) is set to 0.
    If meshTo is a vtkDataSet, the flat index (flatIdDataSetTo) is set to 0.

    The elementMap is a dictionary where:
        - Keys are the flat index of all the datasets of the meshTo.
        - Items are arrays of size (nb elements in datasets, 2).
    
    If an element (idElementTo) of one of the meshTo's dataSet (flatIdDataSetTo) is mapped with no element of the meshFrom:
        - dictElementMap[flatIdDataSetTo][idElementTo] = [-1, -1].
        - The value of the attribute for this element depends of the type of the value of the attribute (0 for unit, -1 for int, nan for float).

    If an element (idElementTo) of one of the meshTo's dataSet (flatIdDataSetTo) is mapped with an element (idElementFrom) of one of the meshFrom's dataset (flatIdDataSetFrom):
        - dictElementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom].
        - The value of the attribute for this element is the value of the element (idElementFrom) of the meshFrom on on the dataSetFrom (flatIdDataSetFrom).

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the attribute to transfer.
        meshTo (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh where to transfer the attribute.
        dictElementMap (dict[int, npt.NDArray[np.int64]]): The elementMap.
        attributeName (str): The name of the attribute to transfer.
        onPoints (bool): True if the attribute is on points, False if it is on cells.
        flatIdDataSetTo (int, Optional): The flat index of the dataSetTo.
            Defaults to 0.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        bool: True if transfer successfully ended.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "transferAttributeWithElementMap", True )

    if isinstance( meshTo, vtkDataSet ):
        return transferAttributeToDataSetWithElementMap( meshFrom, meshTo, dictElementMap, attributeName, onPoints, logger=logger )
    elif isinstance( meshTo, vtkMultiBlockDataSet ):
        listFlatIdMultiBlockDataSetTo: list[ int ] = getBlockElementIndexesFlatten( meshTo )
        for flatIdDataSetTo in range( listFlatIdMultiBlockDataSetTo ):
            dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( meshTo.GetDataSet( flatIdDataSetTo ) )
            if not transferAttributeToDataSetWithElementMap( meshFrom, dataSetTo, dictElementMap, attributeName, onPoints, flatIdDataSetTo=flatIdDataSetTo, logger=logger ):
                logger.error( f"The attribute transfer has failed for the dataset with the flat index { flatIdDataSetTo } of the meshTo.")
                return False
        return True

    return False


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
        iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
        iterator.SetDataSet( mesh )
        iterator.VisitOnlyLeavesOn()
        iterator.GoToFirstItem()
        while iterator.GetCurrentDataObject() is not None:
            block: vtkDataSet = vtkDataSet.SafeDownCast( iterator.GetCurrentDataObject() )
            ret *= int( doCreateCellCenterAttribute( block, cellCenterAttributeName ) )
            iterator.GoToNextItem()
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
