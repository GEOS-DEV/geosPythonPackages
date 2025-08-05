from dataclasses import dataclass
from typing import Collection
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkFiltersGeneral import vtkCellValidator
from vtkmodules.vtkCommonCore import vtkOutputWindow, vtkFileOutputWindow
from vtkmodules.vtkCommonDataModel import vtkPointSet
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
    faces_oriented_incorrectly_elements: Collection[ int ]


def get_invalid_cell_ids( mesh: vtkPointSet, min_distance: float ) -> dict[ str, list[ int ] ]:
    """For every cell element in a vtk mesh, check if the cell is invalid regarding 6 specific criteria:
    "wrong_number_of_points", "intersecting_edges", "intersecting_faces",
    "non_contiguous_edges","non_convex" and "faces_oriented_incorrectly".

    If any of this criteria was met, the cell index is added to a list corresponding to this specific criteria.
    The dict with the complete list of cell indices by criteria is returned.

    Args:
        mesh (vtkPointSet): A vtk grid.
        min_distance (float): Minimum distance in the computation.

    Returns:
        dict[ str, list[ int ] ]:
        {
            "wrong_number_of_points": [ 10, 34, ... ],
            "intersecting_edges": [ ... ],
            "intersecting_faces": [ ... ],
            "non_contiguous_edges": [ ... ],
            "non_convex": [ ... ],
            "faces_oriented_incorrectly": [ ... ]
        }
    """
    # The goal of this first block is to silence the standard error output from VTK. The vtkCellValidator can be very
    # verbose, printing a message for every cell it checks. We redirect the output to /dev/null to remove it.
    err_out = vtkFileOutputWindow()
    err_out.SetFileName( "/dev/null" )
    vtk_std_err_out = vtkOutputWindow()
    vtk_std_err_out.SetInstance( err_out )

    # Different types of cell invalidity are defined as hexadecimal values, specific to vtkCellValidator
    # Here NonPlanarFaces and DegenerateFaces can also be obtained.
    error_masks: dict[ str, int ] = {
        "wrong_number_of_points_elements": 0x01,      # 0000 0001
        "intersecting_edges_elements": 0x02,          # 0000 0010
        "intersecting_faces_elements": 0x04,          # 0000 0100
        "non_contiguous_edges_elements": 0x08,        # 0000 1000
        "non_convex_elements": 0x10,                  # 0001 0000
        "faces_oriented_incorrectly_elements": 0x20,  # 0010 0000
    }

    # The results can be stored in a dictionary where keys are the error names
    # and values are the lists of cell indices with that error.
    # We can initialize it directly from the keys of our error_masks dictionary.
    invalid_cell_ids: dict[ str, list[ int ] ] = { error_name: list() for error_name in error_masks }

    f = vtkCellValidator()
    f.SetTolerance(min_distance)
    f.SetInputData(mesh)
    f.Update()  # executes the filter
    output = f.GetOutput()

    validity = output.GetCellData().GetArray( "ValidityState" )
    assert validity is not None
    # array of np.int16 that combines the flags using a bitwise OR operation for each cell index.
    validity = vtk_to_numpy( validity )
    for cell_index, validity_flag in enumerate( validity ):
        if not validity_flag:  # Skip valid cells ( validity_flag == 0 or 0000 0000 )
            continue
        for error_name, error_mask in error_masks.items():  # Check only invalid cells against all possible errors.
            if validity_flag & error_mask:
                invalid_cell_ids[ error_name ].append( cell_index )

    return invalid_cell_ids


def mesh_action( mesh, options: Options ) -> Result:
    invalid_cell_ids = get_invalid_cell_ids( mesh, options.min_distance )
    return Result( wrong_number_of_points_elements=invalid_cell_ids[ "wrong_number_of_points_elements" ],
                   intersecting_edges_elements=invalid_cell_ids[ "intersecting_edges_elements" ],
                   intersecting_faces_elements=invalid_cell_ids[ "intersecting_faces_elements" ],
                   non_contiguous_edges_elements=invalid_cell_ids[ "non_contiguous_edges_elements" ],
                   non_convex_elements=invalid_cell_ids[ "non_convex_elements" ],
                   faces_oriented_incorrectly_elements=invalid_cell_ids[ "faces_oriented_incorrectly_elements" ] )


def action( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return mesh_action( mesh, options )
