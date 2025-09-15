import pytest
import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkStructuredGrid, VTK_TETRA, VTK_HEXAHEDRON
from geos.mesh.utils.genericHelpers import createSingleCellMesh
from geos.mesh.io.vtkIO import ( VtkFormat, VtkOutput, read_mesh, read_unstructured_grid, write_mesh, READER_MAP,
                                 WRITER_MAP )

__doc__ = """
Test module for vtkIO module.
Tests the functionality of reading and writing various VTK file formats.
"""


@pytest.fixture( scope="module" )
def simple_unstructured_mesh():
    """Fixture for a simple unstructured mesh with tetrahedron."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )


@pytest.fixture( scope="module" )
def simple_hex_mesh():
    """Fixture for a simple hexahedron mesh."""
    return createSingleCellMesh(
        VTK_HEXAHEDRON,
        np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ], [ 1, 0, 1 ], [ 1, 1, 1 ],
                    [ 0, 1, 1 ] ] ) )


@pytest.fixture( scope="module" )
def structured_mesh():
    """Fixture for a simple structured grid."""
    mesh = vtkStructuredGrid()
    mesh.SetDimensions( 2, 2, 2 )

    points = vtkPoints()
    for k in range( 2 ):
        for j in range( 2 ):
            for i in range( 2 ):
                points.InsertNextPoint( i, j, k )

    mesh.SetPoints( points )
    return mesh


class TestVtkFormat:
    """Test class for VtkFormat enumeration."""

    def test_vtk_format_values( self ):
        """Test that VtkFormat enum has correct values."""
        assert VtkFormat.VTK.value == ".vtk"
        assert VtkFormat.VTS.value == ".vts"
        assert VtkFormat.VTU.value == ".vtu"
        assert VtkFormat.PVTU.value == ".pvtu"
        assert VtkFormat.PVTS.value == ".pvts"

    def test_vtk_format_from_string( self ):
        """Test creating VtkFormat from string values."""
        assert VtkFormat( ".vtk" ) == VtkFormat.VTK
        assert VtkFormat( ".vtu" ) == VtkFormat.VTU
        assert VtkFormat( ".vts" ) == VtkFormat.VTS
        assert VtkFormat( ".pvtu" ) == VtkFormat.PVTU
        assert VtkFormat( ".pvts" ) == VtkFormat.PVTS

    def test_invalid_format( self ):
        """Test that invalid format raises ValueError."""
        with pytest.raises( ValueError ):
            VtkFormat( ".invalid" )


class TestVtkOutput:
    """Test class for VtkOutput dataclass."""

    def test_vtk_output_creation( self ):
        """Test VtkOutput creation with default parameters."""
        output = VtkOutput( "test.vtu" )
        assert output.output == "test.vtu"
        assert output.is_data_mode_binary is True

    def test_vtk_output_creation_custom( self ):
        """Test VtkOutput creation with custom parameters."""
        output = VtkOutput( "test.vtu", is_data_mode_binary=False )
        assert output.output == "test.vtu"
        assert output.is_data_mode_binary is False

    def test_vtk_output_immutable( self ):
        """Test that VtkOutput is immutable (frozen dataclass)."""
        output = VtkOutput( "test.vtu" )
        with pytest.raises( AttributeError ):
            output.output = "new_test.vtu"


class TestMappings:
    """Test class for reader and writer mappings."""

    def test_reader_map_completeness( self ):
        """Test that READER_MAP contains all readable formats."""
        expected_formats = { VtkFormat.VTK, VtkFormat.VTS, VtkFormat.VTU, VtkFormat.PVTU, VtkFormat.PVTS }
        assert set( READER_MAP.keys() ) == expected_formats

    def test_writer_map_completeness( self ):
        """Test that WRITER_MAP contains all writable formats."""
        expected_formats = { VtkFormat.VTK, VtkFormat.VTS, VtkFormat.VTU }
        assert set( WRITER_MAP.keys() ) == expected_formats

    def test_reader_map_classes( self ):
        """Test that READER_MAP contains valid reader classes."""
        for format_type, reader_class in READER_MAP.items():
            assert hasattr( reader_class, '__name__' )
            # All readers should be classes
            assert isinstance( reader_class, type )

    def test_writer_map_classes( self ):
        """Test that WRITER_MAP contains valid writer classes."""
        for format_type, writer_class in WRITER_MAP.items():
            assert hasattr( writer_class, '__name__' )
            # All writers should be classes
            assert isinstance( writer_class, type )


class TestWriteMesh:
    """Test class for write_mesh functionality."""

    def test_write_vtu_binary( self, simple_unstructured_mesh, tmp_path ):
        """Test writing VTU file in binary mode."""
        output_file = tmp_path / "test_mesh.vtu"
        vtk_output = VtkOutput( str( output_file ), is_data_mode_binary=True )

        result = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )

        assert result == 1  # VTK success code
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_vtu_ascii( self, simple_unstructured_mesh, tmp_path ):
        """Test writing VTU file in ASCII mode."""
        output_file = tmp_path / "test_mesh_ascii.vtu"
        vtk_output = VtkOutput( str( output_file ), is_data_mode_binary=False )

        result = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )

        assert result == 1  # VTK success code
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_vtk_format( self, simple_unstructured_mesh, tmp_path ):
        """Test writing VTK legacy format."""
        output_file = tmp_path / "test_mesh.vtk"
        vtk_output = VtkOutput( str( output_file ) )

        result = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )

        assert result == 1  # VTK success code
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_vts_format( self, structured_mesh, tmp_path ):
        """Test writing VTS (structured grid) format."""
        output_file = tmp_path / "test_mesh.vts"
        vtk_output = VtkOutput( str( output_file ) )

        result = write_mesh( structured_mesh, vtk_output, can_overwrite=True )

        assert result == 1  # VTK success code
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_file_exists_error( self, simple_unstructured_mesh, tmp_path ):
        """Test that writing to existing file raises error when can_overwrite=False."""
        output_file = tmp_path / "existing_file.vtu"
        output_file.write_text( "dummy content" )  # Create existing file

        vtk_output = VtkOutput( str( output_file ) )

        with pytest.raises( FileExistsError, match="already exists" ):
            write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=False )

    def test_write_unsupported_format( self, simple_unstructured_mesh, tmp_path ):
        """Test that writing unsupported format raises ValueError."""
        output_file = tmp_path / "test_mesh.unsupported"
        vtk_output = VtkOutput( str( output_file ) )

        with pytest.raises( ValueError, match="not supported" ):
            write_mesh( simple_unstructured_mesh, vtk_output )

    def test_write_overwrite_allowed( self, simple_unstructured_mesh, tmp_path ):
        """Test that overwriting is allowed when can_overwrite=True."""
        output_file = tmp_path / "overwrite_test.vtu"
        vtk_output = VtkOutput( str( output_file ) )

        # First write
        result1 = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )
        assert result1 == 1
        assert output_file.exists()

        # Second write (overwrite)
        result2 = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )
        assert result2 == 1
        assert output_file.exists()


class TestReadMesh:
    """Test class for read_mesh functionality."""

    def test_read_nonexistent_file( self ):
        """Test that reading nonexistent file raises FileNotFoundError."""
        with pytest.raises( FileNotFoundError, match="does not exist" ):
            read_mesh( "nonexistent_file.vtu" )

    def test_read_vtu_file( self, simple_unstructured_mesh, tmp_path ):
        """Test reading VTU file."""
        output_file = tmp_path / "test_read.vtu"
        vtk_output = VtkOutput( str( output_file ) )

        # First write the file
        write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )

        # Then read it back
        read_mesh_result = read_mesh( str( output_file ) )

        assert read_mesh_result is not None
        assert isinstance( read_mesh_result, vtkUnstructuredGrid )
        assert read_mesh_result.GetNumberOfPoints() == simple_unstructured_mesh.GetNumberOfPoints()
        assert read_mesh_result.GetNumberOfCells() == simple_unstructured_mesh.GetNumberOfCells()

    def test_read_vtk_file( self, simple_unstructured_mesh, tmp_path ):
        """Test reading VTK legacy file."""
        output_file = tmp_path / "test_read.vtk"
        vtk_output = VtkOutput( str( output_file ) )

        # First write the file
        write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )

        # Then read it back
        read_mesh_result = read_mesh( str( output_file ) )

        assert read_mesh_result is not None
        assert isinstance( read_mesh_result, vtkUnstructuredGrid )
        assert read_mesh_result.GetNumberOfPoints() == simple_unstructured_mesh.GetNumberOfPoints()
        assert read_mesh_result.GetNumberOfCells() == simple_unstructured_mesh.GetNumberOfCells()

    def test_read_vts_file( self, structured_mesh, tmp_path ):
        """Test reading VTS (structured grid) file."""
        output_file = tmp_path / "test_read.vts"
        vtk_output = VtkOutput( str( output_file ) )

        # First write the file
        write_mesh( structured_mesh, vtk_output, can_overwrite=True )

        # Then read it back
        read_mesh_result = read_mesh( str( output_file ) )

        assert read_mesh_result is not None
        assert isinstance( read_mesh_result, vtkStructuredGrid )
        assert read_mesh_result.GetNumberOfPoints() == structured_mesh.GetNumberOfPoints()

    def test_read_unknown_extension( self, simple_unstructured_mesh, tmp_path ):
        """Test reading file with unknown extension falls back to trying all readers."""
        # Create a VTU file but with unknown extension
        vtu_file = tmp_path / "test.vtu"
        unknown_file = tmp_path / "test.unknown"

        # Write as VTU first
        vtk_output = VtkOutput( str( vtu_file ) )
        write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )

        # Copy to unknown extension
        unknown_file.write_bytes( vtu_file.read_bytes() )

        # Should still be able to read it
        read_mesh_result = read_mesh( str( unknown_file ) )

        assert read_mesh_result is not None
        assert isinstance( read_mesh_result, vtkUnstructuredGrid )

    def test_read_invalid_file_content( self, tmp_path ):
        """Test that reading invalid file content raises ValueError."""
        invalid_file = tmp_path / "invalid.vtu"
        invalid_file.write_text( "This is not a valid VTU file" )

        with pytest.raises( ValueError, match="Could not find a suitable reader" ):
            read_mesh( str( invalid_file ) )


class TestReadUnstructuredGrid:
    """Test class for read_unstructured_grid functionality."""

    def test_read_unstructured_grid_success( self, simple_unstructured_mesh, tmp_path ):
        """Test successfully reading an unstructured grid."""
        output_file = tmp_path / "test_ug.vtu"
        vtk_output = VtkOutput( str( output_file ) )

        # Write unstructured grid
        write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )

        # Read back as unstructured grid
        result = read_unstructured_grid( str( output_file ) )

        assert isinstance( result, vtkUnstructuredGrid )
        assert result.GetNumberOfPoints() == simple_unstructured_mesh.GetNumberOfPoints()
        assert result.GetNumberOfCells() == simple_unstructured_mesh.GetNumberOfCells()

    def test_read_unstructured_grid_wrong_type( self, structured_mesh, tmp_path ):
        """Test that reading non-unstructured grid raises TypeError."""
        output_file = tmp_path / "test_sg.vts"
        vtk_output = VtkOutput( str( output_file ) )

        # Write structured grid
        write_mesh( structured_mesh, vtk_output, can_overwrite=True )

        # Try to read as unstructured grid - should fail
        with pytest.raises( TypeError, match="not the expected vtkUnstructuredGrid" ):
            read_unstructured_grid( str( output_file ) )

    def test_read_unstructured_grid_nonexistent( self ):
        """Test that reading nonexistent file raises FileNotFoundError."""
        with pytest.raises( FileNotFoundError, match="does not exist" ):
            read_unstructured_grid( "nonexistent.vtu" )


class TestRoundTripReadWrite:
    """Test class for round-trip read/write operations."""

    def test_vtu_round_trip_binary( self, simple_unstructured_mesh, tmp_path ):
        """Test round-trip write and read for VTU binary format."""
        output_file = tmp_path / "roundtrip_binary.vtu"
        vtk_output = VtkOutput( str( output_file ), is_data_mode_binary=True )

        # Write
        write_result = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )
        assert write_result == 1

        # Read back
        read_result = read_unstructured_grid( str( output_file ) )

        # Compare
        assert read_result.GetNumberOfPoints() == simple_unstructured_mesh.GetNumberOfPoints()
        assert read_result.GetNumberOfCells() == simple_unstructured_mesh.GetNumberOfCells()

        # Check point coordinates are preserved
        for i in range( read_result.GetNumberOfPoints() ):
            orig_point = simple_unstructured_mesh.GetPoint( i )
            read_point = read_result.GetPoint( i )
            np.testing.assert_array_almost_equal( orig_point, read_point, decimal=6 )

    def test_vtu_round_trip_ascii( self, simple_unstructured_mesh, tmp_path ):
        """Test round-trip write and read for VTU ASCII format."""
        output_file = tmp_path / "roundtrip_ascii.vtu"
        vtk_output = VtkOutput( str( output_file ), is_data_mode_binary=False )

        # Write
        write_result = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )
        assert write_result == 1

        # Read back
        read_result = read_unstructured_grid( str( output_file ) )

        # Compare
        assert read_result.GetNumberOfPoints() == simple_unstructured_mesh.GetNumberOfPoints()
        assert read_result.GetNumberOfCells() == simple_unstructured_mesh.GetNumberOfCells()

    def test_vtk_round_trip( self, simple_unstructured_mesh, tmp_path ):
        """Test round-trip write and read for VTK legacy format."""
        output_file = tmp_path / "roundtrip.vtk"
        vtk_output = VtkOutput( str( output_file ) )

        # Write
        write_result = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )
        assert write_result == 1

        # Read back
        read_result = read_unstructured_grid( str( output_file ) )

        # Compare
        assert read_result.GetNumberOfPoints() == simple_unstructured_mesh.GetNumberOfPoints()
        assert read_result.GetNumberOfCells() == simple_unstructured_mesh.GetNumberOfCells()

    def test_vts_round_trip( self, structured_mesh, tmp_path ):
        """Test round-trip write and read for VTS format."""
        output_file = tmp_path / "roundtrip.vts"
        vtk_output = VtkOutput( str( output_file ) )

        # Write
        write_result = write_mesh( structured_mesh, vtk_output, can_overwrite=True )
        assert write_result == 1

        # Read back
        read_result = read_mesh( str( output_file ) )

        # Compare
        assert isinstance( read_result, vtkStructuredGrid )
        assert read_result.GetNumberOfPoints() == structured_mesh.GetNumberOfPoints()


class TestEdgeCases:
    """Test class for edge cases and error conditions."""

    def test_empty_mesh_write( self, tmp_path ):
        """Test writing an empty mesh."""
        empty_mesh = vtkUnstructuredGrid()
        output_file = tmp_path / "empty.vtu"
        vtk_output = VtkOutput( str( output_file ) )

        result = write_mesh( empty_mesh, vtk_output, can_overwrite=True )
        assert result == 1
        assert output_file.exists()

    def test_empty_mesh_round_trip( self, tmp_path ):
        """Test round-trip with empty mesh."""
        empty_mesh = vtkUnstructuredGrid()
        output_file = tmp_path / "empty_roundtrip.vtu"
        vtk_output = VtkOutput( str( output_file ) )

        # Write
        write_result = write_mesh( empty_mesh, vtk_output, can_overwrite=True )
        assert write_result == 1

        # Read back
        read_result = read_unstructured_grid( str( output_file ) )
        assert read_result.GetNumberOfPoints() == 0
        assert read_result.GetNumberOfCells() == 0

    def test_large_path_names( self, simple_unstructured_mesh, tmp_path ):
        """Test handling of long file paths."""
        # Create a deep directory structure
        deep_dir = tmp_path
        for i in range( 5 ):
            deep_dir = deep_dir / f"very_long_directory_name_level_{i}"
        deep_dir.mkdir( parents=True )

        output_file = deep_dir / "mesh_with_very_long_filename_that_should_still_work.vtu"
        vtk_output = VtkOutput( str( output_file ) )

        # Should work fine
        result = write_mesh( simple_unstructured_mesh, vtk_output, can_overwrite=True )
        assert result == 1
        assert output_file.exists()

        # And read back
        read_result = read_unstructured_grid( str( output_file ) )
        assert read_result.GetNumberOfPoints() == simple_unstructured_mesh.GetNumberOfPoints()
