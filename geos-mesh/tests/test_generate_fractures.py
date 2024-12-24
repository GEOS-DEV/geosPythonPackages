from dataclasses import dataclass
import numpy
import pytest
from typing import Iterable, Iterator, Sequence
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkQuad, VTK_HEXAHEDRON, VTK_POLYHEDRON, VTK_QUAD )
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from geos.mesh.doctor.checks.check_fractures import format_collocated_nodes
from geos.mesh.doctor.checks.generate_cube import build_rectilinear_blocks_mesh, XYZ
from geos.mesh.doctor.checks.generate_fractures import ( __split_mesh_on_fractures, Options, FracturePolicy,
                                                         Coordinates3D, IDMapping )
from utils.src.geos.utils.vtk.helpers import to_vtk_id_list


FaceNodesCoords = tuple[ tuple[ float ] ]
IDMatrix = Sequence[ Sequence[ int ] ]


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
    collocated_nodes: IDMatrix
    result: TestResult


def __build_test_case( xs: tuple[ numpy.ndarray, numpy.ndarray, numpy.ndarray ],
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

    options = Options( policy=policy,
                       field="attribute",
                       field_values_combined=fv,
                       field_values_per_fracture=[ fv ],
                       mesh_VtkOutput=None,
                       all_fractures_VtkOutput=None )
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
    collocated_nodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 3, *inc.next( 1 ) ), ( 4, *inc.next( 2 ) ),
                                   ( 7, *inc.next( 1 ) ), ( 1 + 9, *inc.next( 1 ) ), ( 3 + 9, *inc.next( 1 ) ),
                                   ( 4 + 9, *inc.next( 2 ) ), ( 7 + 9, *inc.next( 1 ) ), ( 1 + 18, *inc.next( 1 ) ),
                                   ( 3 + 18, *inc.next( 1 ) ), ( 4 + 18, *inc.next( 2 ) ), ( 7 + 18, *inc.next( 1 ) ) )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), ( 0, 1, 2, 1, 0, 1, 2, 1 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 9 * 4 + 6, 8, 12, 6 ) )

    # Split in 8
    inc = Incrementor( 27 )
    collocated_nodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 3, *inc.next( 1 ) ), ( 4, *inc.next( 3 ) ),
                                   ( 5, *inc.next( 1 ) ), ( 7, *inc.next( 1 ) ), ( 0 + 9, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 3 ) ), ( 2 + 9, *inc.next( 1 ) ), ( 3 + 9, *inc.next( 3 ) ),
                                   ( 4 + 9, *inc.next( 7 ) ), ( 5 + 9, *inc.next( 3 ) ), ( 6 + 9, *inc.next( 1 ) ),
                                   ( 7 + 9, *inc.next( 3 ) ), ( 8 + 9, *inc.next( 1 ) ), ( 1 + 18, *inc.next( 1 ) ),
                                   ( 3 + 18, *inc.next( 1 ) ), ( 4 + 18, *inc.next( 3 ) ), ( 5 + 18, *inc.next( 1 ) ),
                                   ( 7 + 18, *inc.next( 1 ) ) )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), range( 8 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 8 * 8, 8, 3 * 3 * 3 - 8, 12 ) )

    # Straight notch
    inc = Incrementor( 27 )
    collocated_nodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 4, ), ( 1 + 9, *inc.next( 1 ) ), ( 4 + 9, ),
                                   ( 1 + 18, *inc.next( 1 ) ), ( 4 + 18, ) )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), ( 0, 1, 2, 2, 0, 1, 2, 2 ),
                                       field_values=( 0, 1 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 3 * 3 + 3, 8, 6, 2 ) )

    # L-shaped notch
    inc = Incrementor( 27 )
    collocated_nodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 4, *inc.next( 1 ) ), ( 7, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 1 ) ), ( 4 + 9, ), ( 7 + 9, ), ( 19, *inc.next( 1 ) ), ( 22, ) )
    mesh, options = __build_test_case( ( three_nodes, three_nodes, three_nodes ), ( 0, 1, 0, 1, 0, 1, 2, 2 ),
                                       field_values=( 0, 1 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 3 * 3 + 5, 8, 8, 3 ) )

    # 3x1x1 split
    inc = Incrementor( 2 * 2 * 4 )
    collocated_nodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 2, *inc.next( 1 ) ), ( 5, *inc.next( 1 ) ),
                                   ( 6, *inc.next( 1 ) ), ( 1 + 8, *inc.next( 1 ) ), ( 2 + 8, *inc.next( 1 ) ),
                                   ( 5 + 8, *inc.next( 1 ) ), ( 6 + 8, *inc.next( 1 ) ) )
    mesh, options = __build_test_case( ( four_nodes, two_nodes, two_nodes ), ( 0, 1, 2 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 6 * 4, 3, 2 * 4, 2 ) )

    # Discarded fracture element if no node duplication.
    collocated_nodes: IDMatrix = tuple()
    mesh, options = __build_test_case( ( three_nodes, four_nodes, four_nodes ), ( 0, ) * 8 + ( 1, 2 ) + ( 0, ) * 8,
                                       field_values=( 1, 2 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 4 * 4, 2 * 3 * 3, 0, 0 ) )

    # Fracture on a corner
    inc = Incrementor( 3 * 4 * 4 )
    collocated_nodes: IDMatrix = ( ( 1 + 12, ), ( 4 + 12, ), ( 7 + 12, ), ( 1 + 12 * 2, *inc.next( 1 ) ),
                                   ( 4 + 12 * 2, *inc.next( 1 ) ), ( 7 + 12 * 2, ), ( 1 + 12 * 3, *inc.next( 1 ) ),
                                   ( 4 + 12 * 3, *inc.next( 1 ) ), ( 7 + 12 * 3, ) )
    mesh, options = __build_test_case( ( three_nodes, four_nodes, four_nodes ),
                                       ( 0, ) * 6 + ( 1, 2, 1, 2, 0, 0, 1, 2, 1, 2, 0, 0 ),
                                       field_values=( 1, 2 ) )
    yield TestCase( input_mesh=mesh,
                    options=options,
                    collocated_nodes=collocated_nodes,
                    result=TestResult( 3 * 4 * 4 + 4, 2 * 3 * 3, 9, 4 ) )

    # Generate mesh with 2 hexs, one being a standard hex, the other a 42 hex.
    inc = Incrementor( 3 * 2 * 2 )
    collocated_nodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 1 + 3, *inc.next( 1 ) ), ( 1 + 6, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 1 ) ) )
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
    collocated_nodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 1 + 3, *inc.next( 1 ) ), ( 1 + 6, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 1 ) ) )
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
    main_mesh, fracture_meshes = __split_mesh_on_fractures( test_case.input_mesh, test_case.options )
    fracture_mesh: vtkUnstructuredGrid = fracture_meshes[ 0 ]
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


def find_borders_faces_rectilinear_grid( mesh: vtkUnstructuredGrid ) -> tuple[ FaceNodesCoords ]:
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
    mesh_bounds: tuple[ float ] = mesh.GetBounds()
    min_bound: Coordinates3D = [ mesh_bounds[ i ] for i in range( len( mesh_bounds ) ) if i % 2 == 0 ]
    max_bound: Coordinates3D = [ mesh_bounds[ i ] for i in range( len( mesh_bounds ) ) if i % 2 == 1 ]
    center: Coordinates3D = mesh.GetCenter()
    face_diag: tuple[ float ] = ( ( max_bound[ 0 ] - min_bound[ 0 ] ) / 2, ( max_bound[ 1 ] - min_bound[ 1 ] ) / 2,
                                  ( max_bound[ 2 ] - min_bound[ 2 ] ) / 2 )
    node0: Coordinates3D = ( center[ 0 ] - face_diag[ 0 ], center[ 1 ] - face_diag[ 1 ], center[ 2 ] - face_diag[ 2 ] )
    node1: Coordinates3D = ( center[ 0 ] + face_diag[ 0 ], center[ 1 ] - face_diag[ 1 ], center[ 2 ] - face_diag[ 2 ] )
    node2: Coordinates3D = ( center[ 0 ] - face_diag[ 0 ], center[ 1 ] + face_diag[ 1 ], center[ 2 ] - face_diag[ 2 ] )
    node3: Coordinates3D = ( center[ 0 ] + face_diag[ 0 ], center[ 1 ] + face_diag[ 1 ], center[ 2 ] - face_diag[ 2 ] )
    node4: Coordinates3D = ( center[ 0 ] - face_diag[ 0 ], center[ 1 ] - face_diag[ 1 ], center[ 2 ] + face_diag[ 2 ] )
    node5: Coordinates3D = ( center[ 0 ] + face_diag[ 0 ], center[ 1 ] - face_diag[ 1 ], center[ 2 ] + face_diag[ 2 ] )
    node6: Coordinates3D = ( center[ 0 ] - face_diag[ 0 ], center[ 1 ] + face_diag[ 1 ], center[ 2 ] + face_diag[ 2 ] )
    node7: Coordinates3D = ( center[ 0 ] + face_diag[ 0 ], center[ 1 ] + face_diag[ 1 ], center[ 2 ] + face_diag[ 2 ] )
    faces: tuple[ FaceNodesCoords ] = ( ( node0, node1, node3, node2 ), ( node4, node5, node7, node6 ),
                                        ( node0, node2, node6, node4 ), ( node1, node3, node7, node5 ),
                                        ( node0, node1, node5, node4 ), ( node2, node3, node7, node6 ) )
    return faces


def add_quad( mesh: vtkUnstructuredGrid, face: FaceNodesCoords ):
    """Adds a quad cell to each border of an unstructured mesh.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
    """
    points_coords = mesh.GetPoints().GetData()
    quad: vtkQuad = vtkQuad()
    ids_association: IDMapping = {}
    for i in range( mesh.GetNumberOfPoints() ):
        for j in range( len( face ) ):
            if points_coords.GetTuple( i ) == face[ j ]:
                ids_association[ i ] = j
                break
        if len( ids_association ) == 4:
            break

    for vertice_id, quad_coord_index in ids_association.items():
        quad.GetPoints().InsertNextPoint( face[ quad_coord_index ] )
        quad.GetPointIds().SetId( quad_coord_index, vertice_id )

    mesh.InsertNextCell( quad.GetCellType(), quad.GetPointIds() )


def test_copy_fields_when_splitting_mesh():
    """This test is designed to check the __copy_fields method from generate_fractures,
    that will be called when using __split_mesh_on_fractures method from generate_fractures.
    """
    # Generating the rectilinear grid and its quads on all borders
    x: numpy.array = numpy.array( [ 0, 1, 2 ] )
    y: numpy.array = numpy.array( [ 0, 1 ] )
    z: numpy.array = numpy.array( [ 0, 1 ] )
    xyzs: XYZ = XYZ( x, y, z )
    mesh: vtkUnstructuredGrid = build_rectilinear_blocks_mesh( [ xyzs ] )
    assert mesh.GetCells().GetNumberOfCells() == 2
    border_faces: tuple[ FaceNodesCoords ] = find_borders_faces_rectilinear_grid( mesh )
    for face in border_faces:
        add_quad( mesh, face )
    assert mesh.GetCells().GetNumberOfCells() == 8
    # Create a quad cell to represent the fracture surface.
    fracture: FaceNodesCoords = ( ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.0, 1.0, 1.0 ), ( 1.0, 0.0, 1.0 ) )
    add_quad( mesh, fracture )
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
                       field_values_combined=frozenset( map( int, [ "9" ] ) ),
                       field_values_per_fracture=[ frozenset( map( int, [ "9" ] ) ) ],
                       mesh_VtkOutput=None,
                       all_fractures_VtkOutput=None )
    main_mesh, fracture_meshes = __split_mesh_on_fractures( mesh, options )
    fracture_mesh: vtkUnstructuredGrid = fracture_meshes[ 0 ]
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
    with pytest.raises( ValueError ) as pytest_wrapped_e:
        main_mesh, fracture_meshes = __split_mesh_on_fractures( mesh, options )
    assert pytest_wrapped_e.type == ValueError
    # Test for invalid cell field name
    mesh: vtkUnstructuredGrid = build_rectilinear_blocks_mesh( [ xyzs ] )
    border_faces: tuple[ FaceNodesCoords ] = find_borders_faces_rectilinear_grid( mesh )
    for face in border_faces:
        add_quad( mesh, face )
    add_quad( mesh, fracture )
    add_simplified_field_for_cells( mesh, "TestField", 1 )
    add_simplified_field_for_cells( mesh, "GLOBAL_IDS_CELLS", 1 )
    assert mesh.GetCellData().GetNumberOfArrays() == 2
    with pytest.raises( ValueError ) as pytest_wrapped_e:
        main_mesh, fracture_meshes = __split_mesh_on_fractures( mesh, options )
    assert pytest_wrapped_e.type == ValueError
