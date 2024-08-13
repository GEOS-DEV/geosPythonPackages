from dataclasses import dataclass
import logging
from typing import (
    Tuple,
    Iterable,
    Iterator,
    Sequence,
)

import numpy

import pytest

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkQuad,
    VTK_HEXAHEDRON,
    VTK_POLYHEDRON,
    VTK_QUAD,
)
from vtkmodules.util.numpy_support import ( numpy_to_vtk, vtk_to_numpy )

from geos.mesh.doctor.checks.vtk_utils import (
    to_vtk_id_list, )

from geos.mesh.doctor.checks.check_fractures import format_collocated_nodes
from geos.mesh.doctor.checks.generate_cube import build_rectilinear_blocks_mesh, XYZ
from geos.mesh.doctor.checks.generate_fractures import __split_mesh_on_fracture, Options, FracturePolicy


@dataclass( frozen=True )
class TestResult:
    __test__ = False
    main_mesh_num_points: int
    main_mesh_num_cells: int
    fracture_mesh_num_points: int
    fracture_mesh_num_cells: int


@dataclass( frozen=True )
class TestCase:
    __test__ = False
    input_mesh: vtkUnstructuredGrid
    options: Options
    collocated_nodes: Sequence[ Sequence[ int ] ]
    result: TestResult


class QuadCoords:

    def __init__( self, p1, p2, p3, p4 ):
        self.p1: tuple[ float ] = p1
        self.p2: tuple[ float ] = p2
        self.p3: tuple[ float ] = p3
        self.p4: tuple[ float ] = p4
        self.__coordinates: list[ tuple[ float ] ] = [ self.p1, self.p2, self.p3, self.p4 ]

    def get_coordinates( self ):
        return self.__coordinates


def __build_test_case( xs: Tuple[ numpy.ndarray, numpy.ndarray, numpy.ndarray ],
                       attribute: Iterable[ int ],
                       field_values: Iterable[ int ] = None,
                       policy: FracturePolicy = FracturePolicy.FIELD ):
    xyz = XYZ( *xs )

    mesh: vtkUnstructuredGrid = build_rectilinear_blocks_mesh( ( xyz, ) )

    ref = numpy.array( attribute, dtype=int )
    if policy == FracturePolicy.FIELD:
        assert len( ref ) == mesh.GetNumberOfCells()
    attr = numpy_to_vtk( ref )
    attr.SetName( "attribute" )
    mesh.GetCellData().AddArray( attr )

    if field_values is None:
        fv = frozenset( attribute )
    else:
        fv = frozenset( field_values )

    options = Options( policy=policy, field="attribute", field_values=fv, vtk_output=None, vtk_fracture_output=None )
    return mesh, options


# Utility class to generate the new indices of the newly created collocated nodes.
class Incrementor:

    def __init__( self, start ):
        self.__val = start

    def next( self, num: int ) -> Iterable[ int ]:
        self.__val += num
        return range( self.__val - num, self.__val )


def __generate_test_data() -> Iterator[ TestCase ]:
    two_nodes = numpy.arange( 2, dtype=float )
    three_nodes = numpy.arange( 3, dtype=float )
    four_nodes = numpy.arange( 4, dtype=float )

    # Split in 2
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), ( 0, 1, 0, 1, 0, 1, 0, 1 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=tuple( map( lambda i: ( 1 + 3 * i, 27 + i ), range( 9 ) ) ),
                    result=TestResult( 9 * 4, 8, 9, 4 ) )

    # Split in 3
    inc = Incrementor( 27 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1, *inc.next( 1 ) ),
        ( 3, *inc.next( 1 ) ),
        ( 4, *inc.next( 2 ) ),
        ( 7, *inc.next( 1 ) ),
        ( 1 + 9, *inc.next( 1 ) ),
        ( 3 + 9, *inc.next( 1 ) ),
        ( 4 + 9, *inc.next( 2 ) ),
        ( 7 + 9, *inc.next( 1 ) ),
        ( 1 + 18, *inc.next( 1 ) ),
        ( 3 + 18, *inc.next( 1 ) ),
        ( 4 + 18, *inc.next( 2 ) ),
        ( 7 + 18, *inc.next( 1 ) ),
    )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), ( 0, 1, 2, 1, 0, 1, 2, 1 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 9 * 4 + 6, 8, 12, 6 ) )

    # Split in 8
    inc = Incrementor( 27 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1, *inc.next( 1 ) ),
        ( 3, *inc.next( 1 ) ),
        ( 4, *inc.next( 3 ) ),
        ( 5, *inc.next( 1 ) ),
        ( 7, *inc.next( 1 ) ),
        ( 0 + 9, *inc.next( 1 ) ),
        ( 1 + 9, *inc.next( 3 ) ),
        ( 2 + 9, *inc.next( 1 ) ),
        ( 3 + 9, *inc.next( 3 ) ),
        ( 4 + 9, *inc.next( 7 ) ),
        ( 5 + 9, *inc.next( 3 ) ),
        ( 6 + 9, *inc.next( 1 ) ),
        ( 7 + 9, *inc.next( 3 ) ),
        ( 8 + 9, *inc.next( 1 ) ),
        ( 1 + 18, *inc.next( 1 ) ),
        ( 3 + 18, *inc.next( 1 ) ),
        ( 4 + 18, *inc.next( 3 ) ),
        ( 5 + 18, *inc.next( 1 ) ),
        ( 7 + 18, *inc.next( 1 ) ),
    )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), range( 8 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 8 * 8, 8, 3 * 3 * 3 - 8, 12 ) )

    # Straight notch
    inc = Incrementor( 27 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1, *inc.next( 1 ) ),
        ( 4, ),
        ( 1 + 9, *inc.next( 1 ) ),
        ( 4 + 9, ),
        ( 1 + 18, *inc.next( 1 ) ),
        ( 4 + 18, ),
    )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), ( 0, 1, 2, 2, 0, 1, 2, 2 ),
                                       field_values=( 0, 1 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 3 * 3 + 3, 8, 6, 2 ) )

    # L-shaped notch
    inc = Incrementor( 27 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1, *inc.next( 1 ) ),
        ( 4, *inc.next( 1 ) ),
        ( 7, *inc.next( 1 ) ),
        ( 1 + 9, *inc.next( 1 ) ),
        ( 4 + 9, ),
        ( 7 + 9, ),
        ( 1 + 18, *inc.next( 1 ) ),
        ( 4 + 18, ),
    )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), ( 0, 1, 0, 1, 0, 1, 2, 2 ),
                                       field_values=( 0, 1 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 3 * 3 + 5, 8, 8, 3 ) )

    # 3x1x1 split
    inc = Incrementor( 2 * 2 * 4 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1, *inc.next( 1 ) ),
        ( 2, *inc.next( 1 ) ),
        ( 5, *inc.next( 1 ) ),
        ( 6, *inc.next( 1 ) ),
        ( 1 + 8, *inc.next( 1 ) ),
        ( 2 + 8, *inc.next( 1 ) ),
        ( 5 + 8, *inc.next( 1 ) ),
        ( 6 + 8, *inc.next( 1 ) ),
    )
    mesh, options = __build_test_case( ( four_nodes, two_nodes, two_nodes ), ( 0, 1, 2 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 6 * 4, 3, 2 * 4, 2 ) )

    # Discarded fracture element if no node duplication.
    collocated_nodes: Sequence[ Sequence[ int ] ] = ()
    mesh, options = __build_test_case( ( three_nodes, four_nodes, four_nodes ), [
        0,
    ] * 8 + [ 1, 2 ] + [
        0,
    ] * 8,
                                       field_values=( 1, 2 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 4 * 4, 2 * 3 * 3, 0, 0 ) )

    # Fracture on a corner
    inc = Incrementor( 3 * 4 * 4 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1 + 12, ),
        ( 4 + 12, ),
        ( 7 + 12, ),
        ( 1 + 12 * 2, *inc.next( 1 ) ),
        ( 4 + 12 * 2, *inc.next( 1 ) ),
        ( 7 + 12 * 2, ),
        ( 1 + 12 * 3, *inc.next( 1 ) ),
        ( 4 + 12 * 3, *inc.next( 1 ) ),
        ( 7 + 12 * 3, ),
    )
    mesh, options = __build_test_case( ( three_nodes, four_nodes, four_nodes ), [
        0,
    ] * 6 + [ 1, 2, 1, 2, 0, 0, 1, 2, 1, 2, 0, 0 ],
                                       field_values=( 1, 2 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 4 * 4 + 4, 2 * 3 * 3, 9, 4 ) )

    # Generate mesh with 2 hexs, one being a standard hex, the other a 42 hex.
    inc = Incrementor( 3 * 2 * 2 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1, *inc.next( 1 ) ),
        ( 1 + 3, *inc.next( 1 ) ),
        ( 1 + 6, *inc.next( 1 ) ),
        ( 1 + 9, *inc.next( 1 ) ),
    )
    mesh, options = __build_test_case( ( three_nodes, two_nodes, two_nodes ), ( 0, 1 ) )
    polyhedron_mesh = vtkUnstructuredGrid()
    polyhedron_mesh.SetPoints( mesh.GetPoints() )
    polyhedron_mesh.Allocate( 2 )
    polyhedron_mesh.InsertNextCell( VTK_HEXAHEDRON, to_vtk_id_list( ( 1, 2, 5, 4, 7, 8, 10, 11 ) ) )
    poly = to_vtk_id_list( [ 6 ] + [ 4, 0, 1, 7, 6 ] + [ 4, 1, 4, 10, 7 ] + [ 4, 4, 3, 9, 10 ] + [ 4, 3, 0, 6, 9 ] +
                           [ 4, 6, 7, 10, 9 ] + [ 4, 1, 0, 3, 4 ] )
    polyhedron_mesh.InsertNextCell( VTK_POLYHEDRON, poly )
    polyhedron_mesh.GetCellData().AddArray( mesh.GetCellData().GetArray( "attribute" ) )

    yield TestCase( input_mesh=polyhedron_mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 4 * 4, 2, 4, 1 ) )

    # Split in 2 using the internal fracture description
    inc = Incrementor( 3 * 2 * 2 )
    collocated_nodes: Sequence[ Sequence[ int ] ] = (
        ( 1, *inc.next( 1 ) ),
        ( 1 + 3, *inc.next( 1 ) ),
        ( 1 + 6, *inc.next( 1 ) ),
        ( 1 + 9, *inc.next( 1 ) ),
    )
    mesh, options = __build_test_case( ( three_nodes, two_nodes, two_nodes ),
                                       attribute=( 0, 0, 0 ),
                                       field_values=( 0, ),
                                       policy=FracturePolicy.INTERNAL_SURFACES )
    mesh.InsertNextCell( VTK_QUAD, to_vtk_id_list( ( 1, 4, 7, 10 ) ) )  # Add a fracture on the fly
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 4 * 4, 3, 4, 1 ) )


@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_generate_fracture( test_case: TestCase ):
    main_mesh, fracture_mesh = __split_mesh_on_fracture( test_case.input_mesh, test_case.options )
    assert main_mesh.GetNumberOfPoints() == test_case.result.main_mesh_num_points
    assert main_mesh.GetNumberOfCells() == test_case.result.main_mesh_num_cells
    assert fracture_mesh.GetNumberOfPoints() == test_case.result.fracture_mesh_num_points
    assert fracture_mesh.GetNumberOfCells() == test_case.result.fracture_mesh_num_cells

    res = format_collocated_nodes( fracture_mesh )
    assert res == test_case.collocated_nodes
    assert len( res ) == test_case.result.fracture_mesh_num_points


def add_simplified_field_for_cells( mesh: vtkUnstructuredGrid, field_name: str, field_dimension: int ):
    """Reduce functionality obtained from src.geos.mesh.doctor.checks.generate_fracture.__add_fields
    where the goal is to add a cell data array with incrementing values.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
        field_name (str): Name of the field to add to CellData
        field_dimension (int): Number of components for the field.
    """
    data = mesh.GetCellData()
    n = mesh.GetNumberOfCells()
    array = numpy.ones( ( n, field_dimension ), dtype=float )
    array = numpy.arange( 1, n * field_dimension + 1 ).reshape( n, field_dimension )
    vtk_array = numpy_to_vtk( array )
    vtk_array.SetName( field_name )
    data.AddArray( vtk_array )


def find_min_max_coords_rectilinear_grid( mesh: vtkUnstructuredGrid ) -> tuple[ list[ float ] ]:
    """For a vtk rectilinear grid, gives the coordinates of the minimum and maximum points
    of the grid.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.

    Returns:
        tuple[list[float]]: ([Xmin, Ymin, Zmin], [Xmax, Ymax, Zmax])
    """
    points = mesh.GetPoints()
    min_coords: list[ float ] = [ float( 'inf' ) ] * 3
    max_coords: list[ float ] = [ float( '-inf' ) ] * 3
    for i in range( points.GetNumberOfPoints() ):
        coord = points.GetPoint( i )
        for j in range( 3 ):  # Assuming 3D coordinates (x, y, z)
            min_coords[ j ] = min( min_coords[ j ], coord[ j ] )
            max_coords[ j ] = max( max_coords[ j ], coord[ j ] )
    return ( min_coords, max_coords )


def find_borders_coordinates_rectilinear_grid( mesh: vtkUnstructuredGrid ) -> tuple[ QuadCoords ]:
    """
              6+--------+7
              /        /|
             /        / |
           4+--------+5 |
            |        |  |
            | 2+     |  +3
            |        | /
            |        |/
           0+--------+1

    For a vtk rectilinear grid, gives the coordinates of each of its borders face nodes.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.

    Returns:
        tuple[QuadCoords]: For a rectilinear grid, returns a tuple of 6 elements.
    """
    min_coords, max_coords = find_min_max_coords_rectilinear_grid( mesh )
    center: tuple[ float ] = ( ( min_coords[ 0 ] + max_coords[ 0 ] ) / 2, ( min_coords[ 1 ] + max_coords[ 1 ] ) / 2,
                               ( min_coords[ 2 ] + max_coords[ 2 ] ) / 2 )
    # hdl stands for half diagonal lenght
    hdl: tuple[ float ] = ( ( -min_coords[ 0 ] + max_coords[ 0 ] ) / 2, ( -min_coords[ 1 ] + max_coords[ 1 ] ) / 2,
                            ( -min_coords[ 2 ] + max_coords[ 2 ] ) / 2 )
    node0: tuple[ float ] = ( center[ 0 ] - hdl[ 0 ], center[ 1 ] - hdl[ 1 ], center[ 2 ] - hdl[ 2 ] )
    node1: tuple[ float ] = ( center[ 0 ] + hdl[ 0 ], center[ 1 ] - hdl[ 1 ], center[ 2 ] - hdl[ 2 ] )
    node2: tuple[ float ] = ( center[ 0 ] - hdl[ 0 ], center[ 1 ] + hdl[ 1 ], center[ 2 ] - hdl[ 2 ] )
    node3: tuple[ float ] = ( center[ 0 ] + hdl[ 0 ], center[ 1 ] + hdl[ 1 ], center[ 2 ] - hdl[ 2 ] )
    node4: tuple[ float ] = ( center[ 0 ] - hdl[ 0 ], center[ 1 ] - hdl[ 1 ], center[ 2 ] + hdl[ 2 ] )
    node5: tuple[ float ] = ( center[ 0 ] + hdl[ 0 ], center[ 1 ] - hdl[ 1 ], center[ 2 ] + hdl[ 2 ] )
    node6: tuple[ float ] = ( center[ 0 ] - hdl[ 0 ], center[ 1 ] + hdl[ 1 ], center[ 2 ] + hdl[ 2 ] )
    node7: tuple[ float ] = ( center[ 0 ] + hdl[ 0 ], center[ 1 ] + hdl[ 1 ], center[ 2 ] + hdl[ 2 ] )
    faces: tuple[ QuadCoords ] = ( QuadCoords( node0, node1, node3, node2 ), QuadCoords( node4, node5, node7, node6 ),
                                   QuadCoords( node0, node2, node6, node4 ), QuadCoords( node1, node3, node7, node5 ),
                                   QuadCoords( node0, node1, node5, node4 ), QuadCoords( node2, node3, node7, node6 ) )
    return faces


def set_quad_points( mesh: vtkUnstructuredGrid, quad: vtkQuad, coordinates: QuadCoords ):
    """Set the coordinates of a vtkQuad by adding the points and their id. 

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
        quad (vtkQuad): A vtkQuad object.
        coordinates (QuadCoords): A QuadCoords containing 4 points coordinates.
    """
    points_coords = mesh.GetPoints().GetData()
    numpy_coordinates: numpy.array = vtk_to_numpy( points_coords )
    coords_vertices_mesh: list[ tuple ] = [ tuple( row ) for row in numpy_coordinates ]
    coords_vertices_quad: list[ tuple ] = coordinates.get_coordinates()
    ids_association: dict[ int, int ] = {}
    for i in range( len( coords_vertices_mesh ) ):
        for j in range( len( coords_vertices_quad ) ):
            if coords_vertices_mesh[ i ] == coords_vertices_quad[ j ]:
                ids_association[ i ] = j
                break

    for vertice_id, quad_coord_index in ids_association.items():
        quad.GetPoints().InsertNextPoint( coords_vertices_quad[ quad_coord_index ] )
        quad.GetPointIds().SetId( quad_coord_index, vertice_id )


def add_quad( mesh: vtkUnstructuredGrid, coordinates: QuadCoords ):
    """Adds a quad cell to an unstructured mesh by knowing the coordinates of its 4 nodes.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
        coordinates (QuadCoords): A QuadCoords containing 4 points coordinates.
    """
    quad = vtkQuad()
    set_quad_points( mesh, quad, coordinates )
    mesh.InsertNextCell( quad.GetCellType(), quad.GetPointIds() )


def add_quads_to_all_borders_rectilinear_grid( mesh: vtkUnstructuredGrid ):
    """Adds a quad cell to each border of an unstructured mesh.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
    """
    faces: tuple[ QuadCoords ] = find_borders_coordinates_rectilinear_grid( mesh )
    for face in faces:
        add_quad( mesh, face )


def test_copy_fields_when_splitting_mesh():
    """This test is designed to check the __copy_fields method from generate_fractures,
    that will be called when using __split_mesh_on_fracture method from generate_fractures.
    """
    # Generating the rectilinear grid and its quads on all borders
    x: numpy.array = numpy.array( [ 0, 1, 2 ] )
    y: numpy.array = numpy.array( [ 0, 1 ] )
    z: numpy.array = numpy.array( [ 0, 1 ] )
    xyzs: XYZ = XYZ( x, y, z )
    mesh: vtkUnstructuredGrid = build_rectilinear_blocks_mesh( [ xyzs ] )
    assert mesh.GetCells().GetNumberOfCells() == 2
    add_quads_to_all_borders_rectilinear_grid( mesh )
    assert mesh.GetCells().GetNumberOfCells() == 8
    # Create a quad cell to represent the fracture surface.
    fracture_coordinates: QuadCoords = QuadCoords( p1=( 1.0, 0.0, 0.0 ),
                                                   p2=( 1.0, 1.0, 0.0 ),
                                                   p3=( 1.0, 1.0, 1.0 ),
                                                   p4=( 1.0, 0.0, 1.0 ) )
    add_quad( mesh, fracture_coordinates )
    assert mesh.GetCells().GetNumberOfCells() == 9
    # Add a "TestField" array
    assert mesh.GetCellData().GetNumberOfArrays() == 0
    add_simplified_field_for_cells( mesh, "TestField", 1 )
    assert mesh.GetCellData().GetNumberOfArrays() == 1
    assert mesh.GetCellData().GetArrayName( 0 ) == "TestField"
    testField_values: list[ int ] = vtk_to_numpy( mesh.GetCellData().GetArray( 0 ) ).tolist()
    assert testField_values == [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
    # Split the mesh along the fracture surface which is number 9 on TestField
    options = Options( policy=FracturePolicy.INTERNAL_SURFACES,
                       field="TestField",
                       field_values=frozenset( map( int, [ "9" ] ) ),
                       vtk_output=None,
                       vtk_fracture_output=None )
    main_mesh, fracture_mesh = __split_mesh_on_fracture( mesh, options )
    assert main_mesh.GetCellData().GetNumberOfArrays() == 1
    assert fracture_mesh.GetCellData().GetNumberOfArrays() == 1
    assert main_mesh.GetCellData().GetArrayName( 0 ) == "TestField"
    assert fracture_mesh.GetCellData().GetArrayName( 0 ) == "TestField"
    #  Make sure that only 1 correct value is in "TestField" array for fracture_mesh, 9 values for main_mesh
    fracture_mesh_values: list[ int ] = vtk_to_numpy( fracture_mesh.GetCellData().GetArray( 0 ) ).tolist()
    main_mesh_values: list[ int ] = vtk_to_numpy( main_mesh.GetCellData().GetArray( 0 ) ).tolist()
    assert fracture_mesh_values == [ 9 ]  # The value for the fracture surface
    assert main_mesh_values == [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
    # Test for invalid point field name
    add_simplified_field_for_cells( mesh, "GLOBAL_IDS_POINTS", 1 )
    with pytest.raises( SystemExit ) as pytest_wrapped_e:
        main_mesh, fracture_mesh = __split_mesh_on_fracture( mesh, options )
    assert pytest_wrapped_e.type == SystemExit
    # Test for invalid cell field name
    mesh: vtkUnstructuredGrid = build_rectilinear_blocks_mesh( [ xyzs ] )
    add_quads_to_all_borders_rectilinear_grid( mesh )
    add_quad( mesh, fracture_coordinates )
    add_simplified_field_for_cells( mesh, "TestField", 1 )
    add_simplified_field_for_cells( mesh, "GLOBAL_IDS_CELLS", 1 )
    assert mesh.GetCellData().GetNumberOfArrays() == 2
    with pytest.raises( SystemExit ) as pytest_wrapped_e:
        main_mesh, fracture_mesh = __split_mesh_on_fracture( mesh, options )
    assert pytest_wrapped_e.type == SystemExit
