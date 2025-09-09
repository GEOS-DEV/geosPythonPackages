# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
from geos.utils.Logger import logging, Logger, getLogger
from typing_extensions import Self, Union

from vtkmodules.vtkCommonDataModel import (
    vtkDataSet,
    vtkMultiBlockDataSet,
)

from geos.mesh.utils.arrayModifiers import transferAttributeWithElementMap
from geos.mesh.utils.arrayHelpers import ( computeElementMapping, getAttributeSet, isAttributeGlobal )

__doc__ = """
AttributeMapping is a vtk filter that transfer global attributes from a meshFrom to a meshTo for each
cell or point of the two meshes with the same coordinates. For cell, the coordinates of the points in the cell are compared.
The filter update the mesh where attributes are transferred directly, no copy is created.

Input and output meshes can be vtkDataSet or vtkMultiBlockDataSet.
The names of the attributes to transfer are give with a set of string.
The localization of the attributes to transfer is a bool, True for points, False for cells. All the attributes must be on the same piece.
To use a handler of yours, set the variable 'speHandler' to True and add it using the member function addLoggerHandler.

To use the filter:

.. code-block:: python

    from filters.AttributeMapping import AttributeMapping

    # Filter inputs.
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    attributeNames: set[ str ]
    # Optional inputs.
    onPoints: bool  # defaults to False
    speHandler: bool  # defaults to False

    # Instantiate the filter
    filter :AttributeMapping = AttributeMapping( meshFrom,
                                                 meshTo,
                                                 attributeNames,
                                                 onPoints,
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
        onPoints: bool = False,
        speHandler: bool = False,
    ) -> None:
        """Transfer global attributes from the meshFrom to the meshTo mapping the piece of the attributes to transfer.

        Args:
            meshFrom (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh with attributes to transfer.
            meshTo (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh where to transfer attributes.
            attributeNames (set[str]): Names of the attributes to transfer.
            onPoints (bool): True if attributes are on points, False if they are on cells.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = meshFrom
        self.meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = meshTo
        self.attributeNames: set[ str ] = attributeNames
        self.onPoints: bool = onPoints
        self.piece: str = "points" if self.onPoints else "cells"

        # cell map
        self.ElementMap: dict[ int, npt.NDArray[ np.int64 ] ] = {}

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

    def GetElementMap( self: Self ) -> dict[ int, npt.NDArray[ np.int64 ] ]:
        """Getter of the element mapping dictionary.

        If attribute to transfer are on points it will be a pointMap, else it will be a cellMap.

        Returns:
            self.elementMap (dict[int, npt.NDArray[np.int64]]): The element mapping dictionary.
        """
        return self.ElementMap

    def applyFilter( self: Self ) -> bool:
        """Transfer attributes on element from the meshFrom to the meshTo with the elementMap.

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        if len( self.attributeNames ) == 0:
            self.logger.warning( f"Please enter at least one { self.piece } attribute to transfer." )
            self.logger.warning( f"The filter { self.logger.name } has not been used." )
            return False

        wrongAttributeNames: list[ str ] = []
        attributesAlreadyInMeshTo: list = []
        attributesInMeshFrom: set[ str ] = getAttributeSet( self.meshFrom, self.onPoints )
        attributesInMeshTo: set[ str ] = getAttributeSet( self.meshTo, self.onPoints )
        for attributeName in self.attributeNames:
            if attributeName not in attributesInMeshFrom:
                wrongAttributeNames.append( attributeName )

            if attributeName in attributesInMeshTo:
                attributesAlreadyInMeshTo.append( attributeName )

        if len( wrongAttributeNames ) > 0:
            self.logger.error(
                f"The { self.piece } attributes { wrongAttributeNames } are not in the mesh from where to transfer attributes."
            )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False

        if len( attributesAlreadyInMeshTo ) > 0:
            self.logger.error(
                f"The { self.piece } attributes { attributesAlreadyInMeshTo } are already in the mesh where attributes must be transferred."
            )
            self.logger.error( f"The filter { self.logger.name } failed." )
            return False

        if isinstance( self.meshFrom, vtkMultiBlockDataSet ):
            partialAttributes: list[ str ] = []
            for attributeName in self.attributeNames:
                if not isAttributeGlobal( self.meshFrom, attributeName, self.onPoints ):
                    partialAttributes.append( attributeName )

            if len( partialAttributes ) > 0:
                self.logger.error(
                    f"All { self.piece } attributes to transfer must be global, { partialAttributes } are partials." )
                self.logger.error( f"The filter { self.logger.name } failed." )

        self.ElementMap = computeElementMapping( self.meshFrom, self.meshTo, self.onPoints )
        sharedElement: bool = False
        for key in self.ElementMap:
            if np.any( self.ElementMap[ key ] > -1 ):
                sharedElement = True

        if not sharedElement:
            self.logger.warning( f"The two meshes do not have any shared { self.piece }." )
            self.logger.warning( f"The filter { self.logger.name } has not been used." )
            return False

        for attributeName in self.attributeNames:
            if not transferAttributeWithElementMap( self.meshFrom, self.meshTo, self.ElementMap, attributeName,
                                                    self.onPoints, self.logger ):
                return False

        # Log the output message.
        self._logOutputMessage()

        return True

    def _logOutputMessage( self: Self ) -> None:
        """Create and log result messages of the filter."""
        self.logger.info( f"The filter { self.logger.name } succeed." )
