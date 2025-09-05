import pytest
import numpy as np
from pathlib import Path
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    VTK_HEXAHEDRON,
    VTK_POLYHEDRON,
    VTK_QUADRATIC_TETRA,  # An example of an unsupported standard type
    vtkCellTypes )
from vtkmodules.util.numpy_support import vtk_to_numpy
from geos.mesh.doctor.actions.supported_elements import supported_cell_types
from geos.mesh.doctor.filters.SupportedElements import SupportedElements, supportedElements
from geos.mesh.utils.genericHelpers import createSingleCellMesh, createMultiCellMesh


@pytest.fixture
def good_mesh() -> vtkUnstructuredGrid:
    """Creates a mesh with only supported element types."""
    return createSingleCellMesh( VTK_HEXAHEDRON,
                                 np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ],
                                             [ 1, 0, 1 ], [ 1, 1, 1 ], [ 0, 1, 1 ] ] ) )


@pytest.fixture
def mesh_with_unsupported_std_type():
    """Creates a mesh containing an unsupported standard element type (VTK_QUADRATIC_TETRA)."""
    # Check that our chosen unsupported type is actually not in the supported list
    assert VTK_QUADRATIC_TETRA not in supported_cell_types
    return createMultiCellMesh( [ VTK_HEXAHEDRON, VTK_QUADRATIC_TETRA ],
                                [ np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ],
                                              [ 0, 0, 1 ], [ 1, 0, 1 ], [ 1, 1, 1 ], [ 0, 1, 1 ] ] ),
                                  np.array( [ [ 2, 0, 0 ], [ 3, 0, 0 ], [ 2.5, 1, 0 ], [ 2.5, 0.5, 1 ], [ 2.5, 0, 0 ],
                                              [ 2.75, 0.5, 0 ], [ 2.25, 0.5, 0 ], [ 2.75, 0.25, 0.5 ],
                                              [ 2.5, 0.75, 0.5 ], [ 2.25, 0.25, 0.5 ] ] ) ] )


@pytest.fixture
def mesh_with_unsupported_polyhedron() -> vtkUnstructuredGrid:
    """
    Creates a mesh with a convertible polyhedron (Hex) and a non-convertible one.
    The non-convertible one is a triangular bipyramid, which has 6 faces like a hex,
    but a different face-connectivity graph.
    """
    points = [ [ 0, 0, 0 ],  # points for the hex
               [ 1, 0, 0 ],
               [ 1, 1, 0 ],
               [ 0, 1, 0 ],
               [ 0, 0, 1 ],
               [ 1, 0, 1 ],
               [ 1, 1, 1 ],
               [ 0, 1, 1 ],
               [ 2, 0, 1 ],  # other points to add for bipyramid
               [ 3, -1, 0 ],
               [ 3, 1, 0 ],
               [ 1, 0, 0 ],
               [ 2, 0, -1 ] ]

    mesh: vtkUnstructuredGrid = createSingleCellMesh(
        VTK_HEXAHEDRON, np.array( [ points[ 0 ], points[ 1 ], points[ 2 ], points[ 3 ], points[ 4 ], points[ 5 ],
                                    points[ 6 ], points[ 7 ] ] ) )

    # Face stream for the triangular bipyramid (6 faces, 5 points)
    # Format: [num_faces, num_pts_face1, p1, p2, ..., num_pts_face2, p1, p2, ...]
    poly_faces = [
        6,  # Number of faces
        3,  # Face 0 (top)
        8,
        9,
        10,
        3,  # Face 1 (top)
        8,
        10,
        11,
        3,  # Face 2 (top)
        8,
        11,
        9,
        3,  # Face 3 (bottom)
        12,
        10,
        9,
        3,  # Face 4 (bottom)
        12,
        11,
        10,
        3,  # Face 5 (bottom)
        12,
        9,
        11
    ]
    # Insert the polyhedron cell
    face_stream = vtkIdList()
    face_stream.SetNumberOfIds( len( poly_faces ) )
    for i, val in enumerate( poly_faces ):
        face_stream.SetId( i, val )
    # Now, insert the polyhedron cell using the face stream
    mesh.InsertNextCell( VTK_POLYHEDRON, face_stream )
    return mesh


class TestSupportedElements:

    def test_initialization( self, good_mesh ):
        """Tests the constructor and default values."""
        filter_instance = SupportedElements( good_mesh )
        assert filter_instance.numProc == 1
        assert filter_instance.chunkSize == 1
        assert not filter_instance.writeUnsupportedElementTypes
        assert not filter_instance.writeUnsupportedPolyhedrons
        assert len( filter_instance.getUnsupportedElementTypes() ) == 0
        assert len( filter_instance.getUnsupportedPolyhedronElements() ) == 0

    def test_setters( self, good_mesh ):
        """Tests the various setter methods."""
        filt = SupportedElements( good_mesh )
        filt.setNumProc( 8 )
        assert filt.numProc == 8
        filt.setChunkSize( 2000 )
        assert filt.chunkSize == 2000
        filt.setWriteUnsupportedElementTypes( True )
        assert filt.writeUnsupportedElementTypes
        filt.setWriteUnsupportedPolyhedrons( True )
        assert filt.writeUnsupportedPolyhedrons

    def test_apply_on_good_mesh( self, good_mesh ):
        """Tests the filter on a mesh with no unsupported elements."""
        filt = SupportedElements( good_mesh )
        success = filt.applyFilter()
        assert success
        assert len( filt.getUnsupportedElementTypes() ) == 0
        assert len( filt.getUnsupportedPolyhedronElements() ) == 0

    def test_find_unsupported_std_types( self, mesh_with_unsupported_std_type ):
        """Tests detection of unsupported standard element types."""
        filt = SupportedElements( mesh_with_unsupported_std_type )
        success = filt.applyFilter()
        assert success

        unsupported_types = filt.getUnsupportedElementTypes()
        assert len( unsupported_types ) == 1

        type_name = vtkCellTypes.GetClassNameFromTypeId( VTK_QUADRATIC_TETRA )
        expected_str = f"Type {VTK_QUADRATIC_TETRA}: {type_name}"
        assert unsupported_types[ 0 ] == expected_str

        assert len( filt.getUnsupportedPolyhedronElements() ) == 0

    def test_find_unsupported_polyhedrons( self, mesh_with_unsupported_polyhedron ):
        """Tests detection of unsupported polyhedron elements."""
        filt = SupportedElements( mesh_with_unsupported_polyhedron, numProc=2, chunkSize=1 )
        success = filt.applyFilter()
        assert success

        unsupported_polys = filt.getUnsupportedPolyhedronElements()
        assert len( unsupported_polys ) == 1
        # The unsupported polyhedron is the second cell (index 1)
        assert unsupported_polys[ 0 ] == 1

        assert len( filt.getUnsupportedElementTypes() ) == 0

    def test_array_writing( self, mesh_with_unsupported_std_type, mesh_with_unsupported_polyhedron ):
        """Tests that CellData arrays are correctly added to the mesh."""
        # Test standard types array
        filt_std = SupportedElements( mesh_with_unsupported_std_type, writeUnsupportedElementTypes=True )
        filt_std.applyFilter()
        mesh_out_std = filt_std.getMesh()

        std_array = mesh_out_std.GetCellData().GetArray( "HasUnsupportedType" )
        assert std_array is not None
        std_np = vtk_to_numpy( std_array )
        # Cell 0 (Hex) is supported, Cell 1 (QuadTetra) is not.
        np.testing.assert_array_equal( std_np, [ 0, 1 ] )

        # Test polyhedrons array
        filt_poly = SupportedElements( mesh_with_unsupported_polyhedron, writeUnsupportedPolyhedrons=True )
        filt_poly.applyFilter()
        mesh_out_poly = filt_poly.getMesh()

        poly_array = mesh_out_poly.GetCellData().GetArray( "IsUnsupportedPolyhedron" )
        assert poly_array is not None
        poly_np = vtk_to_numpy( poly_array )
        # Cell 0 (Hex) is not an unsupported poly, Cell 1 is.
        np.testing.assert_array_equal( poly_np, [ 0, 1 ] )


def test_standalone_function( tmp_path, mesh_with_unsupported_polyhedron ):
    """Tests the standalone `supportedElements` function."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output_path = output_dir / "test_output.vtu"

    # Run the standalone function
    mesh, types, polys = supportedElements(
        mesh_with_unsupported_polyhedron,
        outputPath=str( output_path ),
        numProc=1,
        chunkSize=1,
        writeUnsupportedPolyhedrons=True  # Ensure array is written
    )

    # Verify returned values
    assert len( types ) == 0
    assert len( polys ) == 1
    assert polys[ 0 ] == 1

    # Verify file was written
    assert Path( output_path ).is_file()

    # Verify the mesh object returned has the new array
    array = mesh.GetCellData().GetArray( "IsUnsupportedPolyhedron" )
    assert array is not None
    np_array = vtk_to_numpy( array )
    np.testing.assert_array_equal( np_array, [ 0, 1 ] )
