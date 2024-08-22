from dataclasses import dataclass
from os import path, access, R_OK, W_OK
import logging
from sys import exit
from typing import (
    Any,
    Iterator,
    Optional,
)

from vtkmodules.vtkCommonCore import (
    vtkIdList, )
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, )
from vtkmodules.vtkIOLegacy import (
    vtkUnstructuredGridWriter,
    vtkUnstructuredGridReader,
)
from vtkmodules.vtkIOXML import (
    vtkXMLUnstructuredGridReader,
    vtkXMLUnstructuredGridWriter,
)


@dataclass( frozen=True )
class VtkOutput:
    output: str
    is_data_mode_binary: bool


def to_vtk_id_list( data ) -> vtkIdList:
    result = vtkIdList()
    result.Allocate( len( data ) )
    for d in data:
        result.InsertNextId( d )
    return result


def vtk_iter( l ) -> Iterator[ Any ]:
    """
    Utility function transforming a vtk "container" (e.g. vtkIdList) into an iterable to be used for building built-ins python containers.
    :param l: A vtk container.
    :return: The iterator.
    """
    if hasattr( l, "GetNumberOfIds" ):
        for i in range( l.GetNumberOfIds() ):
            yield l.GetId( i )
    elif hasattr( l, "GetNumberOfTypes" ):
        for i in range( l.GetNumberOfTypes() ):
            yield l.GetCellType( i )


#  Inspired from https://stackoverflow.com/a/78870363
def is_filepath_valid( filepath: str, is_input=True ) -> bool:
    """Checks if a filepath can be used to read or to create a new file.

    Args:
        filepath (str): A filepath.
        is_input (bool, optional): If the filepath is used to read a file, use True. 
        If the filepath is used to create a new file, use False. Defaults to True.

    Returns:
        bool: False if invalid, True instead.
    """
    dirname = path.dirname( filepath )
    if not path.isdir( dirname ):
        logging.error( f"The directory '{dirname}' specified does not exist." )
        return False
    if is_input:
        if not access( dirname, R_OK ):
            logging.error( f"You do not have rights to read in directory '{dirname}' specified for the file." )
            return False
        if not path.exists( filepath ):
            logging.error( f"The file specified does not exist." )
            return False
    else:
        if not access( dirname, W_OK ):
            logging.error( f"You do not have rights to write in directory '{dirname}' specified for the file." )
            return False
        if path.exists( filepath ):
            logging.error( f"A file with the same name already exists. No over-writing possible." )
            return False
    return True


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
    if not is_filepath_valid( vtk_input_file, True ):
        logging.error( f"Invalid filepath to read. Dying ..." )
        exit( 1 )
    file_extension = path.splitext( vtk_input_file )[ -1 ]
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
    logging.critical( f"Could not find the appropriate VTK reader for file \"{vtk_input_file}\". Dying..." )
    exit( 1 )


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
    if not is_filepath_valid( vtk_output.output, False ):
        logging.error( f"Invalid filepath to write. Dying ..." )
        exit( 1 )
    file_extension = path.splitext( vtk_output.output )[ -1 ]
    if file_extension == ".vtk":
        success_code = __write_vtk( mesh, vtk_output.output )
    elif file_extension == ".vtu":
        success_code = __write_vtu( mesh, vtk_output.output, vtk_output.is_data_mode_binary )
    else:
        # No writer found did work. Dying.
        logging.critical( f"Could not find the appropriate VTK writer for extension \"{file_extension}\". Dying..." )
        exit( 1 )
    return 0 if success_code else 2  # the Write member function return 1 in case of success, 0 otherwise.
