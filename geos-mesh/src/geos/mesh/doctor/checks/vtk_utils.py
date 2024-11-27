import logging
import os.path
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from numpy import array
from typing import Iterator, Optional
from vtkmodules.vtkFiltersCore import vtkCellCenters
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkMultiBlockDataSet, vtkPolyData
from vtkmodules.vtkIOLegacy import vtkUnstructuredGridWriter, vtkUnstructuredGridReader
from vtkmodules.vtkIOXML import ( vtkXMLUnstructuredGridReader, vtkXMLUnstructuredGridWriter,
                                  vtkXMLMultiBlockDataReader, vtkXMLMultiBlockDataWriter )


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


def vtk_iter( l ) -> Iterator[ any ]:
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


def has_invalid_field( mesh: vtkUnstructuredGrid, invalid_fields: list[ str ] ) -> bool:
    """Checks if a mesh contains at least a data arrays within its cell, field or point data
    having a certain name. If so, returns True, else False.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured mesh.
        invalid_fields (list[str]): Field name of an array in any data from the data.

    Returns:
        bool: True if one field found, else False.
    """
    # Check the cell data fields
    cell_data = mesh.GetCellData()
    for i in range( cell_data.GetNumberOfArrays() ):
        if cell_data.GetArrayName( i ) in invalid_fields:
            logging.error( f"The mesh contains an invalid cell field name '{cell_data.GetArrayName( i )}'." )
            return True
    # Check the field data fields
    field_data = mesh.GetFieldData()
    for i in range( field_data.GetNumberOfArrays() ):
        if field_data.GetArrayName( i ) in invalid_fields:
            logging.error( f"The mesh contains an invalid field name '{field_data.GetArrayName( i )}'." )
            return True
    # Check the point data fields
    point_data = mesh.GetPointData()
    for i in range( point_data.GetNumberOfArrays() ):
        if point_data.GetArrayName( i ) in invalid_fields:
            logging.error( f"The mesh contains an invalid point field name '{point_data.GetArrayName( i )}'." )
            return True
    return False


def get_points_coords_from_vtk( data: vtkPolyData ) -> array:
    """Extracts the coordinates of every point from a vtkPolyData and returns them in a numpy array.

    Args:
        data (vtkPolyData): vtkPolyData object.

    Returns:
        array: Numpy array of shape( number_of_points, 3 )
    """
    points = data.GetPoints()
    num_points: int = points.GetNumberOfPoints()
    points_coords: array = array( [ points.GetPoint( i ) for i in range( num_points ) ], dtype=float )
    return points_coords


def get_cell_centers_array( mesh: vtkUnstructuredGrid ) -> array:
    """Returns an array containing the cell centers coordinates for every cell of a mesh.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.

    Returns:
        np.array: Shape=( mesh number of cells, 3 )
    """
    cell_centers_filter: vtkCellCenters = vtkCellCenters()
    cell_centers_filter.SetInputData( mesh )
    cell_centers_filter.Update()
    cell_centers = cell_centers_filter.GetOutput()
    cell_centers_array: array = get_points_coords_from_vtk( cell_centers )
    return cell_centers_array


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
        err_msg: str = f"Invalid file path. Could not read \"{vtk_input_file}\"."
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
    err_msg = f"Could not find the appropriate VTK reader for file \"{vtk_input_file}\"."
    logging.error( err_msg )
    raise ValueError( err_msg )


def read_vtm( vtk_input_file: str ) -> vtkMultiBlockDataSet:
    if not vtk_input_file.endswith( ".vtm" ):
        raise ValueError( f"Input file '{vtk_input_file}' is not a .vtm file. Cannot read it." )
    reader = vtkXMLMultiBlockDataReader()
    reader.SetFileName( vtk_input_file )
    reader.Update()
    return reader.GetOutput()


def get_vtm_filepath_from_pvd( vtk_input_file: str, vtm_index: int ) -> str:
    """From a GEOS output .pvd file, extracts one .vtm file and returns its filepath.

    Args:
        vtk_input_file (str): .pvd filepath
        vtm_index (int): Index that will select which .vtm to choose.

    Returns:
        str: Filepath to the .vtm at the chosen index.
    """
    if not vtk_input_file.endswith( ".pvd" ):
        raise ValueError( f"Input file '{vtk_input_file}' is not a .pvd file. Cannot read it." )
    tree = ET.parse( vtk_input_file )
    root = tree.getroot()
    # Extract all .vtm file paths contained in the .pvd
    vtm_paths: list[ str ] = list()
    for dataset in root.findall( ".//DataSet" ):
        file_path = dataset.get( "file" )
        if file_path.endswith( ".vtm" ):
            vtm_paths.append( file_path )
    number_vtms: int = len( vtm_paths )
    if number_vtms == 0:
        raise ValueError( f"The '{vtk_input_file}' does not contain any .vtm path." )
    if vtm_index >= number_vtms:
        raise ValueError( f"Cannot access the .vtm at index '{vtm_index}' in the '{vtk_input_file}'." +
                          f" The indexes available are between 0 and {number_vtms - 1}." )
    # build the complete filepath of the vtm to use
    directory: str = os.path.dirname( vtk_input_file )
    vtm_filepath: str = os.path.join( directory, vtm_paths[ vtm_index ] )
    return vtm_filepath


def get_vtu_filepaths_from_vtm( vtm_filepath: str ) -> tuple[ str ]:
    """By reading a vtm file, returns all the vtu filepaths present inside it.

    Args:
        vtm_filepath (str): Filepath to a .vtm

    Returns:
        tuple[ str ]: ( "file/path/0.vtu", ..., "file/path/N.vtu" )
    """
    if not vtm_filepath.endswith( ".vtm" ):
        raise ValueError( f"Input file '{vtm_filepath}' is not a .vtm file. Cannot read it." )
    # Parse the XML file and find all DataSet elements
    tree = ET.parse( vtm_filepath )
    root = tree.getroot()
    dataset_elements = root.findall( ".//DataSet" )
    # Extract the file attribute from each DataSet
    vtu_filepaths: list[ str ] = [ ds.get( 'file' ) for ds in dataset_elements if ds.get( 'file' ).endswith( '.vtu' ) ]
    directory: str = os.path.dirname( vtm_filepath )
    vtu_filepaths = [ os.path.join( directory, vtu_filepath ) for vtu_filepath in vtu_filepaths ]
    return tuple( vtu_filepaths )  # to lock the order of the vtus like in the vtm


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
        err_msg = f"Could not find the appropriate VTK writer for extension \"{file_extension}\"."
        logging.error( err_msg )
        raise ValueError( err_msg )
    return 0 if success_code else 2  # the Write member function return 1 in case of success, 0 otherwise.


def write_VTM( multiblock: vtkMultiBlockDataSet, vtk_output: VtkOutput ) -> int:
    if os.path.exists( vtk_output.output ):
        logging.error( f"File \"{vtk_output.output}\" already exists, nothing done." )
        return 1
    writer = vtkXMLMultiBlockDataWriter()
    writer.SetFileName( vtk_output.output )
    writer.SetInputData( multiblock )
    writer.SetDataModeToBinary() if vtk_output.is_data_mode_binary else writer.SetDataModeToAscii()
    writer.Write()
