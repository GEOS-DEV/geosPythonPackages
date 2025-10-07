import pytest
import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkStructuredGrid, VTK_TETRA
from geos.mesh.utils.genericHelpers import createSingleCellMesh
from geos.mesh.io.vtkIO import ( VtkFormat, VtkOutput, readMesh, readUnstructuredGrid, writeMesh, XML_FORMATS,
                                 WRITER_MAP )

__doc__ = """
Test module for vtkIO module.
Tests the functionality of reading and writing various VTK file formats.
"""


@pytest.fixture( scope="module" )
def simpleUnstructuredMesh():
    """Fixture for a simple unstructured mesh with tetrahedron."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )


@pytest.fixture( scope="module" )
def structuredMesh():
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

    def test_vtkFormatValues( self ):
        """Test that VtkFormat enum has correct values."""
        assert VtkFormat.VTK.value == ".vtk"
        assert VtkFormat.VTS.value == ".vts"
        assert VtkFormat.VTU.value == ".vtu"
        assert VtkFormat.VTI.value == ".vti"
        assert VtkFormat.VTP.value == ".vtp"
        assert VtkFormat.VTR.value == ".vtr"
        assert VtkFormat.PVTU.value == ".pvtu"
        assert VtkFormat.PVTS.value == ".pvts"
        assert VtkFormat.PVTI.value == ".pvti"
        assert VtkFormat.PVTP.value == ".pvtp"
        assert VtkFormat.PVTR.value == ".pvtr"

    def test_vtkFormatFromString( self ):
        """Test creating VtkFormat from string values."""
        assert VtkFormat( ".vtk" ) == VtkFormat.VTK
        assert VtkFormat( ".vtu" ) == VtkFormat.VTU
        assert VtkFormat( ".vts" ) == VtkFormat.VTS
        assert VtkFormat( ".vti" ) == VtkFormat.VTI
        assert VtkFormat( ".vtp" ) == VtkFormat.VTP
        assert VtkFormat( ".vtr" ) == VtkFormat.VTR
        assert VtkFormat( ".pvtu" ) == VtkFormat.PVTU
        assert VtkFormat( ".pvts" ) == VtkFormat.PVTS
        assert VtkFormat( ".pvti" ) == VtkFormat.PVTI
        assert VtkFormat( ".pvtp" ) == VtkFormat.PVTP
        assert VtkFormat( ".pvtr" ) == VtkFormat.PVTR

    def test_invalidFormat( self ):
        """Test that invalid format raises ValueError."""
        with pytest.raises( ValueError ):
            VtkFormat( ".invalid" )


class TestVtkOutput:
    """Test class for VtkOutput dataclass."""

    def test_vtkOutputCreation( self ):
        """Test VtkOutput creation with default parameters."""
        output = VtkOutput( "test.vtu" )
        assert output.output == "test.vtu"
        assert output.isDataModeBinary is True

    def test_vtkOutputCreationCustom( self ):
        """Test VtkOutput creation with custom parameters."""
        output = VtkOutput( "test.vtu", isDataModeBinary=False )
        assert output.output == "test.vtu"
        assert output.isDataModeBinary is False

    def test_vtkOutputImmutable( self ):
        """Test that VtkOutput is immutable (frozen dataclass)."""
        output = VtkOutput( "test.vtu" )
        with pytest.raises( AttributeError ):
            output.output = "new_test.vtu"


class TestMappings:
    """Test class for reader and writer mappings."""

    def test_xmlFormatsCompleteness( self ):
        """Test that XML_FORMATS contains all XML-based readable formats."""
        expectedFormats = {
            VtkFormat.VTU, VtkFormat.VTS, VtkFormat.VTI, VtkFormat.VTP, VtkFormat.VTR, VtkFormat.PVTU, VtkFormat.PVTS,
            VtkFormat.PVTI, VtkFormat.PVTP, VtkFormat.PVTR
        }
        assert XML_FORMATS == expectedFormats

    def test_writerMapCompleteness( self ):
        """Test that WRITER_MAP contains all writable formats."""
        expectedFormats = { VtkFormat.VTK, VtkFormat.VTS, VtkFormat.VTU }
        assert set( WRITER_MAP.keys() ) == expectedFormats

    def test_writerMapClasses( self ):
        """Test that WRITER_MAP contains valid writer classes."""
        for formatType, writerClass in WRITER_MAP.items():
            assert hasattr( writerClass, '__name__' )
            # All writers should be classes
            assert isinstance( writerClass, type )


class TestWriteMesh:
    """Test class for writeMesh functionality."""

    def test_writeVtuBinary( self, simpleUnstructuredMesh, tmp_path ):
        """Test writing VTU file in binary mode."""
        outputFile = tmp_path / "testMesh.vtu"
        vtkOutput = VtkOutput( str( outputFile ), isDataModeBinary=True )

        result = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )

        assert result == 1  # VTK success code
        assert outputFile.exists()
        assert outputFile.stat().st_size > 0

    def test_writeVtuAscii( self, simpleUnstructuredMesh, tmp_path ):
        """Test writing VTU file in ASCII mode."""
        outputFile = tmp_path / "testMesh_ascii.vtu"
        vtkOutput = VtkOutput( str( outputFile ), isDataModeBinary=False )

        result = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )

        assert result == 1  # VTK success code
        assert outputFile.exists()
        assert outputFile.stat().st_size > 0

    def test_writeVtkFormat( self, simpleUnstructuredMesh, tmp_path ):
        """Test writing VTK legacy format."""
        outputFile = tmp_path / "testMesh.vtk"
        vtkOutput = VtkOutput( str( outputFile ) )

        result = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )

        assert result == 1  # VTK success code
        assert outputFile.exists()
        assert outputFile.stat().st_size > 0

    def test_writeVtsFormat( self, structuredMesh, tmp_path ):
        """Test writing VTS (structured grid) format."""
        outputFile = tmp_path / "testMesh.vts"
        vtkOutput = VtkOutput( str( outputFile ) )

        result = writeMesh( structuredMesh, vtkOutput, canOverwrite=True )

        assert result == 1  # VTK success code
        assert outputFile.exists()
        assert outputFile.stat().st_size > 0

    def test_writeFileExistsError( self, simpleUnstructuredMesh, tmp_path ):
        """Test that writing to existing file raises error when canOverwrite=False."""
        outputFile = tmp_path / "existingFile.vtu"
        outputFile.write_text( "dummy content" )  # Create existing file

        vtkOutput = VtkOutput( str( outputFile ) )

        with pytest.raises( FileExistsError, match="already exists" ):
            writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=False )

    def test_writeUnsupportedFormat( self, simpleUnstructuredMesh, tmp_path ):
        """Test that writing unsupported format raises ValueError."""
        outputFile = tmp_path / "testMesh.unsupported"
        vtkOutput = VtkOutput( str( outputFile ) )

        with pytest.raises( ValueError, match="not supported" ):
            writeMesh( simpleUnstructuredMesh, vtkOutput )

    def test_writeOverwriteAllowed( self, simpleUnstructuredMesh, tmp_path ):
        """Test that overwriting is allowed when canOverwrite=True."""
        outputFile = tmp_path / "overwrite_test.vtu"
        vtkOutput = VtkOutput( str( outputFile ) )

        # First write
        result1 = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )
        assert result1 == 1
        assert outputFile.exists()

        # Second write (overwrite)
        result2 = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )
        assert result2 == 1
        assert outputFile.exists()


class TestReadMesh:
    """Test class for readMesh functionality."""

    def test_readNonexistentFile( self ):
        """Test that reading nonexistent file raises FileNotFoundError."""
        with pytest.raises( FileNotFoundError, match="does not exist" ):
            readMesh( "nonexistentFile.vtu" )

    def test_readVtuFile( self, simpleUnstructuredMesh, tmp_path ):
        """Test reading VTU file."""
        outputFile = tmp_path / "test_read.vtu"
        vtkOutput = VtkOutput( str( outputFile ) )

        # First write the file
        writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )

        # Then read it back
        readMeshResult = readMesh( str( outputFile ) )

        assert readMeshResult is not None
        assert isinstance( readMeshResult, vtkUnstructuredGrid )
        assert readMeshResult.GetNumberOfPoints() == simpleUnstructuredMesh.GetNumberOfPoints()
        assert readMeshResult.GetNumberOfCells() == simpleUnstructuredMesh.GetNumberOfCells()

    def test_readVtkFile( self, simpleUnstructuredMesh, tmp_path ):
        """Test reading VTK legacy file."""
        outputFile = tmp_path / "test_read.vtk"
        vtkOutput = VtkOutput( str( outputFile ) )

        # First write the file
        writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )

        # Then read it back
        readMeshResult = readMesh( str( outputFile ) )

        assert readMeshResult is not None
        assert isinstance( readMeshResult, vtkUnstructuredGrid )
        assert readMeshResult.GetNumberOfPoints() == simpleUnstructuredMesh.GetNumberOfPoints()
        assert readMeshResult.GetNumberOfCells() == simpleUnstructuredMesh.GetNumberOfCells()

    def test_readVtsFile( self, structuredMesh, tmp_path ):
        """Test reading VTS (structured grid) file."""
        outputFile = tmp_path / "test_read.vts"
        vtkOutput = VtkOutput( str( outputFile ) )

        # First write the file
        writeMesh( structuredMesh, vtkOutput, canOverwrite=True )

        # Then read it back
        readMeshResult = readMesh( str( outputFile ) )

        assert readMeshResult is not None
        assert isinstance( readMeshResult, vtkStructuredGrid )
        assert readMeshResult.GetNumberOfPoints() == structuredMesh.GetNumberOfPoints()

    def test_readUnknownExtension( self, simpleUnstructuredMesh, tmp_path ):
        """Test reading file with unknown extension falls back to trying all readers."""
        # Create a VTU file but with unknown extension
        vtuFile = tmp_path / "test.vtu"
        unknownFile = tmp_path / "test.unknown"

        # Write as VTU first
        vtkOutput = VtkOutput( str( vtuFile ) )
        writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )

        # Copy to unknown extension
        unknownFile.write_bytes( vtuFile.read_bytes() )

        # Should still be able to read it
        readMeshResult = readMesh( str( unknownFile ) )

        assert readMeshResult is not None
        assert isinstance( readMeshResult, vtkUnstructuredGrid )

    def test_readInvalidFileContent( self, tmp_path ):
        """Test that reading invalid file content raises ValueError."""
        invalidFile = tmp_path / "invalid.vtu"
        invalidFile.write_text( "This is not a valid VTU file" )

        with pytest.raises( ValueError, match="Failed to read file" ):
            readMesh( str( invalidFile ) )


class TestReadUnstructuredGrid:
    """Test class for readUnstructuredGrid functionality."""

    def test_readUnstructuredGridSuccess( self, simpleUnstructuredMesh, tmp_path ):
        """Test successfully reading an unstructured grid."""
        outputFile = tmp_path / "test_ug.vtu"
        vtkOutput = VtkOutput( str( outputFile ) )

        # Write unstructured grid
        writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )

        # Read back as unstructured grid
        result = readUnstructuredGrid( str( outputFile ) )

        assert isinstance( result, vtkUnstructuredGrid )
        assert result.GetNumberOfPoints() == simpleUnstructuredMesh.GetNumberOfPoints()
        assert result.GetNumberOfCells() == simpleUnstructuredMesh.GetNumberOfCells()

    def test_readUnstructuredGridWrongType( self, structuredMesh, tmp_path ):
        """Test that reading non-unstructured grid raises TypeError."""
        outputFile = tmp_path / "test_sg.vts"
        vtkOutput = VtkOutput( str( outputFile ) )

        # Write structured grid
        writeMesh( structuredMesh, vtkOutput, canOverwrite=True )

        # Try to read as unstructured grid - should fail
        with pytest.raises( TypeError, match="not the expected vtkUnstructuredGrid" ):
            readUnstructuredGrid( str( outputFile ) )

    def test_readUnstructuredGrid_nonexistent( self ):
        """Test that reading nonexistent file raises FileNotFoundError."""
        with pytest.raises( FileNotFoundError, match="does not exist" ):
            readUnstructuredGrid( "nonexistent.vtu" )


class TestRoundTripReadWrite:
    """Test class for round-trip read/write operations."""

    def test_vtuRoundTripBinary( self, simpleUnstructuredMesh, tmp_path ):
        """Test round-trip write and read for VTU binary format."""
        outputFile = tmp_path / "roundtrip_binary.vtu"
        vtkOutput = VtkOutput( str( outputFile ), isDataModeBinary=True )

        # Write
        writeResult = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )
        assert writeResult == 1

        # Read back
        readResult = readUnstructuredGrid( str( outputFile ) )

        # Compare
        assert readResult.GetNumberOfPoints() == simpleUnstructuredMesh.GetNumberOfPoints()
        assert readResult.GetNumberOfCells() == simpleUnstructuredMesh.GetNumberOfCells()

        # Check point coordinates are preserved
        for i in range( readResult.GetNumberOfPoints() ):
            origPoint = simpleUnstructuredMesh.GetPoint( i )
            readPoint = readResult.GetPoint( i )
            np.testing.assert_array_almost_equal( origPoint, readPoint, decimal=6 )

    def test_vtuRoundTripAscii( self, simpleUnstructuredMesh, tmp_path ):
        """Test round-trip write and read for VTU ASCII format."""
        outputFile = tmp_path / "roundtrip_ascii.vtu"
        vtkOutput = VtkOutput( str( outputFile ), isDataModeBinary=False )

        # Write
        writeResult = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )
        assert writeResult == 1

        # Read back
        readResult = readUnstructuredGrid( str( outputFile ) )

        # Compare
        assert readResult.GetNumberOfPoints() == simpleUnstructuredMesh.GetNumberOfPoints()
        assert readResult.GetNumberOfCells() == simpleUnstructuredMesh.GetNumberOfCells()

    def test_vtkRoundTrip( self, simpleUnstructuredMesh, tmp_path ):
        """Test round-trip write and read for VTK legacy format."""
        outputFile = tmp_path / "roundtrip.vtk"
        vtkOutput = VtkOutput( str( outputFile ) )

        # Write
        writeResult = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )
        assert writeResult == 1

        # Read back
        readResult = readUnstructuredGrid( str( outputFile ) )

        # Compare
        assert readResult.GetNumberOfPoints() == simpleUnstructuredMesh.GetNumberOfPoints()
        assert readResult.GetNumberOfCells() == simpleUnstructuredMesh.GetNumberOfCells()

    def test_vtsRoundTrip( self, structuredMesh, tmp_path ):
        """Test round-trip write and read for VTS format."""
        outputFile = tmp_path / "roundtrip.vts"
        vtkOutput = VtkOutput( str( outputFile ) )

        # Write
        writeResult = writeMesh( structuredMesh, vtkOutput, canOverwrite=True )
        assert writeResult == 1

        # Read back
        readResult = readMesh( str( outputFile ) )

        # Compare
        assert isinstance( readResult, vtkStructuredGrid )
        assert readResult.GetNumberOfPoints() == structuredMesh.GetNumberOfPoints()


class TestEdgeCases:
    """Test class for edge cases and error conditions."""

    def test_emptyMeshWrite( self, tmp_path ):
        """Test writing an empty mesh."""
        emptyMesh = vtkUnstructuredGrid()
        outputFile = tmp_path / "empty.vtu"
        vtkOutput = VtkOutput( str( outputFile ) )

        result = writeMesh( emptyMesh, vtkOutput, canOverwrite=True )
        assert result == 1
        assert outputFile.exists()

    def test_emptyMeshRoundTrip( self, tmp_path ):
        """Test round-trip with empty mesh."""
        emptyMesh = vtkUnstructuredGrid()
        outputFile = tmp_path / "empty_roundtrip.vtu"
        vtkOutput = VtkOutput( str( outputFile ) )

        # Write
        writeResult = writeMesh( emptyMesh, vtkOutput, canOverwrite=True )
        assert writeResult == 1

        # Read back
        readResult = readUnstructuredGrid( str( outputFile ) )
        assert readResult.GetNumberOfPoints() == 0
        assert readResult.GetNumberOfCells() == 0

    def test_largePathNames( self, simpleUnstructuredMesh, tmp_path ):
        """Test handling of long file paths."""
        # Create a deep directory structure
        deepDir = tmp_path
        for i in range( 5 ):
            deepDir = deepDir / f"very_long_directory_name_level_{i}"
        deepDir.mkdir( parents=True )

        outputFile = deepDir / "mesh_with_very_longFilename_that_should_still_work.vtu"
        vtkOutput = VtkOutput( str( outputFile ) )

        # Should work fine
        result = writeMesh( simpleUnstructuredMesh, vtkOutput, canOverwrite=True )
        assert result == 1
        assert outputFile.exists()

        # And read back
        readResult = readUnstructuredGrid( str( outputFile ) )
        assert readResult.GetNumberOfPoints() == simpleUnstructuredMesh.GetNumberOfPoints()
