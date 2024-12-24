import logging
from typing import Iterator
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid


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


def has_invalid_field( mesh: vtkUnstructuredGrid, invalid_fields: list[ str ] ) -> bool:
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