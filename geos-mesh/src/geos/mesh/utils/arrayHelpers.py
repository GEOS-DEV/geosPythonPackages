# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
from typing import Any
import logging
from copy import deepcopy
import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import vtkmodules.util.numpy_support as vnp
from typing import Iterator, Optional, List, Union, cast
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDataArray, vtkDoubleArray
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkFieldData, vtkMultiBlockDataSet, vtkDataSet,
                                            vtkCompositeDataSet, vtkDataObject, vtkPointData, vtkCellData,
                                            vtkDataObjectTreeIterator, vtkPolyData )
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkFiltersCore import vtkCellCenters
from geos.mesh.utils.multiblockHelpers import ( getBlockElementIndexesFlatten, getBlockFromFlatIndex )

__doc__ = """ Utilities methods to get information on VTK Arrays. """


def has_invalid_field( mesh: vtkUnstructuredGrid, invalid_fields: List[ str ] ) -> bool:
    """Checks if a mesh contains at least a data arrays within its cell, field or point data
    having a certain name. If so, returns True, else False.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured mesh.
        invalid_fields (list[str]): Field name of an array in any data from the data.

    Returns:
        bool: True if one field found, else False.
    """
    # Check the cell data fields
    cell_data = mesh.GetCellData()
    for i in range( cell_data.GetNumberOfArrays() ):
        if cell_data.GetArrayName( i ) in invalid_fields:
            logging.error( f"The mesh contains an invalid cell field name '{cell_data.GetArrayName( i )}'." )
            return True
    # Check the field data fields
    field_data = mesh.GetFieldData()
    for i in range( field_data.GetNumberOfArrays() ):
        if field_data.GetArrayName( i ) in invalid_fields:
            logging.error( f"The mesh contains an invalid field name '{field_data.GetArrayName( i )}'." )
            return True
    # Check the point data fields
    point_data = mesh.GetPointData()
    for i in range( point_data.GetNumberOfArrays() ):
        if point_data.GetArrayName( i ) in invalid_fields:
            logging.error( f"The mesh contains an invalid point field name '{point_data.GetArrayName( i )}'." )
            return True
    return False


def getFieldType( data: vtkFieldData ) -> str:
    if not data.IsA( "vtkFieldData" ):
        raise ValueError( f"data '{data}' entered is not a vtkFieldData object." )
    if data.IsA( "vtkCellData" ):
        return "vtkCellData"
    elif data.IsA( "vtkPointData" ):
        return "vtkPointData"
    else:
        return "vtkFieldData"


def getArrayNames( data: vtkFieldData ) -> List[ str ]:
    if not data.IsA( "vtkFieldData" ):
        raise ValueError( f"data '{data}' entered is not a vtkFieldData object." )
    return [ data.GetArrayName( i ) for i in range( data.GetNumberOfArrays() ) ]


def getArrayByName( data: vtkFieldData, name: str ) -> Optional[ vtkDataArray ]:
    if data.HasArray( name ):
        return data.GetArray( name )
    logging.warning( f"No array named '{name}' was found in '{data}'." )
    return None


def getCopyArrayByName( data: vtkFieldData, name: str ) -> Optional[ vtkDataArray ]:
    return deepcopy( getArrayByName( data, name ) )


def getGlobalIdsArray( data: vtkFieldData ) -> Optional[ vtkDataArray ]:
    array_names: List[ str ] = getArrayNames( data )
    for name in array_names:
        if name.startswith( "Global" ) and name.endswith( "Ids" ):
            return getCopyArrayByName( data, name )
    logging.warning( "No GlobalIds array was found." )
    return None


def getNumpyGlobalIdsArray( data: vtkFieldData ) -> Optional[ npt.NDArray[ np.int64 ] ]:
    return vtk_to_numpy( getGlobalIdsArray( data ) )


def getNumpyArrayByName( data: vtkFieldData, name: str, sorted: bool = False ) -> Optional[ Any ]:
    arr: Optional[ npt.NDArray[ Any ] ] = vtk_to_numpy( getArrayByName( data, name ) )
    if arr is not None:
        if sorted:
            sortArrayByGlobalIds( data, arr )
        return arr
    return None


def getCopyNumpyArrayByName( data: vtkFieldData, name: str, sorted: bool = False ) -> Optional[ npt.NDArray[ Any ] ]:
    return deepcopy( getNumpyArrayByName( data, name, sorted=sorted ) )


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
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( dataSet )
    for blockIndex in elementaryBlockIndexes:
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


def AsDF( surface: vtkPolyData, attributeNames: tuple[ str, ...] ) -> pd.DataFrame:
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


def sortArrayByGlobalIds( data: vtkFieldData, arr: npt.NDArray[ np.int64 ] ) -> None:
    """Sort an array following global Ids

    Args:
        data (vtkFieldData): Global Ids array
        arr (npt.NDArray[ np.int64 ]): Array to sort
    """
    globalids: Optional[ npt.NDArray[ np.int64 ] ] = getNumpyGlobalIdsArray( data )
    if globalids is not None:
        arr = arr[ np.argsort( globalids ) ]
    else:
        logging.warning( "No sorting was performed." )
