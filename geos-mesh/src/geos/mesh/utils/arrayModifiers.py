# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Alexandre Benedicto, Paloma Martinez, Romain Baville
import logging
import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from typing import Union, Any
from geos.utils.Logger import ( getLogger, Logger, VTKCaptureLog, RegexExceptionFilter )

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
    vtkPointData,
    vtkCellData,
    vtkCell,
)
from vtkmodules.vtkFiltersCore import (
    vtkArrayRename,
    vtkCellCenters,
    vtkPointDataToCellData,
)
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkPoints,
    vtkLogger,
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
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten
from geos.utils.Errors import VTKError

from geos.utils.pieceEnum import Piece

__doc__ = """
ArrayModifiers contains utilities to process VTK Arrays objects.

These methods include:
    - filling partial VTK arrays with values (useful for block merge)
    - creation of new VTK array, empty or with a given data array
    - copy VTK array from a source mesh to a final mesh
    - transfer VTK array from a source mesh to a final mesh with a element map
    - transfer from VTK point data to VTK cell data
"""


def fillPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    attributeName: str,
    piece: Piece = Piece.CELLS,
    listValues: Union[ list[ Any ], None ] = None,
    logger: Union[ Logger, None ] = None,
    fillAll: bool = False,
) -> None:
    """Fill input partial attribute of multiBlockDataSet with a constant value per component.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): MultiBlockDataSet where to fill the attribute.
        attributeName (str): Attribute name.
        piece (Piece): The piece of the attribute.
            Defaults to Piece.CELLS
        listValues (list[Any], optional): List of filling value for each component.
            Defaults to None, the filling value is for all components:
            -1 for int VTK arrays.
            0 for uint VTK arrays.
            nan for float VTK arrays.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.
        fillAll (bool, optional): True if fillPartialAttributes is used by fillAllPartialAttributes, else False.
            Defaults to False.

    Raises:
        TypeError: Error with the type of the mesh.
        ValueError: Error with the values of the listValues.
        AttributeError: Error with the attribute attributeName.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "fillPartialAttributes", True )

    # Check if the input mesh is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        raise TypeError( "Input mesh has to be inherited from vtkMultiBlockDataSet." )

    # Check if the attribute exist in the input mesh.
    if not isAttributeInObjectMultiBlockDataSet( multiBlockDataSet, attributeName, piece ):
        raise AttributeError( f"The attribute { attributeName } is not in the mesh." )

    # Check if the attribute is partial.
    if isAttributeGlobal( multiBlockDataSet, attributeName, piece ):
        raise AttributeError( f"The attribute { attributeName } is already global." )

    # Get information of the attribute to fill.
    vtkDataType: int = getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, piece )
    nbComponents: int = getNumberOfComponentsMultiBlock( multiBlockDataSet, attributeName, piece )
    componentNames: tuple[ str, ...] = ()
    if nbComponents > 1:
        componentNames = getComponentNames( multiBlockDataSet, attributeName, piece )

    typeMapping: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
    valueType: type = typeMapping[ vtkDataType ]
    # Set the default value depending of the type of the attribute to fill
    if listValues is None:
        defaultValue: Any
        mess: str = f"The attribute { attributeName } is filled with the default value for each component.\n"
        # Default value for float types is nan.
        if vtkDataType in ( VTK_FLOAT, VTK_DOUBLE ):
            defaultValue = valueType( np.nan )
            mess = mess + f"{ attributeName } vtk data type is { vtkDataType } corresponding to { defaultValue.dtype } numpy type, default value is automatically set to nan."
        # Default value for int types is -1.
        elif vtkDataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ):
            defaultValue = valueType( -1 )
            mess = mess + f"{ attributeName } vtk data type is { vtkDataType } corresponding to { defaultValue.dtype } numpy type, default value is automatically set to -1."
        # Default value for uint types is 0.
        elif vtkDataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT,
                              VTK_UNSIGNED_LONG_LONG ):
            defaultValue = valueType( 0 )
            mess = mess + f"{ attributeName } vtk data type is { vtkDataType } corresponding to { defaultValue.dtype } numpy type, default value is automatically set to 0."
        else:
            raise AttributeError( f"The attribute { attributeName } has an unknown type." )

        listValues = [ defaultValue ] * nbComponents

        if not fillAll:
            logger.warning( mess )

    else:
        if len( listValues ) != nbComponents:
            raise ValueError( f"The listValues must have { nbComponents } elements, not { len( listValues ) }." )

        for idValue in range( nbComponents ):
            value: Any = listValues[ idValue ]
            if type( value ) is not valueType:
                listValues[ idValue ] = valueType( listValues[ idValue ] )
                logger.warning(
                    f"The filling value { value } for the attribute { attributeName } has not the correct type, it is convert to the numpy scalar type { valueType().dtype }."
                )

    # Parse the multiBlockDataSet to create and fill the attribute on blocks where it is not.
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        if not isAttributeInObjectDataSet( dataSet, attributeName, piece ):
            createConstantAttribute( dataSet, listValues, attributeName, componentNames, piece, vtkDataType, logger )

    return


def fillAllPartialAttributes(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ],
    logger: Union[ Logger, None ] = None,
) -> None:
    """Fill all partial attributes of a multiBlockDataSet with the default value.

    All components of each attributes are filled with the same value. Depending of the type of the attribute's data, the default value is different:
        0 for uint data,
        -1 for int data,
        nan float data,

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): MultiBlockDataSet where to fill attributes.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the type of the mesh.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "fillAllPartialAttributes", True )

    # Check if the input mesh is inherited from vtkMultiBlockDataSet.
    if not isinstance( multiBlockDataSet, vtkMultiBlockDataSet ):
        raise TypeError( "Input mesh has to be inherited from vtkMultiBlockDataSet." )

    logger.warning(
        "The filling value for the attributes is depending of the type of attribute's data:\n0 for uint data,\n-1 for int data,\nnan for float data."
    )

    # Parse all partial attributes, onPoints and onCells to fill them.
    for piece in [ Piece.POINTS, Piece.CELLS ]:
        infoAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( multiBlockDataSet, piece )
        for attributeName in infoAttributes:
            if not isAttributeGlobal( multiBlockDataSet, attributeName, piece ):
                fillPartialAttributes( multiBlockDataSet, attributeName, piece=piece, logger=logger, fillAll=True )

    return


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

    Raises:
        ValueError: Error with the vtkDataType.

    Returns:
        vtkDataArray: The empty attribute.
    """
    # Check if the vtk data type is correct.
    vtkNumpyTypeMap: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
    if vtkDataType not in vtkNumpyTypeMap:
        raise ValueError( f"Attribute type { vtkDataType } is unknown." )

    nbComponents: int = len( componentNames )

    createdAttribute: vtkDataArray = vtkDataArray.CreateDataArray( vtkDataType )
    createdAttribute.SetName( attributeName )
    createdAttribute.SetNumberOfComponents( nbComponents )
    if nbComponents > 1:
        for i in range( nbComponents ):
            createdAttribute.SetComponentName( i, componentNames[ i ] )

    return createdAttribute


def createConstantAttribute(
    mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet ],
    listValues: list[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    piece: Piece = Piece.CELLS,
    vtkDataType: Union[ int, None ] = None,
    logger: Union[ Logger, None ] = None,
) -> None:
    """Create a new attribute with a constant value in the mesh.

    Args:
        mesh (Union[vtkMultiBlockDataSet, vtkDataSet]): Mesh where to create the attribute.
        listValues (list[Any]): List of values of the attribute for each components. It is recommended to use numpy scalar type for the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        piece (Piece): The piece of the attribute.
            Defaults to Piece.CELLS
        vtkDataType (Union[int, None], optional): Vtk data type of the attribute to create.
            Defaults to None, the vtk data type is given by the type of the values.

            Warning with int8, uint8 and int64 type of value, the corresponding vtk data type are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the type of the input mesh or the type of the input values or the vtkDataType.
        AttributeError: The attribute is already on the mesh.
        ValueError: Error with the vtkDataType (unknown) or with the piece.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "createConstantAttribute", True )

    # Deals with multiBlocksDataSets.
    if isinstance( mesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        # Check if the attribute already exist in the input mesh.
        if isAttributeInObjectMultiBlockDataSet( mesh, attributeName, piece ):
            raise AttributeError( f"The attribute { attributeName } is already on the mesh." )

        # Parse the multiBlockDataSet to create the constant attribute on each blocks.
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for blockIndex in elementaryBlockIndexes:
            dataSet: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( blockIndex ) )
            createConstantAttribute( dataSet, listValues, attributeName, componentNames, piece, vtkDataType, logger )

    # Deals with dataSets.
    elif isinstance( mesh, vtkDataSet ):
        # Check the piece.
        if piece not in [ Piece.POINTS, Piece.CELLS ]:
            raise ValueError( f"The attribute must be created on { Piece.POINTS.value } or { Piece.CELLS.value }." )

        # Check if all the values of listValues have the same type.
        valueType: type = type( listValues[ 0 ] )
        for value in listValues:
            valueTypeTest: type = type( value )
            if valueType != valueTypeTest:
                raise TypeError( "All values in the list of values must have the same type." )

        # Convert int and float type into numpy scalar type.
        if valueType in ( int, float ):
            npType: type = type( np.array( listValues )[ 0 ] )
            logger.warning(
                f"During the creation of the constant attribute { attributeName }, values have been converted from { valueType } to { npType }."
            )
            logger.warning(
                "To avoid any issue with the conversion, please use directly numpy scalar type for the values" )
            valueType = npType

        # Check the consistency between the given value type and the vtk array type if it exists.
        valueType = valueType().dtype
        if vtkDataType is not None:
            vtkNumpyTypeMap: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
            if vtkDataType not in vtkNumpyTypeMap:
                raise ValueError( f"The vtk data type { vtkDataType } is unknown." )

            npArrayTypeFromVtk: npt.DTypeLike = vtkNumpyTypeMap[ vtkDataType ]().dtype
            if npArrayTypeFromVtk != valueType:
                raise TypeError( f"Input values in listValues type must be { npArrayTypeFromVtk }, not { valueType }." )

        # Create the numpy array constant per component.
        nbComponents: int = len( listValues )
        nbElements: int = ( mesh.GetNumberOfPoints() if piece == Piece.POINTS else mesh.GetNumberOfCells() )
        npArray: npt.NDArray[ Any ]
        if nbComponents > 1:
            npArray = np.array( [ listValues for _ in range( nbElements ) ], valueType )
        else:
            npArray = np.array( [ listValues[ 0 ] for _ in range( nbElements ) ], valueType )

        createAttribute( mesh, npArray, attributeName, componentNames, piece, vtkDataType, logger )

    else:
        raise TypeError( "Input mesh has to be inherited from vtkMultiBlockDataSet or vtkDataSet." )

    return


def createAttribute(
    dataSet: vtkDataSet,
    npArray: npt.NDArray[ Any ],
    attributeName: str,
    componentNames: tuple[ str, ...] = (),  # noqa: C408
    piece: Piece = Piece.CELLS,
    vtkDataType: Union[ int, None ] = None,
    logger: Union[ Logger, None ] = None,
) -> None:
    """Create the attribute from the given numpy array on the dataSet.

    Args:
        dataSet (vtkDataSet): DataSet where to create the attribute.
        npArray (NDArray[Any]): Array that contains the values.
        attributeName (str): Name of the attribute.
        componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
            Defaults to an empty tuple.
        piece (Piece): The piece of the attribute.
            Defaults to Piece.CELLS
        vtkDataType (Union[int, None], optional): Vtk data type of the attribute to create.
            Defaults to None, the vtk data type is given by the type of the array.

            Warning with int8, uint8 and int64 type, the corresponding vtk data type are multiples. By default:
            - int8 -> VTK_SIGNED_CHAR
            - uint8 -> VTK_UNSIGNED_CHAR
            - int64 -> VTK_LONG_LONG
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the type of the mesh or the npArray values.
        ValueError: Error with the values of npArray or vtkDataType.
        AttributeError: Error with the attribute attributeName.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "createAttribute", True )

    # Check the piece.
    if piece not in [ Piece.POINTS, Piece.CELLS ]:
        raise ValueError( f"The attribute must be created on { Piece.POINTS.value } or { Piece.CELLS.value }." )

    # Check if the input mesh is inherited from vtkDataSet.
    if not isinstance( dataSet, vtkDataSet ):
        raise TypeError( "Input dataSet has to be inherited from vtkDataSet." )

    # Check if the attribute already exist in the input mesh.
    if isAttributeInObjectDataSet( dataSet, attributeName, piece ):
        raise AttributeError( f"The attribute { attributeName } is already present in the mesh." )

    # Check if an attribute with the same name exist on the opposite piece (points or cells) on the input mesh.
    oppositePiece: Piece = Piece.CELLS if piece == Piece.POINTS else Piece.POINTS
    if isAttributeInObjectDataSet( dataSet, attributeName, oppositePiece ):
        logger.warning( f"The attribute { attributeName } exist on the opposite piece { oppositePiece.value }." )

    # Check the coherency between the given array type and the vtk array type if it exist.
    if vtkDataType is not None:
        vtkNumpyTypeMap: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
        if vtkDataType not in vtkNumpyTypeMap:
            raise ValueError( f"The vtk data type { vtkDataType } is unknown." )

        npArrayTypeFromVtk: npt.DTypeLike = vtkNumpyTypeMap[ vtkDataType ]().dtype
        npArrayTypeFromInput: npt.DTypeLike = npArray.dtype
        if npArrayTypeFromVtk != npArrayTypeFromInput:
            raise TypeError( f"Input npArray type must be { npArrayTypeFromVtk }, not { npArrayTypeFromInput }." )

    data: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if piece == Piece.POINTS:
        data = dataSet.GetPointData()
        nbElements = dataSet.GetNumberOfPoints()
    else:
        data = dataSet.GetCellData()
        nbElements = dataSet.GetNumberOfCells()

    # Check if the input array has the good size.
    if len( npArray ) != nbElements:
        raise ValueError( f"The npArray must have { nbElements } elements, not { len( npArray ) }." )

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

    return


def copyAttribute(
    meshFrom: vtkMultiBlockDataSet | vtkDataSet,
    meshTo: vtkMultiBlockDataSet | vtkDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    piece: Piece = Piece.CELLS,
    logger: Union[ Logger, None ] = None,
) -> None:
    """Copy an attribute from a mesh to a similar one on the same piece.

    The similarity of two meshes means that the two mesh have the same number of elements (cells and points) located in the same coordinates and with the same indexation. Testing this similarity is time consuming therefore, only few metric are compared:
        - the block indexation for multiblock dataset
        - the number of the element where the attribute is located, for multiblock dataset it is done for each block
        - the coordinates of the first element, for multiblock dataset it is done for each block

    Args:
        meshFrom (vtkMultiBlockDataSet | vtkDataSet): mesh from which to copy the attribute.
        meshTo (vtkMultiBlockDataSet | vtkDataSet): mesh where to copy the attribute.
        attributeNameFrom (str): Attribute name in meshFrom.
        attributeNameTo (str): Attribute name to set in meshTo.
        piece (Piece): The piece of the attribute.
            Defaults to Piece.CELLS
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the type of the source or final mesh.
        ValueError: Error with the data of the source or final mesh or the piece.
        AttributeError: Error with the attribute attributeNameFrom or attributeNameTo.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "copyAttribute", True )

    if isinstance( meshTo, vtkDataSet ) and isinstance( meshFrom, vtkDataSet ):
        # Small check to check if the two meshes are similar.
        coordElementTo: set[ tuple[ float, ...] ] = set()
        coordElementFrom: set[ tuple[ float, ...] ] = set()
        if piece == Piece.POINTS:
            coordElementTo.add( meshTo.GetPoint( 0 ) )
            coordElementFrom.add( meshFrom.GetPoint( 0 ) )
        elif piece == Piece.CELLS:
            cellTo: vtkCell = meshTo.GetCell( 0 )
            cellFrom: vtkCell = meshFrom.GetCell( 0 )
            # Get the coordinates of each points of the cell.
            nbPointsTo: int = cellTo.GetNumberOfPoints()
            nbPointsFrom: int = cellTo.GetNumberOfPoints()
            if nbPointsTo != nbPointsFrom:
                raise ValueError( "The two meshes have not the same cells dimension." )

            cellPointsTo: vtkPoints = cellTo.GetPoints()
            cellPointsFrom: vtkPoints = cellFrom.GetPoints()
            for idPoint in range( nbPointsTo ):
                coordElementTo.add( cellPointsTo.GetPoint( idPoint ) )
                coordElementFrom.add( cellPointsFrom.GetPoint( idPoint ) )
        else:
            raise ValueError( "The piece of the attribute to copy must be cells or points." )
        if coordElementTo != coordElementFrom:
            raise ValueError( "The two meshes have not the same element indexation." )

        npArray: npt.NDArray[ Any ] = getArrayInObject( meshFrom, attributeNameFrom, piece )
        componentNames: tuple[ str, ...] = getComponentNamesDataSet( meshFrom, attributeNameFrom, piece )
        vtkArrayType: int = getVtkArrayTypeInObject( meshFrom, attributeNameFrom, piece )

        createAttribute( meshTo, npArray, attributeNameTo, componentNames, piece, vtkArrayType, logger )
    elif isinstance( meshTo, vtkMultiBlockDataSet ) and isinstance( meshFrom, vtkMultiBlockDataSet ):
        # Check if the attribute exist in the meshFrom.
        if not isAttributeInObject( meshFrom, attributeNameFrom, piece ):
            raise AttributeError( f"The attribute { attributeNameFrom } is not present in the source mesh." )

        # Check if the attribute already exist in the meshTo.
        if isAttributeInObject( meshTo, attributeNameTo, piece ):
            raise AttributeError( f"The attribute { attributeNameTo } is already present in the final mesh." )

        # Check if the two multiBlockDataSets are similar.
        elementaryBlockIndexesTo: list[ int ] = getBlockElementIndexesFlatten( meshTo )
        elementaryBlockIndexesFrom: list[ int ] = getBlockElementIndexesFlatten( meshFrom )
        if elementaryBlockIndexesTo != elementaryBlockIndexesFrom:
            raise ValueError( "The two meshes do not have the same block indexes." )

        # Parse blocks of the two meshes to copy the attribute.
        for idBlock in elementaryBlockIndexesTo:
            dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( idBlock ) )
            dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( meshTo.GetDataSet( idBlock ) )

            if isAttributeInObject( dataSetFrom, attributeNameFrom, piece ):
                copyAttribute( dataSetFrom, dataSetTo, attributeNameFrom, attributeNameTo, piece, logger )
    else:
        raise TypeError( "Input meshes must be both inherited from vtkMultiBlockDataSet or vtkDataSet." )

    return


def transferAttributeWithElementMap(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    attributeName: str,
    piece: Piece,
    flatIdDataSetTo: int = 0,
    logger: Union[ Logger, Any ] = None,
) -> None:
    """Transfer attributes from the source mesh to the final mesh using a map of points/cells.

    If the source mesh is a vtkDataSet, its flat index (flatIdDataSetFrom) is set to 0.
    If the final mesh is a vtkDataSet, its flat index (flatIdDataSetTo) is set to 0.

    The map of points/cells used to transfer the attribute is a dictionary where:
        - Keys are the flat indexes of all the datasets of the final mesh.
        - Items are arrays of size (nb elements in datasets of the final mesh, 2).

    If an element (idElementTo) of one dataset (flatIdDataSetTo) of the final mesh is mapped with no element of the source mesh:
        - elementMap[flatIdDataSetTo][idElementTo] = [-1, -1].
        - The value of the attribute for this element depends of the type of the value of the attribute (0 for unit, -1 for int, nan for float).

    If an element (idElementTo) of one dataset (flatIdDataSetTo) of the final mesh is mapped with an element (idElementFrom) of one of the dataset (flatIdDataSetFrom) of the source mesh:
        - elementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom].
        - The value of the attribute for this element is the value of the element (idElementFrom) of the dataset (flatIdDataSetFrom) of the source mesh.

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The source mesh with the attribute to transfer.
        meshTo (Union[vtkDataSet, vtkMultiBlockDataSet]): The final mesh where to transfer the attribute.
        elementMap (dict[int, npt.NDArray[np.int64]]): The map of points/cells.
        attributeName (str): The name of the attribute to transfer.
        piece (Piece): The piece of the attribute.
        flatIdDataSetTo (int, Optional): The flat index of the final mesh considered as a dataset of a vtkMultiblockDataSet.
            Defaults to 0 for final meshes who are not datasets of vtkMultiBlockDataSet.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the type of the mesh to or the mesh from.
        ValueError: Error with the values of the map elementMap.
        AttributeError: Error with the attribute attributeName.
    """
    # Check if an external logger is given.
    if logger is None:
        logger = getLogger( "transferAttributeWithElementMap", True )

    # Check the piece.
    if piece not in [ Piece.POINTS, Piece.CELLS ]:
        raise ValueError( f"The attribute must be on { Piece.POINTS.value } or { Piece.CELLS.value }." )

    # Check the attribute to transfer.
    ## it is in the meshFrom
    if not isAttributeInObject( meshFrom, attributeName, piece ):
        raise AttributeError( f"The attribute { attributeName } is not in the source mesh." )
    ## it is global
    if isinstance( meshFrom, vtkMultiBlockDataSet ) and not isAttributeGlobal( meshFrom, attributeName, piece ):
        raise AttributeError( f"The attribute { attributeName } must be global in the source mesh." )

    # Transfer the attribute
    if isinstance( meshTo, vtkDataSet ):
        if flatIdDataSetTo not in elementMap:
            raise ValueError(
                f"The map is incomplete, there is no data for the final mesh (flat index { flatIdDataSetTo })." )

        nbElementsTo: int = meshTo.GetNumberOfPoints() if piece == Piece.POINTS else meshTo.GetNumberOfCells()
        if len( elementMap[ flatIdDataSetTo ] ) != nbElementsTo:
            raise ValueError(
                f"The map is wrong, there is { nbElementsTo } elements in the final mesh (flat index { flatIdDataSetTo }) but { len( elementMap[ flatIdDataSetTo ] ) } elements in the map."
            )

        componentNames: tuple[ str, ...] = getComponentNames( meshFrom, attributeName, piece )
        nbComponents: int = len( componentNames )

        vtkDataType: int = getVtkDataTypeInObject( meshFrom, attributeName, piece )
        defaultValue: Any
        if vtkDataType in ( VTK_FLOAT, VTK_DOUBLE ):
            defaultValue = np.nan
        elif vtkDataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ):
            defaultValue = -1
        elif vtkDataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT,
                              VTK_UNSIGNED_LONG_LONG ):
            defaultValue = 0
        else:
            raise AttributeError( f"The attribute { attributeName } has an unknown type." )

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
            idElementFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 1 ] )
            if idElementFrom != -1:
                dataFrom: Union[ vtkPointData, vtkCellData ]
                if isinstance( meshFrom, vtkDataSet ):
                    dataFrom = meshFrom.GetPointData() if piece == Piece.POINTS else meshFrom.GetCellData()
                elif isinstance( meshFrom, vtkMultiBlockDataSet ):
                    flatIdDataSetFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 0 ] )
                    dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( flatIdDataSetFrom ) )
                    dataFrom = dataSetFrom.GetPointData() if piece == Piece.POINTS else dataSetFrom.GetCellData()
                else:
                    raise TypeError( "The source mesh has to be inherited from vtkDataSet or vtkMultiBlockDataSet." )

                arrayFrom: npt.NDArray[ Any ] = vnp.vtk_to_numpy( dataFrom.GetArray( attributeName ) )
                valueToTransfer = arrayFrom[ idElementFrom ]

            arrayTo[ idElementTo ] = valueToTransfer

        createAttribute( meshTo,
                         arrayTo,
                         attributeName,
                         componentNames,
                         piece=piece,
                         vtkDataType=vtkDataType,
                         logger=logger )
    elif isinstance( meshTo, vtkMultiBlockDataSet ):
        if isAttributeInObject( meshTo, attributeName, piece ):
            raise AttributeError( f"The attribute { attributeName } is already in the final mesh." )

        listFlatIdDataSetTo: list[ int ] = getBlockElementIndexesFlatten( meshTo )
        for flatIdDataSetTo in listFlatIdDataSetTo:
            dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( meshTo.GetDataSet( flatIdDataSetTo ) )
            transferAttributeWithElementMap( meshFrom,
                                             dataSetTo,
                                             elementMap,
                                             attributeName,
                                             piece,
                                             flatIdDataSetTo=flatIdDataSetTo,
                                             logger=logger )
    else:
        raise TypeError( "The final mesh has to be inherited from vtkDataSet or vtkMultiBlockDataSet." )

    return


def renameAttribute(
    object: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    attributeName: str,
    newAttributeName: str,
    piece: Piece,
    logger: Union[ Logger, Any ] = None,
) -> None:
    """Rename an attribute with a unique name.

    Args:
        object (vtkMultiBlockDataSet): Object where the attribute is.
        attributeName (str): Name of the attribute.
        newAttributeName (str): New name of the attribute.
        piece (Piece): The piece of the attribute.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the type of the mesh.
        AttributeError: Error with the attribute attributeName or newAttributeName.
        VTKError: Error with a VTK function.
    """
    if logger is None:
        logger = getLogger( "renameAttribute", True )

    if not isinstance( object, ( vtkDataSet, vtkMultiBlockDataSet ) ):
        raise TypeError( "The mesh has to be inherited from vtkDataSet or vtkMultiBlockDataSet" )

    if not isAttributeInObject( object, attributeName, piece ):
        raise AttributeError( f"The attribute { attributeName } is not in the mesh." )

    if isAttributeInObject( object, newAttributeName, piece ):
        raise AttributeError( f"The attribute { newAttributeName } is already an attribute." )

    vtkErrorLogger: Logger = logging.getLogger( f"{ logger.name } vtkError Logger" )
    vtkErrorLogger.setLevel( logging.INFO )
    vtkErrorLogger.addHandler( logger.handlers[ 0 ] )
    vtkErrorLogger.propagate = False
    vtkLogger.SetStderrVerbosity( vtkLogger.VERBOSITY_ERROR )
    vtkErrorLogger.addFilter( RegexExceptionFilter() )  # will raise VTKError if captured VTK Error
    with VTKCaptureLog() as capturedLog:
        dim: int
        if piece == Piece.POINTS:
            dim = 0
        elif piece == Piece.CELLS:
            dim = 1
        else:
            raise ValueError(
                f"The attribute to rename must be on { Piece.POINTS.value } or on { Piece.CELLS.value }." )
        renameArrayFilter = vtkArrayRename()
        renameArrayFilter.SetInputData( object )
        renameArrayFilter.SetArrayName( dim, attributeName, newAttributeName )
        renameArrayFilter.Update()

        capturedLog.seek( 0 )
        captured = capturedLog.read().decode()

    if captured != "":
        vtkErrorLogger.error( captured.strip() )

    object.ShallowCopy( renameArrayFilter.GetOutput() )
    if object is None:
        raise VTKError( "Something went wrong with VTK renaming of the attribute." )

    return


def createCellCenterAttribute(
    mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    cellCenterAttributeName: str,
    logger: Union[ Logger, Any ] = None,
) -> None:
    """Create cellElementCenter attribute if it does not exist.

    Args:
        mesh (vtkMultiBlockDataSet | vtkDataSet): Input mesh.
        cellCenterAttributeName (str): Name of the attribute.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the mesh type.
        AttributeError: Error with the attribute cellCenterAttributeName.
    """
    if logger is None:
        logger = getLogger( "createCellCenterAttribute", True )

    if isAttributeInObject( mesh, cellCenterAttributeName, Piece.CELLS ):
        raise AttributeError( f"The attribute { cellCenterAttributeName } in already in the mesh." )

    if isinstance( mesh, vtkMultiBlockDataSet ):
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for blockIndex in elementaryBlockIndexes:
            dataSet: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( blockIndex ) )
            createCellCenterAttribute( dataSet, cellCenterAttributeName, logger )
    elif isinstance( mesh, vtkDataSet ):
        vtkErrorLogger: Logger = logging.getLogger( f"{ logger.name } vtkError Logger" )
        vtkErrorLogger.setLevel( logging.INFO )
        vtkErrorLogger.addHandler( logger.handlers[ 0 ] )
        vtkErrorLogger.propagate = False
        vtkLogger.SetStderrVerbosity( vtkLogger.VERBOSITY_ERROR )
        vtkErrorLogger.addFilter( RegexExceptionFilter() )  # will raise VTKError if captured VTK Error
        with VTKCaptureLog() as capturedLog:
            # apply ElementCenter filter
            cellCenterFilter: vtkCellCenters = vtkCellCenters()
            cellCenterFilter.SetInputData( mesh )
            cellCenterFilter.Update()

            capturedLog.seek( 0 )
            captured = capturedLog.read().decode()

        if captured != "":
            vtkErrorLogger.error( captured.strip() )

        output: vtkPointSet = cellCenterFilter.GetOutputDataObject( 0 )
        if output is None:
            raise VTKError( "Something went wrong with VTK cell center filter." )

        # transfer output to output arrays
        centers: vtkPoints = output.GetPoints()
        if centers is None:
            raise VTKError( "Something went wrong with VTK cell center filter." )

        centerCoords: vtkDataArray = centers.GetData()
        if centerCoords is None:
            raise VTKError( "Something went wrong with VTK cell center filter." )

        centerCoords.SetName( cellCenterAttributeName )
        mesh.GetCellData().AddArray( centerCoords )
        mesh.Modified()
    else:
        raise TypeError( "Input mesh must be a vtkDataSet or vtkMultiBlockDataSet." )

    return


def transferPointDataToCellData(
    mesh: vtkPointSet,
    logger: Union[ Logger, Any ] = None,
) -> vtkPointSet:
    """Transfer point data to cell data.

    Args:
        mesh (vtkPointSet): Input mesh.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Raises:
        TypeError: Error with the type of the mesh.
        VTKError: Error with a VTK function.

    Returns:
        vtkPointSet: Output mesh where point data were transferred to cells.

    """
    if logger is None:
        logger = getLogger( "transferPointDataToCellData", True )

    if not isinstance( mesh, vtkPointSet ):
        raise TypeError( "Input mesh has to be inherited from vtkPointSet." )

    vtkErrorLogger: Logger = logging.getLogger( f"{ logger.name } vtkError Logger" )
    vtkErrorLogger.setLevel( logging.INFO )
    vtkErrorLogger.addHandler( logger.handlers[ 0 ] )
    vtkErrorLogger.propagate = False
    vtkLogger.SetStderrVerbosity( vtkLogger.VERBOSITY_ERROR )
    vtkErrorLogger.addFilter( RegexExceptionFilter() )  # will raise VTKError if captured VTK Error
    with VTKCaptureLog() as capturedLog:
        pointToCellFilter = vtkPointDataToCellData()
        pointToCellFilter.SetInputDataObject( mesh )
        pointToCellFilter.SetProcessAllArrays( True )
        pointToCellFilter.Update()

        capturedLog.seek( 0 )
        captured = capturedLog.read().decode()

    if captured != "":
        vtkErrorLogger.error( captured.strip() )

    output: vtkPointSet = pointToCellFilter.GetOutputDataObject( 0 )
    if output is None:
        raise VTKError( "Something went wrong with VTK pointData to cellData filter." )

    return output
