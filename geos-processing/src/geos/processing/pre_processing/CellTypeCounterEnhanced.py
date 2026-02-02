# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import logging

from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkIntArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkCell, vtkTable, vtkCellTypes, VTK_VERTEX

from geos.mesh.model.CellTypeCounts import CellTypeCounts
from geos.mesh.stats.meshQualityMetricHelpers import getAllCellTypes
from geos.utils.Logger import ( getLogger, Logger, CountWarningHandler, isHandlerInLogger, getLoggerHandlerType )

__doc__ = """
CellTypeCounterEnhanced module is a vtk filter that computes cell type counts.

Filter input is a vtkUnstructuredGrid, output is a vtkTable

To use the filter:

.. code-block:: python

    from geos.processing.pre_processing.CellTypeCounterEnhanced import CellTypeCounterEnhanced

    # Filter inputs
    inputMesh: vtkUnstructuredGrid
    speHandler: bool  # defaults to False

    # Instantiate the filter
    cellTypeCounterEnhancedFilter: CellTypeCounterEnhanced = CellTypeCounterEnhanced( inputMesh, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    cellTypeCounterEnhancedFilter.setLoggerHandler( yourHandler )

    # Do calculations
    try:
        cellTypeCounterEnhancedFilter.applyFilter()
    except TypeError as e:
        cellTypeCounterEnhancedFilter.logger.error( f"The filter { cellTypeCounterEnhancedFilter.logger.name } failed due to: { e }" )
    except Exception as e:
        mess: str = f"The filter { cellTypeCounterEnhancedFilter.logger.name } failed due to: { e }"
        cellTypeCounterEnhancedFilter.logger.critical( mess, exc_info=True )

    # Get result
    counts: CellTypeCounts = cellTypeCounterEnhancedFilter.GetCellTypeCountsObject()
    outputTable: vtkTable = cellTypeCounterEnhancedFilter.getOutput()
"""

loggerTitle: str = "Cell Type Counter Enhanced"


class CellTypeCounterEnhanced():

    def __init__(
        self: Self,
        inputMesh: vtkUnstructuredGrid,
        speHandler: bool = False,
    ) -> None:
        """CellTypeCounterEnhanced filter computes mesh stats.

        Args:
            inputMesh (vtkUnstructuredGrid): The input mesh.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.inputMesh: vtkUnstructuredGrid = inputMesh
        self.outTable: vtkTable = vtkTable()
        self._counts: CellTypeCounts = CellTypeCounts()

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

        counter: CountWarningHandler = CountWarningHandler()
        self.counter: CountWarningHandler
        self.nbWarnings: int = 0
        try:
            self.counter = getLoggerHandlerType( type( counter ), self.logger )
            self.counter.resetWarningCount()
        except:
            self.counter = counter
            self.counter.setLevel( logging.INFO )

        self.logger.addHandler( self.counter )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not isHandlerInLogger( handler, self.logger ):
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has this handler, it has not be added." )

    def applyFilter( self: Self ) -> None:
        """Apply CellTypeCounterEnhanced filter.

        Raises:
            TypeError: Errors with the type of the cells.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        # Compute cell type counts
        self._counts.reset()
        self._counts.setTypeCount( VTK_VERTEX, self.inputMesh.GetNumberOfPoints() )
        for i in range( self.inputMesh.GetNumberOfCells() ):
            cell: vtkCell = self.inputMesh.GetCell( i )
            self._counts.addType( cell.GetCellType() )

        # Create output table
        # First reset output table
        self.outTable.RemoveAllRows()
        self.outTable.RemoveAllColumns()
        self.outTable.SetNumberOfRows( 1 )

        # Create columns per types
        for cellType in getAllCellTypes():
            array: vtkIntArray = vtkIntArray()
            array.SetName( vtkCellTypes.GetClassNameFromTypeId( cellType ) )
            array.SetNumberOfComponents( 1 )
            array.SetNumberOfValues( 1 )
            array.SetValue( 0, self._counts.getTypeCount( cellType ) )
            self.outTable.AddColumn( array )

        result: str = f"The filter { self.logger.name } succeeded"
        if self.counter.warningCount > 0:
            self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
        else:
            self.logger.info( f"{ result }." )

        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        return

    def GetCellTypeCountsObject( self: Self ) -> CellTypeCounts:
        """Get CellTypeCounts object.

        Returns:
            CellTypeCounts: CellTypeCounts object.
        """
        return self._counts

    def getOutput( self: Self ) -> vtkTable:
        """Get the computed vtkTable."""
        return self.outTable
