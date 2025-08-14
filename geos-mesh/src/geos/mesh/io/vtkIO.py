# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from dataclasses import dataclass
from enum import Enum
import os.path
from typing import Optional
from vtkmodules.vtkCommonDataModel import vtkPointSet, vtkUnstructuredGrid
from vtkmodules.vtkIOCore import vtkWriter
from vtkmodules.vtkIOLegacy import vtkDataReader, vtkUnstructuredGridWriter, vtkUnstructuredGridReader
from vtkmodules.vtkIOXML import ( vtkXMLDataReader, vtkXMLUnstructuredGridReader, vtkXMLUnstructuredGridWriter,
                                  vtkXMLWriter, vtkXMLStructuredGridReader, vtkXMLPUnstructuredGridReader,
                                  vtkXMLPStructuredGridReader, vtkXMLStructuredGridWriter )
from geos.utils.Logger import getLogger

__doc__ = """
Input and Ouput methods for VTK meshes:
    - VTK, VTU, VTS, PVTU, PVTS readers
    - VTK, VTS, VTU writers
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


# Centralized mapping of formats to their corresponding reader classes
READER_MAP: dict[ VtkFormat, vtkDataReader | vtkXMLDataReader ] = {
    VtkFormat.VTK: vtkUnstructuredGridReader,
    VtkFormat.VTS: vtkXMLStructuredGridReader,
    VtkFormat.VTU: vtkXMLUnstructuredGridReader,
    VtkFormat.PVTU: vtkXMLPUnstructuredGridReader,
    VtkFormat.PVTS: vtkXMLPStructuredGridReader
}

# Centralized mapping of formats to their corresponding writer classes
WRITER_MAP: dict[ VtkFormat, vtkWriter | vtkXMLWriter ] = {
    VtkFormat.VTK: vtkUnstructuredGridWriter,
    VtkFormat.VTS: vtkXMLStructuredGridWriter,
    VtkFormat.VTU: vtkXMLUnstructuredGridWriter,
}


@dataclass( frozen=True )
class VtkOutput:
    """Configuration for writing a VTK file."""
    output: str
    is_data_mode_binary: bool = True


def _read_data( filepath: str, reader_class: vtkDataReader | vtkXMLDataReader ) -> Optional[ vtkPointSet ]:
    """Generic helper to read a VTK file using a specific reader class."""
    reader: vtkDataReader | vtkXMLDataReader = reader_class()
    io_logger.info( f"Attempting to read '{filepath}' with {reader_class.__name__}..." )

    # VTK readers have different methods to check file compatibility
    can_read: bool = False
    if hasattr( reader, 'CanReadFile' ):
        can_read = reader.CanReadFile( filepath )
    elif hasattr( reader, 'IsFileUnstructuredGrid' ):  # Legacy reader
        can_read = reader.IsFileUnstructuredGrid()

    if can_read:
        reader.SetFileName( filepath )
        reader.Update()
        io_logger.info( "Read successful." )
        return reader.GetOutput()

    io_logger.info( "Reader did not match the file format." )
    return None


def _write_data( mesh: vtkPointSet, writer_class: vtkWriter | vtkXMLWriter, output_path: str, is_binary: bool ) -> int:
    """Generic helper to write a VTK file using a specific writer class."""
    io_logger.info( f"Writing mesh to '{output_path}' using {writer_class.__name__}..." )
    writer: vtkWriter | vtkXMLWriter = writer_class()
    writer.SetFileName( output_path )
    writer.SetInputData( mesh )

    # Set data mode only for XML writers that support it
    if hasattr( writer, 'SetDataModeToBinary' ):
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
    back to trying all available readers if the first attempt fails.

    Args:
        filepath (str): The path to the VTK file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If no suitable reader can be found for the file.

    Returns:
        vtkPointSet: The resulting mesh data.
    """
    if not os.path.exists( filepath ):
        raise FileNotFoundError( f"Invalid file path: '{filepath}' does not exist." )

    _, extension = os.path.splitext( filepath )
    output_mesh: Optional[ vtkPointSet ] = None

    # 1. Try the reader associated with the file extension first
    try:
        file_format = VtkFormat( extension )
        if file_format in READER_MAP:
            reader_class = READER_MAP[ file_format ]
            output_mesh = _read_data( filepath, reader_class )
    except ValueError:
        io_logger.warning( f"Unknown file extension '{extension}'. Trying all readers." )

    # 2. If the first attempt failed or extension was unknown, try all readers
    if not output_mesh:
        for reader_class in set( READER_MAP.values() ):  # Use set to avoid duplicates
            output_mesh = _read_data( filepath, reader_class )
            if output_mesh:
                break

    if not output_mesh:
        raise ValueError( f"Could not find a suitable reader for '{filepath}'." )

    return output_mesh


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

    # Reuse the generic mesh reader
    mesh = read_mesh( filepath )

    # Check the type of the resulting mesh
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
    if os.path.exists( vtk_output.output ) and not can_overwrite:
        raise FileExistsError(
            f"File '{vtk_output.output}' already exists. Set can_overwrite=True to replace it." )

    _, extension = os.path.splitext( vtk_output.output )

    try:
        file_format = VtkFormat( extension )
        if file_format not in WRITER_MAP:
            raise ValueError( f"Writing to extension '{extension}' is not supported." )

        writer_class = WRITER_MAP[ file_format ]
        success_code = _write_data( mesh, writer_class, vtk_output.output, vtk_output.is_data_mode_binary )

        if not success_code:
            raise RuntimeError( f"VTK writer failed to write file '{vtk_output.output}'." )

        io_logger.info( f"Successfully wrote mesh to '{vtk_output.output}'." )
        return success_code  # VTK writers return 1 for success

    except ValueError as e:
        io_logger.error( e )
        raise
