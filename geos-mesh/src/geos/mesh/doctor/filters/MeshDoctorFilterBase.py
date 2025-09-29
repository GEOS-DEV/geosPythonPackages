from typing_extensions import Self
from typing import Union
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.utils.Logger import getLogger, Logger
from geos.mesh.io.vtkIO import VtkOutput, write_mesh

__doc__ = """
MeshDoctorFilterBase module provides base classes for all mesh doctor filters using direct mesh manipulation.

MeshDoctorFilterBase serves as the foundation class for filters that process existing meshes,
while MeshDoctorGenerator is for filters that generate new meshes from scratch.

These base classes provide common functionality including:
- Logger management and setup
- Mesh access and manipulation methods
- File I/O operations for writing VTK unstructured grids
- Consistent interface across all mesh doctor filters

Unlike the VTK pipeline-based MeshDoctorBase, these classes work with direct mesh manipulation
following the FillPartialArrays pattern for simpler, more Pythonic usage.

Example usage patterns
----------------------

.. code-block:: python

    # For filters that process existing meshes
    from filters.MeshDoctorFilterBase import MeshDoctorFilterBase

    class MyProcessingFilter(MeshDoctorFilterBase):
        def __init__(self, mesh, parameter1=default_value):
            super().__init__(mesh, "My Filter Name")
            self.parameter1 = parameter1

        def applyFilter(self):
            # Process self.mesh directly
            # Return True on success, False on failure
            pass

    # For filters that generate meshes from scratch
    from filters.MeshDoctorFilterBase import MeshDoctorGeneratorBase

    class MyGeneratorFilter(MeshDoctorGeneratorBase):
        def __init__(self, parameter1=default_value):
            super().__init__("My Generator Name")
            self.parameter1 = parameter1

        def applyFilter(self):
            # Generate new mesh and assign to self.mesh
            # Return True on success, False on failure
            pass
"""


class MeshDoctorFilterBase:
    """Base class for all mesh doctor filters using direct mesh manipulation."""

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        filterName: str,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the base mesh doctor filter."""
        # Check the 'mesh' input
        if not isinstance( mesh, vtkUnstructuredGrid ):
            raise TypeError( f"Input 'mesh' must be a vtkUnstructuredGrid, but got {type(mesh).__name__}." )
        if mesh.GetNumberOfCells() == 0:
            raise ValueError( "Input 'mesh' cannot be empty." )

        # Check the 'filterName' input
        if not isinstance( filterName, str ):
            raise TypeError( f"Input 'filterName' must be a string, but got {type(filterName).__name__}." )
        if not filterName.strip():
            raise ValueError( "Input 'filterName' cannot be an empty or whitespace-only string." )

        # Check the 'useExternalLogger' input
        if not isinstance( useExternalLogger, bool ):
            raise TypeError(
                f"Input 'useExternalLogger' must be a boolean, but got {type(useExternalLogger).__name__}." )

        # Non-destructive behavior.
        # The filter should contain a COPY of the mesh, not the original object.
        self.mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
        self.mesh.DeepCopy( mesh )
        self.filterName: str = filterName

        # Logger setup
        self.logger: Logger
        if not useExternalLogger:
            self.logger = getLogger( filterName, True )
        else:
            import logging
            self.logger = logging.getLogger( filterName )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler ) -> None:
        """Set a specific handler for the filter logger.

        Args:
            handler: The logging handler to add.
        """
        if not self.logger.handlers:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has a handler, to use yours set 'useExternalLogger' "
                                 "to True during initialization." )

    def getMesh( self: Self ) -> vtkUnstructuredGrid:
        """Get the processed mesh.

        Returns:
            vtkUnstructuredGrid: The processed mesh
        """
        return self.mesh

    def writeGrid( self: Self, filepath: str, isDataModeBinary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of the vtkUnstructuredGrid at the specified filepath.

        Args:
            filepath (str): /path/to/your/file.vtu
            isDataModeBinary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        if self.mesh:
            vtk_output = VtkOutput( filepath, isDataModeBinary )
            write_mesh( self.mesh, vtk_output, canOverwrite )
        else:
            self.logger.error( f"No mesh available. Cannot output vtkUnstructuredGrid at {filepath}." )

    def copyMesh( self: Self, sourceMesh: vtkUnstructuredGrid ) -> vtkUnstructuredGrid:
        """Helper method to create a copy of a mesh with structure and attributes.

        Args:
            sourceMesh (vtkUnstructuredGrid): Source mesh to copy from.

        Returns:
            vtkUnstructuredGrid: New mesh with copied structure and attributes.
        """
        output_mesh: vtkUnstructuredGrid = sourceMesh.NewInstance()
        output_mesh.CopyStructure( sourceMesh )
        output_mesh.CopyAttributes( sourceMesh )
        return output_mesh

    def applyFilter( self: Self ) -> bool:
        """Apply the filter operation.

        This method should be overridden by subclasses to implement specific filter logic.

        Returns:
            bool: True if filter applied successfully, False otherwise.
        """
        raise NotImplementedError( "Subclasses must implement applyFilter method." )


class MeshDoctorGeneratorBase:
    """Base class for mesh doctor generator filters (no input mesh required).

    This class provides functionality for filters that generate meshes
    from scratch without requiring input meshes.
    """

    def __init__(
        self: Self,
        filterName: str,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the base mesh doctor generator filter.

        Args:
            filterName (str): Name of the filter for logging.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        # Check the 'filterName' input
        if not isinstance( filterName, str ):
            raise TypeError( f"Input 'filterName' must be a string, but got {type(filterName).__name__}." )
        if not filterName.strip():
            raise ValueError( "Input 'filterName' cannot be an empty or whitespace-only string." )

        # Check the 'useExternalLogger' input
        if not isinstance( useExternalLogger, bool ):
            raise TypeError(
                f"Input 'useExternalLogger' must be a boolean, but got {type(useExternalLogger).__name__}." )

        self.mesh: Union[ vtkUnstructuredGrid, None ] = None
        self.filterName: str = filterName

        # Logger setup
        self.logger: Logger
        if not useExternalLogger:
            self.logger = getLogger( filterName, True )
        else:
            import logging
            self.logger = logging.getLogger( filterName )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler ) -> None:
        """Set a specific handler for the filter logger.

        Args:
            handler: The logging handler to add.
        """
        if not self.logger.handlers:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has a handler, to use yours set 'useExternalLogger' "
                                 "to True during initialization." )

    def getMesh( self: Self ) -> Union[ vtkUnstructuredGrid, None ]:
        """Get the generated mesh.

        Returns:
            Union[vtkUnstructuredGrid, None]: The generated mesh, or None if not yet generated.
        """
        return self.mesh

    def writeGrid( self: Self, filepath: str, isDataModeBinary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of the vtkUnstructuredGrid at the specified filepath.

        Args:
            filepath (str): /path/to/your/file.vtu
            isDataModeBinary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        if self.mesh:
            vtk_output = VtkOutput( filepath, isDataModeBinary )
            write_mesh( self.mesh, vtk_output, canOverwrite )
        else:
            self.logger.error( f"No mesh generated. Cannot output vtkUnstructuredGrid at {filepath}." )

    def applyFilter( self: Self ) -> bool:
        """Apply the filter operation to generate a mesh.

        This method should be overridden by subclasses to implement specific generation logic.
        The generated mesh should be assigned to self.mesh.

        Returns:
            bool: True if mesh generated successfully, False otherwise.
        """
        raise NotImplementedError( "Subclasses must implement applyFilter method." )
