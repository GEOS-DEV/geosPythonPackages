# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------
import numpy as np
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.numpy_interface import dataset_adapter as dsa
from geos.mesh.utils.genericHelpers import find_2D_cell_ids, find_cells_near_faces
from geos.utils.Logger import logging, Logger, getLogger

__doc__ = """
Find Damage/Fractured Zone (DMZ) cells in mesh based on proximity to fault faces.

Input mesh is vtkUnstructuredGrid and output is the same mesh with added DMZ array.

The DMZ is identified by finding cells within a specified distance from fault faces
in a given active region.

To use a handler of yours for the logger, set the variable 'speHandler' to True and add it to the filter
with the member function setLoggerHandler.

To use it:

.. code-block:: python

    from geos.mesh.fault.DMZFinder import DMZFinder

    # Filter inputs.
    unstructuredGrid: vtkUnstructuredGrid
    region_array_name: str = "attribute"
    active_region_id: int = 0
    active_fault_id: int = 0
    output_array_name: str = "isDMZ"
    dmz_length: float = 100.0
    # Optional inputs.
    speHandler: bool

    # Instantiate the filter.
    filter: DMZFinder = DMZFinder( unstructuredGrid, region_array_name, active_region_id,
                                   active_fault_id, output_array_name, dmz_length, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    filter.setLoggerHandler( yourHandler )

    # Do calculations.
    filter.applyFilter()
"""

loggerTitle: str = "DMZ Finder"


class DMZFinder:

    def __init__(
        self: Self,
        unstructuredGrid: vtkUnstructuredGrid,
        region_array_name: str = "attribute",
        active_region_id: int = 0,
        active_fault_id: int = 0,
        output_array_name: str = "isDMZ",
        dmz_length: float = 100.0,
        speHandler: bool = False,
    ) -> None:
        """Find Damage/Fractured Zone (DMZ) cells in mesh.

        Args:
            unstructuredGrid (vtkUnstructuredGrid): The mesh where to find DMZ cells.
            region_array_name (str, optional): Name of the region array. Defaults to "attribute".
            active_region_id (int, optional): ID of the active region. Defaults to 0.
            active_fault_id (int, optional): ID of the active fault. Defaults to 0.
            output_array_name (str, optional): Name of the output DMZ array. Defaults to "isDMZ".
            dmz_length (float, optional): Distance for DMZ identification. Defaults to 100.0.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.unstructuredGrid: vtkUnstructuredGrid = unstructuredGrid
        self.region_array_name: str = region_array_name
        self.active_region_id: int = active_region_id
        self.active_fault_id: int = active_fault_id
        self.output_array_name: str = output_array_name
        self.dmz_length: float = dmz_length

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are used, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has a handler, to use yours set the argument 'speHandler' to True "
                                 "during the filter initialization." )

    def applyFilter( self: Self ) -> bool:
        """Apply the DMZ finding algorithm to the mesh.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        input_grid = dsa.WrapDataObject( self.unstructuredGrid )

        if not self._check_inputs( input_grid ):
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False

        # Get the array that defines the geological regions
        region_array = input_grid.CellData[ self.region_array_name ]

        all_mesh_face_ids: set[ int ] = find_2D_cell_ids( self.unstructuredGrid )
        if not all_mesh_face_ids:
            self.logger.error( "No 2D face cells found." )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False

        number_cells: int = self.unstructuredGrid.GetNumberOfCells()
        # identify which faces are in the active region
        all_faces_mask = np.zeros( number_cells, dtype=bool )
        all_faces_mask[ list( all_mesh_face_ids ) ] = True
        active_region_mask = ( region_array == self.active_region_id )
        active_fault_mask = ( region_array == self.active_fault_id )
        active_fault_faces_mask = np.logical_and( all_faces_mask, active_fault_mask )
        active_fault_faces: set[ int ] = set( np.where( active_fault_faces_mask )[ 0 ] )
        cells_near_faces: set[ int ] = find_cells_near_faces( self.unstructuredGrid, active_fault_faces,
                                                              self.dmz_length )

        # Identify which cells are in the DMZ
        dmz_mask = np.zeros( number_cells, dtype=bool )
        dmz_mask[ list( cells_near_faces ) ] = True
        final_mask = np.logical_and( dmz_mask, active_region_mask )

        # Create the new CellData array
        new_region_id_array = np.zeros( region_array.shape, dtype=int )
        new_region_id_array[ final_mask ] = 1

        # Add new isDMZ array to the input_grid (which modifies the original mesh)
        input_grid.CellData.append( new_region_id_array, self.output_array_name )

        self.logger.info( f"The filter { self.logger.name } succeed." )
        return True

    def _check_inputs( self: Self, dsa_mesh: dsa.UnstructuredGrid ) -> bool:
        """Check if inputs are valid.

        Args:
            dsa_mesh (dsa.UnstructuredGrid): The wrapped mesh to check.

        Returns:
            bool: True if inputs are valid, False otherwise.
        """
        if self.output_array_name == self.region_array_name:
            self.logger.error( "Output array name cannot be the same as region array name." )
            return False

        if dsa_mesh is None:
            self.logger.error( "Input mesh is not set." )
            return False

        region_array = dsa_mesh.CellData[ self.region_array_name ]
        if region_array is None:
            self.logger.error( f"Region array '{self.region_array_name}' is not found in input mesh." )
            return False
        else:
            if self.active_region_id not in region_array:
                self.logger.error( f"Active region ID '{self.active_region_id}' is not found in region array." )
                return False

        return True
