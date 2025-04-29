import logging
from copy import deepcopy
import numpy as np
import numpy.typing as npt
from typing import Iterator, Optional, List, Sequence, Union, Sized
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkPoints,
    vtkIdList,
    reference,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkFieldData,
    vtkCellData,
    vtkPointData,
    vtkDataSet,
    vtkIncrementalOctreePointLocator,
)

GLOBAL_IDS_ARRAY_NAME: str = "GlobalIds"

# TODO: copy from vtkUtils
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


def getBounds( cellPtsCoord: list[ npt.NDArray[ np.float64 ] ] ) -> Sequence[ float ]:
    """Compute bounding box coordinates of the list of points.

    Args:
        cellPtsCoord (list[npt.NDArray[np.float64]]): list of points

    Returns:
        Sequence[float]: bounding box coordinates (xmin, xmax, ymin, ymax, zmin, zmax)
    """
    bounds: list[ float ] = [
        np.inf,
        -np.inf,
        np.inf,
        -np.inf,
        np.inf,
        -np.inf,
    ]
    for ptsCoords in cellPtsCoord:
        mins: npt.NDArray[ np.float64 ] = np.min( ptsCoords, axis=0 )
        maxs: npt.NDArray[ np.float64 ] = np.max( ptsCoords, axis=0 )
        for i in range( 3 ):
            bounds[ 2 * i ] = float( min( bounds[ 2 * i ], mins[ i ] ) )
            bounds[ 2 * i + 1 ] = float( max( bounds[ 2 * i + 1 ], maxs[ i ] ) )
    return bounds


def createSingleCellMesh( cellType: int, ptsCoord: npt.NDArray[ np.float64 ] ) -> vtkUnstructuredGrid:
    """Create a mesh that consists of a single cell.

    Args:
        cellType (int): cell type
        ptsCoord (1DArray[np.float64]): cell point coordinates

    Returns:
        vtkUnstructuredGrid: output mesh
    """
    nbPoints: int = ptsCoord.shape[ 0 ]
    points: npt.NDArray[ np.float64 ] = np.vstack( ( ptsCoord, ) )
    # Convert points to vtkPoints object
    vtkpts: vtkPoints = vtkPoints()
    vtkpts.SetData( numpy_to_vtk( points ) )

    # create cells from point ids
    cellsID: vtkIdList = vtkIdList()
    for j in range( nbPoints ):
        cellsID.InsertNextId( j )

    # add cell to mesh
    mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
    mesh.SetPoints( vtkpts )
    mesh.Allocate( 1 )
    mesh.InsertNextCell( cellType, cellsID )
    return mesh


def createMultiCellMesh( cellTypes: list[ int ],
                         cellPtsCoord: list[ npt.NDArray[ np.float64 ] ],
                         sharePoints: bool = True ) -> vtkUnstructuredGrid:
    """Create a mesh that consists of multiple cells.

    .. WARNING:: the mesh is not check for conformity.

    Args:
        cellTypes (list[int]): cell type
        cellPtsCoord (list[1DArray[np.float64]]): list of cell point coordinates
        sharePoints (bool): if True, cells share points, else a new point is created fro each cell vertex

    Returns:
        vtkUnstructuredGrid: output mesh
    """
    assert len( cellPtsCoord ) == len( cellTypes ), "The lists of cell types of point coordinates must be of same size."
    nbCells: int = len( cellPtsCoord )
    mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
    points: vtkPoints
    cellVertexMapAll: list[ tuple[ int, ...] ]
    points, cellVertexMapAll = createVertices( cellPtsCoord, sharePoints )
    assert len( cellVertexMapAll ) == len(
        cellTypes ), "The lists of cell types of cell point ids must be of same size."
    mesh.SetPoints( points )
    mesh.Allocate( nbCells )
    # create mesh cells
    for cellType, ptsId in zip( cellTypes, cellVertexMapAll, strict=True ):
        # create cells from point ids
        cellsID: vtkIdList = vtkIdList()
        for ptId in ptsId:
            cellsID.InsertNextId( ptId )
        mesh.InsertNextCell( cellType, cellsID )
    return mesh


def createVertices( cellPtsCoord: list[ npt.NDArray[ np.float64 ] ],
                    shared: bool = True ) -> tuple[ vtkPoints, list[ tuple[ int, ...] ] ]:
    """Create vertices from cell point coordinates list.

    Args:
        cellPtsCoord (list[npt.NDArray[np.float64]]): list of cell point coordinates
        shared (bool, optional): If True, collocated points are merged. Defaults to True.

    Returns:
        tuple[vtkPoints, list[tuple[int, ...]]]: tuple containing points and the
            map of cell point ids
    """
    # get point bounds
    bounds: list[ float ] = getBounds( cellPtsCoord )
    points: vtkPoints = vtkPoints()
    # use point locator to check for colocated points
    pointsLocator = vtkIncrementalOctreePointLocator()
    pointsLocator.InitPointInsertion( points, bounds )
    cellVertexMapAll: list[ tuple[ int, ...] ] = []
    ptId: reference = reference( 0 )
    ptsCoords: npt.NDArray[ np.float64 ]
    for ptsCoords in cellPtsCoord:
        cellVertexMap: list[ reference ] = []
        pt: npt.NDArray[ np.float64 ]  # 1DArray
        for pt in ptsCoords:
            if shared:
                pointsLocator.InsertUniquePoint( pt.tolist(), ptId )
            else:
                pointsLocator.InsertPointWithoutChecking( pt.tolist(), ptId, 1 )
            cellVertexMap += [ ptId.get() ]
        cellVertexMapAll += [ tuple( cellVertexMap ) ]
    return points, cellVertexMapAll

def to_vtk_id_list( data: Sized ) -> vtkIdList:
    """Generate vtkIdList from sized object.

    Args:
        data (Sized): sized object

    Returns:
        vtkIdList: id ilst
    """
    result = vtkIdList()
    result.Allocate( len( data ) )
    for d in data:
        result.InsertNextId( d )
    return result


def vtk_iter( vtkContainer: any ) -> Iterator[ any ]:
    """Create an iterable from a vtk "container" (e.g. vtkIdList).

    To be used for building built-inspython containers.

    Args:
        vtkContainer: A vtk container.

    Yields:
        Iterator[ any ]: The iterator.
    """
    if hasattr( vtkContainer, "GetNumberOfIds" ):
        for i in range( vtkContainer.GetNumberOfIds() ):
            yield vtkContainer.GetId( i )
    elif hasattr( vtkContainer, "GetNumberOfTypes" ):
        for i in range( vtkContainer.GetNumberOfTypes() ):
            yield vtkContainer.GetCellType( i )


def has_invalid_arrays( object: vtkDataSet, invalid_arrays: List[ str ] ) -> bool:
    """Check object contains arrays from invalid_arrays list.

    Checks if a mesh contains at least a data arrays within its cell, field or point data
    having a certain name. If so, returns True, else False.

    Args:
        object (vtkDataSet): An object.
        invalid_arrays (list[str]): Array names to check.

    Returns:
        bool: True if at least one array was found, else False.
    """
    # Check the cell data arrays
    cell_data = object.GetCellData()
    for i in range( cell_data.GetNumberOfArrays() ):
        if cell_data.GetArrayName( i ) in invalid_arrays:
            logging.error( f"The mesh contains an invalid cell array name '{cell_data.GetArrayName( i )}'." )
            return True
    # Check the field data arrays
    field_data = object.GetFieldData()
    for i in range( field_data.GetNumberOfArrays() ):
        if field_data.GetArrayName( i ) in invalid_arrays:
            logging.error( f"The mesh contains an invalid field array name '{field_data.GetArrayName( i )}'." )
            return True
    # Check the point data arrays
    point_data = object.GetPointData()
    for i in range( point_data.GetNumberOfArrays() ):
        if point_data.GetArrayName( i ) in invalid_arrays:
            logging.error( f"The mesh contains an invalid point array name '{point_data.GetArrayName( i )}'." )
            return True
    return False


def getArrayType( data: vtkFieldData ) -> str:
    """Get field data type.

    Args:
        data (vtkFieldData): input vtkFieldData.

    Raises:
        ValueError: if input is not a vtkFieldData.

    Returns:
        str: array type.
    """
    if not data.IsA( "vtkFieldData" ):
        raise ValueError( f"data '{data}' entered is not a vtkFieldData object." )
    if data.IsA( "vtkCellData" ):
        return "vtkCellData"
    elif data.IsA( "vtkPointData" ):
        return "vtkPointData"
    else:
        return "vtkFieldData"


def getArrayNames( data: vtkFieldData ) -> List[ str ]:
    """Get all array names.

    Args:
        data (vtkFieldData): input vtkFieldData

    Raises:
        ValueError: if input is not a vtkFieldData

    Returns:
        List[ str ]: list of array names.
    """
    if not data.IsA( "vtkFieldData" ):
        raise ValueError( f"data '{data}' entered is not a vtkFieldData object." )
    return [ data.GetArrayName( i ) for i in range( data.GetNumberOfArrays() ) ]


def getArrayByName( data: vtkFieldData, name: str ) -> Optional[ vtkDataArray ]:
    """Get array from name.

    Args:
        data (vtkFieldData): field data
        name (str): name of the array

    Returns:
        Optional[ vtkDataArray ]: output array if it exists or None.
    """
    if data.HasArray( name ):
        return data.GetArray( name )
    logging.warning( f"No array named '{name}' was found in '{data}'." )
    return None


def getCopyArrayByName( data: vtkFieldData, name: str ) -> Optional[ vtkDataArray ]:
    """Get a deep copy of an array from name.

    Args:
        data (vtkFieldData): field data
        name (str): name of the array

    Returns:
        Optional[ vtkDataArray ]: deep copy of the array if it exists or None.
    """
    return deepcopy( getArrayByName( data, name ) )


def getGlobalIdsArray( data: vtkFieldData ) -> Optional[ vtkDataArray ]:
    """Get GlobalIds array.

    Args:
        data (vtkFieldData): field data

    Returns:
        Optional[ vtkDataArray ]: output array
    """
    array_names: List[ str ] = getArrayNames( data )
    for name in array_names:
        if name == GLOBAL_IDS_ARRAY_NAME:
            return getCopyArrayByName( data, name )
    logging.warning( f"No {GLOBAL_IDS_ARRAY_NAME} array was found." )


def getNumpyGlobalIdsArray( data: vtkFieldData ) -> Optional[npt.NDArray[np.int64]]:
    """Get GlobalIds array as numpy array.

    Args:
        data (vtkFieldData): field data

    Returns:
        Optional[npt.NDArray[np.int64]]: output numpy array
    """
    return vtk_to_numpy( getGlobalIdsArray( data ) )


def sortArrayByGlobalIds( data: vtkFieldData, arr: npt.NDArray[np.int64] ) -> None:
    """Sort input array by GlobalIds.

    Args:
        data (vtkFieldData): field data
        arr (npt.NDArray[np.int64]): array to sort
    """
    globalids: npt.NDArray[np.int64] = getNumpyGlobalIdsArray( data )
    if globalids is not None:
        arr = arr[ np.argsort( globalids ) ]
    else:
        logging.warning( "No sorting was performed." )


def getNumpyArrayByName( data: vtkFieldData, name: str, sorted: bool = False ) -> Optional[npt.NDArray[np.float64]]:
    """Get numpy array from name.

    Args:
        data (vtkFieldData): field data
        name (str): array name
        sorted (bool): True to sort output array. Defaults to False.

    Returns:
        Optional[npt.NDArray[np.int64]]: output numpy array
    """
    arr: npt.NDArray[np.float64] = vtk_to_numpy( getArrayByName( data, name ) )
    if arr is not None:
        if sorted:
            array_names: List[ str ] = getArrayNames( data )
            sortArrayByGlobalIds( data, arr, array_names )
        return arr
    return None


def getCopyNumpyArrayByName( data: vtkFieldData, name: str, sorted: bool = False ) -> Optional[npt.NDArray[np.float64]]:
    """Get a deep copy of numpy array from name.

    Args:
        data (vtkFieldData): field data
        name (str): array name
        sorted (bool): True to sort output array. Defaults to False.

    Returns:
        Optional[npt.NDArray[np.int64]]: output numpy array
    """
    return deepcopy( getNumpyArrayByName( data, name, sorted=sorted ) )
