# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
from typing import Any, Iterator, List
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkPolyData, vtkPlane, vtkCellTypes
from vtkmodules.vtkFiltersCore import vtk3DLinearGridPlaneCutter

__doc__ = """ Generic VTK utilities."""


def to_vtk_id_list( data: List[ int ] ) -> vtkIdList:
    """Utility function transforming a list of ids into a vtkIdList.

    Args:
        data (list[int]): Id list

    Returns:
        result (vtkIdList):  Vtk Id List corresponding to input data
    """
    result = vtkIdList()
    result.Allocate( len( data ) )
    for d in data:
        result.InsertNextId( d )
    return result


def vtk_iter( vtkContainer: vtkIdList | vtkCellTypes ) -> Iterator[ Any ]:
    """Utility function transforming a vtk "container" into an iterable.

    Args:
        vtkContainer (vtkIdList | vtkCellTypes): A vtk container

    Returns:
        Iterator[ Any ]: The iterator
    """
    if isinstance( vtkContainer, vtkIdList ):
        for i in range( vtkContainer.GetNumberOfIds() ):
            yield vtkContainer.GetId( i )
    elif isinstance( vtkContainer, vtkCellTypes ):
        for i in range( vtkContainer.GetNumberOfTypes() ):
            yield vtkContainer.GetCellType( i )


def extractSurfaceFromElevation( mesh: vtkUnstructuredGrid, elevation: float ) -> vtkPolyData:
    """Extract surface at a constant elevation from a mesh.

    Args:
        mesh (vtkUnstructuredGrid): input mesh
        elevation (float): elevation at which to extract the surface

    Returns:
        vtkPolyData: output surface
    """
    assert mesh is not None, "Input mesh is undefined."
    assert isinstance( mesh, vtkUnstructuredGrid ), "Wrong object type"

    bounds: tuple[ float, float, float, float, float, float ] = mesh.GetBounds()
    ooX: float = ( bounds[ 0 ] + bounds[ 1 ] ) / 2.0
    ooY: float = ( bounds[ 2 ] + bounds[ 3 ] ) / 2.0

    # check plane z coordinates against mesh bounds
    assert ( elevation <= bounds[ 5 ] ) and ( elevation >= bounds[ 4 ] ), "Plane is out of input mesh bounds."

    plane: vtkPlane = vtkPlane()
    plane.SetNormal( 0.0, 0.0, 1.0 )
    plane.SetOrigin( ooX, ooY, elevation )

    cutter = vtk3DLinearGridPlaneCutter()
    cutter.SetInputDataObject( mesh )
    cutter.SetPlane( plane )
    cutter.SetInterpolateAttributes( True )
    cutter.Update()
    return cutter.GetOutputDataObject( 0 )
