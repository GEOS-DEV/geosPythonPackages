from dataclasses import dataclass
from sys import exit
from os import path, access, W_OK
import logging
import numpy as np
from typing import (
    List,
    Dict,
    Set,
    FrozenSet,
)

from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkCell
from vtk import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import (
    vtkDataSet,
    VTK_HEXAHEDRON,
    VTK_TETRA,
    VTK_PYRAMID,
    VTK_WEDGE,
    VTK_VOXEL,
    VTK_PENTAGONAL_PRISM,
    VTK_HEXAGONAL_PRISM,
)

from . import vtk_utils
from .vtk_utils import (
    to_vtk_id_list,
    VtkOutput,
)


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
    VTK_PENTAGONAL_PRISM: "Pentagonal prism",
    VTK_HEXAGONAL_PRISM: "Pentagonal prism",
}


def plan_normal_from_3_points( p1: tuple[ float ], p2: tuple[ float ], p3: tuple[ float ] ) -> np.array:
    """Calculate the normal vector of the plan created by 3 points.

    Args:
        p1 (tuple[ float ]): ( point1_x, point1_y, point1_z )
        p2 (tuple[ float ]): ( point2_x, point2_y, point2_z )
        p3 (tuple[ float ]): ( point3_x, point3_y, point3_z )

    Returns:
        np.array: Normal vector of the plan composed of those 3 points.
    """
    try:
        for point in [ p1, p2, p3 ]:
            assert len( point ) == 3
    except Exception as e:
        logging.error( "Points entered are not tuple of 3D coordinates. Dying ..." )
        exit( 1 )
    point1, point2, point3 = [ np.array( p ) for p in [ p1, p2, p3 ] ]
    vector1: np.array = point3 - point1
    vector2: np.array = point2 - point1
    plan_normal: np.array = np.cross( vector1, vector2 )
    return plan_normal


def get_cell_nodes_coordinates( cell: vtkCell ) -> list[ tuple[ float ] ]:
    """Returns the tuple of coordinates for every node of a vtkCell element.

    Args:
        cell (vtkCell): A vtkCell.

    Returns:
        list[ tuple[ float ] ]: [ ( node0_x, node0_y, node0_z ), ..., ( nodeN_x, nodeN_y, nodeN_z ) ]
    """
    nodes_coordinates: list[ tuple[ float ] ] = []
    for v in cell.GetNumberOfPoints():
        nodes_coordinates.append( cell.GetPoints().GetPoint( v ) )
    return nodes_coordinates


def get_sign_of_cell_volume( cell: vtkCell ) -> int:
    """For a vtkCell, tells if a volume is positive, negative or null based on vtk cell convention for nodes ordering.
    DISCLAIMER: only works for VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON,
    VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM

    Args:
        cell (vtkCell): A vtkCell.

    Returns:
        int: 1 if volume > 0.0, -1 elif volume < 0.0, else 0.
    """
    cell_type_volume_calculation: dict[ int, any ] = { VTK_TETRA: vtkMeshQuality.TetVolume,
                                                       VTK_PYRAMID: vtkMeshQuality.PyramidVolume,
                                                       VTK_WEDGE: vtkMeshQuality.WedgeVolume,
                                                       VTK_HEXAHEDRON: vtkMeshQuality.HexVolume }
    cell_type: int = cell.GetCellType()
    if cell_type in cell_type_volume_calculation:
        volume: float = cell_type_volume_calculation[ cell_type ]( cell )
        return int( volume / abs(volume) ) if volume != 0 else 0  # needs to return -1, 0 or 1
    elif cell_type in [ VTK_VOXEL, VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM ]:
        points: list[ tuple[float] ] = get_cell_nodes_coordinates( cell )
        midpoint: int = len( points ) // 2
        plan1_nodes, plan2_nodes = points[ :midpoint ], points[ midpoint: ]
        normal_plan1: np.array = plan_normal_from_3_points(plan1_nodes[0], plan1_nodes[1], plan1_nodes[2])
        normal_plan2: np.array = plan_normal_from_3_points(plan2_nodes[0], plan2_nodes[1], plan2_nodes[2])
        dot_product: float = np.dot( normal_plan1, normal_plan2 )
        return int( dot_product / abs(dot_product) ) if dot_product != 0 else 0  # needs to return -1, 0 or 1
    else:
        logging.error( f"Invalid cell type number '{cell_type}' encountered. Dying ..." )
        exit( 1 )


def is_cell_to_reorder( cell: vtkCell, volume_to_reorder: str ) -> bool:
    """Check if a vtkCell needs to be reordered.

    Args:
        cell (vtkCell): A vtkCell.
        volume_to_reorder (str): Condition imposed in Options.volume_to_reorder

    Returns:
        bool: True if cell needs to be reordered
    """
    if volume_to_reorder == "all":
        return True
    sign_of_cell_volume: int = get_sign_of_cell_volume( cell )
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
    all_cells_type: np.array = np.zeros( ( number_cells, 1 ), dtype=int )
    for cell_id in range( number_cells ):
        all_cells_type = mesh.GetCellType( cell_id )
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
    for cell_type in options.cell_type_to_ordering.keys():
        sub_array = np.where( all_cells_type == cell_type )[ 0 ]
        cell_ids_to_check[ cell_type ] = sub_array
        all_cells_type = all_cells_type[ all_cells_type != cell_type ]
    return cell_ids_to_check


def reorder_nodes_to_new_mesh( old_mesh: vtkDataSet, options: Options ) -> tuple:
    """From an old mesh, creates a new one where certain cell nodes are reordered to obtain a correct volume.

    Args:
        old_mesh (vtkDataSet): A vtk grid needing nodes to be reordered.
        options (Options): Options defined by the user.

    Returns:
        tuple: ( vtkDataSet, reordering_stats )
    """
    # a new mesh with the same data is created from the old mesh
    new_mesh: vtkDataSet = old_mesh.NewInstance()
    new_mesh.CopyStructure( old_mesh )
    new_mesh.CopyAttributes( old_mesh )
    cells = new_mesh.GetCells()
    # this part will get the cell ids that need to be verified and if invalid, to have their nodes be reodered
    all_cells_type: np.array = get_all_cells_type( new_mesh )
    cell_ids_to_check: dict[ int, np.array ] = get_cell_ids_to_check( old_mesh, options )
    unique_cell_types, total_per_cell_types = np.unique( all_cells_type, return_counts=True )
    unique_cell_types, total_per_cell_types = unique_cell_types.tolist(), total_per_cell_types.tolist()
    unique_cell_types_names: list[ str ] = [ cell_type_names[ i ] for i in unique_cell_types ]
    reordering_stats: dict[ str, list[ any ] ] = {
        "Types reordered": [],
        "Number of cells reordered": [],
        "Types non reordered": unique_cell_types_names,
        "Number of cells non reordered": total_per_cell_types
    }
    for cell_type, cell_ids in cell_ids_to_check:
        counter_cells_reordered: int = 0
        for cell_id in cell_ids:
            cell: vtkCell = new_mesh.GetCell( cell_id )
            if is_cell_to_reorder( cell, options.volume_to_reorder ):
                support_point_ids = vtkIdList()
                cells.GetCellAtId( cell_id, support_point_ids )
                new_support_point_ids = []
                node_ordering: list[ int ] = options.cell_type_to_ordering[ cell_type ]
                for i in range( len( node_ordering ) ):
                    new_support_point_ids.append( support_point_ids.GetId( node_ordering[ i ] ) )
                cells.ReplaceCellAtId( cell_id, to_vtk_id_list( new_support_point_ids ) )
                counter_cells_reordered += 1
        # for reordering_stats
        cell_type_name: str = cell_type_names[ cell_type ]
        if counter_cells_reordered > 0:
            reordering_stats[ "Types reordered" ].append( cell_type_name )
            reordering_stats[ "Number of cells reordered" ].append( counter_cells_reordered )
            cell_type_position: int = reordering_stats[ "Types non reordered" ].index( cell_type_name )
            reordering_stats[ "Number of cells non reordered" ][ cell_type_position ] -= counter_cells_reordered
            if reordering_stats[ "Number of cells non reordered" ][ cell_type_position ] == 0:
                reordering_stats[ "Types non reordered" ].pop( cell_type_position )
                reordering_stats[ "Number of cells non reordered" ].pop( cell_type_position )
    return ( new_mesh, reordering_stats )


def __check( mesh, options: Options ) -> Result:
    output_mesh, reordering_stats = reorder_nodes_to_new_mesh( mesh, options )
    vtk_utils.write_mesh( output_mesh, options.vtk_output )
    return Result( output=options.vtk_output.output, reordering_stats=reordering_stats )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = vtk_utils.read_mesh( vtk_input_file )
    return __check( mesh, options )
