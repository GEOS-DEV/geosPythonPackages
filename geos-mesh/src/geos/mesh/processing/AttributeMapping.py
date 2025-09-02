# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay, Romain Baville
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
    vtkCell,
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
from geos.mesh.utils.arrayHelpers import ( getAttributeSet, getVtkArrayInObject, computeCellCenterCoordinates, isAttributeGlobal )

__doc__ = """
AttributeMapping is a vtk filter that transfer attributes from a source mesh to the working mesh for each
cell of the two meshes with the same coordinates.
The filter update the working mesh directly, no copy is created.

Input and output meshes can be vtkDataSet or vtkMultiBlockDataSet.
The names of the attributes to transfer are give with a set of string.
To use a handler of yours, set the variable 'speHandler' to True and add it using the member function addLoggerHandler.

To use the filter:

.. code-block:: python

    from filters.AttributeMapping import AttributeMapping

    # filter inputs.
    sourceMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    workingMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    transferredAttributeNames: set[ str ]
    # Optional inputs.
    speHandler: bool

    # instantiate the filter
    filter :AttributeMapping = AttributeMapping( sourceMesh,
                                                 workingMesh,
                                                 transferredAttributeNames,
                                                 speHandler,
    )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    filter.setLoggerHandler( yourHandler )

    # Do calculations.
    filter.applyFilter()
"""

loggerTitle: str = "Attribute Mapping"


class AttributeMapping:

    def __init__(
            self: Self, 
            sourceMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ],
            workingMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ],
            transferredAttributeNames: set[ str ],
            speHandler: bool = False,
        ) -> None:
        """Map attributes of the source mesh to the working mesh.
        
        Args:
            sourceMesh (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh with attributes to transfer.
            workingMesh (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh where to copy attributes.
            transferredAttributeNames (set[str]): Names of the attributes to transfer.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.sourceMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = sourceMesh
        self.workingMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = workingMesh
        self.transferredAttributeNames: set[ str ] = transferredAttributeNames

        # cell map
        self.m_cellMap = np.full( workingMesh.GetNumberOfCells(), -1 ).astype( int )

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


    def GetCellMap( self: Self ) -> npt.NDArray[ np.int64 ]:
        """Getter of cell map."""
        return self.m_cellMap


    def applyFilter( self: Self ) -> bool:
        """Map attributes from the source mesh to the working mesh for the shared cells.

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        if len( self.transferredAttributeNames ) == 0:
            self.logger.warning( "Please enter at least one attribute to transfer." )
            self.logger.warning( f"The filter { self.logger.name } has not been used." )
            return False            

        falseAttributeNames: list[ str ] = []
        attributeNameSource: set[ str ] = getAttributeSet( self.sourceMesh, False )
        for attribute in self.transferredAttributeNames:
            if attribute not in attributeNameSource:
                falseAttributeNames.append( attribute )
        if len( falseAttributeNames ) > 0:
            self.logger.error( f"The attributes { falseAttributeNames } are not in the mesh." )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False

        sourceDataSet: vtkUnstructuredGrid = vtkUnstructuredGrid()
        if isinstance( self.sourceMesh, vtkDataSet ):
            sourceDataSet.ShallowCopy( self.sourceMesh )
        elif isinstance( self.sourceMesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
            sourceMultiBlockDataSet: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
            sourceMultiBlockDataSet.ShallowCopy( self.sourceMesh )
            for attributeName in self.transferredAttributeNames:
                if not isAttributeGlobal( self.sourceMesh, attributeName, False ):
                    fillPartialAttributes( sourceMultiBlockDataSet, attributeName, logger=self.logger )
            sourceDataSet.ShallowCopy( mergeBlocks( sourceMultiBlockDataSet ) )
        else:
            self.logger.error( "The source mesh data type is not vtkDataSet nor vtkMultiBlockDataSet." )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False
        
        if isinstance( self.workingMesh, vtkDataSet ):
            if not self._transferAttributes( sourceDataSet, self.workingMesh ):
                self.logger.warning( "Source mesh and working mesh do not have any shared cell." )
                self.logger.warning( f"The filter { self.logger.name } has not been used." )
                return False
        elif isinstance( self.workingMesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
            if not self._transferAttributesMultiBlock( sourceDataSet ):
                return False
        else:
            self.logger.error( "The working mesh data type is not vtkDataSet nor vtkMultiBlockDataSet." )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False
        
        # Log the output message.
        self._logOutputMessage()

        return True

    def _computeCellMapping(
            self: Self,
            sourceMesh: vtkUnstructuredGrid,
            workingMesh: vtkUnstructuredGrid,
        ) -> bool:
        """Create the cell map from the source mesh to the working mesh cell indexes.

        For each cell index of the working mesh, stores the index of the cell
        in the source mesh.

        Args:
            sourceMesh (vtkUnstructuredGrid): The mesh with attributes to transfer.
            workingMesh (vtkUnstructuredGrid): The mesh where to copy attributes.

        Returns:
            bool: True if the map was computed.

        """
        self.m_cellMap = np.full( workingMesh.GetNumberOfCells(), -1 ).astype( int )
        for idCellWorking in range( workingMesh.GetNumberOfCells() ):
            workingCell: vtkCell = workingMesh.GetCell( idCellWorking )
            boundsWorkingCell: list[ float ] = workingCell.GetBounds()
            idCellSource: int = 0
            cellFund: bool = False
            while idCellSource < sourceMesh.GetNumberOfCells() and not cellFund:
                sourceCell: vtkCell = sourceMesh.GetCell( idCellSource )
                boundsSourceCell: list[ float ] = sourceCell.GetBounds()
                if boundsSourceCell == boundsWorkingCell:
                    self.m_cellMap[ idCellWorking ] = idCellSource
                    cellFund = True
                idCellSource += 1
        return True

    def _transferAttributes( 
            self: Self,
            sourceMesh: vtkUnstructuredGrid,
            workingMesh: vtkUnstructuredGrid,
        ) -> bool:
        """Transfer attributes from the source mesh to the working meshes using cell mapping.

        Args:
            sourceMesh (vtkUnstructuredGrid): The mesh with attributes to transfer.
            workingMesh (vtkUnstructuredGrid): The mesh where to copy attributes.

        Returns:
            bool: True if transfer successfully ended.
        """
        # create cell map
        self._computeCellMapping( sourceMesh, workingMesh )

        # transfer attributes if at least one corresponding cell
        if np.any( self.m_cellMap > -1 ):
            for attributeName in self.transferredAttributeNames:
                array: vtkDataArray = getVtkArrayInObject( sourceMesh, attributeName, False )

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


    def _transferAttributesMultiBlock( self: Self, sourceMesh: vtkUnstructuredGrid ) -> bool:
        """Transfer attributes from a source vtkUnstructuredGrid to a working multiblock.

        Args:
            sourceMesh (vtkUnstructuredGrid): The source mesh with attributes to transfer.

        Returns:
            boolean (bool): True if attributes were successfully transferred.
        """
        usedCheck: bool = False
        nbBlocks: int = self.workingMesh.GetNumberOfBlocks()
        for idBlock in range( nbBlocks ):
            workingBlock: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( self.workingMesh.GetBlock( idBlock ) )
            if not self._transferAttributes( sourceMesh, workingBlock ):
                self.logger.warning( f"Source mesh and the working mesh block number { idBlock } do not have any shared cell." )
            else:
                usedCheck = True

        if usedCheck:
            return True
        
        self.logger.warning( f"The filter { self.logger.name } has not been used." )
        return False

        
    def _logOutputMessage( self: Self ) -> None:
        """Create and log result messages of the filter."""
        self.logger.info( f"The filter { self.logger.name } succeed." )

