# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
import logging

from typing_extensions import Self

from geos.utils.Logger import ( getLogger, Logger, CountVerbosityHandler, isHandlerInLogger, getLoggerHandlerType )
from geos.mesh.utils.multiblockModifiers import mergeBlocks

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkUnstructuredGrid

__doc__ = """
Merge Blocks Keeping Partial Attributes is a filter that allows to merge blocks from a multiblock dataset
while keeping partial attributes.

Input is a vtkMultiBlockDataSet and output is a vtkUnstructuredGrid.

.. Note::
    - You may encounter issues if two datasets of the input multiblock dataset have duplicated cell IDs.
    - Partial attributes are filled with default values depending on their types.
        - 0 for uint data.
        - -1 for int data.
        - nan for float data.


To use it:

.. code-block:: python

    from geos.processing.generic_processing_tools.MergeBlockEnhanced import MergeBlockEnhanced
    import logging
    from geos.utils.Errors import VTKError

    # Define filter inputs
    multiblockdataset: vtkMultiblockDataSet
    speHandler: bool # optional

    # Instantiate the filter
    mergeBlockEnhancedFilter: MergeBlockEnhanced = MergeBlockEnhanced( multiblockdataset, speHandler )

    # Use your own handler (if speHandler is True)
    yourHandler: logging.Handler
    mergeBlockEnhancedFilter.setLoggerHandler( yourHandler )

    # Do calculations
    try:
        mergeBlockEnhancedFilter.applyFilter()
    except VTKError as e:
        mergeBlockEnhancedFilter.logger.error( f"The filter { mergeBlockEnhancedFilter.logger.name } failed due to: { e }" )
    except Exception as e:
        mess: str = f"The filter { mergeBlockEnhancedFilter.logger.name } failed due to: { e }"
        mergeBlockEnhancedFilter.logger.critical( mess, exc_info=True )

    # Get the merged mesh
    mergeBlockEnhancedFilter.getOutput()
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
            self.logger.propagate = False

        counter: CountVerbosityHandler = CountVerbosityHandler()
        self.counter: CountVerbosityHandler
        self.nbWarnings: int = 0
        try:
            self.counter = getLoggerHandlerType( type( counter ), self.logger )
            self.counter.resetWarningCount()
        except ValueError:
            self.counter = counter
            self.counter.setLevel( logging.INFO )

        self.logger.addHandler( self.counter )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not isHandlerInLogger( handler, self.logger ):
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has this handler, it has not been added." )

    def applyFilter( self: Self ) -> None:
        """Merge the blocks of a multiblock dataset mesh.

        Raises:
            VTKError (geos.utils.Errors): Errors captured if any from the VTK log.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        outputMesh: vtkUnstructuredGrid
        outputMesh = mergeBlocks( self.inputMesh, keepPartialAttributes=True, logger=self.logger )
        self.outputMesh = outputMesh

        result: str = f"The filter { self.logger.name } succeeded"
        if self.counter.warningCount > 0:
            self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
        else:
            self.logger.info( f"{ result }." )

        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        return

    def getOutput( self: Self ) -> vtkUnstructuredGrid:
        """Get the merged mesh.

        Returns:
            vtkUnstructuredGrid: The merged mesh.
        """
        return self.outputMesh
