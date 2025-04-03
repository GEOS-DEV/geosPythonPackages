import logging
from copy import deepcopy
from numpy import argsort, array
from typing import Iterator, Optional, List
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDataArray, vtkIdList
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkFieldData


def to_vtk_id_list( data ) -> vtkIdList:
    result = vtkIdList()
    result.Allocate( len( data ) )
    for d in data:
        result.InsertNextId( d )
    return result


def vtk_iter( l ) -> Iterator[ any ]:
    """
    Utility function transforming a vtk "container" (e.g. vtkIdList) into an iterable to be used for building built-ins
    python containers.
    :param l: A vtk container.
    :return: The iterator.
    """
    if hasattr( l, "GetNumberOfIds" ):
        for i in range( l.GetNumberOfIds() ):
            yield l.GetId( i )
    elif hasattr( l, "GetNumberOfTypes" ):
        for i in range( l.GetNumberOfTypes() ):
            yield l.GetCellType( i )


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
        if name.startswith("Global") and name.endswith("Ids"):
            return getCopyArrayByName( data, name )
    logging.warning( f"No GlobalIds array was found." )


def getNumpyGlobalIdsArray( data: vtkFieldData ) -> Optional[ array ]:
    return vtk_to_numpy( getGlobalIdsArray( data ) )


def sortArrayByGlobalIds( data: vtkFieldData, arr: array ) -> None:
    globalids: array = getNumpyGlobalIdsArray( data )
    if globalids is not None:
        arr = arr[ argsort( globalids ) ]
    else:
        logging.warning( f"No sorting was performed." )


def getNumpyArrayByName( data: vtkFieldData, name: str, sorted: bool=False ) -> Optional[ array ]:
    arr: array = vtk_to_numpy( getArrayByName( data, name ) )
    if arr is not None:
        if sorted:
            array_names: List[ str ] = getArrayNames( data )
            sortArrayByGlobalIds( data, arr, array_names )
        return arr
    return None


def getCopyNumpyArrayByName( data: vtkFieldData, name: str, sorted: bool=False ) -> Optional[ array ]:
    return deepcopy( getNumpyArrayByName( data, name, sorted=sorted ) )
