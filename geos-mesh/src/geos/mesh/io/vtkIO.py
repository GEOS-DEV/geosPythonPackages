# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Type, TypeAlias
from vtkmodules.vtkCommonDataModel import vtkPointSet, vtkUnstructuredGrid
from vtkmodules.vtkIOCore import vtkWriter
from vtkmodules.vtkIOLegacy import vtkDataReader, vtkUnstructuredGridWriter, vtkUnstructuredGridReader
from vtkmodules.vtkIOXML import ( vtkXMLDataReader, vtkXMLUnstructuredGridReader, vtkXMLUnstructuredGridWriter,
                                  vtkXMLWriter, vtkXMLStructuredGridReader, vtkXMLPUnstructuredGridReader,
                                  vtkXMLPStructuredGridReader, vtkXMLStructuredGridWriter )
from geos.utils.Logger import getLogger

__doc__ = """
Input and Output methods for various VTK mesh formats.
Supports reading: .vtk, .vtu, .vts, .pvtu, .pvts
Supports writing: .vtk, .vtu, .vts
"""

io_logger = getLogger( "IO for geos-mesh" )
io_logger.propagate = False


class VtkFormat( Enum ):
    """Enumeration for supported VTK file formats and their extensions."""
    VTK = ".vtk"
    VTS = ".vts"
    VTU = ".vtu"
    PVTU = ".pvtu"
    PVTS = ".pvts"


# Improved: Use TypeAlias for cleaner and more readable type hints
VtkReaderClass: TypeAlias = Type[ vtkDataReader | vtkXMLDataReader ]
VtkWriterClass: TypeAlias = Type[ vtkWriter | vtkXMLWriter ]

# Centralized mapping of formats to their corresponding reader classes
READER_MAP: dict[ VtkFormat, VtkReaderClass ] = {
    VtkFormat.VTK: vtkUnstructuredGridReader,
    VtkFormat.VTS: vtkXMLStructuredGridReader,
    VtkFormat.VTU: vtkXMLUnstructuredGridReader,
    VtkFormat.PVTU: vtkXMLPUnstructuredGridReader,
    VtkFormat.PVTS: vtkXMLPStructuredGridReader
}

# Centralized mapping of formats to their corresponding writer classes
WRITER_MAP: dict[ VtkFormat, VtkWriterClass ] = {
    VtkFormat.VTK: vtkUnstructuredGridWriter,
    VtkFormat.VTS: vtkXMLStructuredGridWriter,
    VtkFormat.VTU: vtkXMLUnstructuredGridWriter,
}


@dataclass( frozen=True )
class VtkOutput:
    """Configuration for writing a VTK file."""
    output: str
    is_data_mode_binary: bool = True


def _read_data( filepath: str, reader_class: VtkReaderClass ) -> Optional[ vtkPointSet ]:
    """Generic helper to read a VTK file using a specific reader class.

    Args:
        filepath (str): Path to the VTK file.
        reader_class (VtkReaderClass): The VTK reader class to use.

    Returns:
        Optional[ vtkPointSet ]: The read VTK point set, or None if reading failed.
    """
    reader = reader_class()
    io_logger.info( f"Attempting to read '{filepath}' with {reader_class.__name__}..." )

    reader.SetFileName( str( filepath ) )

    # For XML-based readers, CanReadFile is a reliable and fast pre-check.
    if hasattr( reader, 'CanReadFile' ) and not reader.CanReadFile( filepath ):
        io_logger.error( f"Reader {reader_class.__name__} reports it cannot read file '{filepath}'." )
        return None

    reader.Update()

    # FIX: Check the reader's error code. This is the most reliable way to
    # detect a failed read, as GetOutput() can return a default empty object on failure.
    if hasattr( reader, 'GetErrorCode' ) and reader.GetErrorCode() != 0:
        io_logger.warning(
            f"VTK reader {reader_class.__name__} reported an error code after attempting to read '{filepath}'." )
        return None

    output = reader.GetOutput()

    if output is None:
        return None

    io_logger.info( "Read successful." )
    return output


def _write_data( mesh: vtkPointSet, writer_class: VtkWriterClass, output: str, is_binary: bool ) -> int:
    """Generic helper to write a VTK file using a specific writer class.

    Args:
        mesh (vtkPointSet): The grid data to write.
        writer_class (VtkWriterClass): The VTK writer class to use.
        output (str): The output file path.
        is_binary (bool): Whether to write the file in binary mode.

    Returns:
        int: The result of the write operation.
    """
    io_logger.info( f"Writing mesh to '{output}' using {writer_class.__name__}..." )
    writer = writer_class()
    writer.SetFileName( output )
    writer.SetInputData( mesh )

    # Set data mode only for XML writers that support it
    if isinstance( writer, vtkXMLWriter ):
        if is_binary:
            writer.SetDataModeToBinary()
            io_logger.info( "Data mode set to Binary." )
        else:
            writer.SetDataModeToAscii()
            io_logger.info( "Data mode set to ASCII." )

    return writer.Write()


def read_mesh( filepath: str ) -> vtkPointSet:
    """
    Reads a VTK file, automatically detecting the format.

    It first tries the reader associated with the file extension, then falls
    back to trying all other available readers if the first attempt fails.

    Args:
        filepath (str): The path to the VTK file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If no suitable reader can be found for the file.

    Returns:
        vtkPointSet: The resulting mesh data.
    """
    filepath_path: Path = Path( filepath )
    if not filepath_path.exists():
        raise FileNotFoundError( f"Invalid file path: '{filepath}' does not exist." )

    candidate_readers: list[ VtkReaderClass ] = []
    # 1. Prioritize the reader associated with the file extension
    try:
        file_format = VtkFormat( filepath_path.suffix )
        if file_format in READER_MAP:
            candidate_readers.append( READER_MAP[ file_format ] )
    except ValueError:
        io_logger.warning( f"Unknown file extension '{filepath_path.suffix}'. Trying all available readers." )

    # 2. Add all other unique readers as fallbacks
    for reader_cls in READER_MAP.values():
        if reader_cls not in candidate_readers:
            candidate_readers.append( reader_cls )

    # 3. Attempt to read with the candidates in order
    for reader_class in candidate_readers:
        output_mesh = _read_data( filepath, reader_class )
        if output_mesh:
            return output_mesh

    raise ValueError( f"Could not find a suitable reader for '{filepath}'." )


def read_unstructured_grid( filepath: str ) -> vtkUnstructuredGrid:
    """
    Reads a VTK file and ensures it is a vtkUnstructuredGrid.

    This function uses the general `read_mesh` to load the data and then
    validates its type.

    Args:
        filepath (str): The path to the VTK file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If no suitable reader can be found for the file.
        TypeError: If the file is read successfully but is not a vtkUnstructuredGrid.

    Returns:
        vtkUnstructuredGrid: The resulting unstructured grid data.
    """
    io_logger.info( f"Reading file '{filepath}' and expecting vtkUnstructuredGrid." )
    mesh = read_mesh( filepath )

    if not isinstance( mesh, vtkUnstructuredGrid ):
        error_msg = ( f"File '{filepath}' was read successfully, but it is of type "
                      f"'{type(mesh).__name__}', not the expected vtkUnstructuredGrid." )
        io_logger.error( error_msg )
        raise TypeError( error_msg )

    io_logger.info( "Validation successful. Mesh is a vtkUnstructuredGrid." )
    return mesh


def write_mesh( mesh: vtkPointSet, vtk_output: VtkOutput, can_overwrite: bool = False ) -> int:
    """
    Writes a vtkPointSet to a file.

    The format is determined by the file extension in `VtkOutput.output`.

    Args:
        mesh (vtkPointSet): The grid data to write.
        vtk_output (VtkOutput): Configuration for the output file.
        can_overwrite (bool, optional): If False, raises an error if the file
                                      already exists. Defaults to False.

    Raises:
        FileExistsError: If the output file exists and `can_overwrite` is False.
        ValueError: If the file extension is not a supported write format.
        RuntimeError: If the VTK writer fails to write the file.

    Returns:
        int: Returns 1 on success, consistent with the VTK writer's return code.
    """
    output_path = Path( vtk_output.output )
    if output_path.exists() and not can_overwrite:
        raise FileExistsError( f"File '{output_path}' already exists. Set can_overwrite=True to replace it." )

    try:
        # Catch the ValueError from an invalid enum to provide a consistent error message.
        try:
            file_format = VtkFormat( output_path.suffix )
        except ValueError:
            # Re-raise with the message expected by the test.
            raise ValueError( f"Writing to extension '{output_path.suffix}' is not supported." )

        writer_class = WRITER_MAP.get( file_format )
        if not writer_class:
            raise ValueError( f"Writing to extension '{output_path.suffix}' is not supported." )

        success_code = _write_data( mesh, writer_class, str( output_path ), vtk_output.is_data_mode_binary )
        if not success_code:
            raise RuntimeError( f"VTK writer failed to write file '{output_path}'." )

        io_logger.info( f"Successfully wrote mesh to '{output_path}'." )
        return success_code

    except ( ValueError, RuntimeError ) as e:
        io_logger.error( e )
        raise
