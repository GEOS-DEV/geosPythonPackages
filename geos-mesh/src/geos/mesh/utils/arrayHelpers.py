# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez, Romain Baville
import logging
import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import vtkmodules.util.numpy_support as vnp
from typing import Optional, Union, Any
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDataArray, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkFieldData, vtkMultiBlockDataSet, vtkDataSet,
                                            vtkCompositeDataSet, vtkDataObject, vtkPointData, vtkCellData, vtkPolyData,
                                            vtkCell )
from vtkmodules.vtkFiltersCore import vtkCellCenters
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten

from geos.utils.pieceEnum import Piece

__doc__ = """
ArrayHelpers module contains several utilities methods to get information on arrays in VTK meshes.

There are two types of functions:
    - Getters
    - Checks

The getter functions:
    - get the array of an attribute (one for dataset, one for multiblockDataset, one for the both and one for fieldData)
    - get the component names of an attribute
    - get the number of components of an attribute
    - get the piece of an attribute
    - get the values of an attribute as data frame (for polyData only)
    - get the vtk type of an attribute (one for dataset, one for multiblockDataset and one for the both)
    - get the set of attributes on one piece of a mesh
    - get the attribute and they number of component on one piece of a mesh
    - get all the cells dimension of a mesh
    - get the GlobalIds array on one piece of a mesh
    - get the cell center coordinates of a mesh
    - get the mapping between cells or points shared by two meshes

The check functions:
    - check if an attribute is on a mesh (one for dataset, one for multiblockDataset, one for the both and one for a list of attributes)
    - check if an attribute is global (for multiblockDataset meshes)
    - check if a value is a value of an attribute (one for dataset and one for multiblockDataset)
"""


def getCellDimension( mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ] ) -> set[ int ]:
    """Get the set of the different cells dimension of a mesh.

    Args:
        mesh (Union[vtkMultiBlockDataSet, vtkDataSet]): The input mesh with the cells dimension to get.

    Returns:
        set[int]: The set of the different cells dimension in the input mesh.
    """
    cellDim: set[ int ] = set()
    if isinstance( mesh, vtkDataSet ):
        cellIter = mesh.NewCellIterator()
        cellIter.InitTraversal()
        while not cellIter.IsDoneWithTraversal():
            cellDim.add( cellIter.GetCellDimension() )
            cellIter.GoToNextCell()
    elif isinstance( mesh, vtkMultiBlockDataSet ):
        listDataSetFlattenIds: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for dataSetFlattenId in listDataSetFlattenIds:
            dataSet: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( dataSetFlattenId ) )
            cellDim.update( getCellDimension( dataSet ) )
    else:
        raise TypeError( "The input mesh must be a vtkMultiBlockDataSet or a vtkDataSet." )

    return cellDim


def computeElementMapping(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    piece: Piece,
) -> dict[ int, npt.NDArray ]:
    """Compute the map of points/cells between the source mesh and the final mesh.

    If the source mesh is a vtkDataSet, its flat index (flatIdDataSetFrom) is set to 0.
    If the final mesh is a vtkDataSet, its flat index (flatIdDataSetTo) is set to 0.

    The elementMap is a dictionary where:
        - Keys are the flat index of all the datasets of the final mesh.
        - Items are arrays of size (nb elements in datasets of the final mesh, 2).

    For each element (idElementTo) of each dataset (flatIdDataSetTo) of the final mesh,
    if the coordinates of an element (idElementFrom) of one dataset (flatIdDataSetFrom) of the source mesh
    are the same as the coordinates of the element of the final mesh,
    elementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom]
    else, elementMap[flatIdDataSetTo][idElementTo] = [-1, -1].

    For cells, the coordinates of the points in the cell are compared.
    If one of the two meshes is a surface and the other a volume, all the points of the surface must be points of the volume.

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The source mesh with the element to map.
        meshTo (Union[vtkDataSet, vtkMultiBlockDataSet]): The final mesh with the reference element coordinates.
        piece (Piece): The element to map.

    Returns:
        elementMap (dict[int, npt.NDArray[np.int64]]): The map of points/cells between the two meshes.
    """
    if piece not in [ Piece.CELLS, Piece.POINTS ]:
        raise ValueError( f"Only { Piece.POINTS.value } or { Piece.CELLS.value } can be mapped." )

    elementMap: dict[ int, npt.NDArray ] = {}
    if isinstance( meshTo, vtkDataSet ):
        nbElementsTo: int = meshTo.GetNumberOfPoints() if piece == Piece.POINTS else meshTo.GetNumberOfCells()
        elementMap[ 0 ] = np.full( ( nbElementsTo, 2 ), -1, np.int64 )
        if isinstance( meshFrom, vtkDataSet ):
            idElementsFromFund: list[ int ] = []
            nbElementsFrom: int = meshFrom.GetNumberOfPoints() if piece == Piece.POINTS else meshFrom.GetNumberOfCells()
            for idElementTo in range( nbElementsTo ):
                typeElemTo: int
                coordElementTo: set[ tuple[ float, ...] ] = set()
                if piece == Piece.POINTS:
                    typeElemTo = 0
                    coordElementTo.add( meshTo.GetPoint( idElementTo ) )
                else:
                    cellTo: vtkCell = meshTo.GetCell( idElementTo )
                    typeElemTo = cellTo.GetCellType()
                    # Get the coordinates of each points of the cell.
                    nbPointsTo: int = cellTo.GetNumberOfPoints()
                    cellPointsTo: vtkPoints = cellTo.GetPoints()
                    for idPointTo in range( nbPointsTo ):
                        coordElementTo.add( cellPointsTo.GetPoint( idPointTo ) )

                idElementFrom: int = 0
                elementFromFund: bool = False
                while idElementFrom < nbElementsFrom and not elementFromFund:
                    # Test if the element of the source mesh is already mapped.
                    if idElementFrom not in idElementsFromFund:
                        typeElemFrom: int
                        coordElementFrom: set[ tuple[ float, ...] ] = set()
                        if piece == Piece.POINTS:
                            typeElemFrom = 0
                            coordElementFrom.add( meshFrom.GetPoint( idElementFrom ) )
                        else:
                            cellFrom: vtkCell = meshFrom.GetCell( idElementFrom )
                            typeElemFrom = cellFrom.GetCellType()
                            # Get the coordinates of each points of the face.
                            nbPointsFrom: int = cellFrom.GetNumberOfPoints()
                            cellPointsFrom: vtkPoints = cellFrom.GetPoints()
                            for idPointFrom in range( nbPointsFrom ):
                                coordElementFrom.add( cellPointsFrom.GetPoint( idPointFrom ) )

                        pointShared: bool = True
                        if typeElemTo == typeElemFrom:
                            if coordElementTo != coordElementFrom:
                                pointShared = False
                        else:
                            if nbPointsTo < nbPointsFrom:
                                if not coordElementTo.issubset( coordElementFrom ):
                                    pointShared = False
                            else:
                                if not coordElementTo.issuperset( coordElementFrom ):
                                    pointShared = False

                        if pointShared:
                            elementMap[ 0 ][ idElementTo ] = [ 0, idElementFrom ]
                            elementFromFund = True
                            idElementsFromFund.append( idElementFrom )

                    idElementFrom += 1
        elif isinstance( meshFrom, vtkMultiBlockDataSet ):
            listDataSetFromIds: list[ int ] = getBlockElementIndexesFlatten( meshFrom )
            for dataSetFromId in listDataSetFromIds:
                dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( dataSetFromId ) )
                dataSetFromMap: npt.NDArray = computeElementMapping( dataSetFrom, meshTo, piece )[ 0 ]
                for idElementTo in range( nbElementsTo ):
                    if -1 in elementMap[ 0 ][ idElementTo ] and -1 not in dataSetFromMap[ idElementTo ]:
                        elementMap[ 0 ][ idElementTo ] = [ dataSetFromId, dataSetFromMap[ idElementTo ][ 1 ] ]
    elif isinstance( meshTo, vtkMultiBlockDataSet ):
        listDataSetToFlattenIds: list[ int ] = getBlockElementIndexesFlatten( meshTo )
        for dataSetToFlattenId in listDataSetToFlattenIds:
            dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( meshTo.GetDataSet( dataSetToFlattenId ) )
            elementMap[ dataSetToFlattenId ] = computeElementMapping( meshFrom, dataSetTo, piece )[ 0 ]

    return elementMap


def hasArray( mesh: vtkUnstructuredGrid, arrayNames: list[ str ] ) -> bool:
    """Checks if input mesh contains at least one of input data arrays.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured mesh.
        arrayNames (list[str]): List of array names.

    Returns:
        bool: True if at least one array is found, else False.
    """
    # Check the cell data fields
    data: Union[ vtkFieldData, None ]
    for data in ( mesh.GetCellData(), mesh.GetFieldData(), mesh.GetPointData() ):
        if data is None:
            continue  # type: ignore[unreachable]
        for arrayName in arrayNames:
            if data.HasArray( arrayName ):
                logging.error( f"The mesh contains the array named '{arrayName}'." )
                return True
    return False


def getAttributePieceInfo(
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    attributeName: str,
) -> Piece:
    """Get the attribute piece.

    Args:
        mesh (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the attribute.
        attributeName (str): The name of the attribute.

    Returns:
        Piece: The piece of the attribute.
    """
    if isAttributeInObject( mesh, attributeName, Piece.FIELD ):
        return Piece.FIELD
    elif isAttributeInObject( mesh, attributeName, Piece.BOTH ):
        return Piece.BOTH
    elif isAttributeInObject( mesh, attributeName, Piece.POINTS ):
        return Piece.POINTS
    elif isAttributeInObject( mesh, attributeName, Piece.CELLS ):
        return Piece.CELLS
    else:
        return Piece.NONE


def checkValidValuesInMultiBlock(
    multiBlockDataSet: vtkMultiBlockDataSet,
    attributeName: str,
    listValues: list[ Any ],
    piece: Piece,
) -> tuple[ list[ Any ], list[ Any ] ]:
    """Check if each value is valid , ie if that value is a data of the attribute in at least one dataset of the multiblock.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): The multiblock dataset mesh to check.
        attributeName (str): The name of the attribute with the data.
        listValues (list[Any]): The list of values to check.
        piece (Piece): The piece of the attribute.

    Returns:
        tuple[list[Any], list[Any]]: Tuple containing the list of valid values and the list of the invalid ones.
    """
    validValues: list[ Any ] = []
    invalidValues: list[ Any ] = []
    listFlatIdDataSet: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for flatIdDataSet in listFlatIdDataSet:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( flatIdDataSet ) )
        # Get the valid values of the dataset.
        validValuesDataSet: list[ Any ] = checkValidValuesInDataSet( dataSet, attributeName, listValues, piece )[ 0 ]

        # Keep the new true values.
        for value in validValuesDataSet:
            if value not in validValues:
                validValues.append( value )

    # Get the false indexes.
    for value in listValues:
        if value not in validValues:
            invalidValues.append( value )

    return ( validValues, invalidValues )


def checkValidValuesInDataSet(
    dataSet: vtkDataSet,
    attributeName: str,
    listValues: list[ Any ],
    piece: Piece,
) -> tuple[ list[ Any ], list[ Any ] ]:
    """Check if each value is valid , ie if that value is a data of the attribute in the dataset.

    Args:
        dataSet (vtkDataSet): The dataset mesh to check.
        attributeName (str): The name of the attribute with the data.
        listValues (list[Any]): The list of values to check.
        piece (Piece): The piece of the attribute.

    Returns:
        tuple[list[Any], list[Any]]: Tuple containing the list of valid values and the list of the invalid ones.
    """
    attributeNpArray = getArrayInObject( dataSet, attributeName, piece )
    validValues: list[ Any ] = []
    invalidValues: list[ Any ] = []
    for value in listValues:
        if value in attributeNpArray:
            validValues.append( value )
        else:
            invalidValues.append( value )

    return ( validValues, invalidValues )


def getNumpyGlobalIdsArray( data: Union[ vtkCellData, vtkPointData ] ) -> npt.NDArray:
    """Get a numpy array of the GlobalIds if it exist.

    Args:
        data (Union[ vtkCellData, vtkPointData ]): Cell or point array.

    Returns:
        (npt.NDArray): The numpy array of GlobalIds.

    Raises:
        TypeError: The data entered is not a vtkFieldDate object.
        AttributeError: There is no GlobalIds in the given data.
    """
    if not isinstance( data, vtkFieldData ):
        raise TypeError( f"data '{ data }' entered is not a vtkFieldData object." )

    global_ids: Optional[ vtkDataArray ] = data.GetGlobalIds()
    if global_ids is None:
        raise AttributeError( "There is no GlobalIds in the given fieldData." )
    return vtk_to_numpy( global_ids )


def getNumpyArrayByName( data: Union[ vtkCellData, vtkPointData ], name: str, sorted: bool = False ) -> npt.NDArray:
    """Get the numpy array of a given vtkDataArray found by its name.

    If sorted is selected, this allows the option to reorder the values wrt GlobalIds. If not GlobalIds was found,
    no reordering will be perform.

    Args:
        data (Union[vtkCellData, vtkPointData]): Vtk field data.
        name (str): Array name to sort.
        sorted (bool, optional): Sort the output array with the help of GlobalIds. Defaults to False.

    Returns:
        npt.NDArray: Sorted array.

    Raises:
        AttributeError: There is no array with the given name in the data.
    """
    if not data.HasArray( name ):
        raise AttributeError( f"There is no array named { name } in the given fieldData." )

    npArray: npt.NDArray = vtk_to_numpy( data.GetArray( name ) )
    if sorted and ( data.IsA( "vtkCellData" ) or data.IsA( "vtkPointData" ) ):
        globalids: npt.NDArray = getNumpyGlobalIdsArray( data )
        npArray = npArray[ np.argsort( globalids ) ]

    return npArray


def getAttributeSet( mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ], piece: Piece ) -> set[ str ]:
    """Get the set of all attributes from an mesh on points or on cells.

    Args:
        mesh (Union[vtkMultiBlockDataSet, vtkDataSet]): Mesh where to find the attributes.
        piece (Piece): The piece of the attributes to get.

    Returns:
        set[str]: Set of attribute names present in input mesh.
    """
    dictAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( mesh, piece )
    attributeSet: set[ str ] = set( dictAttributes.keys() )

    return attributeSet


def getAttributesWithNumberOfComponents(
    mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet, vtkDataObject ],
    piece: Piece,
) -> dict[ str, int ]:
    """Get the dictionary of all attributes from object on points or cells.

    Args:
        mesh (vtkMultiBlockDataSet | vtkDataSet): Mesh where to find the attributes.
        piece (Piece): The piece of the attributes to get.

    Returns:
        dict[str, int]: Dictionary where keys are the names of the attributes and values the number of components.

    Raises:
        ValueError: The piece must be cells or points only
        AttributeError: One attribute one the mesh is null.
        TypeError: Input mesh must be a vtkDataSet or vtkMultiBlockDataSet.
    """
    attributes: dict[ str, int ] = {}
    if isinstance( mesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for blockIndex in elementaryBlockIndexes:
            dataSet: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( blockIndex ) )
            blockAttributes: dict[ str, int ] = getAttributesWithNumberOfComponents( dataSet, piece )
            for attributeName, nbComponents in blockAttributes.items():
                if attributeName not in attributes:
                    attributes[ attributeName ] = nbComponents
    elif isinstance( mesh, vtkDataSet ):
        data: Union[ vtkPointData, vtkCellData ]
        if piece == Piece.POINTS:
            data = mesh.GetPointData()
        elif piece == Piece.CELLS:
            data = mesh.GetCellData()
        else:
            raise ValueError( f"The attribute piece must be { Piece.POINTS.value } or { Piece.CELLS.value }." )

        nbAttributes: int = data.GetNumberOfArrays()
        for i in range( nbAttributes ):
            attributeName: str = data.GetArrayName( i )
            attribute: vtkDataArray = data.GetArray( attributeName )
            if attribute is None:
                raise AttributeError( f"The attribute { attributeName } is null" )

            nbComponents: int = attribute.GetNumberOfComponents()
            attributes[ attributeName ] = nbComponents
    else:
        raise TypeError( "Input mesh must be a vtkDataSet or vtkMultiBlockDataSet." )

    return attributes


def isAttributeInObject( mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ], attributeName: str, piece: Piece ) -> bool:
    """Check if an attribute is in the input mesh for the given piece.

    Args:
        mesh (vtkMultiBlockDataSet | vtkDataSet): Input mesh.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        bool: True if the attribute is on the mesh, False otherwise.

    Raises:
        TypeError: The mesh has to be inherited from vtkMultiBlockDataSet or vtkDataSet.
    """
    if isinstance( mesh, vtkDataSet ):
        if piece == Piece.FIELD:
            return bool( mesh.GetFieldData().HasArray( attributeName ) )
        elif piece == Piece.POINTS:
            return bool( mesh.GetPointData().HasArray( attributeName ) )
        elif piece == Piece.CELLS:
            return bool( mesh.GetCellData().HasArray( attributeName ) )
        elif piece == Piece.BOTH:
            onPoints: int = mesh.GetPointData().HasArray( attributeName )
            onCells: int = mesh.GetCellData().HasArray( attributeName )
            return onCells == onPoints == 1
    elif isinstance( mesh, vtkMultiBlockDataSet ):
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for blockIndex in elementaryBlockIndexes:
            dataSet: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( blockIndex ) )
            if isAttributeInObject( dataSet, attributeName, piece ):
                return True
    else:
        raise TypeError( "Input object must be a vtkDataSet or vtkMultiBlockDataSet." )

    return False


def isAttributeGlobal( multiBlockDataSet: vtkMultiBlockDataSet, attributeName: str, piece: Piece ) -> bool:
    """Check if an attribute is global in the input multiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        bool: True if the attribute is global, False if not.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        if not isAttributeInObject( dataSet, attributeName, piece ):
            return False
    return True


def getArrayInObject( dataSet: vtkDataSet, attributeName: str, piece: Piece ) -> npt.NDArray[ Any ]:
    """Return the numpy array corresponding to input attribute name in table.

    Args:
        dataSet (vtkDataSet): Input dataSet.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        ArrayLike[Any]: The numpy array corresponding to input attribute name.
    """
    vtkArray: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, piece )
    npArray: npt.NDArray[ Any ] = vnp.vtk_to_numpy( vtkArray )  # type: ignore[no-untyped-call]
    return npArray


def getVtkDataTypeInObject( mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ], attributeName: str, piece: Piece ) -> int:
    """Return VTK type of requested array from input mesh.

    Args:
        mesh (Union[vtkDataSet, vtkMultiBlockDataSet]): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        int: The type of the vtk array corresponding to input attribute name.
    """
    if isinstance( mesh, vtkDataSet ):
        return getVtkArrayTypeInObject( mesh, attributeName, piece )
    else:
        return getVtkArrayTypeInMultiBlock( mesh, attributeName, piece )


def getVtkArrayTypeInObject( dataSet: vtkDataSet, attributeName: str, piece: Piece ) -> int:
    """Return VTK type of requested array from dataset input.

    Args:
        dataSet (vtkDataSet): Input dataSet.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        int: The type of the vtk array corresponding to input attribute name.
    """
    array: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, piece )
    vtkArrayType: int = array.GetDataType()

    return vtkArrayType


def getVtkArrayTypeInMultiBlock( multiBlockDataSet: vtkMultiBlockDataSet, attributeName: str, piece: Piece ) -> int:
    """Return VTK type of requested array from multiblock dataset input, if existing.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        int: Type of the requested vtk array if existing in input multiblock dataset.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        listAttributes: set[ str ] = getAttributeSet( dataSet, piece )
        if attributeName in listAttributes:
            return getVtkArrayTypeInObject( dataSet, attributeName, piece )

    raise AssertionError( "The vtkMultiBlockDataSet has no attribute with the name " + attributeName + "." )


def getVtkArrayInObject( dataSet: vtkDataSet, attributeName: str, piece: Piece ) -> vtkDataArray:
    """Return the array corresponding to input attribute name in table.

    Args:
        dataSet (vtkDataSet): Input dataSet.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        vtkDataArray: The vtk array corresponding to input attribute name.
    """
    if not isAttributeInObject( dataSet, attributeName, piece ):
        raise AttributeError( f"{ attributeName } is not in input mesh." )

    dataArray: vtkDataArray
    if piece == Piece.POINTS:
        dataArray = dataSet.GetPointData().GetArray( attributeName )
    elif piece == Piece.CELLS:
        dataArray = dataSet.GetCellData().GetArray( attributeName )
    elif piece == Piece.FIELD:
        dataArray = dataSet.GetFieldData().GetArray( attributeName )
    else:
        raise ValueError(
            f"The attribute piece must be { Piece.FIELD.value }, { Piece.POINTS.value } or { Piece.CELLS.value }." )

    return dataArray


def getNumberOfComponents(
    mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet ],
    attributeName: str,
    piece: Piece,
) -> int:
    """Get the number of components of the attribute 'attributeName' in the mesh for a given piece.

    Args:
        mesh (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataSet): Mesh where the attribute is.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        int: Number of components.

    Raises:
        AttributeError: The attribute 'attributeName' is not in the mesh for the given piece.
        TypeError: The mesh has to be inherited from vtkMultiBlockDataSet or vtkDataSet.
        ValueError: The attribute's piece must be 'cells', 'points' or 'field'.
    """
    nbComponents: int = 0
    if isinstance( mesh, vtkDataSet ):
        array: vtkDataArray = getVtkArrayInObject( mesh, attributeName, piece )
        nbComponents = array.GetNumberOfComponents()
    elif isinstance( mesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for blockIndex in elementaryBlockIndexes:
            dataSet: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( blockIndex ) )
            try:
                return getNumberOfComponents( dataSet, attributeName, piece )
            except ValueError as e:
                raise e
            except AttributeError:
                continue
        raise AttributeError( f"The attribute '{ attributeName }' is not in the mesh for the given piece { piece }.")
    else:
        raise TypeError( "The mesh has to be inherited from vtkMultiBlockDataSet or vtkDataSet." )

    return nbComponents


def getComponentNames(
    mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet, vtkDataObject ],
    attributeName: str,
    piece: Piece,
) -> tuple[ str, ...]:
    """Get the name of the components of the attribute 'attributeName' in a mesh.

    Args:
        mesh (vtkDataSet | vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): Mesh where the attribute is.
        attributeName (str): Name of the attribute.
        piece (Piece): The piece of the attribute.

    Returns:
        tuple[str,...]: Names of the components.

    Raises:
        AttributeError: The attribute 'attributeName' is not in the mesh for the given piece.
        TypeError: The mesh has to be inherited from vtkMultiBlockDataSet or vtkDataSet.
        ValueError: The attribute's piece must be 'cells', 'points' or 'field'.
    """
    componentNames: list[ str ] = []
    if isinstance( mesh, vtkDataSet ):
        array: vtkDataArray = getVtkArrayInObject( mesh, attributeName, piece )
        if array.GetNumberOfComponents() > 1:
            componentNames += [ array.GetComponentName( i ) for i in range( array.GetNumberOfComponents() ) ]
    elif isinstance( mesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( mesh )
        for blockIndex in elementaryBlockIndexes:
            dataSet: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( blockIndex ) )
            try:
                return getComponentNames( dataSet, attributeName, piece )
            except ValueError as e:
                raise e
            except AttributeError:
                continue
        raise AttributeError( f"The attribute '{ attributeName }' is not in the mesh for the given piece { piece }.")
    else:
        raise TypeError( "The mesh has to be inherited from vtkMultiBlockDataSet or vtkDataSet." )

    return tuple( componentNames )


def getAttributeValuesAsDF( surface: vtkPolyData,
                            attributeNames: tuple[ str, ...],
                            piece: Piece = Piece.CELLS ) -> pd.DataFrame:
    """Get attribute values from input surface.

    Args:
        surface (vtkPolyData): Mesh where to get attribute values.
        attributeNames (tuple[str,...]): Tuple of attribute names to get the values.
        piece (Piece): The piece of the attribute.
            Defaults to Piece.CELLS

    Returns:
        pd.DataFrame: DataFrame containing property names as columns.

    """
    nbRows: int
    if piece == Piece.POINTS:
        nbRows = surface.GetNumberOfPoints()
    elif piece == Piece.CELLS:
        nbRows = surface.GetNumberOfCells()
    else:
        raise ValueError( f"The attribute piece must be { Piece.POINTS.value } or { Piece.CELLS.value }." )

    data: pd.DataFrame = pd.DataFrame( np.full( ( nbRows, len( attributeNames ) ), np.nan ), columns=attributeNames )
    for attributeName in attributeNames:
        if not isAttributeInObject( surface, attributeName, piece ):
            logging.warning( f"Attribute {attributeName} is not in the mesh." )
            continue
        array: npt.NDArray[ np.float64 ] = getArrayInObject( surface, attributeName, piece )

        if len( array.shape ) > 1:
            for i in range( array.shape[ 1 ] ):
                data[ attributeName + f"_{ i }" ] = array[ :, i ]
            data.drop( columns=[ attributeName ], inplace=True )
        else:
            data[ attributeName ] = array
    return data


def computeCellCenterCoordinates( mesh: vtkDataSet ) -> vtkDataArray:
    """Get the coordinates of Cell center.

    Args:
        mesh (vtkDataSet): Input surface.

    Returns:
        vtkPoints: Cell center coordinates.
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
