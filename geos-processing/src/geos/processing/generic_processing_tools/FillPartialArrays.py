# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville, Martin Lemay

from typing_extensions import Self
from typing import Union, Any

from geos.utils.Logger import logging, Logger, getLogger
from geos.utils.pieceEnum import Piece
from geos.mesh.utils.arrayModifiers import fillPartialAttributes
from geos.mesh.utils.arrayHelpers import getAttributePieceInfo

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

__doc__ = """
Fill partial attributes of the input mesh with constant values per component.

Input mesh is vtkMultiBlockDataSet and attributes to fill must be partial.

The list of filling values per attribute is given by a dictionary.
Its keys are the attribute names and its items are the list of filling values for each component.

If the list of filling value is None, attributes are filled with the same constant value for each component:
0 for uint data, -1 for int data and nan for float data.

To use a handler of yours for the logger, set the variable 'speHandler' to True and add it to the filter
with the member function setLoggerHandler.

To use it:

.. code-block:: python

    from geos.processing.generic_processing_tools.FillPartialArrays import FillPartialArrays

    # Filter inputs.
    multiBlockDataSet: vtkMultiBlockDataSet
    dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ]
    # Optional inputs.
    speHandler: bool

    # Instantiate the filter.
    fillPartialArraysFilter: FillPartialArrays = FillPartialArrays(
        multiBlockDataSet,
        dictAttributesValues,
        speHandler
    )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    fillPartialArraysFilter.setLoggerHandler( yourHandler )

    # Do calculations.
    fillPartialArraysFilter.applyFilter()
"""

loggerTitle: str = "Fill Partial Attribute"


class FillPartialArrays:

    def __init__(
        self: Self,
        multiBlockDataSet: vtkMultiBlockDataSet,
        dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ],
        speHandler: bool = False,
    ) -> None:
        """Fill partial attributes with constant value per component.

        If the list of filling values for an attribute is None,
        it will be filled with the default value for each component:

        - 0 for uint data.
        - -1 for int data.
        - nan for float data.

        Args:
            multiBlockDataSet (vtkMultiBlockDataSet): The mesh where to fill the attribute.
            dictAttributesValues (dict[str, Any]): The dictionary with the attribute to fill as keys
                                                   and the list of filling values as values.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.multiBlockDataSet: vtkMultiBlockDataSet = multiBlockDataSet
        self.dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ] = dictAttributesValues

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler' to True"
                                 " during the filter initialization." )

    def applyFilter( self: Self ) -> bool:
        """Create a constant attribute per region in the mesh.

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        piece: Piece
        for attributeName in self.dictAttributesValues:
            piece = getAttributePieceInfo( self.multiBlockDataSet, attributeName )
            if piece == Piece.NONE:
                self.logger.error( f"{ attributeName } is not in the mesh." )
                self.logger.error( f"The attribute { attributeName } has not been filled." )
                self.logger.error( f"The filter { self.logger.name } failed." )
                return False
            elif piece == Piece.BOTH:
                self.logger.error( f"There is two attribute named { attributeName },"
                                   " one on points and the other on cells. The attribute must be unique." )
                self.logger.error( f"The attribute { attributeName } has not been filled." )
                self.logger.error( f"The filter { self.logger.name } failed." )
                return False

            if not fillPartialAttributes( self.multiBlockDataSet,
                                          attributeName,
                                          piece=piece,
                                          listValues=self.dictAttributesValues[ attributeName ],
                                          logger=self.logger ):
                self.logger.error( f"The filter { self.logger.name } failed." )
                return False

        self.logger.info( f"The filter { self.logger.name } succeed." )

        return True
