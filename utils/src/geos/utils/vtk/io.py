import os.path
import logging
from dataclasses import dataclass
from typing import Optional
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkIOLegacy import vtkUnstructuredGridWriter, vtkUnstructuredGridReader
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader, vtkXMLUnstructuredGridWriter


@dataclass( frozen=True )
class VtkOutput:
    output: str
    is_data_mode_binary: bool


def __read_vtk( vtk_input_file: str ) -> Optional[ vtkUnstructuredGrid ]:
    reader = vtkUnstructuredGridReader()
    logging.info( f"Testing file format \"{vtk_input_file}\" using legacy format reader..." )
    reader.SetFileName( vtk_input_file )
    if reader.IsFileUnstructuredGrid():
        logging.info( f"Reader matches. Reading file \"{vtk_input_file}\" using legacy format reader." )
        reader.Update()
        return reader.GetOutput()
    else:
        logging.info( "Reader did not match the input file format." )
        return None


def __read_vtu( vtk_input_file: str ) -> Optional[ vtkUnstructuredGrid ]:
    reader = vtkXMLUnstructuredGridReader()
    logging.info( f"Testing file format \"{vtk_input_file}\" using XML format reader..." )
    if reader.CanReadFile( vtk_input_file ):
        reader.SetFileName( vtk_input_file )
        logging.info( f"Reader matches. Reading file \"{vtk_input_file}\" using XML format reader." )
        reader.Update()
        return reader.GetOutput()
    else:
        logging.info( "Reader did not match the input file format." )
        return None


def read_mesh( vtk_input_file: str ) -> vtkUnstructuredGrid:
    """
    Read the vtk file and builds an unstructured grid from it.
    :param vtk_input_file: The file name. The extension will be used to guess the file format.
        If first guess does not work, eventually all the others reader available will be tested.
    :return: A unstructured grid.
    """
    if not os.path.exists( vtk_input_file ):
        err_msg: str = f"Invalid file path. Could not read \"{vtk_input_file}\". Dying..."
        logging.error( err_msg )
        raise ValueError( err_msg )
    file_extension = os.path.splitext( vtk_input_file )[ -1 ]
    extension_to_reader = { ".vtk": __read_vtk, ".vtu": __read_vtu }
    # Testing first the reader that should match
    if file_extension in extension_to_reader:
        output_mesh = extension_to_reader.pop( file_extension )( vtk_input_file )
        if output_mesh:
            return output_mesh
    # If it does not match, then test all the others.
    for reader in extension_to_reader.values():
        output_mesh = reader( vtk_input_file )
        if output_mesh:
            return output_mesh
    # No reader did work. Dying.
    err_msg = f"Could not find the appropriate VTK reader for file \"{vtk_input_file}\". Dying..."
    logging.error( err_msg )
    raise ValueError( err_msg )


def __write_vtk( mesh: vtkUnstructuredGrid, output: str ) -> int:
    logging.info( f"Writing mesh into file \"{output}\" using legacy format." )
    writer = vtkUnstructuredGridWriter()
    writer.SetFileName( output )
    writer.SetInputData( mesh )
    return writer.Write()


def __write_vtu( mesh: vtkUnstructuredGrid, output: str, is_data_mode_binary: bool ) -> int:
    logging.info( f"Writing mesh into file \"{output}\" using XML format." )
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName( output )
    writer.SetInputData( mesh )
    writer.SetDataModeToBinary() if is_data_mode_binary else writer.SetDataModeToAscii()
    return writer.Write()


def write_mesh( mesh: vtkUnstructuredGrid, vtk_output: VtkOutput ) -> int:
    """
    Writes the mesh to disk.
    Nothing will be done if the file already exists.
    :param mesh: The unstructured grid to write.
    :param vtk_output: Where to write. The file extension will be used to select the VTK file format.
    :return: 0 in case of success.
    """
    if os.path.exists( vtk_output.output ):
        logging.error( f"File \"{vtk_output.output}\" already exists, nothing done." )
        return 1
    file_extension = os.path.splitext( vtk_output.output )[ -1 ]
    if file_extension == ".vtk":
        success_code = __write_vtk( mesh, vtk_output.output )
    elif file_extension == ".vtu":
        success_code = __write_vtu( mesh, vtk_output.output, vtk_output.is_data_mode_binary )
    else:
        # No writer found did work. Dying.
        err_msg = f"Could not find the appropriate VTK writer for extension \"{file_extension}\". Dying..."
        logging.error( err_msg )
        raise ValueError( err_msg )
    return 0 if success_code else 2  # the Write member function return 1 in case of success, 0 otherwise.
