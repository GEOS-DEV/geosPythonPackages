import numpy as np
import logging
from math import sqrt
from dataclasses import dataclass
from itertools import permutations
from typing import TypeAlias
from vtk import vtkCellSizeFilter, vtkIdList
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkCell, VTK_HEXAHEDRON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE,
                                            VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM )
from geos.mesh.doctor.checks.vtk_utils import VtkOutput, to_vtk_id_list, write_mesh, read_mesh


@dataclass( frozen=True )
class Options:
    vtk_output: VtkOutput
    cell_names_to_reorder: tuple[ str ]
    volume_to_reorder: str


@dataclass( frozen=True )
class Result:
    output: str
    reordering_stats: dict[ str, list[ int ] ]


Coordinates3D: TypeAlias = tuple[ float, float, float ]
Points3D: TypeAlias = tuple[ Coordinates3D ]
NodeOrdering: TypeAlias = tuple[ int ]

GEOS_ACCEPTED_TYPES = [ VTK_HEXAHEDRON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_PENTAGONAL_PRISM, VTK_HEXAGONAL_PRISM ]
VTK_TYPES_NUMBER_POINTS: dict[ int, tuple[ int, str ] ] = {
    VTK_TETRA: ( 4, "Tetrahedron" ),
    VTK_HEXAHEDRON: ( 8, "Hexahedron" ),
    VTK_PYRAMID: ( 5, "Pyramid" ),
    VTK_WEDGE: ( 6, "Wedge" ),
    VTK_PENTAGONAL_PRISM: ( 10, "Pentagonal prism" ),
    VTK_HEXAGONAL_PRISM: ( 12, "Hexagonal prism" )
}
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


def cell_ids_to_reorder_by_cell_type( mesh: vtkDataSet, options: Options ) -> dict[ int, np.array ]:
    """Create an array of cell_ids for each vtk_type chosen by the user when the cell pointed by the cell_id
    needs to be reorder.

    Args:
        mesh (vtkDataSet): A vtk grid.
        options (Options): Options defined by the user.

    Returns:
        dict[ int, np.array ]: { vtk_type1: np.array, ..., vtk_typeN: np.array }
    """
    all_cells_volume: np.array = compute_mesh_cells_volume( mesh )
    number_cells: int = mesh.GetNumberOfCells()
    useful_VTK_TYPEs: list[ int ] = [ NAME_TO_VTK_TYPE[ name ] for name in options.cell_names_to_reorder ]
    all_cells: np.array = np.zeros( ( number_cells, 3 ), dtype=int )  # col0: cell_ids, col1: vtk_type, col2: 0 or 1
    for cell_id in range( number_cells ):
        vtk_type: int = mesh.GetCellType( cell_id )
        all_cells[ cell_id ][ 0 ] = cell_id
        all_cells[ cell_id ][ 1 ] = vtk_type
        if vtk_type in useful_VTK_TYPEs:
            if is_cell_to_reorder( float( all_cells_volume[ cell_id ] ), options ):
                all_cells[ cell_id ][ 2 ] = 1
                continue
        all_cells[ cell_id ][ 2 ] = 0
    to_reorder: np.array = all_cells[ :, 2 ] == 1  # We need to remove rows where col2 == 0
    cells_to_reorder: np.array = all_cells[ to_reorder ][ :, [ 0, 1 ] ]  # col0: cell_ids, col1: vtk_type
    unique_values: np.array = np.unique( cells_to_reorder[ :, 1 ] )
    # Create a dictionary to store arrays of cells_id to reorder for each unique value
    cells_to_reorder_by_cell_type: dict[ int, np.array ] = {
        int( value ): cells_to_reorder[ cells_to_reorder[ :, 1 ] == value ][ :, 0 ]
        for value in unique_values
    }
    return cells_to_reorder_by_cell_type


def is_polygon_counterclockwise( points: Points3D, ref_pt: np.array ) -> bool:
    """Determines if a set of points in 3D are being ordered counterclockwise or clockwise
    with respect to a reference point of observation.

    Args:
        points (Points3D): A set of points in 3D coordinates.
        ref_pt (np.array): A point in 3D coordinates.

    Raises:
        ValueError: "Polygon checked is concave with points: {points}"

    Returns:
        bool: True if counterclockwise, False if clockwise.
    """
    nbr_pts: int = len( points )
    assert nbr_pts > 2
    points_array = np.array( points )
    polygon_centroid = np.mean( points_array, axis=0 )
    towards_ref_vect = ref_pt - polygon_centroid
    # Determine the projection plane
    abs_vect = np.abs( towards_ref_vect )
    if abs_vect[ 0 ] > abs_vect[ 1 ] and abs_vect[ 0 ] > abs_vect[ 2 ]:
        # Project onto the YZ-plane
        projected_points: list[ Coordinates3D ] = [ list( points[ i ] )[ 1: ] for i in range( nbr_pts ) ]
        is_sign_positive: bool = True if towards_ref_vect[ 0 ] < 0.0 else False
    elif abs_vect[ 1 ] > abs_vect[ 0 ] and abs_vect[ 1 ] > abs_vect[ 2 ]:
        # Project onto the XZ-plane
        projected_points = [ [ points[ i ][ 0 ], points[ i ][ 2 ] ] for i in range( nbr_pts ) ]
        is_sign_positive = True if towards_ref_vect[ 1 ] > 0.0 else False
    elif abs_vect[ 2 ] > abs_vect[ 0 ] and abs_vect[ 2 ] > abs_vect[ 1 ]:
        # Project onto the XY-plane
        projected_points = [ list( points[ i ] )[ :2 ] for i in range( nbr_pts ) ]
        is_sign_positive = True if towards_ref_vect[ 2 ] < 0.0 else False
    elif abs_vect[ 0 ] > abs_vect[ 2 ] and abs_vect[ 1 ] > abs_vect[ 2 ] and abs_vect[ 0 ] == abs_vect[ 1 ]:
        # Project onto the XZ-plane
        projected_points = [ [ points[ i ][ 0 ], points[ i ][ 2 ] ] for i in range( nbr_pts ) ]
        is_sign_positive = True if towards_ref_vect[ 1 ] > 0.0 else False
    elif abs_vect[ 0 ] > abs_vect[ 1 ] and abs_vect[ 2 ] > abs_vect[ 1 ] and abs_vect[ 0 ] == abs_vect[ 2 ]:
        # Project onto the YZ-plane
        projected_points = [ list( points[ i ] )[ 1: ] for i in range( nbr_pts ) ]
        is_sign_positive = True if towards_ref_vect[ 0 ] < 0.0 else False
    elif abs_vect[ 1 ] > abs_vect[ 0 ] and abs_vect[ 2 ] > abs_vect[ 0 ] and abs_vect[ 1 ] == abs_vect[ 2 ]:
        # Project onto the XY-plane
        projected_points = [ list( points[ i ] )[ :2 ] for i in range( nbr_pts ) ]
        is_sign_positive = True if towards_ref_vect[ 2 ] < 0.0 else False

    # translate the projected points to be with positive coordinates for det calculation
    min_x = min( [ x for x, y in projected_points ] )
    min_y = min( [ y for x, y in projected_points ] )
    if min_x < 0.0:
        for i in range( nbr_pts ):
            projected_points[ i ][ 0 ] += abs( min_x )
    if min_y < 0.0:
        for i in range( nbr_pts ):
            projected_points[ i ][ 1 ] += abs( min_y )

    turning_direction = None
    for v in range( nbr_pts ):
        A = projected_points[ v ]
        B = projected_points[ ( v + 1 ) % nbr_pts ]
        C = projected_points[ ( v + 2 ) % nbr_pts ]
        det = ( B[ 0 ] - A[ 0 ] ) * ( C[ 1 ] - A[ 1 ] ) - ( C[ 0 ] - A[ 0 ] ) * ( B[ 1 ] - A[ 1 ] )
        if det != 0:
            current_turn = 'ccw' if det > 0 else 'cw'
            if turning_direction is None:
                turning_direction = current_turn
            elif turning_direction != current_turn:
                raise ValueError( f"Polygon checked is concave with points: {points}." )
    if turning_direction == 'cw' and is_sign_positive:
        return True
    elif turning_direction == 'ccw' and not is_sign_positive:
        return True
    return False


def choose_correct_polygon( polygons: list[ Points3D ] ) -> Points3D:
    """When choosing between polygons, whose points are ordered counterclockwise (ccw) or clockwise (cw)
    AND that have more than 4 points, most of them will have an inappropriate shape that can generate concavity while
    still being ordered correctly ccw / cw (like with a set of 5 points supposed to look like a pentagon but end being
    the shape of a star).
    Therefore, to choose the correct polygon, we calculate the distance between each pair of "adjacent" points and try
    to minimize it to only choose the appropriate shape.

    Args:
        polygons (list[ Points3D ]): All possible permutations of a set of 5 points forming a ccw / cw polygon.

    Returns:
        Points3D: The correct polygon.
    """
    min_sum_distance: float = 1e10
    min_index: int = 0
    for i, polygon_pts in enumerate( polygons ):
        sum_distance: float = 0.0
        number_points: int = len( polygon_pts )
        for j in range( number_points ):
            A, B = polygon_pts[ j ], polygon_pts[ ( j + 1 ) % number_points ]
            sum_distance += sqrt( ( B[ 0 ] - A[ 0 ] )**2 + ( B[ 1 ] - A[ 1 ] )**2 + ( B[ 2 ] - A[ 2 ] )**2 )
        if sum_distance < min_sum_distance:
            min_sum_distance = sum_distance
            min_index = i
    return polygons[ min_index ]


def check_points_to_reorder( vtk_type: int ):
    """Check that the input tuple of points for any reorder function are of the right type,
    the correct number of points wrt to a VTK_TYPE and do not contain duplicates.

    Args:
        vtk_type (int): VTK
    """

    def decorator( reorder_func ):

        def wrapper( arg ):
            # Perform a check of the points to be reordered
            if not isinstance( arg, tuple ):
                raise ValueError( f"Points {arg} are not a tuple." )
            elif not isinstance( arg[ 0 ], tuple ):
                raise ValueError( f"Points {arg} are not a tuple[ tuple ]." )
            elif not isinstance( arg[ 0 ][ 0 ], float ):
                raise ValueError( f"Points {arg} are not a tuple[ tuple[ float ] ]." )
            elif len( arg[ 0 ] ) != 3:
                raise ValueError( f"Points {arg} coordinates are not in 3D." )

            try:
                number_points, element_name = VTK_TYPES_NUMBER_POINTS[ vtk_type ]
            except KeyError:
                raise ValueError( f"This VTK_TYPE '{vtk_type}' is not available for fix_elements_reorderings." )
            if len( set( arg ) ) != number_points:
                raise ValueError( f"Duplicated points were found in the cell {element_name} with points '{arg}'." +
                                  " Or you meant to use a reordering function for another type of VTK cell." +
                                  " Cannot perform reordering in this condition." )

            # Call the original function
            return reorder_func( arg )

        return wrapper

    return decorator


@check_points_to_reorder( VTK_TETRA )
def reorder_tetrahedron( points: Points3D ) -> Points3D:
    points_array: np.array = np.array( points )
    centroid: np.array = np.mean( points_array, axis=0 )
    face0_pts: Points3D = ( points[ 0 ], points[ 1 ], points[ 3 ] )  # face 0 in convention
    face1_pts: Points3D = ( points[ 1 ], points[ 2 ], points[ 3 ] )  # face 1 in convention
    is_face0_ccw: bool = is_polygon_counterclockwise( face0_pts, centroid )
    is_face1_ccw: bool = is_polygon_counterclockwise( face1_pts, centroid )
    if not is_face0_ccw and not is_face1_ccw:
        return points
    else:
        perms = list( permutations( points ) )[ 1: ]  # first permutation is not different from input, no need to use it
        for perm in perms:
            face0_pts = ( perm[ 0 ], perm[ 1 ], perm[ 3 ] )
            face1_pts = ( perm[ 1 ], perm[ 2 ], perm[ 3 ] )
            is_face0_ccw = is_polygon_counterclockwise( face0_pts, centroid )
            is_face1_ccw = is_polygon_counterclockwise( face1_pts, centroid )
            if is_face0_ccw or is_face1_ccw:
                continue
            else:
                correct_ordering: Points3D = ( face0_pts[ 0 ], face0_pts[ 1 ], face1_pts[ 1 ], face1_pts[ 2 ] )
                if len( set( correct_ordering ) ) == 4:
                    return correct_ordering
    raise ValueError( "Error when reordering the tetrahedron." )


# BIG HYPOTHESIS: The first 4 points of the pyramid represent its basis, while the 5th represent its apex.
@check_points_to_reorder( VTK_PYRAMID )
def reorder_pyramid( points: Points3D ) -> Points3D:
    points_array: np.array = np.array( points )
    centroid: np.array = np.mean( points_array, axis=0 )
    quad_pts: Points3D = ( points[ 0 ], points[ 1 ], points[ 2 ], points[ 3 ] )  # face 0 in convention
    # first we verify the verify the hypothesis that the 4 first points of the pyramid represent its basis
    try:
        is_quad_ccw: bool = is_polygon_counterclockwise( quad_pts, centroid )
    except ValueError:
        raise ValueError( "The first 4 points of your pyramid do not represent its base. No ordering possible." )

    if is_quad_ccw:
        return points
    else:
        perms = list( permutations( points[ :4 ] ) )[ 1: ]
        for perm in perms:
            try:
                is_quad_ccw = is_polygon_counterclockwise( perm, centroid )
            except ValueError:  # polygon created was concave
                continue
            if not is_quad_ccw:
                continue
            else:
                correct_ordering: Points3D = perm + ( points[ 4 ], )
                return correct_ordering
        raise ValueError( "Error when reordering the pyramid." )


# BIG HYPOTHESIS: The first 3 points define the first triangle face and the next 3 define the other triangle face.
# If it is not the case, the volume of the element created will be negative
@check_points_to_reorder( VTK_WEDGE )
def reorder_wedge( points: Points3D ) -> Points3D:
    points_array: np.array = np.array( points )
    centroid: np.array = np.mean( points_array, axis=0 )
    # we check that the two supposed triangle basis are oriented the same wrt to the centroid of the wedge
    initial_triangle0_pts: Points3D = ( points[ 0 ], points[ 1 ], points[ 2 ] )  # face 0 in convention
    initial_triangle1_pts: Points3D = ( points[ 3 ], points[ 4 ], points[ 5 ] )  # face 1 in convention
    is_triangle0_ccw: bool = is_polygon_counterclockwise( initial_triangle0_pts, centroid )
    is_triangle1_ccw: bool = is_polygon_counterclockwise( initial_triangle1_pts, centroid )
    if is_triangle0_ccw == is_triangle1_ccw:  # when correct, one should be true and the other false
        raise ValueError( "When looking at a wedge cell for reordering, we need to construct the two triangle faces" +
                          " that represent the basis. With respect to the centroid of the wedge, the faces are both" +
                          f" oriented in the same direction with points0 '{initial_triangle0_pts}' and with points1" +
                          f" '{initial_triangle1_pts}'. When respecting VTK convention, they should be oriented in" +
                          " opposite direction. This create a degenerated wedge that cannot be reordered." )
    # We check that the 3 quad faces are not concave to validate our hypothesis for triangle basis definition
    try:
        quad0 = ( points[ 0 ], points[ 3 ], points[ 4 ], points[ 1 ] )
        quad1 = ( points[ 1 ], points[ 4 ], points[ 5 ], points[ 2 ] )
        quad2 = ( points[ 2 ], points[ 5 ], points[ 3 ], points[ 0 ] )
        counter = 0
        for quad in ( quad0, quad1, quad2 ):
            if not is_polygon_counterclockwise( quad, centroid ):
                counter += 1
        if counter == 3:
            return points  # the wedge is already ordered correctly
    except ValueError:  # quad is concave
        raise ValueError( "When looking at a wedge cell for reordering, we need to construct the two triangle faces" +
                          " that represent the basis. When checking its geometry, the first 3 points" +
                          f"'{initial_triangle0_pts}' and/or last 3 points '{initial_triangle1_pts}' cannot" +
                          " represent the wedge basis because they created quad faces that are concave." +
                          " This create a degenerated wedge that cannot be reordered." )
    # We can now reorder one triangle face base to be counterclockwise.
    # Once we find the right ordering for the first one, we can deduce it for the second
    # We first need to find just one correct ordering of the first triangle face of the wedge
    if is_triangle0_ccw:
        perms = list( permutations( points[ :3 ] ) )[ 1: ]
        for perm in perms:
            is_triangle_ccw = is_polygon_counterclockwise( perm, centroid )
            if is_triangle_ccw:
                continue
            else:
                correct_triangle0_pts = perm
                break
    correct_triangle1_pts = list()
    for pt in correct_triangle0_pts:
        correct_index = initial_triangle0_pts.index( pt )
        correct_triangle1_pts.append( initial_triangle1_pts[ correct_index ] )
    correct_triangle1_pts = tuple( correct_triangle1_pts )
    # we verify that the 2nd base has the correct ordering
    if is_polygon_counterclockwise( correct_triangle1_pts, centroid ):
        # you just need to add the two triangle points together to form the wedge
        correct_ordering = correct_triangle0_pts + correct_triangle1_pts
        return correct_ordering
    else:
        raise ValueError( "Error when reordering the wedge." )


# BIG HYPOTHESIS: The first 4 points define a quad and the next 4 define another quad.
@check_points_to_reorder( VTK_HEXAHEDRON )
def reorder_hexahedron( points: Points3D ) -> Points3D:
    points_array: np.array = np.array( points )
    centroid: np.array = np.mean( points_array, axis=0 )
    initial_quad0_pts: Points3D = ( points[ 0 ], points[ 3 ], points[ 2 ], points[ 1 ] )  # face 4 in convention
    initial_quad1_pts: Points3D = ( points[ 4 ], points[ 5 ], points[ 6 ], points[ 7 ] )  # face 5 in convention
    try:
        is_quad0_ccw: bool = is_polygon_counterclockwise( initial_quad0_pts, centroid )
        is_quad1_ccw: bool = is_polygon_counterclockwise( initial_quad1_pts, centroid )
    except ValueError:  # quad is concave
        raise ValueError( "When looking at a hexahedron cell for reordering, we need to construct two quad faces" +
                          " that represent two faces that do not have a point common. When checking its geometry," +
                          f" the first 4 points '{initial_quad0_pts}' and/or last 4 points '{initial_quad1_pts}'" +
                          " cannot represent two hexahedron quad faces because they are concave." +
                          " This create a degenerated hexahedron that cannot be reordered." )
    if not is_quad0_ccw and not is_quad1_ccw:
        return points  # the hexahedron is already correctly ordered
    if is_quad0_ccw != is_quad1_ccw:  # when correct, both should be false or true
        raise ValueError( "When looking at a hexahedron cell for reordering, we need to construct two quad faces" +
                          " that represent two faces that do not have a point common. With respect to the centroid" +
                          " of the hexahedron, the faces are not both oriented in the same direction with points0" +
                          f" '{initial_quad0_pts}' and with points1 '{initial_quad1_pts}'. When respecting VTK" +
                          " convention, they both should be oriented in the same direction. This create a degenerated" +
                          " hexahedron that cannot be reordered." )
    # We can now reorder the first quad face base to be counterclockwise.
    # Once we find the right ordering for the first one, we can deduce it for the second
    # We first need to find just one correct ordering of the first quad face of the hexahedron
    if is_quad0_ccw:
        perms = list( permutations( ( points[ 0 ], points[ 3 ], points[ 2 ], points[ 1 ] ) ) )[ 1: ]
        for perm in perms:
            try:
                is_quad0_ccw = is_polygon_counterclockwise( ( perm[ 0 ], perm[ 3 ], perm[ 2 ], perm[ 1 ] ), centroid )
            except ValueError:
                continue
            if is_quad0_ccw:
                continue
            else:
                correct_quad0_pts = ( perm[ 3 ], perm[ 0 ], perm[ 1 ], perm[ 2 ] )
                break
    correct_quad1_pts = list()
    correspondance_table = { 0: 0, 3: 1, 2: 2, 1: 3 }
    for pt in correct_quad0_pts:
        correct_index = initial_quad0_pts.index( pt )
        correct_quad1_pts.append( initial_quad1_pts[ correspondance_table[ correct_index ] ] )
    correct_quad1_pts = tuple( correct_quad1_pts )
    # we verify that the 2nd quad has the correct ordering
    if not is_polygon_counterclockwise( correct_quad1_pts, centroid ):
        # you just need to add the two quad points together to form the hexahedron
        correct_ordering = correct_quad0_pts + correct_quad1_pts
        return correct_ordering
    else:
        raise ValueError( "Error when reordering the hexahedron." )


# BIG HYPOTHESIS: The first 5 points define a pentagon face and the next 5 define another pentagon face.
@check_points_to_reorder( VTK_PENTAGONAL_PRISM )
def reorder_pentagonal_prism( points: Points3D ) -> Points3D:
    points_array: np.array = np.array( points )
    centroid: np.array = np.mean( points_array, axis=0 )
    initial_penta0_pts: Points3D = ( points[ 0 ], points[ 4 ], points[ 3 ], points[ 2 ], points[ 1 ] )  # face 0
    initial_penta1_pts: Points3D = ( points[ 5 ], points[ 6 ], points[ 7 ], points[ 8 ], points[ 9 ] )  # face 1
    try:
        is_penta0_ccw: bool = is_polygon_counterclockwise( initial_penta0_pts, centroid )
        is_penta1_ccw: bool = is_polygon_counterclockwise( initial_penta1_pts, centroid )
    except ValueError:
        raise ValueError( "When looking at a pentagonal prism cell for reordering, we need to construct the two" +
                          " pentagon faces that represent the basis. When checking its geometry, the first 5 points" +
                          f"'{initial_penta0_pts}' and/or last 5 points '{initial_penta1_pts}' cannot" +
                          " represent the pentagonal prism basis because they created pentagon faces that are"
                          " concave. This create a degenerated pentagonal prism that cannot be reordered." )
    if not is_penta0_ccw and not is_penta1_ccw:
        return points  # the pentagonal prism is already correctly ordered
    if is_penta0_ccw != is_penta1_ccw:  # when correct, both should be false or true
        raise ValueError( "When looking at a pentagonal prism cell for reordering, we need to construct the two" +
                          " pentagon faces that represent the basis. With respect to the centroid of the wedge, the" +
                          f" faces are oriented in opposite direction with points0 '{initial_penta0_pts}' and" +
                          f" with points1 '{initial_penta1_pts}'. When respecting VTK convention, they should be" +
                          " oriented in the same direction. This create a degenerated pentagonal prism that cannot be" +
                          " reordered." )
    # We can now reorder the first penta face base to be counterclockwise.
    # Once we find the right ordering for the first one, we can deduce it for the second
    # We first need to find just one correct ordering of the first penta face of the pentagonal prism
    possible_penta0_polygons: list[ Points3D ] = list()
    if is_penta0_ccw:
        perms = list( permutations( ( points[ 0 ], points[ 4 ], points[ 3 ], points[ 2 ], points[ 1 ] ) ) )[ 1: ]
        for perm in perms:
            try:
                is_penta0_ccw = is_polygon_counterclockwise( ( perm[ 0 ], perm[ 4 ], perm[ 3 ], perm[ 2 ], perm[ 1 ] ),
                                                             centroid )
            except ValueError:
                continue
            if is_penta0_ccw:
                continue
            else:
                possible_penta0_polygons.append( ( perm[ 0 ], perm[ 3 ], perm[ 1 ], perm[ 4 ], perm[ 2 ] ) )
    correct_penta0_pts: Points3D = choose_correct_polygon( possible_penta0_polygons )
    correct_penta1_pts = list()
    correspondance_table = { 0: 0, 4: 1, 3: 2, 2: 3, 1: 4 }
    for pt in correct_penta0_pts:
        correct_index = initial_penta0_pts.index( pt )
        correct_penta1_pts.append( initial_penta1_pts[ correspondance_table[ correct_index ] ] )
    correct_penta1_pts = tuple( correct_penta1_pts )
    # we verify that the 2nd penta has the correct ordering
    if not is_polygon_counterclockwise( correct_penta1_pts, centroid ):
        # you just need to add the two penta points together to form the pentagonal prism
        correct_ordering = correct_penta0_pts + correct_penta1_pts
        return correct_ordering
    else:
        raise ValueError( "Error when reordering the pentagonal prism." )


# BIG HYPOTHESIS: The first 6 points define a hexagon face and the next 6 define another hexagon face.
@check_points_to_reorder( VTK_HEXAGONAL_PRISM )
def reorder_hexagonal_prism( points: Points3D ) -> Points3D:
    points_array: np.array = np.array( points )
    centroid: np.array = np.mean( points_array, axis=0 )
    initial_hexa0_pts: Points3D = ( points[ 0 ], points[ 5 ], points[ 4 ], points[ 3 ], points[ 2 ], points[ 1 ] )
    initial_hexa1_pts: Points3D = ( points[ 6 ], points[ 7 ], points[ 8 ], points[ 9 ], points[ 10 ], points[ 11 ] )
    try:
        is_hexa0_ccw: bool = is_polygon_counterclockwise( initial_hexa0_pts, centroid )
        is_hexa1_ccw: bool = is_polygon_counterclockwise( initial_hexa1_pts, centroid )
    except ValueError:
        raise ValueError( "When looking at a hexagonal prism cell for reordering, we need to construct the two" +
                          " hexagon faces that represent the basis. When checking its geometry, the first 6 points" +
                          f"'{initial_hexa0_pts}' and/or last 6 points '{initial_hexa1_pts}' cannot" +
                          " represent the hexagonal prism basis because they created hexagon faces that are" +
                          " concave. This create a degenerated hexagonal prism that cannot be reordered." )
    if not is_hexa0_ccw and not is_hexa1_ccw:
        return points  # the hexagonal prism is already correctly ordered
    if is_hexa0_ccw != is_hexa1_ccw:  # when correct, both should be false or true
        raise ValueError( "When looking at a hexagonal prism cell for reordering, we need to construct the two" +
                          " hexagon faces that represent the basis. With respect to the centroid of the wedge, the" +
                          f" faces are oriented in opposite direction with points0 '{initial_hexa0_pts}' and" +
                          f" with points1 '{initial_hexa1_pts}'. When respecting VTK convention, they should be" +
                          " oriented in the same direction. This create a degenerated hexagonal prism that cannot be" +
                          " reordered." )
    # We can now reorder the first hexagon face base to be counterclockwise.
    # Once we find the right ordering for the first one, we can deduce it for the second
    # We first need to find just one correct ordering of the first hexagon face of the hexagonal prism
    possible_hexa0_polygons: list[ Points3D ] = list()
    if is_hexa0_ccw:
        perms = list( permutations(
            ( points[ 0 ], points[ 5 ], points[ 4 ], points[ 3 ], points[ 2 ], points[ 1 ] ) ) )[ 1: ]
        for perm in perms:
            try:
                is_hexa0_ccw = is_polygon_counterclockwise(
                    ( perm[ 0 ], perm[ 5 ], perm[ 4 ], perm[ 3 ], perm[ 2 ], perm[ 1 ] ), centroid )
            except ValueError:
                continue
            if is_hexa0_ccw:
                continue
            else:
                possible_hexa0_polygons.append( ( perm[ 0 ], perm[ 3 ], perm[ 1 ], perm[ 4 ], perm[ 2 ], perm[ 5 ] ) )
    correct_hexa0_pts: Points3D = choose_correct_polygon( possible_hexa0_polygons )
    correct_hexa1_pts = list()
    correspondance_table = { 0: 0, 5: 1, 4: 2, 3: 3, 2: 4, 1: 5 }
    for pt in correct_hexa0_pts:
        correct_index = initial_hexa0_pts.index( pt )
        correct_hexa1_pts.append( initial_hexa1_pts[ correspondance_table[ correct_index ] ] )
    correct_hexa1_pts = tuple( correct_hexa1_pts )
    # we verify that the 2nd hexagon has the correct ordering
    if not is_polygon_counterclockwise( correct_hexa1_pts, centroid ):
        # you just need to add the two hexagon points together to form the hexagonal prism
        correct_ordering = correct_hexa0_pts + correct_hexa1_pts
        return correct_ordering
    else:
        raise ValueError( "Error when reordering the hexagonal prism." )


REORDERING_FUNCTION: dict[ int, any ] = {
    VTK_TETRA: reorder_tetrahedron,
    VTK_PYRAMID: reorder_pyramid,
    VTK_WEDGE: reorder_wedge,
    VTK_HEXAHEDRON: reorder_hexahedron,
    VTK_PENTAGONAL_PRISM: reorder_pentagonal_prism,
    VTK_HEXAGONAL_PRISM: reorder_hexagonal_prism
}


def cell_point_ids_ordering_method( cell: vtkCell, vtk_type: int ) -> tuple[ tuple[ int ], bool ]:
    """For a vtkCell, gives back the correct ordering of point ids respecting the VTK convention.
    If the ordering is the same as the one given as input, specifies it by returning False as a second value ; True
    if the ordering is different and therefore needs to be applied later on in other algorithms.

    Args:
        cell (vtkCell): A vtk cell.
        vtk_type (int): Int value describing the type of vtk cell to reorder.

    Returns:
        tuple[ tuple[ int ], bool ]: ( The ordering method, if_ordering_is_different )
    """
    points: list[ Coordinates3D ] = list()
    for v in range( cell.GetNumberOfPoints() ):
        points.append( cell.GetPoints().GetPoint( v ) )
    initial_cell_points: Points3D = tuple( points )
    reordered_points: Points3D = REORDERING_FUNCTION[ vtk_type ]( initial_cell_points )
    reordering_method: list[ int ] = list()
    for reorder_point in reordered_points:
        matching_id: int = initial_cell_points.index( reorder_point )
        reordering_method.append( matching_id )
    no_reordering = [ i for i in range( len( reordering_method ) ) ]
    change_order = not no_reordering == reordering_method
    return ( tuple( reordering_method ), change_order )


def reorder_points_to_new_mesh( old_mesh: vtkDataSet, options: Options ) -> tuple:
    reordering_stats: dict[ str, list[ any ] ] = {
        "Types reordered": list(),
        "Number of cells reordered": list(),
        "Types non reordered because ordering is already correct": list(),
        "Number of cells non reordered because ordering is already correct": list(),
        "Types non reordered because of errors": list(),
        "Number of cells non reordered because of errors": list(),
        "Error message given": list()
    }
    # 1st step: find the correct ordering method for each vtk type. This type should be unique because a mesh cannot
    # be built with cells that use different points ordering, only one per cell type
    cell_ids_to_reorder: dict[ int, np.array ] = cell_ids_to_reorder_by_cell_type( old_mesh, options )
    ordering_method_per_vtk_type: dict[ int, tuple[ int ] ] = dict()
    for vtk_type, cell_ids in cell_ids_to_reorder.items():
        cell_to_check: vtkCell = old_mesh.GetCell( cell_ids[ 0 ] )
        cell_counter = 1
        try:
            ordering_method, change_order = cell_point_ids_ordering_method( cell_to_check, vtk_type )
            while change_order == False and cell_counter < cell_ids.size:
                cell_to_check = old_mesh.GetCell( cell_ids[ cell_counter ] )
                ordering_method, change_order = cell_point_ids_ordering_method( cell_to_check, vtk_type )
                cell_counter += 1
            if change_order:
                ordering_method_per_vtk_type[ vtk_type ] = ordering_method
                reordering_stats[ "Types reordered" ].append( VTK_TYPE_TO_NAME[ vtk_type ] )
                reordering_stats[ "Number of cells reordered" ].append( cell_ids.size )
            else:
                ordering_method_per_vtk_type[ vtk_type ] = ordering_method
                # yapf: disable
                reordering_stats[ "Types non reordered because ordering is already correct" ].append( VTK_TYPE_TO_NAME[ vtk_type ] )
                reordering_stats[ "Number of cells non reordered because ordering is already correct" ].append( cell_ids.size )
                # yapf: enable
        except ValueError as err_msg:
            reordering_stats[ "Types non reordered because of errors" ].append( VTK_TYPE_TO_NAME[ vtk_type ] )
            reordering_stats[ "Number of cells non reordered because of errors" ].append( cell_ids.size )
            reordering_stats[ "Error message given" ].append( err_msg )

    # 2nd step: once the ordering has been found for each vtk type, we can modify the ordering of the cells
    # of this type if they have to be reordered
    new_mesh = old_mesh.NewInstance()
    new_mesh.CopyStructure( old_mesh )
    new_mesh.CopyAttributes( old_mesh )
    cells = new_mesh.GetCells()
    for vtk_type, new_ordering in ordering_method_per_vtk_type.items():
        cell_ids: np.array = cell_ids_to_reorder[ vtk_type ]
        for cell_id in cell_ids:
            support_point_ids = vtkIdList()
            cells.GetCellAtId( cell_id, support_point_ids )
            new_support_point_ids: list[ int ] = list()
            for matching_id in new_ordering:
                new_support_point_ids.append( support_point_ids.GetId( matching_id ) )
            cells.ReplaceCellAtId( cell_id, to_vtk_id_list( new_support_point_ids ) )

    return ( new_mesh, reordering_stats )


def __check( mesh, options: Options ) -> Result:
    output_mesh, reordering_stats = reorder_points_to_new_mesh( mesh, options )
    write_mesh( output_mesh, options.vtk_output )
    return Result( output=options.vtk_output.output, reordering_stats=reordering_stats )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __check( mesh, options )
