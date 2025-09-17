# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Union
from typing_extensions import Self

from geos.utils.Logger import logging, Logger, getLogger
from geos.mesh.utils.multiblockModifiers import mergeBlocks

from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

__doc__ = """
Merge Blocks Keeping Partial Attributes is a filter that allows to merge blocks from a multiblock dataset while keeping partial attributes.

Input is a vtkMultiBlockDataSet and output is a vtkUnstructuredGrid.

.. Note::
    - This filter is intended to be used for GEOS VTK outputs. You may encounter issues if two datasets of the input multiblock dataset have duplicated cell IDs.
    - Partial attributes are filled with default values depending on their types.
        - 0 for uint data.
        - -1 for int data.
        - nan for float data.


To use it:

.. code-block:: python

    from geos.mesh.processing.MergeBlockEnhanced import MergeBlockEnhanced

    # Define filter inputs
    multiblockdataset: vtkMultiblockDataSet
    speHandler: bool # optional

    # Instantiate the filter
    filter: MergeBlockEnhanced = MergeBlockEnhanced( multiblockdataset, speHandler )

    # Use your own handler (if speHandler is True)
    yourHandler: logging.Handler
    filter.addLoggerHandler( yourHandler )

    # Do calculations
    filter.applyFilter()

    # Get the merged mesh
    filter.getOutput()
"""

loggerTitle: str = "Merge Block Enhanced"


class MergeBlockEnhanced:

    def __init__(
        self: Self,
        inputMesh: vtkMultiBlockDataSet,
        speHandler: bool = False,
    ) -> None:
        """Merge a multiblock dataset and keep the partial attributes in the output mesh.

        Partial attributes are filled with default values depending on the data type such that:
            - 0 for uint data.
            - -1 for int data.
            - nan for float data.

        Args:
            inputMesh (vtkMultiBlockDataSet): The input multiblock dataset to merge.
            speHandler (bool, optional) : True to use a specific handler, False to use the internal handler.
            Defaults to False.
        """
        self.inputMesh: vtkMultiBlockDataSet = inputMesh
        self.outputMesh: vtkUnstructuredGrid = vtkUnstructuredGrid()

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            self.logger.warning(
                "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization."
            )

    def applyFilter( self: Self ) -> bool:
        """Merge the blocks of a multiblock dataset mesh.

        Returns:
            bool: True if the blocks were successfully merged, False otherwise.
        """
        self.logger.info( f"Applying filter { self.logger.name }." )

        if not isinstance( self.inputMesh, vtkCompositeDataSet ) or not isinstance( self.inputMesh,
                                                                                    vtkMultiBlockDataSet ):
            self.logger.error(
                f"Expected a vtkMultiblockdataset or vtkCompositeDataSet, Got a {type(self.inputMesh)} \n The filter { self.logger.name } failed."
            )
            return False

        success: bool
        outputMesh: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet, vtkCompositeDataSet ]
        success, outputMesh = mergeBlocks( self.inputMesh, True, self.logger )

        if not success:
            self.logger.error( f"The filter {self.logger.name} failed." )
            return False

        else:
            self.logger.info( f"The filter { self.logger.name } succeeded." )
            self.outputMesh = outputMesh
        return True

    def getOutput( self: Self ) -> vtkUnstructuredGrid:
        """Get the merged mesh.

        Returns:
            vtkUnstructuredGrid: The merged mesh.
        """
        return self.outputMesh
