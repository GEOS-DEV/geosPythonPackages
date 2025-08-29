from dataclasses import dataclass
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkFiltersGeneral import vtkCellValidator
from vtkmodules.vtkCommonCore import vtkOutputWindow, vtkFileOutputWindow
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.io.vtkIO import read_unstructured_grid


@dataclass( frozen=True )
class Options:
    min_distance: float


@dataclass( frozen=True )
class Result:
    invalid_cell_ids: dict[ str, list[ int ] ]


def get_invalid_cell_ids( mesh: vtkUnstructuredGrid, min_distance: float ) -> dict[ str, list[ int ] ]:
    """For every cell element in a vtk mesh, check if the cell is invalid regarding 8 specific criteria:
    "wrong_number_of_points", "intersecting_edges", "intersecting_faces", "non_contiguous_edges","non_convex",
    "faces_oriented_incorrectly", "non_planar_faces_elements" and "degenerate_faces_elements".

    If any of this criteria was met, the cell index is added to a list corresponding to this specific criteria.
    The dict with the complete list of cell indices by criteria is returned.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.
        min_distance (float): Minimum distance in the computation.

    Returns:
        dict[ str, list[ int ] ]:
        {
            "wrong_number_of_points": [ 10, 34, ... ],
            "intersecting_edges": [ ... ],
            "intersecting_faces": [ ... ],
            "non_contiguous_edges": [ ... ],
            "non_convex": [ ... ],
            "faces_oriented_incorrectly": [ ... ],
            "non_planar_faces_elements": [ ... ],
            "degenerate_faces_elements": [ ... ]
        }
    """
    # The goal of this first block is to silence the standard error output from VTK. The vtkCellValidator can be very
    # verbose, printing a message for every cell it checks. We redirect the output to /dev/null to remove it.
    err_out = vtkFileOutputWindow()
    err_out.SetFileName( "/dev/null" )
    vtk_std_err_out = vtkOutputWindow()
    vtk_std_err_out.SetInstance( err_out )

    # Different types of cell invalidity are defined as hexadecimal values, specific to vtkCellValidator
    # Complete set of validity checks available in vtkCellValidator
    error_masks: dict[ str, int ] = {
        "wrongNumberOfPointsElements": 0x01,  # 0000 0001
        "intersectingEdgesElements": 0x02,  # 0000 0010
        "intersectingFacesElements": 0x04,  # 0000 0100
        "nonContiguousEdgesElements": 0x08,  # 0000 1000
        "nonConvexElements": 0x10,  # 0001 0000
        "facesOrientedIncorrectlyElements": 0x20,  # 0010 0000
        "nonPlanarFacesElements": 0x40,  # 0100 0000
        "degenerateFacesElements": 0x80,  # 1000 0000
    }

    # The results can be stored in a dictionary where keys are the error names
    # and values are the lists of cell indices with that error.
    # We can initialize it directly from the keys of our error_masks dictionary.
    invalid_cell_ids: dict[ str, list[ int ] ] = { error_name: list() for error_name in error_masks }

    f = vtkCellValidator()
    f.SetTolerance( min_distance )
    f.SetInputData( mesh )
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


def mesh_action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    invalid_cell_ids: dict[ str, list[ int ] ] = get_invalid_cell_ids( mesh, options.min_distance )
    return Result( invalid_cell_ids )


def action( vtk_input_file: str, options: Options ) -> Result:
    mesh: vtkUnstructuredGrid = read_unstructured_grid( vtk_input_file )
    return mesh_action( mesh, options )
