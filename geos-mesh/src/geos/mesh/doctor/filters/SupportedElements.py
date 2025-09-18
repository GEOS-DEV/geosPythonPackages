import numpy as np
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.supported_elements import ( Options, find_unsupported_std_elements_types,
                                                          find_unsupported_polyhedron_elements )
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing.supported_elements_parsing import logger_results

__doc__ = """
SupportedElements module identifies unsupported element types and problematic polyhedron
elements in a vtkUnstructuredGrid. It checks for element types that are not supported by GEOS and validates
polyhedron elements for geometric correctness.

To use the filter
-----------------

.. code-block:: python

    from geos.mesh.doctor.filters.SupportedElements import SupportedElements

    # instantiate the filter
    supportedElementsFilter = SupportedElements(mesh, writeUnsupportedElementTypes=True,
                                                writeUnsupportedPolyhedrons=True,
                                                numProc=4, chunkSize=1000)

    # execute the filter
    success = supportedElementsFilter.applyFilter()

    # get unsupported element types
    unsupportedTypes = supportedElementsFilter.getUnsupportedElementTypes()

    # get unsupported polyhedron elements
    unsupportedPolyhedrons = supportedElementsFilter.getUnsupportedPolyhedronElements()

    # get the processed mesh with support information
    outputMesh = supportedElementsFilter.getMesh()

    # write the output mesh
    supportedElementsFilter.writeGrid("output/mesh_with_support_info.vtu")

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.SupportedElements import supportedElements

    # apply filter directly
    outputMesh, unsupportedTypes, unsupportedPolyhedrons = supportedElements(
        mesh,
        outputPath="output/mesh_with_support_info.vtu",
        numProc=4,
        chunkSize=1000,
        writeUnsupportedElementTypes=True,
        writeUnsupportedPolyhedrons=True
    )
"""

loggerTitle: str = "Supported Elements Filter"


class SupportedElements( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        numProc: int = 1,
        chunkSize: int = 1,
        writeUnsupportedElementTypes: bool = False,
        writeUnsupportedPolyhedrons: bool = False,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the supported elements filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze.
            writeUnsupportedElementTypes (bool): Whether to add new CellData array marking unsupported element types.
                                                 Defaults to False.
            writeUnsupportedPolyhedrons (bool): Whether to add new CellData array marking unsupported polyhedrons.
                                               Defaults to False.
            numProc (int): Number of processes for multiprocessing. Defaults to 1.
            chunkSize (int): Chunk size for multiprocessing. Defaults to 1.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, useExternalLogger )
        self.numProc: int = numProc
        self.chunkSize: int = chunkSize
        self.unsupportedElementTypes: list[ str ] = []
        self.unsupportedPolyhedronElements: list[ int ] = []
        self.writeUnsupportedElementTypes: bool = writeUnsupportedElementTypes
        self.writeUnsupportedPolyhedrons: bool = writeUnsupportedPolyhedrons

    def applyFilter( self: Self ) -> bool:
        """Apply the supported elements analysis.

        Returns:
            bool: True if analysis completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}." )

        # Find unsupported standard element types
        self.unsupportedElementTypes = find_unsupported_std_elements_types( self.mesh )

        if len( self.unsupportedElementTypes ) > 0:
            if self.writeUnsupportedElementTypes:
                self._addUnsupportedElementTypesArray()

        # Find unsupported polyhedron elements
        options = Options( self.numProc, self.chunkSize )
        self.unsupportedPolyhedronElements = find_unsupported_polyhedron_elements( self.mesh, options )

        if len( self.unsupportedPolyhedronElements ) > 0:
            if self.writeUnsupportedPolyhedrons:
                self._addUnsupportedPolyhedronsArray()

        logger_results( self.logger, self.unsupportedPolyhedronElements, self.unsupportedElementTypes )

        self.logger.info( f"The filter {self.logger.name} succeeded." )
        return True

    def getUnsupportedElementTypes( self: Self ) -> list[ str ]:
        """Get the list of unsupported element types.

        Returns:
            list[ str ]: List of unsupported element type descriptions.
        """
        return self.unsupportedElementTypes

    def getUnsupportedPolyhedronElements( self: Self ) -> list[ int ]:
        """Get the list of unsupported polyhedron element indices.

        Returns:
            list[ int ]: List of element indices for unsupported polyhedrons.
        """
        return self.unsupportedPolyhedronElements

    def setWriteUnsupportedElementTypes( self: Self, write: bool ) -> None:
        """Set whether to write unsupported element types.

        Args:
            write (bool): True to enable writing, False to disable.
        """
        self.writeUnsupportedElementTypes = write

    def setWriteUnsupportedPolyhedrons( self: Self, write: bool ) -> None:
        """Set whether to write unsupported polyhedrons.

        Args:
            write (bool): True to enable writing, False to disable.
        """
        self.writeUnsupportedPolyhedrons = write

    def setNumProc( self: Self, numProc: int ) -> None:
        """Set the number of processes for multiprocessing.

        Args:
            numProc (int): Number of processes.
        """
        self.numProc = numProc

    def setChunkSize( self: Self, chunkSize: int ) -> None:
        """Set the chunk size for multiprocessing.

        Args:
            chunkSize (int): Chunk size.
        """
        self.chunkSize = chunkSize

    def _addUnsupportedElementTypesArray( self: Self ) -> None:
        """Add an array marking elements with unsupported types on the mesh."""
        self.logger.info( "Adding CellData array marking elements with unsupported types." )

        numCells: int = self.mesh.GetNumberOfCells()
        unsupportedTypesArray = np.zeros( numCells, dtype=np.int32 )

        # Get unsupported type IDs from the string descriptions
        unsupportedTypeIds = set()
        for description in self.unsupportedElementTypes:
            # Extract type ID from description like "Type 42: vtkSomeElementType"
            if description.startswith( "Type " ):
                typeId = int( description.split( ":" )[ 0 ].replace( "Type ", "" ) )
                unsupportedTypeIds.add( typeId )

        # Mark cells with unsupported types
        for i in range( numCells ):
            cellType: int = self.mesh.GetCellType( i )
            if cellType in unsupportedTypeIds:
                unsupportedTypesArray[ i ] = 1

        vtkArray: vtkDataArray = numpy_to_vtk( unsupportedTypesArray )
        vtkArray.SetName( "HasUnsupportedType" )
        self.mesh.GetCellData().AddArray( vtkArray )

    def _addUnsupportedPolyhedronsArray( self: Self ) -> None:
        """Add an array marking unsupported polyhedron elements on the mesh."""
        self.logger.info( "Adding CellData array marking unsupported polyhedron elements." )

        numCells: int = self.mesh.GetNumberOfCells()
        unsupportedPolyhedronsArray = np.zeros( numCells, dtype=np.int32 )
        unsupportedPolyhedronsArray[ self.unsupportedPolyhedronElements ] = 1

        vtkArray: vtkDataArray = numpy_to_vtk( unsupportedPolyhedronsArray )
        vtkArray.SetName( "IsUnsupportedPolyhedron" )
        self.mesh.GetCellData().AddArray( vtkArray )


# Main function for standalone use
def supportedElements(
    mesh: vtkUnstructuredGrid,
    outputPath: str,
    numProc: int = 1,
    chunkSize: int = 1,
    writeUnsupportedElementTypes: bool = False,
    writeUnsupportedPolyhedrons: bool = False,
) -> tuple[ vtkUnstructuredGrid, list[ str ], list[ int ] ]:
    """Apply supported elements analysis to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        outputPath (str): Output file path for writing the mesh.
        numProc (int): Number of processes for multiprocessing. Defaults to 1.
        chunkSize (int): Chunk size for multiprocessing. Defaults to 1.
        writeUnsupportedElementTypes (bool): Whether to write unsupported element types. Defaults to False.
        writeUnsupportedPolyhedrons (bool): Whether to write unsupported polyhedrons. Defaults to False.

    Returns:
        tuple[vtkUnstructuredGrid, list[ str ], list[ int ]]:
            Processed mesh, list of unsupported element types, list of unsupported polyhedron indices.
    """
    filterInstance = SupportedElements( mesh, numProc, chunkSize, writeUnsupportedElementTypes,
                                        writeUnsupportedPolyhedrons )
    success = filterInstance.applyFilter()
    if not success:
        raise RuntimeError( "Supported elements identification failed." )

    filterInstance.writeGrid( outputPath )

    return (
        filterInstance.getMesh(),
        filterInstance.getUnsupportedElementTypes(),
        filterInstance.getUnsupportedPolyhedronElements(),
    )
