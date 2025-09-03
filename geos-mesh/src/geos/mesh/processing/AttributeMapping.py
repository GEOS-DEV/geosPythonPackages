# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
from geos.utils.Logger import logging, Logger, getLogger
from typing_extensions import Self, Union, Any
import vtkmodules.util.numpy_support as vnp

from vtk import (  # type: ignore[import-untyped]
    VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG,
    VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE, VTK_FLOAT, VTK_DOUBLE,
)
from vtkmodules.vtkCommonDataModel import (
    vtkDataSet,
    vtkMultiBlockDataSet,
)

from geos.mesh.utils.arrayModifiers import createAttribute
from geos.mesh.utils.arrayHelpers import ( computeCellMapping, getAttributeSet, getComponentNames,
                                           getVtkDataTypeInObject, isAttributeGlobal )

__doc__ = """
AttributeMapping is a vtk filter that transfer global attributes from a source mesh (meshFrom) to another (meshTo) for each
cell of the two meshes with the same bounds coordinates.
The filter update the mesh where attributes are transferred directly, no copy is created.

Input and output meshes can be vtkDataSet or vtkMultiBlockDataSet.
The names of the attributes to transfer are give with a set of string.
To use a handler of yours, set the variable 'speHandler' to True and add it using the member function addLoggerHandler.

To use the filter:

.. code-block:: python

    from filters.AttributeMapping import AttributeMapping

    # filter inputs.
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    attributeNames: set[ str ]
    # Optional inputs.
    speHandler: bool

    # instantiate the filter
    filter :AttributeMapping = AttributeMapping( meshFrom,
                                                 meshTo,
                                                 attributeNames,
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
        meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
        meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ],
        attributeNames: set[ str ],
        speHandler: bool = False,
    ) -> None:
        """Map attributes of the source mesh (meshFrom) to the other mesh (meshTo).

        Args:
            meshFrom (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh with attributes to transfer.
            meshTo (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh where to copy attributes.
            attributeNames (set[str]): Names of the attributes to transfer.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = meshFrom
        self.meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = meshTo
        self.attributeNames: set[ str ] = attributeNames

        # cell map
        self.dictCellMap: dict[ int, npt.NDArray[ np.int64 ] ] = {}

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

    def GetCellMap( self: Self ) -> dict[ int, npt.NDArray[ np.int64 ] ]:
        """Getter of cell mapping dictionary.

        Returns:
            self.dictCellMap (dict[int, npt.NDArray[np.int64]]): The cell mapping dictionary.
        """
        return self.dictCellMap

    def applyFilter( self: Self ) -> bool:
        """Map attributes from the source mesh (meshFrom) to the other (meshTo) for the shared cells.

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        if len( self.attributeNames ) == 0:
            self.logger.warning( "Please enter at least one attribute to transfer." )
            self.logger.warning( f"The filter { self.logger.name } has not been used." )
            return False

        wrongAttributeNames: list[ str ] = []
        attributesAlreadyInMeshTo: list = []
        attributesInMeshFrom: set[ str ] = getAttributeSet( self.meshFrom, False )
        attributesInMeshTo: set[ str ] = getAttributeSet( self.meshTo, False )
        for attributeName in self.attributeNames:
            if attributeName not in attributesInMeshFrom:
                wrongAttributeNames.append( attributeName )

            if attributeName in attributesInMeshTo:
                attributesAlreadyInMeshTo.append( attributeName )

        if len( wrongAttributeNames ) > 0:
            self.logger.error(
                f"The attributes { wrongAttributeNames } are not in the mesh from where to transfer attributes." )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False

        if len( attributesAlreadyInMeshTo ) > 0:
            self.logger.error(
                f"The attributes { attributesAlreadyInMeshTo } are already in the mesh where attributes must be transferred."
            )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False

        if isinstance( self.meshFrom, vtkMultiBlockDataSet ):
            partialAttributes: list[ str ] = []
            for attributeName in self.attributeNames:
                if not isAttributeGlobal( self.meshFrom, attributeName, False ):
                    partialAttributes.append( attributeName )

            if len( partialAttributes ) > 0:
                self.logger.error( f"All attributes to transfer must be global, { partialAttributes } are partials." )
                self.logger.error( f"The filter { self.logger.name } failed." )

        self.dictCellMap = computeCellMapping( self.meshFrom, self.meshTo )
        sharedCell: bool = False
        for key in self.dictCellMap:
            if np.any( self.dictCellMap[ key ] > -1 ):
                sharedCell = True

        if not sharedCell:
            self.logger.warning( "The two meshes do not have any shared cell." )
            self.logger.warning( f"The filter { self.logger.name } has not been used." )
            return False

        for attributeName in self.attributeNames:
            componentNames: tuple[ str, ...] = getComponentNames( self.meshFrom, attributeName, False )

            vtkDataType: int = getVtkDataTypeInObject( self.meshFrom, attributeName, False )
            defaultValue: Any
            if vtkDataType in ( VTK_FLOAT, VTK_DOUBLE ):
                defaultValue = np.nan
            elif vtkDataType in ( VTK_CHAR, VTK_SIGNED_CHAR, VTK_SHORT, VTK_LONG, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE ):
                defaultValue = -1
            elif vtkDataType in ( VTK_BIT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_LONG, VTK_UNSIGNED_INT,
                                  VTK_UNSIGNED_LONG_LONG ):
                defaultValue = 0

            if isinstance( self.meshTo, vtkDataSet ):
                if not self._transferAttribute( self.meshFrom, self.meshTo, attributeName, componentNames, vtkDataType,
                                                defaultValue ):
                    return False
            elif isinstance( self.meshTo, vtkMultiBlockDataSet ):
                nbBlocksTo: int = self.meshTo.GetNumberOfBlocks()
                for idBlockTo in range( nbBlocksTo ):
                    blockTo: vtkDataSet = vtkDataSet.SafeDownCast( self.meshTo.GetBlock( idBlockTo ) )
                    if not self._transferAttribute( self.meshFrom, blockTo, attributeName, componentNames, vtkDataType,
                                                    defaultValue, idBlockTo ):
                        return False

        # Log the output message.
        self._logOutputMessage()

        return True

    def _transferAttribute(
        self: Self,
        meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
        dataSetTo: vtkDataSet,
        attributeName: str,
        componentNames: tuple[ str, ...],
        vtkDataType: int,
        defaultValue: Any,
        idBlockTo: int = 0,
    ) -> bool:
        """Transfer attributes from the source mesh to the working meshes using cell mapping.

        dataSetTo is considered as block of a vtkMultiblockDataSet, if not, 0 is use as block index.

        Args:
            meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The mesh with attributes to transfer.
            dataSetTo (vtkDataSet): The mesh where to transfer attributes.
            attributeName (str): The name of the attribute to transfer.
            componentNames (tuple[str, ...]): The name of the component of the attributes to transfer. If no component, set an empty tuple.
            vtkDataType (int): The vtk type of the attribute to transfer.
            defaultValue (Any): The value to use for the cell not mapped.
            idBlockTo (int, Optional): The block index of the dataSetTo.
                Defaults to 0.

        Returns:
            bool: True if transfer successfully ended.
        """
        nbCellTo: int = dataSetTo.GetNumberOfCells()
        nbComponents: int = len( componentNames )
        typeMapping: dict[ int, type ] = vnp.get_vtk_to_numpy_typemap()
        valueType: type = typeMapping[ vtkDataType ]
        arrayTo: npt.NDArray[ Any ]
        if nbComponents > 1:
            defaultValue = [ defaultValue ] * nbComponents
            arrayTo = np.full( ( nbCellTo, nbComponents ), defaultValue, dtype=valueType )
        else:
            arrayTo = np.array( [ defaultValue for _ in range( nbCellTo ) ], dtype=valueType )

        for idCellTo in range( nbCellTo ):
            value: Any = defaultValue
            idCellFrom: int = self.dictCellMap[ idBlockTo ][ idCellTo ][ 1 ]
            if idCellFrom != -1:
                idBlockFrom = self.dictCellMap[ idBlockTo ][ idCellTo ][ 0 ]
                arrayFrom: npt.NDArray[ Any ]
                if isinstance( meshFrom, vtkDataSet ):
                    arrayFrom = vnp.vtk_to_numpy( meshFrom.GetCellData().GetArray( attributeName ) )
                elif isinstance( meshFrom, vtkMultiBlockDataSet ):
                    blockFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetBlock( idBlockFrom ) )
                    arrayFrom = vnp.vtk_to_numpy( blockFrom.GetCellData().GetArray( attributeName ) )
                value = arrayFrom[ idCellFrom ]
            arrayTo[ idCellTo ] = value

        return createAttribute( dataSetTo,
                                arrayTo,
                                attributeName,
                                componentNames,
                                onPoints=False,
                                vtkDataType=vtkDataType,
                                logger=self.logger )

    def _logOutputMessage( self: Self ) -> None:
        """Create and log result messages of the filter."""
        self.logger.info( f"The filter { self.logger.name } succeed." )
