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

ioLogger = getLogger( "IO for geos-mesh" )
ioLogger.propagate = False


class VtkFormat( Enum ):
    """Enumeration for supported VTK file formats and their extensions."""
    VTK = ".vtk"
    VTS = ".vts"
    VTU = ".vtu"
    PVTU = ".pvtu"
    PVTS = ".pvts"


# Use TypeAlias for cleaner and more readable type hints
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
    isDataModeBinary: bool = True


def _readData( filepath: str, readerClass: VtkReaderClass ) -> Optional[ vtkPointSet ]:
    """Generic helper to read a VTK file using a specific reader class.

    Args:
        filepath (str): Path to the VTK file.
        readerClass (VtkReaderClass): The VTK reader class to use.

    Returns:
        Optional[ vtkPointSet ]: The read VTK point set, or None if reading failed.
    """
    reader = readerClass()
    ioLogger.info( f"Attempting to read '{filepath}' with {readerClass.__name__}..." )

    reader.SetFileName( str( filepath ) )

    # For XML-based readers, CanReadFile is a reliable and fast pre-check.
    if hasattr( reader, 'CanReadFile' ) and not reader.CanReadFile( filepath ):
        ioLogger.error( f"Reader {readerClass.__name__} reports it cannot read file '{filepath}'." )
        return None

    reader.Update()

    # Check the reader's error code. This is the most reliable way to
    # detect a failed read, as GetOutput() can return a default empty object on failure.
    if hasattr( reader, 'GetErrorCode' ) and reader.GetErrorCode() != 0:
        ioLogger.warning(
            f"VTK reader {readerClass.__name__} reported an error code after attempting to read '{filepath}'." )
        return None

    output = reader.GetOutput()

    if output is None:
        return None

    ioLogger.info( "Read successful." )
    return output


def _writeData( mesh: vtkPointSet, writerClass: VtkWriterClass, output: str, isBinary: bool ) -> int:
    """Generic helper to write a VTK file using a specific writer class.

    Args:
        mesh (vtkPointSet): The grid data to write.
        writerClass (VtkWriterClass): The VTK writer class to use.
        output (str): The output file path.
        isBinary (bool): Whether to write the file in binary mode (True) or ASCII (False).

    Returns:
        int: 1 if success, 0 otherwise.
    """
    ioLogger.info( f"Writing mesh to '{output}' using {writerClass.__name__}..." )
    writer = writerClass()
    writer.SetFileName( output )
    writer.SetInputData( mesh )

    # Set data mode only for XML writers that support it
    if isinstance( writer, vtkXMLWriter ):
        if isBinary:
            writer.SetDataModeToBinary()
            ioLogger.info( "Data mode set to Binary." )
        else:
            writer.SetDataModeToAscii()
            ioLogger.info( "Data mode set to ASCII." )

    return writer.Write()


def readMesh( filepath: str ) -> vtkPointSet:
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
    filepathPath: Path = Path( filepath )
    if not filepathPath.exists():
        raise FileNotFoundError( f"Invalid file path: '{filepath}' does not exist." )

    candidateReaders: list[ VtkReaderClass ] = []
    # 1. Prioritize the reader associated with the file extension
    try:
        fileFormat = VtkFormat( filepathPath.suffix )
        if fileFormat in READER_MAP:
            candidateReaders.append( READER_MAP[ fileFormat ] )
    except ValueError:
        ioLogger.warning( f"Unknown file extension '{filepathPath.suffix}'. Trying all available readers." )

    # 2. Add all other unique readers as fallbacks
    for readerCls in READER_MAP.values():
        if readerCls not in candidateReaders:
            candidateReaders.append( readerCls )

    # 3. Attempt to read with the candidates in order
    for readerClass in candidateReaders:
        outputMesh = _readData( filepath, readerClass )
        if outputMesh:
            return outputMesh

    raise ValueError( f"Could not find a suitable reader for '{filepath}'." )


def readUnstructuredGrid( filepath: str ) -> vtkUnstructuredGrid:
    """
    Reads a VTK file and ensures it is a vtkUnstructuredGrid.

    This function uses the general `readMesh` to load the data and then
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
    ioLogger.info( f"Reading file '{filepath}' and expecting vtkUnstructuredGrid." )
    mesh = readMesh( filepath )

    if not isinstance( mesh, vtkUnstructuredGrid ):
        errorMsg = ( f"File '{filepath}' was read successfully, but it is of type "
                     f"'{type(mesh).__name__}', not the expected vtkUnstructuredGrid." )
        ioLogger.error( errorMsg )
        raise TypeError( errorMsg )

    ioLogger.info( "Validation successful. Mesh is a vtkUnstructuredGrid." )
    return mesh


def writeMesh( mesh: vtkPointSet, vtkOutput: VtkOutput, canOverwrite: bool = False ) -> int:
    """
    Writes a vtkPointSet to a file.

    The format is determined by the file extension in `VtkOutput.output`.

    Args:
        mesh (vtkPointSet): The grid data to write.
        vtkOutput (VtkOutput): Configuration for the output file.
        canOverwrite (bool, optional): If False, raises an error if the file
                                      already exists. Defaults to False.

    Raises:
        FileExistsError: If the output file exists and `canOverwrite` is False.
        ValueError: If the file extension is not a supported write format.
        RuntimeError: If the VTK writer fails to write the file.

    Returns:
        int: Returns 1 on success, consistent with the VTK writer's return code.
    """
    outputPath = Path( vtkOutput.output )
    if outputPath.exists() and not canOverwrite:
        raise FileExistsError( f"File '{outputPath}' already exists. Set canOverwrite=True to replace it." )

    try:
        # Catch the ValueError from an invalid enum to provide a consistent error message.
        try:
            fileFormat = VtkFormat( outputPath.suffix )
        except ValueError:
            # Re-raise with the message expected by the test.
            raise ValueError( f"Writing to extension '{outputPath.suffix}' is not supported." )

        writerClass = WRITER_MAP.get( fileFormat )
        if not writerClass:
            raise ValueError( f"Writing to extension '{outputPath.suffix}' is not supported." )

        successCode = _writeData( mesh, writerClass, str( outputPath ), vtkOutput.isDataModeBinary )
        if not successCode:
            raise RuntimeError( f"VTK writer failed to write file '{outputPath}'." )

        ioLogger.info( f"Successfully wrote mesh to '{outputPath}'." )
        return successCode

    except ( ValueError, RuntimeError ) as e:
        ioLogger.error( e )
        raise
