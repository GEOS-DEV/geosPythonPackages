# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file

from collections.abc import MutableSequence

import numpy as np
import numpy.typing as npt
from geos.utils.Logger import logging, Logger, getLogger
from typing_extensions import Self, Union, Any

from vtk import (  # type: ignore[import-untyped]
    VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG,
    VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE, VTK_FLOAT, VTK_DOUBLE,
)
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import (
    vtkCellData,
    vtkCellLocator,
    vtkDataSet,
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
    vtkCompositeDataSet,
)

from geos.mesh.utils.arrayModifiers import fillPartialAttributes
from geos.mesh.utils.multiblockModifiers import mergeBlocks
from geos.mesh.utils.arrayModifiers import createEmptyAttribute
from geos.mesh.utils.arrayHelpers import ( getVtkArrayInObject, computeCellCenterCoordinates, isAttributeGlobal )

__doc__ = """
AttributeMappingFromCellCoords module is a vtk filter that map two identical mesh (or a mesh is
an extract from the other one) and create an attribute containing shared cell ids.

Filter input and output types are vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.AttributeMappingFromCellCoords import AttributeMappingFromCellCoords

    # filter inputs
    logger :Logger
    input :vtkUnstructuredGrid
    TransferAttributeName : str

    # instantiate the filter
    filter :AttributeMappingFromCellCoords = AttributeMappingFromCellCoords()
    # set the logger
    filter.SetLogger(logger)
    # set input data object
    filter.SetInputDataObject(input)
    # set Attribute to transfer
    filter.SetTransferAttributeNames(AttributeName)
    # set Attribute to compare
    filter.SetIDAttributeName(AttributeName)
    # do calculations
    filter.Update()
    # get output object
    output :vtkPolyData = filter.GetOutputDataObject(0)
    # get created attribute names
    newAttributeNames :set[str] = filter.GetNewAttributeNames()
"""

loggerTitle: str = "Attribute Mapping"


class AttributeMappingFromCellCoords:

    def __init__(
            self: Self, 
            sourceMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ],
            workingMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ],
            speHandler: bool = False,
        ) -> None:
        """Map the properties of the source mesh to the working mesh."""

        self.sourceMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = sourceMesh
        self.workingMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = workingMesh

        # cell map
        self.m_cellMap: npt.NDArray[ np.int64 ] = np.empty( 0 ).astype( int )

        # Transfer Attribute name
        self.m_transferredAttributeNames: set[ str ] = set()

        # Logger.
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


    def SetTransferAttributeNames( self: Self, transferredAttributeNames: set[ str ] ) -> None:
        """Setter for transferredAttributeName.

        Args:
            transferredAttributeNames (set[str]): set of names of the
                attributes to transfer.

        """
        self.m_transferredAttributeNames.clear()
        for name in transferredAttributeNames:
            self.m_transferredAttributeNames.add( name )


    def GetCellMap( self: Self ) -> npt.NDArray[ np.int64 ]:
        """Getter of cell map."""
        return self.m_cellMap


    def applyFilter( self: Self ) -> bool:
        """Map the properties from the source mesh to the working mesh for the common cells.

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        if isinstance( self.sourceMesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
            for attributeName in self.m_transferredAttributeNames:
                if not isAttributeGlobal( self.sourceMesh, attributeName, False ):
                    fillPartialAttributes( self.sourceMesh, attributeName, logger=self.logger )
            self.sourceMesh = mergeBlocks( self.sourceMesh )
        elif not isinstance( self.sourceMesh, vtkDataSet ):
            self.logger.error( "The source mesh data type is not vtkDataSet nor vtkMultiBlockDataSet." )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False
        
        if isinstance( self.workingMesh, vtkDataSet ):
            if not self._transferAttributes( self.workingMesh ):
                self.logger.warning( "Source mesh and working mesh do not have any corresponding cells." )
                self.logger.warning( f"The filter { self.logger.name } has not been needed." )
                return False
        elif isinstance( self.workingMesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
            if not self._transferAttributesMultiBlock():
                return False
        else:
            self.logger.error( "The working mesh data type is not vtkDataSet nor vtkMultiBlockDataSet." )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False
        
        # Log the output message.
        self._logOutputMessage()

        return True

    def _computeCellMapping( self: Self, workingMesh ) -> bool:
        """Create the cell map from the source mesh to the working mesh cell indexes.

        For each cell index of the working mesh, stores the index of the cell
        in the source mesh.

        Returns:
            bool: True if the map was computed.

        """
        self.m_cellMap = np.full( workingMesh.GetNumberOfCells(), -1 ).astype( int )
        cellLocator: vtkCellLocator = vtkCellLocator()
        cellLocator.SetDataSet( self.sourceMesh )
        cellLocator.BuildLocator()

        cellCenters: vtkDataArray = computeCellCenterCoordinates( self.sourceMesh )
        for i in range( workingMesh.GetNumberOfCells() ):
            cellCoords: MutableSequence[ float ] = [ 0.0, 0.0, 0.0 ]
            cellCenters.GetTuple( i, cellCoords )
            cellIndex: int = cellLocator.FindCell( cellCoords )
            self.m_cellMap[ i ] = cellIndex
        return True

    def _transferAttributes( self: Self, workingMesh: vtkUnstructuredGrid ) -> bool:
        """Transfer attributes from the source mesh to the working meshes using cell mapping.

        Returns:
            bool: True if transfer successfully ended.

        """
        # create cell map
        self._computeCellMapping( workingMesh )

        # transfer attributes if at least one corresponding cell
        if np.any( self.m_cellMap > -1 ):
            for attributeName in self.m_transferredAttributeNames:
                array: vtkDataArray = getVtkArrayInObject( self.sourceMesh, attributeName, False )

                dataType = array.GetDataType()
                nbComponents: int = array.GetNumberOfComponents()
                componentNames: list[ str ] = []

                defaultValue: Any
                if dataType in ( VTK_FLOAT, VTK_DOUBLE ):
                    defaultValue =[ np.nan for _ in range( nbComponents ) ]
                elif dataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ):
                    defaultValue = [ -1 for _ in range( nbComponents ) ]
                elif dataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT,
                                VTK_UNSIGNED_LONG_LONG ):
                    defaultValue = [ 0 for _ in range( nbComponents ) ]

                if nbComponents > 1:
                    for i in range( nbComponents ):
                        componentNames.append( array.GetComponentName( i ) )
                newArray: vtkDataArray = createEmptyAttribute( attributeName, tuple( componentNames ), dataType )
                
                for indexWorking in range( workingMesh.GetNumberOfCells() ):
                    indexSource: int = self.m_cellMap[ indexWorking ]
                    data: MutableSequence[ float ] = defaultValue
                    if indexSource > -1:
                        array.GetTuple( indexSource, data )
                    newArray.InsertNextTuple( data )

                cellData: vtkCellData = workingMesh.GetCellData()
                assert cellData is not None, "CellData is undefined."
                cellData.AddArray( newArray )
                cellData.Modified()

            return True
        
        return False


    def _transferAttributesMultiBlock( self: Self ) -> bool:
        """Transfer attributes from a vtkUnstructuredGrid to a multiblock.

        Returns:
            bool: True if attributes were successfully transferred.

        """
        usedCheck: bool = False
        nbBlocks: int = self.workingMesh.GetNumberOfBlocks()
        for idBlock in range( nbBlocks ):
            workingBlock: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( self.workingMesh.GetBlock( idBlock ) )
            if not self._transferAttributes( workingBlock ):
                self.logger.warning( f"Source mesh and the working mesh block number { idBlock } do not have any corresponding cells." )
            else:
                usedCheck = True

        if usedCheck:
            return True
        
        self.logger.warning( f"The filter { self.logger.name } has not been needed." )
        return False

        
    def _logOutputMessage( self: Self ) -> None:
        self.logger.info( f"The filter { self.logger.name } succeed." )

