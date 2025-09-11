# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez, Romain Baville
from copy import deepcopy
import logging
import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import vtkmodules.util.numpy_support as vnp
from typing import Optional, Union, Any
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDataArray, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkFieldData, vtkMultiBlockDataSet, vtkDataSet,
                                            vtkCompositeDataSet, vtkDataObject, vtkPointData, vtkCellData, vtkPolyData )
from vtkmodules.vtkFiltersCore import vtkCellCenters
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten

__doc__ = """
ArrayHelpers module contains several utilities methods to get information on arrays in VTK datasets.

These methods include:
    - mesh element localization mapping by indexes
    - array getters, with conversion into numpy array or pandas dataframe
    - boolean functions to check whether an array is present in the dataset
    - bounds getter for vtu and multiblock datasets
"""


def computeElementMapping(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    points: bool,
) -> dict[ int, npt.NDArray ]:
    """Compute the elementMap from the meshFrom to the meshTo.

    If meshFrom is a vtkDataSet, the flat index (flatIdDataSetFrom) is set to 0.
    If meshTo is a vtkDataSet, the flat index (flatIdDataSetTo) is set to 0.

    The elementMap is a dictionary where:
        - Keys are the flat index of all the datasets of the meshTo.
        - Items are arrays of size (nb elements in datasets, 2).

    For each element (idElementTo) of each dataset (flatIdDataSetTo) of meshTo,
    if the points coordinates of an element (idElementFrom) of one meshFrom's dataSet (flatIdDataSetFrom)
    are the same as the points coordinates of the elementTo,
    elementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom]
    else, elementMap[flatIdDataSetTo][idElementTo] = [-1, -1].

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the element to map.
        meshTo (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the reference element.
        points (bool): True if elements to map are points, False if they are cells.

    Returns:
        elementMap (dict[int, npt.NDArray[np.int64]]): The elementMap with the element indexes in the two meshes.
    """
    elementMap: dict[ int, npt.NDArray ] = {}
    if isinstance( meshTo, vtkDataSet ):
        UpdateElementMappingToDataSet( meshFrom, meshTo, elementMap, points )
    elif isinstance( meshTo, vtkMultiBlockDataSet ):
        UpdateElementMappingToMultiBlockDataSet( meshFrom, meshTo, elementMap, points )

    return elementMap


def UpdateElementMappingToMultiBlockDataSet(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    multiBlockDataSetTo: vtkMultiBlockDataSet,
    elementMap: dict[ int, npt.NDArray ],
    points: bool,
) -> None:
    """Update the elementMap from the meshFrom to the multiBlockDataSetTo.

    If meshFrom is a vtkDataSet, the flat index (flatIdDataSetFrom) is set to 0.

    Add the mapping for of the multiBlockDataSetTo:
        - Keys are the flat index of all the datasets of the multiBlockDataSetTo.
        - Items are arrays of size (nb elements in datasets, 2).

    For each element (idElementTo) of each dataset (flatIdDataSetTo) of multiBlockDataSetTo,
    if the points coordinates of an element (idElementFrom) of one meshFrom's dataSet (flatIdDataSetFrom)
    are the same as the points coordinates of the elementTo,
    elementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom]
    else, elementMap[flatIdDataSetTo][idElementTo] = [-1, -1].

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the element to map.
        multiBlockDataSetTo (vtkMultiBlockDataSet): The mesh with the reference element.
        elementMap (dict[int, npt.NDArray[np.int64]]): The elementMap to update.
        points (bool): True if elements to map are points, False if they are cells.
    """
    listFlatIdMultiBlockDataSetTo: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetTo )
    for flatIdDataSetTo in listFlatIdMultiBlockDataSetTo:
        dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTo.GetDataSet( flatIdDataSetTo ) )
        UpdateElementMappingToDataSet( meshFrom, dataSetTo, elementMap, points, flatIdDataSetTo=flatIdDataSetTo )


def UpdateElementMappingToDataSet(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    dataSetTo: vtkDataSet,
    elementMap: dict[ int, npt.NDArray ],
    points: bool,
    flatIdDataSetTo: int = 0,
) -> None:
    """Update the elementMap from the meshFrom to the dataSetTo.

    If meshFrom is a vtkDataSet, the flat index (flatIdDataSetFrom) is set to 0.
    dataSetTo is considered as block of vtkMultiblockDataSet, if not the flat index (flatIdDataSetTo) is set to 0.

    Add the mapping for the dataSetTo:
        - The keys is the flat index of the dataSetTo (flatIdDataSetTo).
        - The item is an array of size (nb elements in dataSetTo, 2).

    For each element (idElementTo) of the mesh dataSetTo,
    if the points coordinates of an element (idElementFrom) of one meshFrom's dataSet (flatIdDataSetFrom)
    are the same as the points coordinates of the elementTo,
    elementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom]
    else, elementMap[flatIdDataSetTo][idElementTo] = [-1, -1].

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the element to map.
        dataSetTo (vtkDataSet): The dataset with the reference element.
        elementMap (dict[int, npt.NDArray[np.int64]]): The elementMap to update.
        points (bool): True if elements to map are points, False if they are cells.
        flatIdDataSetTo (int, Optional): The flat index of the dataSetTo.
            Defaults to 0.
    """
    nbElementsTo: int = dataSetTo.GetNumberOfPoints() if points else dataSetTo.GetNumberOfCells()
    elementMap[ flatIdDataSetTo ] = np.full( ( nbElementsTo, 2 ), -1, np.int64 )
    if isinstance( meshFrom, vtkDataSet ):
        UpdateDictElementMappingFromDataSetToDataSet( meshFrom,
                                                      dataSetTo,
                                                      elementMap,
                                                      points,
                                                      flatIdDataSetTo=flatIdDataSetTo )
    elif isinstance( meshFrom, vtkMultiBlockDataSet ):
        UpdateElementMappingFromMultiBlockDataSetToDataSet( meshFrom,
                                                            dataSetTo,
                                                            elementMap,
                                                            points,
                                                            flatIdDataSetTo=flatIdDataSetTo )


def UpdateElementMappingFromMultiBlockDataSetToDataSet(
    multiBlockDataSetFrom: vtkMultiBlockDataSet,
    dataSetTo: vtkDataSet,
    elementMap: dict[ int, npt.NDArray ],
    points: bool,
    flatIdDataSetTo: int = 0,
) -> None:
    """Update the elementMap from the multiBlockDataSetFrom to the dataSetTo.

    dataSetTo is considered as block of a vtkMultiblockDataSet, if not the flat index (flatIdDataSetTo) is set to 0.

    For each element (idElementTo) of the dataSetTo not yet mapped (elementMap[flatIdDataSetTo][idElementTo] = [-1, -1]),
    if the points coordinates of an element (idElementFrom) of a block (flatIdDataSetFrom) of multiBlockDataSetFrom
    are the same as the points coordinates of the elementTo,
    the elementMap is update to elementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom].

    Args:
        multiBlockDataSetFrom (vtkMultiBlockDataSet): The mesh with the element to map.
        dataSetTo (vtkDataSet): The dataset with the reference element.
        elementMap (dict[int, npt.NDArray[np.int64]]): The elementMap to update with;
            The flat index of the dataSetTo as keys.
            An array of size (nb elements in dataSetTo, 2) as item.
        points (bool): True if elements to map are points, False if they are cells.
        flatIdDataSetTo (int, Optional): The flat index of the dataSetTo.
            Defaults to 0.
    """
    listFlatIdMultiBlockDataSetFrom: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetFrom )
    for flatIdDataSetFrom in listFlatIdMultiBlockDataSetFrom:
        dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetFrom.GetDataSet( flatIdDataSetFrom ) )
        UpdateDictElementMappingFromDataSetToDataSet( dataSetFrom,
                                                      dataSetTo,
                                                      elementMap,
                                                      points,
                                                      flatIdDataSetFrom=flatIdDataSetFrom,
                                                      flatIdDataSetTo=flatIdDataSetTo )


def UpdateDictElementMappingFromDataSetToDataSet(
    dataSetFrom: vtkDataSet,
    dataSetTo: vtkDataSet,
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    points: bool,
    flatIdDataSetFrom: int = 0,
    flatIdDataSetTo: int = 0,
) -> None:
    """Update the elementMap from the dataSetFrom to the dataSetTo.

    dataSetFrom is considered as block of vtkMultiblockDataSet, if not the flat index (flatIdDataSetFrom) is set to 0.
    dataSetTo is considered as block of vtkMultiblockDataSet, if not the flat index (flatIdDataSetTo) is set to 0.

    For each element (idElementTo) of the dataSetTo not yet mapped (elementMap[flatIdDataSetTo][idElementTo] = [-1, -1]),
    if the points coordinates of an element (idElementFrom) of the dataSetFrom
    are the same as the points coordinates of the elementTo,
    the elementMap is updated to elementMap[flatIdDataSetTo][idElementTo] = [flatIdDataSetFrom, idElementFrom].

    Args:
        dataSetFrom (vtkDataSet): The dataset with the element to map.
        dataSetTo (vtkDataSet): The dataset with the reference element.
        elementMap (dict[int, npt.NDArray[np.int64]]): The elementMap to update with;
            The flat index of the dataSetTo as keys.
            An array of size (nb elements in dataSetTo, 2) as item.
        points (bool): True if elements to map are points, False if they are cells.
        flatIdDataSetFrom (int, Optional): The flat index of the dataSetFrom.
            Defaults to 0.
        flatIdDataSetTo (int, Optional): The flat index of the dataSetTo.
            Defaults to 0.
    """
    idElementsFromFund: list[ int ] = []
    nbElementsTo: int = len( elementMap[ flatIdDataSetTo ] )
    nbElementsFrom: int = dataSetFrom.GetNumberOfPoints() if points else dataSetFrom.GetNumberOfCells()
    for idElementTo in range( nbElementsTo ):
        # Test if the element of the dataSetTo is already mapped.
        if -1 in elementMap[ flatIdDataSetTo ][ idElementTo ]:
            coordElementTo: tuple[ float, ...]
            if points:
                coordElementTo = dataSetTo.GetPoint( idElementTo )
            else:
                # Get the coordinates of each points of the cell.
                nbPointsTo: int = dataSetTo.GetCell( idElementTo ).GetNumberOfPoints()
                cellPointsTo: vtkPoints = dataSetTo.GetCell( idElementTo ).GetPoints()
                coordPointsTo: list = []
                for idPointTo in range( nbPointsTo ):
                    coordPointsTo.extend( cellPointsTo.GetPoint( idPointTo ) )
                coordElementTo = tuple( coordPointsTo )

            idElementFrom: int = 0
            ElementFromFund: bool = False
            while idElementFrom < nbElementsFrom and not ElementFromFund:
                # Test if the element of the dataSetFrom is already mapped.
                if idElementFrom not in idElementsFromFund:
                    coordElementFrom: tuple[ float, ...]
                    if points:
                        coordElementFrom = dataSetFrom.GetPoint( idElementFrom )
                    else:
                        # Get the coordinates of each points of the cell.
                        nbPointsFrom: int = dataSetFrom.GetCell( idElementFrom ).GetNumberOfPoints()
                        cellPointsFrom: vtkPoints = dataSetFrom.GetCell( idElementFrom ).GetPoints()
                        coordPointsFrom: list = []
                        for idPointFrom in range( nbPointsFrom ):
                            coordPointsFrom.extend( cellPointsFrom.GetPoint( idPointFrom ) )
                        coordElementFrom = tuple( coordPointsFrom )

                    if coordElementFrom == coordElementTo:
                        elementMap[ flatIdDataSetTo ][ idElementTo ] = [ flatIdDataSetFrom, idElementFrom ]
                        ElementFromFund = True
                        idElementsFromFund.append( idElementFrom )

                idElementFrom += 1


def has_array( mesh: vtkUnstructuredGrid, array_names: list[ str ] ) -> bool:
    """Checks if input mesh contains at least one of input data arrays.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured mesh.
        array_names (list[str]): List of array names.

    Returns:
        bool: True if at least one array is found, else False.
    """
    # Check the cell data fields
    data: Union[ vtkFieldData, None ]
    for data in ( mesh.GetCellData(), mesh.GetFieldData(), mesh.GetPointData() ):
        if data is None:
            continue  # type: ignore[unreachable]
        for arrayName in array_names:
            if data.HasArray( arrayName ):
                logging.error( f"The mesh contains the array named '{arrayName}'." )
                return True
    return False


def getFieldType( data: vtkFieldData ) -> str:
    """Returns whether the data is "vtkFieldData", "vtkCellData" or "vtkPointData".

    A vtk mesh can contain 3 types of field data:
    - vtkFieldData (parent class)
    - vtkCellData  (inheritance of vtkFieldData)
    - vtkPointData (inheritance of vtkFieldData)

    Args:
        data (vtkFieldData): Vtk field data.

    Returns:
        str: "vtkFieldData", "vtkCellData" or "vtkPointData"
    """
    if not data.IsA( "vtkFieldData" ):
        raise ValueError( f"data '{ data }' entered is not a vtkFieldData object." )
    if data.IsA( "vtkCellData" ):
        return "vtkCellData"
    elif data.IsA( "vtkPointData" ):
        return "vtkPointData"
    else:
        return "vtkFieldData"


def getArrayNames( data: vtkFieldData ) -> list[ str ]:
    """Get the names of all arrays stored in a "vtkFieldData", "vtkCellData" or "vtkPointData".

    Args:
        data (vtkFieldData): Vtk field data.

    Returns:
        list[str]: The array names in the order that they are stored in the field data.
    """
    if not data.IsA( "vtkFieldData" ):
        raise ValueError( f"data '{ data }' entered is not a vtkFieldData object." )
    return [ data.GetArrayName( i ) for i in range( data.GetNumberOfArrays() ) ]


def getArrayByName( data: vtkFieldData, name: str ) -> Optional[ vtkDataArray ]:
    """Get the vtkDataArray corresponding to the given name.

    Args:
        data (vtkFieldData): Vtk field data.
        name (str): Array name.

    Returns:
        Optional[ vtkDataArray ]: The vtkDataArray associated with the name given. None if not found.
    """
    if data.HasArray( name ):
        return data.GetArray( name )
    logging.warning( f"No array named '{ name }' was found in '{ data }'." )
    return None


def getCopyArrayByName( data: vtkFieldData, name: str ) -> Optional[ vtkDataArray ]:
    """Get the copy of a vtkDataArray corresponding to the given name.

    Args:
        data (vtkFieldData): Vtk field data.
        name (str): Array name.

    Returns:
        Optional[ vtkDataArray ]: The copy of the vtkDataArray associated with the name given. None if not found.
    """
    dataArray: Optional[ vtkDataArray ] = getArrayByName( data, name )
    if dataArray is not None:
        return deepcopy( dataArray )
    return None


def getNumpyGlobalIdsArray( data: Union[ vtkCellData, vtkPointData ] ) -> Optional[ npt.NDArray[ np.int64 ] ]:
    """Get a numpy array of the GlobalIds.

    Args:
        data (Union[ vtkCellData, vtkPointData ]): Cell or point array.

    Returns:
        Optional[ npt.NDArray[ np.int64 ] ]: The numpy array of GlobalIds.
    """
    global_ids: Optional[ vtkDataArray ] = data.GetGlobalIds()
    if global_ids is None:
        logging.warning( "No GlobalIds array was found." )
        return None
    return vtk_to_numpy( global_ids )


def getNumpyArrayByName( data: Union[ vtkCellData, vtkPointData ],
                         name: str,
                         sorted: bool = False ) -> Optional[ npt.NDArray ]:
    """Get the numpy array of a given vtkDataArray found by its name.

    If sorted is selected, this allows the option to reorder the values wrt GlobalIds. If not GlobalIds was found,
    no reordering will be perform.

    Args:
        data (Union[vtkCellData, vtkPointData]): Vtk field data.
        name (str): Array name to sort.
        sorted (bool, optional): Sort the output array with the help of GlobalIds. Defaults to False.

    Returns:
        Optional[ npt.NDArray ]: Sorted array.
    """
    dataArray: Optional[ vtkDataArray ] = getArrayByName( data, name )
    if dataArray is not None:
        arr: npt.NDArray[ np.float64 ] = vtk_to_numpy( dataArray )
        if sorted and ( data.IsA( "vtkCellData" ) or data.IsA( "vtkPointData" ) ):
            sortArrayByGlobalIds( data, arr )
        return arr
    return None


def getAttributeSet( mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ], onPoints: bool ) -> set[ str ]:
    """Get the set of all attributes from an mesh on points or on cells.

    Args:
        mesh (Any): Mesh where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        set[str]: Set of attribute names present in input mesh.
    """
    attributes: dict[ str, int ]
    if isinstance( mesh, vtkMultiBlockDataSet ):
        attributes = getAttributesFromMultiBlockDataSet( mesh, onPoints )
    elif isinstance( mesh, vtkDataSet ):
        attributes = getAttributesFromDataSet( mesh, onPoints )
    else:
        raise TypeError( "Input mesh must be a vtkDataSet or vtkMultiBlockDataSet." )

    assert attributes is not None, "Attribute list is undefined."

    return set( attributes.keys() ) if attributes is not None else set()


def getAttributesWithNumberOfComponents(
    mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet, vtkDataObject ],
    onPoints: bool,
) -> dict[ str, int ]:
    """Get the dictionary of all attributes from object on points or cells.

    Args:
        mesh (Any): Mesh where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        dict[str, int]: Dictionary where keys are the names of the attributes and values the number of components.
    """
    attributes: dict[ str, int ]
    if isinstance( mesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        attributes = getAttributesFromMultiBlockDataSet( mesh, onPoints )
    elif isinstance( mesh, vtkDataSet ):
        attributes = getAttributesFromDataSet( mesh, onPoints )
    else:
        raise TypeError( "Input mesh must be a vtkDataSet or vtkMultiBlockDataSet." )
    return attributes


def getAttributesFromMultiBlockDataSet( multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
                                        onPoints: bool ) -> dict[ str, int ]:
    """Get the dictionary of all attributes of object on points or on cells.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): multiBlockDataSet where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        dict[str, int]: Dictionary of the names of the attributes as keys, and number of components as values.
    """
    attributes: dict[ str, int ] = {}
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        blockAttributes: dict[ str, int ] = getAttributesFromDataSet( dataSet, onPoints )
        for attributeName, nbComponents in blockAttributes.items():
            if attributeName not in attributes:
                attributes[ attributeName ] = nbComponents

    return attributes


def getAttributesFromDataSet( dataSet: vtkDataSet, onPoints: bool ) -> dict[ str, int ]:
    """Get the dictionary of all attributes of a vtkDataSet on points or cells.

    Args:
        dataSet (vtkDataSet): DataSet where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        dict[str, int]: List of the names of the attributes.
    """
    attributes: dict[ str, int ] = {}
    data: Union[ vtkPointData, vtkCellData ]
    sup: str = ""
    if onPoints:
        data = dataSet.GetPointData()
        sup = "Point"
    else:
        data = dataSet.GetCellData()
        sup = "Cell"
    assert data is not None, f"{sup} data was not recovered."

    nbAttributes: int = data.GetNumberOfArrays()
    for i in range( nbAttributes ):
        attributeName: str = data.GetArrayName( i )
        attribute: vtkDataArray = data.GetArray( attributeName )
        assert attribute is not None, f"Attribute {attributeName} is null"
        nbComponents: int = attribute.GetNumberOfComponents()
        attributes[ attributeName ] = nbComponents
    return attributes


def isAttributeInObject( mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ], attributeName: str, onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        mesh (vtkMultiBlockDataSet | vtkDataSet): Input mesh.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise.
    """
    if isinstance( mesh, vtkMultiBlockDataSet ):
        return isAttributeInObjectMultiBlockDataSet( mesh, attributeName, onPoints )
    elif isinstance( mesh, vtkDataSet ):
        return isAttributeInObjectDataSet( mesh, attributeName, onPoints )
    else:
        raise TypeError( "Input object must be a vtkDataSet or vtkMultiBlockDataSet." )


def isAttributeInObjectMultiBlockDataSet( multiBlockDataSet: vtkMultiBlockDataSet, attributeName: str,
                                          onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        if isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
            return True

    return False


def isAttributeInObjectDataSet( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        dataSet (vtkDataSet): Input dataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise.
    """
    data: Union[ vtkPointData, vtkCellData ]
    sup: str = ""
    if onPoints:
        data = dataSet.GetPointData()
        sup = "Point"
    else:
        data = dataSet.GetCellData()
        sup = "Cell"
    assert data is not None, f"{ sup } data was not recovered."
    return bool( data.HasArray( attributeName ) )


def isAttributeGlobal( multiBlockDataSet: vtkMultiBlockDataSet, attributeName: str, onPoints: bool ) -> bool:
    """Check if an attribute is global in the input multiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is global, False if not.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        if not isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
            return False

    return True


def getArrayInObject( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> npt.NDArray[ Any ]:
    """Return the numpy array corresponding to input attribute name in table.

    Args:
        dataSet (vtkDataSet): Input dataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        ArrayLike[Any]: The numpy array corresponding to input attribute name.
    """
    vtkArray: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
    npArray: npt.NDArray[ Any ] = vnp.vtk_to_numpy( vtkArray )  # type: ignore[no-untyped-call]
    return npArray


def getVtkDataTypeInObject( multiBlockDataSet: Union[ vtkDataSet, vtkMultiBlockDataSet ], attributeName: str,
                            onPoints: bool ) -> int:
    """Return VTK type of requested array from input mesh.

    Args:
        multiBlockDataSet (Union[vtkDataSet, vtkMultiBlockDataSet]): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: The type of the vtk array corresponding to input attribute name.
    """
    if isinstance( multiBlockDataSet, vtkDataSet ):
        return getVtkArrayTypeInObject( multiBlockDataSet, attributeName, onPoints )
    else:
        return getVtkArrayTypeInMultiBlock( multiBlockDataSet, attributeName, onPoints )


def getVtkArrayTypeInObject( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> int:
    """Return VTK type of requested array from dataset input.

    Args:
        dataSet (vtkDataSet): Input dataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: The type of the vtk array corresponding to input attribute name.
    """
    array: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
    vtkArrayType: int = array.GetDataType()

    return vtkArrayType


def getVtkArrayTypeInMultiBlock( multiBlockDataSet: vtkMultiBlockDataSet, attributeName: str, onPoints: bool ) -> int:
    """Return VTK type of requested array from multiblock dataset input, if existing.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Type of the requested vtk array if existing in input multiblock dataset.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        listAttributes: set[ str ] = getAttributeSet( dataSet, onPoints )
        if attributeName in listAttributes:
            return getVtkArrayTypeInObject( dataSet, attributeName, onPoints )

    raise AssertionError( "The vtkMultiBlockDataSet has no attribute with the name " + attributeName + "." )


def getVtkArrayInObject( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> vtkDataArray:
    """Return the array corresponding to input attribute name in table.

    Args:
        dataSet (vtkDataSet): Input dataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        vtkDataArray: The vtk array corresponding to input attribute name.
    """
    assert isAttributeInObject( dataSet, attributeName, onPoints ), f"{attributeName} is not in input mesh."
    return dataSet.GetPointData().GetArray( attributeName ) if onPoints else dataSet.GetCellData().GetArray(
        attributeName )


def getNumberOfComponents(
    mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet ],
    attributeName: str,
    onPoints: bool,
) -> int:
    """Get the number of components of attribute attributeName in dataSet.

    Args:
        mesh (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataSet): Mesh where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Number of components.
    """
    if isinstance( mesh, vtkDataSet ):
        return getNumberOfComponentsDataSet( mesh, attributeName, onPoints )
    elif isinstance( mesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return getNumberOfComponentsMultiBlock( mesh, attributeName, onPoints )
    else:
        raise AssertionError( "Object type is not managed." )


def getNumberOfComponentsDataSet( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> int:
    """Get the number of components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkDataSet): DataSet where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Number of components.
    """
    array: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
    return array.GetNumberOfComponents()


def getNumberOfComponentsMultiBlock(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    attributeName: str,
    onPoints: bool,
) -> int:
    """Get the number of components of attribute attributeName in dataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): multi block data Set where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Number of components.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        if isAttributeInObject( dataSet, attributeName, onPoints ):
            array: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
            return array.GetNumberOfComponents()
    return 0


def getComponentNames(
    mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet, vtkDataObject ],
    attributeName: str,
    onPoints: bool,
) -> tuple[ str, ...]:
    """Get the name of the components of attribute attributeName in dataSet.

    Args:
        mesh (vtkDataSet | vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): Mesh where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        tuple[str,...]: Names of the components.
    """
    if isinstance( mesh, vtkDataSet ):
        return getComponentNamesDataSet( mesh, attributeName, onPoints )
    elif isinstance( mesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
        return getComponentNamesMultiBlock( mesh, attributeName, onPoints )
    else:
        raise AssertionError( "Mesh type is not managed." )


def getComponentNamesDataSet( dataSet: vtkDataSet, attributeName: str, onPoints: bool ) -> tuple[ str, ...]:
    """Get the name of the components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkDataSet): DataSet where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        tuple[str,...]: Names of the components.
    """
    array: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
    componentNames: list[ str ] = []

    if array.GetNumberOfComponents() > 1:
        componentNames += [ array.GetComponentName( i ) for i in range( array.GetNumberOfComponents() ) ]
    return tuple( componentNames )


def getComponentNamesMultiBlock(
    multiBlockDataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    attributeName: str,
    onPoints: bool,
) -> tuple[ str, ...]:
    """Get the name of the components of attribute in MultiBlockDataSet.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): DataSet where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        tuple[str,...]: Names of the components.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSet )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetDataSet( blockIndex ) )
        if isAttributeInObject( dataSet, attributeName, onPoints ):
            return getComponentNamesDataSet( dataSet, attributeName, onPoints )
    return ()


def getAttributeValuesAsDF( surface: vtkPolyData, attributeNames: tuple[ str, ...] ) -> pd.DataFrame:
    """Get attribute values from input surface.

    Args:
        surface (vtkPolyData): Mesh where to get attribute values.
        attributeNames (tuple[str,...]): Tuple of attribute names to get the values.

    Returns:
        pd.DataFrame: DataFrame containing property names as columns.

    """
    nbRows: int = surface.GetNumberOfCells()
    data: pd.DataFrame = pd.DataFrame( np.full( ( nbRows, len( attributeNames ) ), np.nan ), columns=attributeNames )
    for attributeName in attributeNames:
        if not isAttributeInObject( surface, attributeName, False ):
            logging.warning( f"Attribute {attributeName} is not in the mesh." )
            continue
        array: npt.NDArray[ np.float64 ] = getArrayInObject( surface, attributeName, False )

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


def sortArrayByGlobalIds( data: Union[ vtkCellData, vtkPointData ], arr: npt.NDArray[ np.float64 ] ) -> None:
    """Sort an array following global Ids.

    Args:
        data (vtkFieldData): Global Ids array.
        arr (npt.NDArray[ np.float64 ]): Array to sort.
    """
    globalids: Optional[ npt.NDArray[ np.int64 ] ] = getNumpyGlobalIdsArray( data )
    if globalids is not None:
        arr = arr[ np.argsort( globalids ) ]
    else:
        logging.warning( "No sorting was performed." )
