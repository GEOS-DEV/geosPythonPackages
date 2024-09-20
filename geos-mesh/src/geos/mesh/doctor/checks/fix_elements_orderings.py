import numpy as np
import logging
from dataclasses import dataclass
from itertools import permutations
from vtk import vtkCellSizeFilter
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkCell, VTK_HEXAHEDRON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE,
                                            VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM )
from geos.mesh.doctor.checks.vtk_utils import VtkOutput, vtk_iter, to_vtk_id_list, write_mesh, read_mesh


@dataclass( frozen=True )
class Options:
    vtk_output: VtkOutput
    cell_names_to_reorder: tuple[ str ]
    volume_to_reorder: str


@dataclass( frozen=True )
class Result:
    output: str
    reordering_stats: dict[ str, list[ int ] ]


GEOS_ACCEPTED_TYPES = [ VTK_HEXAHEDRON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM ]
# the number of different nodes that needs to be entered in parsing when dealing with a specific vtk element
NAME_TO_VTK_TYPE = {
    "Hexahedron": VTK_HEXAHEDRON,
    "Tetrahedron": VTK_TETRA,
    "Pyramid": VTK_PYRAMID,
    "Wedge": VTK_WEDGE,
    "Prism5": VTK_PENTAGONAL_PRISM,
    "Prism6": VTK_HEXAGONAL_PRISM
}
VTK_TYPE_TO_NAME = { vtk_type: name for name, vtk_type in NAME_TO_VTK_TYPE.items() }


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


def get_cell_types_and_number( mesh: vtkDataSet ) -> tuple[ list[ int ] ]:
    """Gets the cell type for every cell of a mesh and the amount for each cell type.

    Args:
        mesh (vtkDataSet): A vtk grid.

    Raises:
        ValueError: "Invalid type '{cell_type}' for GEOS is in the mesh. Dying ..."

    Returns:
        tuple[ list[ int ] ]: ( unique_cell_types, total_per_cell_types )
    """
    number_cells: int = mesh.GetNumberOfCells()
    all_cells_type: np.array = np.ones( number_cells, dtype=int )
    for cell_id in range( number_cells ):
        all_cells_type[ cell_id ] = mesh.GetCellType( cell_id )
    unique_cell_types, total_per_cell_types = np.unique( all_cells_type, return_counts=True )
    unique_cell_types, total_per_cell_types = unique_cell_types.tolist(), total_per_cell_types.tolist()
    for cell_type in unique_cell_types:
        if cell_type not in GEOS_ACCEPTED_TYPES:
            err_msg: str = f"Invalid type '{cell_type}' for GEOS is in the mesh. Dying ..."
            logging.error( err_msg )
            raise ValueError( err_msg )
    return ( unique_cell_types, total_per_cell_types )


def is_cell_to_reorder( cell_volume: str, options: Options ) -> bool:
    """Check if the volume of vtkCell qualifies the cell to be reordered.

    Args:
        cell_volume (float): The volume of a vtkCell.
        options (Options): Options defined by the user.

    Returns:
        bool: True if cell needs to be reordered
    """
    if options.volume_to_reorder == "all":
        return True
    if cell_volume == 0.0:
        return True
    sign_of_cell_volume: int = int( cell_volume / abs( cell_volume ) )
    if options.volume_to_reorder == "positive" and sign_of_cell_volume == 1:
        return True
    elif options.volume_to_reorder == "negative" and sign_of_cell_volume == -1:
        return True
    return False


def are_face_nodes_counterclockwise( face: any ) -> bool:
    """Checks if the nodes of a face are ordered counterclockwise when looking at the plan created by the face.

    Args:
        face (any): Face of a vtkCell.

    Returns:
        bool: True if counterclockwise, False instead.
    """
    face_points = face.GetPoints()
    number_points = face_points.GetNumberOfPoints()
    if number_points < 3:
        err_msg = f"The face has less than 3 nodes which is invalid."
        logging.error( err_msg )
        raise ValueError( err_msg )
    # first calculate the normal vector of the face
    a = np.array( face_points.GetPoint( 0 ) )
    b = np.array( face_points.GetPoint( 1 ) )
    c = np.array( face_points.GetPoint( 2 ) )
    AB = b - a
    AC = c - a
    normal = np.cross( AB, AC )

    # then calculate the vector cross products sum of all points of the face with a random point P
    # from discussion https://math.stackexchange.com/questions/2152623/determine-the-order-of-a-3d-polygon
    P = np.array( [ 0.0, 0.0, 0.0 ] )  # P position does not change the value of sum
    all_points = [ np.array( face_points.GetPoint( v ) ) for v in range( number_points ) ]
    vector_sum = np.array( [ 0.0, 0.0, 0.0 ] )
    for i in range( number_points ):
        PAi = all_points[ i % number_points ] - P
        PAiplus1 = all_points[ ( i + 1 ) % number_points ] - P
        vector_sum += np.cross( PAi, PAiplus1 )
    vector_sum = vector_sum / 2  # needs to be half

    # if dot product is positive, the nodes are ordered counterclockwise
    if np.dot( vector_sum, normal ) > 0.0:
        return True
    return False


def valid_cell_point_ids_ordering( cell: vtkCell ) -> list[ int ]:
    """Returns the valid order of point ids of a cell that respect counterclockwise convention of each face.

    Args:
        cell (vtkCell): A cell of vtk grid.

    Raises:
        ValueError: "No node ids permutation made the face nodes to be ordered counterclockwise."

    Returns:
        list[ int ]: [ pt_id0, pt_id2, pt_id1, ..., pt_idN ]
    """
    initial_ids_order: list[ int ] = list( vtk_iter( cell.GetPointIds() ) )
    valid_points_id: list[ int ] = initial_ids_order.copy()

    for face_id in range( cell.GetNumberOfFaces() ):
        face = cell.GetFace( face_id )
        if are_face_nodes_counterclockwise( face ):
            continue  # the face nodes respect the convention so continue to next face

        reordered = False
        initial_ids: list[ int ] = [ face.GetPointId( i ) for i in range( face.GetNumberOfPoints() ) ]
        initial_coords: list[ float ] = [ face.GetPoints().GetPoint( v ) for v in range( face.GetNumberOfPoints() ) ]
        for permutation_ids in permutations( initial_ids ):
            for i, node_id in enumerate( permutation_ids ):
                face.GetPointIds().SetId( i, node_id )
                face.GetPoints().SetPoint( i, initial_coords[ initial_ids.index( node_id ) ] )

            if are_face_nodes_counterclockwise( face ):  # the correct permutation was found
                for j, initial_id in enumerate( initial_ids ):
                    if initial_id != permutation_ids[ j ]:
                        valid_points_id[ initial_ids_order.index( initial_id ) ] = permutation_ids[ j ]
                reordered = True
                break

        if not reordered:
            err_msg = ( f"For face with nodes id '{initial_ids}', that corresponds to coordinates '{initial_coords}'" +
                        ", no node ids permutation made the face nodes to be ordered counterclockwise." )
            logging.error( err_msg )
            raise ValueError( err_msg )

    return valid_points_id


def reorder_nodes_to_new_mesh( old_mesh: vtkDataSet, options: Options ) -> tuple:
    """From an old mesh, creates a new one where certain cell nodes are reordered to obtain a correct volume.

    Args:
        old_mesh (vtkDataSet): A vtk grid needing nodes to be reordered.
        options (Options): Options defined by the user.

    Returns:
        tuple: ( vtkDataSet, reordering_stats )
    """
    unique_cell_types, total_per_cell_types = get_cell_types_and_number( old_mesh )
    unique_cell_names: list[ str ] = [ VTK_TYPE_TO_NAME[ vtk_type ] for vtk_type in unique_cell_types ]
    names_with_totals: dict[ str, int ] = { n: v for n, v in zip( unique_cell_names, total_per_cell_types ) }
    # sorted dict allow for sorted output of reordering_stats
    names_with_totals_sorted: dict[ str, int ] = dict( sorted( names_with_totals.items() ) )
    useful_VTK_TYPEs: list[ int ] = [ NAME_TO_VTK_TYPE[ name ] for name in options.cell_names_to_reorder ]
    all_cells_volume: np.array = compute_mesh_cells_volume( old_mesh )
    # a new mesh with the same data is created from the old mesh
    new_mesh: vtkDataSet = old_mesh.NewInstance()
    new_mesh.CopyStructure( old_mesh )
    new_mesh.CopyAttributes( old_mesh )
    cells = new_mesh.GetCells()
    # Statistics on how many cells have or have not been reordered
    reordering_stats: dict[ str, list[ any ] ] = {
        "Types reordered": list(),
        "Number of cells reordered": list(),
        "Types non reordered": list( names_with_totals_sorted.keys() ),
        "Number of cells non reordered": list( names_with_totals_sorted.values() )
    }
    counter_cells_reordered: dict[ str, int ] = { name: 0 for name in options.cell_names_to_reorder }
    # sorted dict allow for sorted output of reordering_stats
    ounter_cells_reordered_sorted: dict[ str, int ] = dict( sorted( counter_cells_reordered.items() ) )
    # Reordering operations
    for cell_id in range( new_mesh.GetNumberOfCells() ):
        vtk_type: int = new_mesh.GetCellType( cell_id )
        if vtk_type in useful_VTK_TYPEs:  # only cell types specified are checked
            if is_cell_to_reorder( float( all_cells_volume[ cell_id ] ), options ):
                cell_name: str = VTK_TYPE_TO_NAME[ vtk_type ]
                point_ids_ordering: list[ int ] = valid_cell_point_ids_ordering( new_mesh.GetCell( cell_id ) )
                cells.ReplaceCellAtId( cell_id, to_vtk_id_list( point_ids_ordering ) )
                ounter_cells_reordered_sorted[ cell_name ] += 1
    # Calculation of stats
    for cell_name_reordered, amount in ounter_cells_reordered_sorted.items():
        if amount > 0:
            reordering_stats[ "Types reordered" ].append( cell_name_reordered )
            reordering_stats[ "Number of cells reordered" ].append( amount )
            index_non_reordered: int = reordering_stats[ "Types non reordered" ].index( cell_name_reordered )
            reordering_stats[ "Number of cells non reordered" ][ index_non_reordered ] -= amount
            if reordering_stats[ "Number of cells non reordered" ][ index_non_reordered ] == 0:
                reordering_stats[ "Types non reordered" ].pop( index_non_reordered )
                reordering_stats[ "Number of cells non reordered" ].pop( index_non_reordered )
    return ( new_mesh, reordering_stats )


def __check( mesh, options: Options ) -> Result:
    output_mesh, reordering_stats = reorder_nodes_to_new_mesh( mesh, options )
    write_mesh( output_mesh, options.vtk_output )
    return Result( output=options.vtk_output.output, reordering_stats=reordering_stats )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __check( mesh, options )
