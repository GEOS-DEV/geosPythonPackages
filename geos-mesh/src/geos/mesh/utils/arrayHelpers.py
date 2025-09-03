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
                                            vtkCompositeDataSet, vtkDataObject, vtkPointData, vtkCellData,
                                            vtkDataObjectTreeIterator, vtkPolyData, vtkCell )
from vtkmodules.vtkFiltersCore import vtkCellCenters
from geos.mesh.utils.multiblockHelpers import ( getBlockElementIndexesFlatten, getBlockFromFlatIndex )

__doc__ = """
ArrayHelpers module contains several utilities methods to get information on arrays in VTK datasets.

These methods include:

    - array getters, with conversion into numpy array or pandas dataframe
    - boolean functions to check whether an array is present in the dataset
    - bounds getter for vtu and multiblock datasets
"""

def computeCellMapping(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ],
) ->  dict[ int, npt.NDArray ]:
    """Compute the cell index mapping dictionary from the mesh meshFrom to the mesh meshTo. 

    If meshes are vtkDataSet, 0 is use as block index.

    For each cell (idCellTo) of each block (idBlockTo) of meshTo:
        - if a cell (idCellFrom) of a block (idBlockFrom) of meshFrom has the same bounds coordinates,
        dictCellMap[idBlockTo][idCellTo] = [idBlockFrom, idCellFrom].
        - else, dictCellMap[idBlockTo][idCellTo] = [-1, -1].

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the cell indexes to map.
        meshTo (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the reference cell indexes.

    Returns:
        dictCellMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary where:
            - Keys are the block index of the multiBlockDataSetTo.
            - Items are arrays of size (nb cell in block, 2) filled with:
                + [-1, -1] for cells not shared by the two mesh.
                + [idBlockFrom, idCellFrom] for cells shared by the two meshes.
    """
    dictCellMap: dict[ int, npt.NDArray ] = {}
    if isinstance( meshTo, vtkDataSet ):
        UpdateCellMappingToDataSet( meshFrom, meshTo, dictCellMap )
    elif isinstance( meshTo, vtkMultiBlockDataSet ):
        UpdateCellMappingToMultiBlockDataSet( meshFrom, meshTo, dictCellMap )
    
    return dictCellMap


def UpdateCellMappingToMultiBlockDataSet(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    multiBlockDataSetTo: vtkMultiBlockDataSet,
    dictCellMap: dict[ int, npt.NDArray ],
) -> None:
    """Update the cell index mapping dictionary from the mesh meshFrom to the mesh multiBlockDataSetTo. 

    If meshFrom is a vtkDataSet, 0 is use as block index.

    Add the mapping for each block (idBlockTo) of the multiBlockDataSetTo:
        - Keys are the block index of the multiBlockDataSetTo.
        - Items are arrays of size (nb cell in block, 2). 

    For each cell (idCellTo) of each block (idBlockTo) of multiBlockDataSetTo:
        - if a cell (idCellFrom) of a block (idBlockFrom) of meshFrom has the same bounds coordinates,
        dictCellMap[idBlockTo][idCellTo] = [idBlockFrom, idCellFrom].
        - else, dictCellMap[idBlockTo][idCellTo] = [-1, -1].

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the cell indexes to map.
        multiBlockDataSetTo (vtkMultiBlockDataSet): The mesh with the reference cell indexes.
        dictCellMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary to update with the mapping of all blocks of the multiBlockDataSetTo.
    """
    nbBlocksTo: int = multiBlockDataSetTo.GetNumberOfBlocks()
    for idBlockTo in range( nbBlocksTo ):
        blockTo: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTo.GetBlock( idBlockTo ) )
        UpdateCellMappingToDataSet( meshFrom, blockTo, dictCellMap, idBlockTo=idBlockTo )


def UpdateCellMappingToDataSet(
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
    dataSetTo: vtkDataSet,
    dictCellMap: dict[ int, npt.NDArray ],
    idBlockTo: int = 0,
) -> None:
    """Update the cell index mapping dictionary from the mesh meshFrom to the mesh dataSetTo. 

    If meshFrom is a vtkDataSet, 0 is use as block index.
    dataSetTo is considered as block of a vtkMultiblockDataSet, if not, 0 is use as block index.

    Add the mapping for the dataSetTo:
        - The keys is the block index of the dataSetTo (idBlockTo).
        - The item is an array of size (nb cell in dataSetTo, 2). 

    For each cell (idCellTo) of the mesh dataSetTo:
        - if a cell (idCellFrom) of the meshFrom or one of its block (idBlockFrom) has the same bounds coordinates,
        dictCellMap[idBlockTo][idCellTo] = [idBlockFrom, idCellFrom].
        - else, dictCellMap[idBlockTo][idCellTo] = [-1, -1].

    Args:
        meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with the cell indexes to map.
        dataSetTo (vtkDataSet): The mesh with the reference cell indexes.
        dictCellMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary to update with the mapping for the dataSetTo.
        idBlockTo (int, Optional): The block index of the dataSetTo.
            Defaults to 0.
    """
    dictCellMap[ idBlockTo ] = np.full( ( dataSetTo.GetNumberOfCells(), 2 ), -1, int )
    if isinstance( meshFrom, vtkDataSet ):
        UpdateCellMappingFromDataSetToDataSet( meshFrom, dataSetTo, dictCellMap, idBlockTo=idBlockTo )
    elif isinstance( meshFrom, vtkMultiBlockDataSet ):
        UpdateCellMappingFromMultiBlockDataSetToDataSet( meshFrom, dataSetTo, dictCellMap, idBlockTo=idBlockTo )


def UpdateCellMappingFromMultiBlockDataSetToDataSet(
    multiBlockDataSetFrom: vtkMultiBlockDataSet,
    dataSetTo: vtkDataSet,
    dictCellMap: dict[ int, npt.NDArray ],
    idBlockTo: int = 0,
) -> None:
    """Update the cell index mapping dictionary from the mesh multiBlockDataSetFrom to the mesh dataSetTo. 
    
    dataSetTo is considered as block of a vtkMultiblockDataSet, if not, 0 is use as block index. 

    For each cell (idCellTo) of the mesh dataSetTo not yet mapped (dictCellMap[idBlockTo][idCellTo] = [-1, -1]),
    if a cell (idCellFrom) of a block (idBlockFrom) of multiBlockDataSetFrom has the same bounds coordinates,
    the dictCellMap is update to dictCellMap[idBlockTo][idCellTo] = [idBlockFrom, idCellFrom].

    Args:
        multiBlockDataSetFrom (vtkMultiBlockDataSet): The mesh with the cell indexes to map.
        dataSetTo (vtkDataSet): The mesh with the reference cell indexes.
        dictCellMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary to update with:
            - The block index of the dataSetTo as keys.
            - An array of size (nb cell in dataSetTo, 2) as items filled with:
                + [-1, -1] for cell not yet mapped.
                + [idBlockFrom, idCellFrom] for cell already mapped.
        idBlockTo (int, Optional): The block index of the dataSetTo.
            Defaults to 0.
    """
    nbBlocksFrom: int = multiBlockDataSetFrom.GetNumberOfBlocks()
    for idBlockFrom in range( nbBlocksFrom ):
        blockFrom: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetFrom.GetBlock( idBlockFrom ) )
        UpdateCellMappingFromDataSetToDataSet( blockFrom, dataSetTo, dictCellMap, idBlockFrom=idBlockFrom, idBlockTo=idBlockTo )


def UpdateCellMappingFromDataSetToDataSet(
    dataSetFrom: vtkDataSet,
    dataSetTo: vtkDataSet,
    dictCellMap: dict[ int, npt.NDArray[ np.int64 ] ],
    idBlockFrom: int = 0,
    idBlockTo: int = 0,
) -> None:
    """Update the cell index mapping dictionary from the mesh dataSetFrom to the mesh dataSetTo. 

    Meshes are considered as block of vtkMultiblockDataSet, if not, 0 is use as block index. 

    For each cell (idCellTo) of the mesh dataSetTo not yet mapped (dictCellMap[idBlockTo][idCellTo] = [-1, -1]),
    if a cell (idCellFrom) of the mesh dataSetFrom has the same bounds coordinates,
    the dictCellMap is update to dictCellMap[idBlockTo][idCellTo] = [idBlockFrom, idCellFrom].

    Args:
        dataSetFrom (vtkDataSet): The mesh with the cell indexes to map.
        dataSetTo (vtkDataSet): The mesh with the reference cell indexes.
        dictCellMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary to update with:
            - The block index of the dataSetTo as keys.
            - An array of size (nb cell in dataSetTo, 2) as items filled with:
                + [-1, -1] for cell not yet mapped.
                + [idBlockFrom, idCellFrom] for cell already mapped.
        idBlockFrom (int, Optional): The block index of the dataSetFrom.
            Defaults to 0.
        idBlockTo (int, Optional): The block index of the dataSetTo.
            Defaults to 0.
    """
    idCellFromFund: list[ int ] = []
    nbCellsTo: int = dataSetTo.GetNumberOfCells()
    nbCellsFrom: int = dataSetFrom.GetNumberOfCells()
    for idCellTo in range( nbCellsTo ):
        # Test if the cell is already mapped.
        if -1 in dictCellMap[ idBlockTo ][ idCellTo ]:
            cellTo: vtkCell = dataSetTo.GetCell( idCellTo )
            boundsCellTo: list[ float ] = cellTo.GetBounds()

            idCellFrom: int = 0
            cellFund: bool = False
            while idCellFrom < nbCellsFrom and not cellFund:
                # Test if the cell is already mapped.
                if idCellFrom not in idCellFromFund:         
                    cellFrom: vtkCell = dataSetFrom.GetCell( idCellFrom )
                    boundsCellFrom: list[ float ] = cellFrom.GetBounds()
                    if boundsCellFrom == boundsCellTo:
                        dictCellMap[ idBlockTo ][ idCellTo ] = [ idBlockFrom, idCellFrom ]
                        cellFund = True
                        idCellFromFund.append( idCellFrom )
                
                idCellFrom += 1


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


def getAttributeSet( object: Union[ vtkMultiBlockDataSet, vtkDataSet ], onPoints: bool ) -> set[ str ]:
    """Get the set of all attributes from an object on points or on cells.

    Args:
        object (Any): Object where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        set[str]: Set of attribute names present in input object.
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
    """Get the dictionary of all attributes from object on points or cells.

    Args:
        object (Any): Object where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        dict[str, int]: Dictionary where keys are the names of the attributes and values the number of components.
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
    """Get the dictionary of all attributes of object on points or on cells.

    Args:
        object (vtkMultiBlockDataSet | vtkCompositeDataSet): Object where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        dict[str, int]: Dictionary of the names of the attributes as keys, and number of components as values.
    """
    attributes: dict[ str, int ] = {}
    # initialize data object tree iterator
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( object )
    iterator.VisitOnlyLeavesOn()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iterator.GetCurrentDataObject() )
        blockAttributes: dict[ str, int ] = getAttributesFromDataSet( dataSet, onPoints )
        for attributeName, nbComponents in blockAttributes.items():
            if attributeName not in attributes:
                attributes[ attributeName ] = nbComponents

        iterator.GoToNextItem()
    return attributes


def getAttributesFromDataSet( object: vtkDataSet, onPoints: bool ) -> dict[ str, int ]:
    """Get the dictionary of all attributes of a vtkDataSet on points or cells.

    Args:
        object (vtkDataSet): Object where to find the attributes.
        onPoints (bool): True if attributes are on points, False if they are on cells.

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

    nbAttributes: int = data.GetNumberOfArrays()
    for i in range( nbAttributes ):
        attributeName: str = data.GetArrayName( i )
        attribute: vtkDataArray = data.GetArray( attributeName )
        assert attribute is not None, f"Attribute {attributeName} is null"
        nbComponents: int = attribute.GetNumberOfComponents()
        attributes[ attributeName ] = nbComponents
    return attributes


def isAttributeInObject( object: Union[ vtkMultiBlockDataSet, vtkDataSet ], attributeName: str,
                         onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        object (vtkMultiBlockDataSet | vtkDataSet): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise.
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
        object (vtkMultiBlockDataSet): Input multiBlockDataSet.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise.
    """
    iterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
    iterator.SetDataSet( object )
    iterator.VisitOnlyLeavesOn()
    iterator.GoToFirstItem()
    while iterator.GetCurrentDataObject() is not None:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( iterator.GetCurrentDataObject() )
        if isAttributeInObjectDataSet( dataSet, attributeName, onPoints ):
            return True
        iterator.GoToNextItem()
    return False


def isAttributeInObjectDataSet( object: vtkDataSet, attributeName: str, onPoints: bool ) -> bool:
    """Check if an attribute is in the input object.

    Args:
        object (vtkDataSet): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is in the table, False otherwise.
    """
    data: Union[ vtkPointData, vtkCellData ]
    sup: str = ""
    if onPoints:
        data = object.GetPointData()
        sup = "Point"
    else:
        data = object.GetCellData()
        sup = "Cell"
    assert data is not None, f"{ sup } data was not recovered."
    return bool( data.HasArray( attributeName ) )


def isAttributeGlobal( object: vtkMultiBlockDataSet, attributeName: str, onPoints: bool ) -> bool:
    """Check if an attribute is global in the input multiBlockDataSet.

    Args:
        object (vtkMultiBlockDataSet): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        bool: True if the attribute is global, False if not.
    """
    isOnBlock: bool
    nbBlock: int = object.GetNumberOfBlocks()
    for idBlock in range( nbBlock ):
        block: vtkDataSet = vtkDataSet.SafeDownCast( object.GetBlock( idBlock ) )
        isOnBlock = isAttributeInObjectDataSet( block, attributeName, onPoints )
        if not isOnBlock:
            return False

    return True


def getArrayInObject( object: vtkDataSet, attributeName: str, onPoints: bool ) -> npt.NDArray[ Any ]:
    """Return the numpy array corresponding to input attribute name in table.

    Args:
        object (PointSet or UnstructuredGrid): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        ArrayLike[Any]: The numpy array corresponding to input attribute name.
    """
    vtkArray: vtkDataArray = getVtkArrayInObject( object, attributeName, onPoints )
    npArray: npt.NDArray[ Any ] = vnp.vtk_to_numpy( vtkArray )  # type: ignore[no-untyped-call]
    return npArray


def getVtkDataTypeInObject( object: Union[ vtkDataSet, vtkMultiBlockDataSet ], attributeName: str,
                            onPoints: bool ) -> int:
    """Return VTK type of requested array from input mesh.

    Args:
        object (Union[vtkDataSet, vtkMultiBlockDataSet]): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: The type of the vtk array corresponding to input attribute name.
    """
    if isinstance( object, vtkDataSet ):
        return getVtkArrayTypeInObject( object, attributeName, onPoints )
    else:
        return getVtkArrayTypeInMultiBlock( object, attributeName, onPoints )


def getVtkArrayTypeInObject( object: vtkDataSet, attributeName: str, onPoints: bool ) -> int:
    """Return VTK type of requested array from dataset input.

    Args:
        object (PointSet or UnstructuredGrid): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: The type of the vtk array corresponding to input attribute name.
    """
    array: vtkDataArray = getVtkArrayInObject( object, attributeName, onPoints )
    vtkArrayType: int = array.GetDataType()

    return vtkArrayType


def getVtkArrayTypeInMultiBlock( multiBlockDataSet: vtkMultiBlockDataSet, attributeName: str, onPoints: bool ) -> int:
    """Return VTK type of requested array from multiblock dataset input, if existing.

    Args:
        multiBlockDataSet (vtkMultiBlockDataSet): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Type of the requested vtk array if existing in input multiblock dataset.
    """
    nbBlocks = multiBlockDataSet.GetNumberOfBlocks()
    for idBlock in range( nbBlocks ):
        object: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetBlock( idBlock ) )
        listAttributes: set[ str ] = getAttributeSet( object, onPoints )
        if attributeName in listAttributes:
            return getVtkArrayTypeInObject( object, attributeName, onPoints )

    raise AssertionError( "The vtkMultiBlockDataSet has no attribute with the name " + attributeName + "." )


def getVtkArrayInObject( object: vtkDataSet, attributeName: str, onPoints: bool ) -> vtkDataArray:
    """Return the array corresponding to input attribute name in table.

    Args:
        object (PointSet or UnstructuredGrid): Input object.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        vtkDataArray: The vtk array corresponding to input attribute name.
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
        dataSet (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataSet): DataSet where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Number of components.
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
        dataSet (vtkDataSet): DataSet where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Number of components.
    """
    array: vtkDataArray = getVtkArrayInObject( dataSet, attributeName, onPoints )
    return array.GetNumberOfComponents()


def getNumberOfComponentsMultiBlock(
    dataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    attributeName: str,
    onPoints: bool,
) -> int:
    """Get the number of components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): multi block data Set where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        int: Number of components.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( dataSet )
    for blockIndex in elementaryBlockIndexes:
        block: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( dataSet, blockIndex ) )
        if isAttributeInObject( block, attributeName, onPoints ):
            array: vtkDataArray = getVtkArrayInObject( block, attributeName, onPoints )
            return array.GetNumberOfComponents()
    return 0


def getComponentNames(
    dataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataSet, vtkDataObject ],
    attributeName: str,
    onPoints: bool,
) -> tuple[ str, ...]:
    """Get the name of the components of attribute attributeName in dataSet.

    Args:
        dataSet (vtkDataSet | vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): DataSet where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        tuple[str,...]: Names of the components.
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
    dataSet: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
    attributeName: str,
    onPoints: bool,
) -> tuple[ str, ...]:
    """Get the name of the components of attribute in MultiBlockDataSet.

    Args:
        dataSet (vtkMultiBlockDataSet | vtkCompositeDataSet): DataSet where the attribute is.
        attributeName (str): Name of the attribute.
        onPoints (bool): True if attributes are on points, False if they are on cells.

    Returns:
        tuple[str,...]: Names of the components.
    """
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( dataSet )
    for blockIndex in elementaryBlockIndexes:
        block: vtkDataSet = vtkDataSet.SafeDownCast( getBlockFromFlatIndex( dataSet, blockIndex ) )
        if isAttributeInObject( block, attributeName, onPoints ):
            return getComponentNamesDataSet( block, attributeName, onPoints )
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
