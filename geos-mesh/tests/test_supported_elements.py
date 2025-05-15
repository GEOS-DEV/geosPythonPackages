# import os
import pytest
import numpy as np
from typing import Tuple
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkQuad, vtkTetra, vtkHexahedron, vtkPolyhedron,
                                            vtkCellArray, VTK_POLYHEDRON, VTK_QUAD, VTK_TETRA, VTK_HEXAHEDRON )
# from geos.mesh.doctor.checks.supported_elements import Options, check, __check
from geos.mesh.doctor.checks.vtk_polyhedron import parse_face_stream, FaceStream
from geos.mesh.doctor.filters.SupportedElements import SupportedElements
from geos.mesh.vtk.helpers import to_vtk_id_list


# TODO Update this test to have access to another meshTests file
@pytest.mark.parametrize( "base_name", ( "supportedElements.vtk", "supportedElementsAsVTKPolyhedra.vtk" ) )
def test_supported_elements( base_name ) -> None:
    """
    Testing that the supported elements are properly detected as supported!
    :param base_name: Supported elements are provided as standard elements or polyhedron elements.
    """
    ...
    # directory = os.path.dirname( os.path.realpath( __file__ ) )
    # supported_elements_file_name = os.path.join( directory, "../../../../unitTests/meshTests", base_name )
    # options = Options( chunk_size=1, num_proc=4 )
    # result = check( supported_elements_file_name, options )
    # assert not result.unsupported_std_elements_types
    # assert not result.unsupported_polyhedron_elements


def make_dodecahedron() -> Tuple[ vtkPoints, vtkIdList ]:
    """
    Returns the points and faces for a dodecahedron.
    This code was adapted from an official vtk example.
    :return: The tuple of points and faces (as vtk instances).
    """
    # yapf: disable
    points = (
        (1.21412, 0, 1.58931),
        (0.375185, 1.1547, 1.58931),
        (-0.982247, 0.713644, 1.58931),
        (-0.982247, -0.713644, 1.58931),
        (0.375185, -1.1547, 1.58931),
        (1.96449, 0, 0.375185),
        (0.607062, 1.86835, 0.375185),
        (-1.58931, 1.1547, 0.375185),
        (-1.58931, -1.1547, 0.375185),
        (0.607062, -1.86835, 0.375185),
        (1.58931, 1.1547, -0.375185),
        (-0.607062, 1.86835, -0.375185),
        (-1.96449, 0, -0.375185),
        (-0.607062, -1.86835, -0.375185),
        (1.58931, -1.1547, -0.375185),
        (0.982247, 0.713644, -1.58931),
        (-0.375185, 1.1547, -1.58931),
        (-1.21412, 0, -1.58931),
        (-0.375185, -1.1547, -1.58931),
        (0.982247, -0.713644, -1.58931)
    )

    faces = (12,  # number of faces
             5, 0, 1, 2, 3, 4,  # number of ids on face, ids
             5, 0, 5, 10, 6, 1,
             5, 1, 6, 11, 7, 2,
             5, 2, 7, 12, 8, 3,
             5, 3, 8, 13, 9, 4,
             5, 4, 9, 14, 5, 0,
             5, 15, 10, 5, 14, 19,
             5, 16, 11, 6, 10, 15,
             5, 17, 12, 7, 11, 16,
             5, 18, 13, 8, 12, 17,
             5, 19, 14, 9, 13, 18,
             5, 19, 18, 17, 16, 15)
    # yapf: enable

    p = vtkPoints()
    p.Allocate( len( points ) )
    for coords in points:
        p.InsertNextPoint( coords )

    f = to_vtk_id_list( faces )

    return p, f


# TODO make this test work
def test_dodecahedron() -> None:
    """
    Tests whether a dodecahedron is support by GEOS or not.
    """
    points, faces = make_dodecahedron()
    mesh = vtkUnstructuredGrid()
    mesh.Allocate( 1 )
    mesh.SetPoints( points )
    mesh.InsertNextCell( VTK_POLYHEDRON, faces )

    # TODO Why does __check triggers an assertion error with 'assert MESH is not None' ?
    # result = __check( mesh, Options( num_proc=1, chunk_size=1 ) )
    # assert set( result.unsupported_polyhedron_elements ) == { 0 }
    # assert not result.unsupported_std_elements_types


def test_parse_face_stream() -> None:
    _, faces = make_dodecahedron()
    result = parse_face_stream( faces )
    # yapf: disable
    expected = (
        (0, 1, 2, 3, 4),
        (0, 5, 10, 6, 1),
        (1, 6, 11, 7, 2),
        (2, 7, 12, 8, 3),
        (3, 8, 13, 9, 4),
        (4, 9, 14, 5, 0),
        (15, 10, 5, 14, 19),
        (16, 11, 6, 10, 15),
        (17, 12, 7, 11, 16),
        (18, 13, 8, 12, 17),
        (19, 14, 9, 13, 18),
        (19, 18, 17, 16, 15)
    )
    # yapf: enable
    assert result == expected
    face_stream = FaceStream.build_from_vtk_id_list( faces )
    assert face_stream.num_faces == 12
    assert face_stream.num_support_points == 20


def create_simple_tetra_grid():
    """Create a simple tetrahedral grid for testing"""
    # Create an unstructured grid
    points_tetras: vtkPoints = vtkPoints()
    points_tetras_coords: list[ tuple[ float ] ] = [ ( 1.0, 0.5, 0.0 ),  # point0
                                                     ( 1.0, 0.0, 1.0 ),
                                                     ( 1.0, 1.0, 1.0 ),
                                                     ( 0.0, 0.5, 0.5 ),
                                                     ( 2.0, 0.5, 0.5 ),
                                                     ( 1.0, 0.5, 2.0 ),  # point5
                                                     ( 0.0, 0.5, 1.5 ),
                                                     ( 2.0, 0.5, 1.5 ) ]
    for point_tetra in points_tetras_coords:
        points_tetras.InsertNextPoint( point_tetra )

    tetra1: vtkTetra = vtkTetra()
    tetra1.GetPointIds().SetId( 0, 0 )
    tetra1.GetPointIds().SetId( 1, 1 )
    tetra1.GetPointIds().SetId( 2, 2 )
    tetra1.GetPointIds().SetId( 3, 3 )

    tetra2: vtkTetra = vtkTetra()
    tetra2.GetPointIds().SetId( 0, 0 )
    tetra2.GetPointIds().SetId( 1, 2 )
    tetra2.GetPointIds().SetId( 2, 1 )
    tetra2.GetPointIds().SetId( 3, 4 )

    tetra3: vtkTetra = vtkTetra()
    tetra3.GetPointIds().SetId( 0, 1 )
    tetra3.GetPointIds().SetId( 1, 5 )
    tetra3.GetPointIds().SetId( 2, 2 )
    tetra3.GetPointIds().SetId( 3, 6 )

    tetra4: vtkTetra = vtkTetra()
    tetra4.GetPointIds().SetId( 0, 1 )
    tetra4.GetPointIds().SetId( 1, 2 )
    tetra4.GetPointIds().SetId( 2, 5 )
    tetra4.GetPointIds().SetId( 3, 7 )

    tetras_cells: vtkCellArray = vtkCellArray()
    tetras_cells.InsertNextCell( tetra1 )
    tetras_cells.InsertNextCell( tetra2 )
    tetras_cells.InsertNextCell( tetra3 )
    tetras_cells.InsertNextCell( tetra4 )

    tetras_grid: vtkUnstructuredGrid = vtkUnstructuredGrid()
    tetras_grid.SetPoints( points_tetras )
    tetras_grid.SetCells( VTK_TETRA, tetras_cells )
    return tetras_grid


def create_mixed_grid():
    """Create a grid with supported and unsupported cell types, 4 Hexahedrons with 2 quad fracs vertical"""
    # Create an unstructured grid
    four_hexs_points: vtkPoints = vtkPoints()
    four_hexs_points_coords: list[ tuple[ float ] ] = [ ( 0.0, 0.0, 0.0 ),  # point0
                                                        ( 1.0, 0.0, 0.0 ),  # point1
                                                        ( 2.0, 0.0, 0.0 ),  # point2
                                                        ( 0.0, 1.0, 0.0 ),  # point3
                                                        ( 1.0, 1.0, 0.0 ),  # point4
                                                        ( 2.0, 1.0, 0.0 ),  # point5
                                                        ( 0.0, 0.0, 1.0 ),  # point6
                                                        ( 1.0, 0.0, 1.0 ),  # point7
                                                        ( 2.0, 0.0, 1.0 ),  # point8
                                                        ( 0.0, 1.0, 1.0 ),  # point9
                                                        ( 1.0, 1.0, 1.0 ),  # point10
                                                        ( 2.0, 1.0, 1.0 ),  # point11
                                                        ( 0.0, 0.0, 2.0 ),  # point12
                                                        ( 1.0, 0.0, 2.0 ),  # point13
                                                        ( 2.0, 0.0, 2.0 ),  # point14
                                                        ( 0.0, 1.0, 2.0 ),  # point15
                                                        ( 1.0, 1.0, 2.0 ),  # point16
                                                        ( 2.0, 1.0, 2.0 ) ]
    for four_hexs_point in four_hexs_points_coords:
        four_hexs_points.InsertNextPoint( four_hexs_point )

    # hex1
    four_hex1: vtkHexahedron = vtkHexahedron()
    four_hex1.GetPointIds().SetId( 0, 0 )
    four_hex1.GetPointIds().SetId( 1, 1 )
    four_hex1.GetPointIds().SetId( 2, 4 )
    four_hex1.GetPointIds().SetId( 3, 3 )
    four_hex1.GetPointIds().SetId( 4, 6 )
    four_hex1.GetPointIds().SetId( 5, 7 )
    four_hex1.GetPointIds().SetId( 6, 10 )
    four_hex1.GetPointIds().SetId( 7, 9 )

    # hex2
    four_hex2: vtkHexahedron = vtkHexahedron()
    four_hex2.GetPointIds().SetId( 0, 0 + 1 )
    four_hex2.GetPointIds().SetId( 1, 1 + 1 )
    four_hex2.GetPointIds().SetId( 2, 4 + 1 )
    four_hex2.GetPointIds().SetId( 3, 3 + 1 )
    four_hex2.GetPointIds().SetId( 4, 6 + 1 )
    four_hex2.GetPointIds().SetId( 5, 7 + 1 )
    four_hex2.GetPointIds().SetId( 6, 10 + 1 )
    four_hex2.GetPointIds().SetId( 7, 9 + 1 )

    # hex3
    four_hex3: vtkHexahedron = vtkHexahedron()
    four_hex3.GetPointIds().SetId( 0, 0 + 6 )
    four_hex3.GetPointIds().SetId( 1, 1 + 6 )
    four_hex3.GetPointIds().SetId( 2, 4 + 6 )
    four_hex3.GetPointIds().SetId( 3, 3 + 6 )
    four_hex3.GetPointIds().SetId( 4, 6 + 6 )
    four_hex3.GetPointIds().SetId( 5, 7 + 6 )
    four_hex3.GetPointIds().SetId( 6, 10 + 6 )
    four_hex3.GetPointIds().SetId( 7, 9 + 6 )

    # hex4
    four_hex4: vtkHexahedron = vtkHexahedron()
    four_hex4.GetPointIds().SetId( 0, 0 + 7 )
    four_hex4.GetPointIds().SetId( 1, 1 + 7 )
    four_hex4.GetPointIds().SetId( 2, 4 + 7 )
    four_hex4.GetPointIds().SetId( 3, 3 + 7 )
    four_hex4.GetPointIds().SetId( 4, 6 + 7 )
    four_hex4.GetPointIds().SetId( 5, 7 + 7 )
    four_hex4.GetPointIds().SetId( 6, 10 + 7 )
    four_hex4.GetPointIds().SetId( 7, 9 + 7 )

    # quad1
    four_hex_quad1: vtkQuad = vtkQuad()
    four_hex_quad1.GetPointIds().SetId( 0, 1 )
    four_hex_quad1.GetPointIds().SetId( 1, 4 )
    four_hex_quad1.GetPointIds().SetId( 2, 10 )
    four_hex_quad1.GetPointIds().SetId( 3, 7 )

    # quad2
    four_hex_quad2: vtkQuad = vtkQuad()
    four_hex_quad2.GetPointIds().SetId( 0, 1 + 6 )
    four_hex_quad2.GetPointIds().SetId( 1, 4 + 6 )
    four_hex_quad2.GetPointIds().SetId( 2, 10 + 6 )
    four_hex_quad2.GetPointIds().SetId( 3, 7 + 6 )

    four_hex_grid_2_quads = vtkUnstructuredGrid()
    four_hex_grid_2_quads.SetPoints( four_hexs_points )
    all_cell_types_four_hex_grid_2_quads = [ VTK_HEXAHEDRON ] * 4 + [ VTK_QUAD ] * 2
    all_cells_four_hex_grid_2_quads = [ four_hex1, four_hex2, four_hex3, four_hex4, four_hex_quad1, four_hex_quad2 ]
    for cell_type, cell in zip( all_cell_types_four_hex_grid_2_quads, all_cells_four_hex_grid_2_quads ):
        four_hex_grid_2_quads.InsertNextCell( cell_type, cell.GetPointIds() )
    return four_hex_grid_2_quads


def create_unsupported_polyhedron_grid():
    """Create a grid with an unsupported polyhedron (non-convex)"""
    grid = vtkUnstructuredGrid()
    # Create points for the grid
    points = vtkPoints()  # Need to import vtkPoints
    # Create points for a non-convex polyhedron
    point_coords = np.array( [
        [ 0.0, 0.0, 0.0 ],  # 0
        [ 1.0, 0.0, 0.0 ],  # 1
        [ 1.0, 1.0, 0.0 ],  # 2
        [ 0.0, 1.0, 0.0 ],  # 3
        [ 0.0, 0.0, 1.0 ],  # 4
        [ 1.0, 0.0, 1.0 ],  # 5
        [ 1.0, 1.0, 1.0 ],  # 6
        [ 0.0, 1.0, 1.0 ],  # 7
        [ 0.5, 0.5, -0.5 ]  # 8 (point makes it non-convex)
    ] )
    # Add points to the points array
    for point in point_coords:
        points.InsertNextPoint( point )
    # Set the points in the grid
    grid.SetPoints( points )
    # Create a polyhedron
    polyhedron = vtkPolyhedron()
    # For simplicity, we'll create a polyhedron that would be recognized as unsupported
    # This is a simplified example - you may need to adjust based on your actual implementation
    polyhedron.GetPointIds().SetNumberOfIds( 9 )
    for i in range( 9 ):
        polyhedron.GetPointIds().SetId( i, i )
    # Add the polyhedron to the grid
    grid.InsertNextCell( polyhedron.GetCellType(), polyhedron.GetPointIds() )
    return grid


class TestSupportedElements:

    def test_only_supported_elements( self ):
        """Test a grid with only supported element types"""
        # Create grid with only supported elements (tetra)
        grid = create_simple_tetra_grid()
        # Apply the filter
        filter = SupportedElements()
        filter.SetInputDataObject( grid )
        filter.Update()
        result = filter.getGrid()
        assert result is not None
        # Verify no arrays were added (since all elements are supported)
        assert result.GetCellData().GetArray( "HasUnsupportedType" ) is None
        assert result.GetCellData().GetArray( "IsUnsupportedPolyhedron" ) is None

    def test_unsupported_element_types( self ):
        """Test a grid with unsupported element types"""
        # Create grid with unsupported elements
        grid = create_mixed_grid()
        # Apply the filter with painting enabled
        filter = SupportedElements()
        filter.m_logger.critical( "test_unsupported_element_types" )
        filter.SetInputDataObject( grid )
        filter.setPaintUnsupportedElementTypes( 1 )
        filter.Update()
        result = filter.getGrid()
        assert result is not None
        # Verify the array was added
        unsupported_array = result.GetCellData().GetArray( "HasUnsupportedType" )
        assert unsupported_array is not None
        for i in range( 0, 4 ):
            assert unsupported_array.GetValue( i ) == 0  # Hexahedron should be supported
        for j in range( 4, 6 ):
            assert unsupported_array.GetValue( j ) == 1  # Quad should not be supported

    # TODO Needs parallelism to work
    # def test_unsupported_polyhedron( self ):
    #     """Test a grid with unsupported polyhedron"""
    #     # Create grid with unsupported polyhedron
    #     grid = create_unsupported_polyhedron_grid()
    #     # Apply the filter with painting enabled
    #     filter = SupportedElements()
    #     filter.m_logger.critical( "test_unsupported_polyhedron" )
    #     filter.SetInputDataObject( grid )
    #     filter.setPaintUnsupportedPolyhedrons( 1 )
    #     filter.Update()
    #     result = filter.getGrid()
    #     assert result is not None
    #     # Verify the array was added
    #     polyhedron_array = result.GetCellData().GetArray( "IsUnsupportedPolyhedron" )
    #     assert polyhedron_array is None
    #     # Since we created an unsupported polyhedron, it should be marked
    #     assert polyhedron_array.GetValue( 0 ) == 1

    def test_paint_flags( self ):
        """Test setting invalid paint flags"""
        filter = SupportedElements()
        # Should log an error but not raise an exception
        filter.setPaintUnsupportedElementTypes( 2 )  # Invalid value
        filter.setPaintUnsupportedPolyhedrons( 2 )  # Invalid value
        # Values should remain unchanged
        assert filter.m_paintUnsupportedElementTypes == 0
        assert filter.m_paintUnsupportedPolyhedrons == 0

    def test_set_chunk_size( self ):
        """Test that setChunkSize properly updates the chunk size"""
        # Create filter instance
        filter = SupportedElements()
        # Note the initial value
        initial_chunk_size = filter.m_chunk_size
        # Set a new chunk size
        new_chunk_size = 100
        filter.setChunkSize( new_chunk_size )
        # Verify the chunk size was updated
        assert filter.m_chunk_size == new_chunk_size
        assert filter.m_chunk_size != initial_chunk_size

    def test_set_num_proc( self ):
        """Test that setNumProc properly updates the number of processors"""
        # Create filter instance
        filter = SupportedElements()
        # Note the initial value
        initial_num_proc = filter.m_num_proc
        # Set a new number of processors
        new_num_proc = 4
        filter.setNumProc( new_num_proc )
        # Verify the number of processors was updated
        assert filter.m_num_proc == new_num_proc
        assert filter.m_num_proc != initial_num_proc
