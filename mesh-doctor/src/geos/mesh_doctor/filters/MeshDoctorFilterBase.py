# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
import logging
from typing import Union
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.io.vtkIO import VtkOutput, writeMesh
from geos.mesh.utils.genericHelpers import copyMesh
from geos.utils.Logger import ( Logger, getLogger )

__doc__ = """
MeshDoctorFilterBase module provides base classes for all mesh doctor filters using direct mesh manipulation.

MeshDoctorFilterBase serves as the foundation class for filters that process existing meshes,
while MeshDoctorGenerator is for filters that generate new meshes from scratch.

These base classes provide common functionalities including:
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
        speHandler: bool = False,
        disableMeshCopy: bool = False,
    ) -> None:
        """Initialize the base mesh doctor filter.

        Args:
            self (Self)
            mesh (vtkUnstructuredGrid): The input VTU mesh to process.
            filterName (str): The name of the filter.
            speHandler (bool, optional): Whether to use a special handler. Defaults to False.
            disableMeshCopy (bool, optional): Whether to disable mesh copying. Defaults to False.
        """
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

        # Check the 'speHandler' input
        if not isinstance( speHandler, bool ):
            raise TypeError( f"Input 'speHandler' must be a boolean, but got {type(speHandler).__name__}." )

        # Check the 'speHandler' input
        if not isinstance( disableMeshCopy, bool ):
            raise TypeError( f"Input 'disableMeshCopy' must be a boolean, but got {type(disableMeshCopy).__name__}." )

        # Non-destructive behavior.
        # The filter should contain a COPY of the mesh, not the original object.
        self._mesh: vtkUnstructuredGrid = mesh if disableMeshCopy else copyMesh( mesh )
        self._filterName: str = filterName

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( filterName, True )
        else:
            self.logger = logging.getLogger( filterName )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        Args:
            handler: The logging handler to add.
        """
        if not self.logger.handlers:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has a handler, to use yours set 'speHandler' "
                                 "to True during initialization." )

    def applyFilter( self: Self ) -> None:
        """Apply the filter operation.

        This method should be overridden by subclasses to implement specific filter logic.
        """
        raise NotImplementedError( "Subclasses must implement applyFilter method." )

    @property
    def name( self: Self ) -> str:
        """Get the filter name.

        Returns:
            str: The filter name.
        """
        return self._filterName

    @name.setter
    def name( self: Self, name: str ) -> None:
        """Set the filter name.

        Args:
            name (str): The new filter name.
        """
        if not isinstance( name, str ):
            raise TypeError( f"Input 'name' must be a string, but got {type(name).__name__}." )
        if not name.strip():
            raise ValueError( "Input 'name' cannot be an empty or whitespace-only string." )
        self._filterName = name

    @property
    def mesh( self: Self ) -> Union[ vtkUnstructuredGrid, None ]:
        """Get the mesh.

        Returns:
            vtkUnstructuredGrid: The mesh being processed.
        """
        return self._mesh

    def writeMesh( self: Self, filepath: str, isDataModeBinary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of the vtkUnstructuredGrid at the specified filepath.

        Args:
            filepath (str): /path/to/your/file.vtu
            isDataModeBinary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        if self.mesh:
            vtkOutput = VtkOutput( filepath, isDataModeBinary, canOverwrite )
            try:
                writeMesh( self.mesh, vtkOutput, vtkOutput.canOverwrite )
            except FileExistsError as e:
                self.logger.error( f"{e} Set canOverwrite=True to allow overwriting existing files." )
                raise
        else:
            self.logger.error( f"No mesh available. Cannot output vtkUnstructuredGrid at {filepath}." )


class MeshDoctorGeneratorBase:
    """Base class for mesh doctor generator filters (no input mesh required).

    This class provides functionality for filters that generate meshes
    from scratch without requiring input meshes.
    """

    def __init__(
        self: Self,
        filterName: str,
        speHandler: bool = False,
    ) -> None:
        """Initialize the base mesh doctor generator filter.

        Args:
            filterName (str): Name of the filter for logging.
            speHandler (bool): Whether to use a special handler. Defaults to False.
        """
        # Check the 'filterName' input
        if not isinstance( filterName, str ):
            raise TypeError( f"Input 'filterName' must be a string, but got {type(filterName).__name__}." )
        if not filterName.strip():
            raise ValueError( "Input 'filterName' cannot be an empty or whitespace-only string." )

        # Check the 'speHandler' input
        if not isinstance( speHandler, bool ):
            raise TypeError( f"Input 'speHandler' must be a boolean, but got {type(speHandler).__name__}." )

        self._mesh: Union[ vtkUnstructuredGrid, None ] = None
        self._filterName: str = filterName

        # Logger setup
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( filterName, True )
        else:
            self.logger = logging.getLogger( filterName )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        Args:
            handler: The logging handler to add.
        """
        if not self.logger.handlers:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has a handler, to use yours set 'speHandler' "
                                 "to True during initialization." )

    def applyFilter( self: Self ) -> None:
        """Apply the filter operation to generate a mesh.

        This method should be overridden by subclasses to implement specific generation logic.
        The generated mesh should be assigned to self.mesh.
        """
        raise NotImplementedError( "Subclasses must implement applyFilter method." )

    @property
    def name( self: Self ) -> str:
        """Get the filter name.

        Returns:
            str: The filter name.
        """
        return self._filterName

    @name.setter
    def name( self: Self, name: str ) -> None:
        """Set the filter name.

        Args:
            name (str): The new filter name.
        """
        if not isinstance( name, str ):
            raise TypeError( f"Input 'name' must be a string, but got {type(name).__name__}." )
        if not name.strip():
            raise ValueError( "Input 'name' cannot be an empty or whitespace-only string." )
        self._filterName = name

    @property
    def mesh( self: Self ) -> Union[ vtkUnstructuredGrid, None ]:
        """Get the generated mesh.

        Returns:
            Union[vtkUnstructuredGrid, None]: The generated mesh, or None if not yet generated.
        """
        if self._mesh is None:
            self.logger.warning( "Mesh has not been generated yet. Call applyFilter() first." )
            return None
        else:
            return self._mesh

    def writeMesh( self: Self, filepath: str, isDataModeBinary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of the mesh handled by the filter at the specified filepath.

        Args:
            filepath (str): The path for the output mesh file.
            isDataModeBinary (bool, optional): Writes the file in binary format (True) or ascii (False).
                                               Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        if self.mesh:
            vtkOutput = VtkOutput( filepath, isDataModeBinary, canOverwrite )
            try:
                writeMesh( self.mesh, vtkOutput, vtkOutput.canOverwrite )
            except FileExistsError as e:
                self.logger.error( f"{e} Set canOverwrite=True to allow overwriting existing files." )
                raise
        else:
            self.logger.error( f"No mesh generated. Cannot output vtkUnstructuredGrid at {filepath}." )
