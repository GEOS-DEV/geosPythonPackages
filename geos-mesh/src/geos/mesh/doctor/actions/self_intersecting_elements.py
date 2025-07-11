from dataclasses import dataclass
from typing import Collection, List
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkFiltersGeneral import vtkCellValidator
from vtkmodules.vtkCommonCore import vtkOutputWindow, vtkFileOutputWindow
from geos.mesh.io.vtkIO import read_mesh


@dataclass( frozen=True )
class Options:
    min_distance: float


@dataclass( frozen=True )
class Result:
    wrong_number_of_points_elements: Collection[ int ]
    intersecting_edges_elements: Collection[ int ]
    intersecting_faces_elements: Collection[ int ]
    non_contiguous_edges_elements: Collection[ int ]
    non_convex_elements: Collection[ int ]
    faces_are_oriented_incorrectly_elements: Collection[ int ]


def __action( mesh, options: Options ) -> Result:
    err_out = vtkFileOutputWindow()
    err_out.SetFileName( "/dev/null" )  # vtkCellValidator outputs loads for each cell...
    vtk_std_err_out = vtkOutputWindow()
    vtk_std_err_out.SetInstance( err_out )

    valid = 0x0
    wrong_number_of_points = 0x01
    intersecting_edges = 0x02
    intersecting_faces = 0x04
    non_contiguous_edges = 0x08
    non_convex = 0x10
    faces_are_oriented_incorrectly = 0x20

    wrong_number_of_points_elements: List[ int ] = []
    intersecting_edges_elements: List[ int ] = []
    intersecting_faces_elements: List[ int ] = []
    non_contiguous_edges_elements: List[ int ] = []
    non_convex_elements: List[ int ] = []
    faces_are_oriented_incorrectly_elements: List[ int ] = []

    f = vtkCellValidator()
    f.SetTolerance( options.min_distance )

    f.SetInputData( mesh )
    f.Update()
    output = f.GetOutput()

    validity = output.GetCellData().GetArray( "ValidityState" )  # Could not change name using the vtk interface.
    assert validity is not None
    validity = vtk_to_numpy( validity )
    for i, v in enumerate( validity ):
        if not v & valid:
            if v & wrong_number_of_points:
                wrong_number_of_points_elements.append( i )
            if v & intersecting_edges:
                intersecting_edges_elements.append( i )
            if v & intersecting_faces:
                intersecting_faces_elements.append( i )
            if v & non_contiguous_edges:
                non_contiguous_edges_elements.append( i )
            if v & non_convex:
                non_convex_elements.append( i )
            if v & faces_are_oriented_incorrectly:
                faces_are_oriented_incorrectly_elements.append( i )
    return Result( wrong_number_of_points_elements=wrong_number_of_points_elements,
                   intersecting_edges_elements=intersecting_edges_elements,
                   intersecting_faces_elements=intersecting_faces_elements,
                   non_contiguous_edges_elements=non_contiguous_edges_elements,
                   non_convex_elements=non_convex_elements,
                   faces_are_oriented_incorrectly_elements=faces_are_oriented_incorrectly_elements )


def action( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __action( mesh, options )
