# TODO Find an implementation to keep multiprocessing while using vtkFilter

# import numpy as np
# import numpy.typing as npt
# from typing_extensions import Self
# from vtkmodules.util.numpy_support import numpy_to_vtk
# from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
# from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector, vtkDataArray, VTK_INT
# from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
# from geos.mesh.doctor.actions.supported_elements import ( Options, find_unsupported_std_elements_types,
#                                                           find_unsupported_polyhedron_elements )
# from geos.mesh.io.vtkIO import VtkOutput, write_mesh
# from geos.utils.Logger import Logger, getLogger

# __doc__ = """
# SupportedElements module is a vtk filter that identifies unsupported element types and problematic polyhedron
# elements in a vtkUnstructuredGrid. It checks for element types that are not supported by GEOS and validates
# polyhedron elements for geometric correctness.
#
# One filter input is vtkUnstructuredGrid, one filter output which is vtkUnstructuredGrid.
#
# To use the filter:
#
# .. code-block:: python
#
#     from filters.SupportedElements import SupportedElements
#
#     # instantiate the filter
#     supportedElementsFilter: SupportedElements = SupportedElements()
#
#     # optionally enable painting of unsupported element types
#     supportedElementsFilter.setPaintUnsupportedElementTypes(1)  # 1 to enable, 0 to disable
#
#     # set input mesh
#     supportedElementsFilter.SetInputData(mesh)
#
#     # execute the filter
#     output_mesh: vtkUnstructuredGrid = supportedElementsFilter.getGrid()
#
#     # get unsupported elements
#     unsupported_elements = supportedElementsFilter.getUnsupportedElements()
#
#     # write the output mesh
#     supportedElementsFilter.writeGrid("output/mesh_with_support_info.vtu")
#
# Note: This filter is currently disabled due to multiprocessing requirements.
# """

# class SupportedElements( VTKPythonAlgorithmBase ):

#     def __init__( self: Self ) -> None:
#         """Vtk filter to ... a vtkUnstructuredGrid.

#         Output mesh is vtkUnstructuredGrid.
#         """
#         super().__init__( nInputPorts=1,
#                           nOutputPorts=1,
#                           inputType='vtkUnstructuredGrid',
#                           outputType='vtkUnstructuredGrid' )
#         self.m_paintUnsupportedElementTypes: int = 0
#         # TODO Needs parallelism to work
#         # self.m_paintUnsupportedPolyhedrons: int = 0
#         # self.m_chunk_size: int = 1
#         # self.m_num_proc: int = 1
#         self.m_logger: Logger = getLogger( "Element Volumes Filter" )

#     def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
#         """Inherited from VTKPythonAlgorithmBase::RequestInformation.

#         Args:
#             port (int): input port
#             info (vtkInformationVector): info

#         Returns:
#             int: 1 if calculation successfully ended, 0 otherwise.
#         """
#         if port == 0:
#             info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid" )
#         return 1

#     def RequestInformation(
#         self: Self,
#         request: vtkInformation,  # noqa: F841
#         inInfoVec: list[ vtkInformationVector ],  # noqa: F841
#         outInfoVec: vtkInformationVector,
#     ) -> int:
#         """Inherited from VTKPythonAlgorithmBase::RequestInformation.

#         Args:
#             request (vtkInformation): request
#             inInfoVec (list[vtkInformationVector]): input objects
#             outInfoVec (vtkInformationVector): output objects

#         Returns:
#             int: 1 if calculation successfully ended, 0 otherwise.
#         """
#         executive = self.GetExecutive()  # noqa: F841
#         outInfo = outInfoVec.GetInformationObject( 0 )  # noqa: F841
#         return 1

#     def RequestData(
#         self: Self,
#         request: vtkInformation,
#         inInfoVec: list[ vtkInformationVector ],
#         outInfo: vtkInformationVector
#     ) -> int:
#         """Inherited from VTKPythonAlgorithmBase::RequestData.

#         Args:
#             request (vtkInformation): request
#             inInfoVec (list[vtkInformationVector]): input objects
#             outInfoVec (vtkInformationVector): output objects

#         Returns:
#             int: 1 if calculation successfully ended, 0 otherwise.
#         """
#         input_mesh: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
#         output = vtkUnstructuredGrid.GetData( outInfo )

#         output_mesh: vtkUnstructuredGrid = input_mesh.NewInstance()
#         output_mesh.CopyStructure( input_mesh )
#         output_mesh.CopyAttributes( input_mesh )

#         unsupported_std_elt_types: set[ int ] = find_unsupported_std_elements_types( input_mesh )
#         if len( unsupported_std_elt_types ) > 0:
#             self.m_logger.info( "The following vtk element types in your mesh are not supported by GEOS:" )
#             self.m_logger.info( unsupported_std_elt_types )

#             if self.m_paintUnsupportedElementTypes:
#                 nbr_cells: int = output_mesh.GetNumberOfCells()
#                 arrayCellTypes: npt.NDArray = np.zeros( nbr_cells, dtype=int )
#                 for i in range( nbr_cells ):
#                     arrayCellTypes[ i ] = output_mesh.GetCellType(i)

#                 arrayUET: npt.NDArray = np.zeros( nbr_cells, dtype=int )
#                 arrayUET[ np.isin( arrayCellTypes, list( unsupported_std_elt_types ) ) ] = 1
#                 vtkArrayWSP: vtkDataArray = numpy_to_vtk( arrayUET )
#                 vtkArrayWSP.SetName( "HasUnsupportedType" )
#                 output_mesh.GetCellData().AddArray( vtkArrayWSP )

#         # TODO Needs parallelism to work
#         # options = Options( self.m_num_proc, self.m_chunk_size )
#         # unsupported_polyhedron_elts: list[ int ] = find_unsupported_polyhedron_elements( input_mesh, options )
#         # if len( unsupported_polyhedron_elts ) > 0:
#         #     self.m_logger.info( "These vtk polyhedron cell indexes in your mesh are not supported by GEOS:" )
#         #     self.m_logger.info( unsupported_polyhedron_elts )

#         #     if self.m_paintUnsupportedPolyhedrons:
#         #         arrayUP: npt.NDArray = np.zeros( output_mesh.GetNumberOfCells(), dtype=int )
#         #         arrayUP[ unsupported_polyhedron_elts ] = 1
#         #         self.m_logger.info( f"arrayUP: {arrayUP}" )
#         #         vtkArrayWSP: vtkDataArray = numpy_to_vtk( arrayUP )
#         #         vtkArrayWSP.SetName( "IsUnsupportedPolyhedron" )
#         #         output_mesh.GetCellData().AddArray( vtkArrayWSP )

#         output.ShallowCopy( output_mesh )

#         return 1

#     def SetLogger( self: Self, logger: Logger ) -> None:
#         """Set the logger.

#         Args:
#             logger (Logger): logger
#         """
#         self.m_logger = logger
#         self.Modified()

#     def getGrid( self: Self ) -> vtkUnstructuredGrid:
#         """Returns the vtkUnstructuredGrid with volumes.

#         Args:
#             self (Self)

#         Returns:
#             vtkUnstructuredGrid
#         """
#         self.Update()  # triggers RequestData
#         return self.GetOutputDataObject( 0 )

#     def setPaintUnsupportedElementTypes( self: Self, choice: int ) -> None:
#         """Set 0 or 1 to choose if you want to create a new "HasUnsupportedType" array in your output data.

#         Args:
#             self (Self)
#             choice (int): 0 or 1
#         """
#         if choice not in [ 0, 1 ]:
#             self.m_logger.error( f"setPaintUnsupportedElementTypes: Please choose either 0 or 1 not '{choice}'." )
#         else:
#             self.m_paintUnsupportedElementTypes = choice
#             self.Modified()

#     # TODO Needs parallelism to work
#     # def setPaintUnsupportedPolyhedrons( self: Self, choice: int ) -> None:
#     #     """Set 0 or 1 to choose if you want to create a new "IsUnsupportedPolyhedron" array in your output data.

#     #     Args:
#     #         self (Self)
#     #         choice (int): 0 or 1
#     #     """
#     #     if choice not in [ 0, 1 ]:
#     #         self.m_logger.error( f"setPaintUnsupportedPolyhedrons: Please choose either 0 or 1 not '{choice}'." )
#     #     else:
#     #         self.m_paintUnsupportedPolyhedrons = choice
#     #         self.Modified()

#     # def setChunkSize( self: Self, new_chunk_size: int ) -> None:
#     #     self.m_chunk_size = new_chunk_size
#     #     self.Modified()

#     # def setNumProc( self: Self, new_num_proc: int ) -> None:
#     #     self.m_num_proc = new_num_proc
#     #     self.Modified()

#     def writeGrid( self: Self, filepath: str, is_data_mode_binary: bool = True, canOverwrite: bool = False ) -> None:
#         """Writes a .vtu file of the vtkUnstructuredGrid at the specified filepath with volumes.

#         Args:
#             filepath (str): /path/to/your/file.vtu
#             is_data_mode_binary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
#             canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing
#                                             file. Defaults to False.
#         """
#         mesh: vtkUnstructuredGrid = self.getGrid()
#         if mesh:
#             write_mesh( filepath, VtkOutput( filepath, is_data_mode_binary ), canOverwrite )
#         else:
#             self.m_logger.error( f"No output grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )
