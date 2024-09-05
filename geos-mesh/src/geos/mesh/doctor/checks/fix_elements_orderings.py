from dataclasses import dataclass
import numpy as np
from typing import (
    List,
    Dict,
)
from vtk import vtkCellSizeFilter
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, VTK_HEXAHEDRON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_VOXEL,
                                            VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM )
from .vtk_utils import VtkOutput, to_vtk_id_list, write_mesh, read_mesh


@dataclass( frozen=True )
class Options:
    vtk_output: VtkOutput
    cell_type_to_ordering: Dict[ int, List[ int ] ]
    volume_to_reorder: str


@dataclass( frozen=True )
class Result:
    output: str
    reordering_stats: dict[ str, list[ int ] ]


cell_type_names: dict[ int, str ] = {
    VTK_HEXAHEDRON: "Hexahedron",
    VTK_TETRA: "Tetra",
    VTK_PYRAMID: "Pyramid",
    VTK_WEDGE: "Wedge",
    VTK_VOXEL: "Voxel",
    VTK_PENTAGONAL_PRISM: "Prism5",
    VTK_HEXAGONAL_PRISM: "Prism6"
}


# Knowing the calculation of cell volumes in vtk was discussed there: https://github.com/GEOS-DEV/GEOS/issues/2253
# Here, we do not need to have the exact volumes matching the simulation softwares results
# because we are mostly interested in knowing the sign of the volume for the rest of the workflow.
# Therefore, there is no need to use vtkMeshQuality for specific cell types when vtkCellSizeFilter works with all types.
def compute_mesh_cells_volume( mesh: vtkDataSet ) -> np.array:
    """Generates a volume array that was calculated on all cells of a mesh.

    Args:
        mesh (vtkDataSet): A vtk grid.

    Returns:
        np.array: Volume for every cell of a mesh.
    """
    cell_size_filter = vtkCellSizeFilter()
    cell_size_filter.SetInputData( mesh )
    cell_size_filter.SetComputeVolume( True )
    cell_size_filter.Update()
    return vtk_to_numpy( cell_size_filter.GetOutput().GetCellData().GetArray( "Volume" ) )


def is_cell_to_reorder( cell_volume: float, volume_to_reorder: str ) -> bool:
    """Check if the volume of vtkCell qualifies the cell to be reordered.

    Args:
        cell_volume (float): The volume of a vtkCell.
        volume_to_reorder (str): Condition imposed in Options.volume_to_reorder

    Returns:
        bool: True if cell needs to be reordered
    """
    if volume_to_reorder == "all":
        return True
    if cell_volume == 0.0:
        return True
    sign_of_cell_volume: int = int( cell_volume / abs( cell_volume ) )
    if volume_to_reorder == "positive" and sign_of_cell_volume == 1:
        return True
    elif volume_to_reorder == "negative" and sign_of_cell_volume == -1:
        return True
    return False


def get_all_cells_type( mesh: vtkDataSet ) -> np.array:
    """Gets the cell type for every cell of a mesh.

    Args:
        mesh (vtk grid): A vtk grid.

    Returns:
        np.array: ( [ cell0_type, cell1_type, ..., cellN_type ] )
    """
    number_cells: int = mesh.GetNumberOfCells()
    all_cells_type: np.array = np.ones( number_cells, dtype=int )
    for cell_id in range( number_cells ):
        all_cells_type[ cell_id ] = mesh.GetCellType( cell_id )
    return all_cells_type


def get_cell_ids_to_check( all_cells_type: np.array, options: Options ) -> dict[ int, np.array ]:
    """For every cell type, returns a numpy array with only the indexes of the cell elements that have the same
    type as specified in options. So if the cell type to check was tetrahedron, only the indexes of all
    tetrahedrons in the mesh are returned.

    Args:
        all_cells_type (np.array): Array of cell types for every cell of a mesh.
        options (Options): Options defined by the user.

    Returns:
        dict[ int, np.array ]: Indexes in ascending order of every cell being of a certain type.
    """
    cell_ids_to_check: dict[ int, np.array ] = {}
    available_types: list[ int ] = np.unique( all_cells_type ).tolist()
    for cell_type in options.cell_type_to_ordering.keys():
        if cell_type in available_types:
            sub_array = np.where( all_cells_type == cell_type )[ 0 ]
            cell_ids_to_check[ cell_type ] = sub_array
    return cell_ids_to_check


def reorder_nodes_to_new_mesh( old_mesh: vtkDataSet, options: Options ) -> tuple:
    """From an old mesh, creates a new one where certain cell nodes are reordered to obtain a correct volume.

    Args:
        old_mesh (vtkDataSet): A vtk grid needing nodes to be reordered.
        options (Options): Options defined by the user.

    Returns:
        tuple: ( vtkDataSet, reordering_stats )
    """
    # gets all the cell types found in the mesh
    all_cells_type: np.array = get_all_cells_type( old_mesh )
    unique_cell_types, total_per_cell_types = np.unique( all_cells_type, return_counts=True )
    unique_cell_types, total_per_cell_types = unique_cell_types.tolist(), total_per_cell_types.tolist()
    # voxel elements are not accepted as input for GEOS mesh, so no need to perform reordering
    if VTK_VOXEL in unique_cell_types:
        raise ValueError( "Voxel elements were found in the grid. This element cannot be used in GEOS. Dying ..." )
    # volumes and cell ids that have the element type suggested for reordering are collected
    all_cells_volume: np.array = compute_mesh_cells_volume( old_mesh )
    cell_ids_to_check: dict[ int, np.array ] = get_cell_ids_to_check( all_cells_type, options )
    # a new mesh with the same data is created from the old mesh
    new_mesh: vtkDataSet = old_mesh.NewInstance()
    new_mesh.CopyStructure( old_mesh )
    new_mesh.CopyAttributes( old_mesh )
    cells = new_mesh.GetCells()
    # Statistics on how many cells have or have not been reordered
    reordering_stats: dict[ str, list[ any ] ] = {
        "Types reordered": [],
        "Number of cells reordered": [],
        "Types non reordered": unique_cell_types,
        "Number of cells non reordered": total_per_cell_types
    }
    for cell_type, cell_ids in cell_ids_to_check.items():
        counter_cells_reordered: int = 0
        for cell_id in cell_ids:
            if is_cell_to_reorder( float( all_cells_volume[ cell_id ] ), options.volume_to_reorder ):
                support_point_ids = vtkIdList()
                cells.GetCellAtId( cell_id, support_point_ids )
                new_support_point_ids = []
                node_ordering: list[ int ] = options.cell_type_to_ordering[ cell_type ]
                for i in range( len( node_ordering ) ):
                    new_support_point_ids.append( support_point_ids.GetId( node_ordering[ i ] ) )
                cells.ReplaceCellAtId( cell_id, to_vtk_id_list( new_support_point_ids ) )
                counter_cells_reordered += 1
        if counter_cells_reordered > 0:
            reordering_stats[ "Types reordered" ].append( cell_type )
            reordering_stats[ "Number of cells reordered" ].append( counter_cells_reordered )
            cell_type_position: int = reordering_stats[ "Types non reordered" ].index( cell_type )
            reordering_stats[ "Number of cells non reordered" ][ cell_type_position ] -= counter_cells_reordered
            if reordering_stats[ "Number of cells non reordered" ][ cell_type_position ] == 0:
                reordering_stats[ "Types non reordered" ].pop( cell_type_position )
                reordering_stats[ "Number of cells non reordered" ].pop( cell_type_position )
    return ( new_mesh, reordering_stats )


def __check( mesh, options: Options ) -> Result:
    output_mesh, reordering_stats = reorder_nodes_to_new_mesh( mesh, options )
    write_mesh( output_mesh, options.vtk_output )
    return Result( output=options.vtk_output.output, reordering_stats=reordering_stats )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __check( mesh, options )
