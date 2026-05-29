# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville, Martin Lemay
import logging
from typing_extensions import Self
from typing import Union, Any

from geos.utils.Logger import getLogger
from geos.mesh.utils.arrayModifiers import fillPartialAttributes
from geos.mesh.utils.arrayHelpers import getAttributePieceInfo

# from geos.utils.details import addLogSupport
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
    try:
        fillPartialArraysFilter.applyFilter()
    except ( ValueError, AttributeError ) as e:
        fillPartialArraysFilter.logger.error( f"The filter { fillPartialArraysFilter.logger.name } failed due to: { e }" )
    except Exception as e:
        mess: str = f"The filter { fillPartialArraysFilter.logger.name } failed due to: { e }"
        fillPartialArraysFilter.logger.critical( mess, exc_info=True )
"""

loggerTitle: str = "Fill Partial Attribute"


class FillPartialArrays:

    def __init__(
        self: Self,
        multiBlockDataSet: vtkMultiBlockDataSet,
        dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ],
    ) -> None:
        """Fill partial attributes with constant value per component.

        If the list of filling values for an attribute is None,
        it will be filled with the default value for each component:

        - 0 for uint data.
        - -1 for int data.
        - nan for float data.

        Args:
            multiBlockDataSet (vtkMultiBlockDataSet): The mesh where to fill the attribute.
            dictAttributesValues (dict[str, Any]): The dictionary with the attribute to fill as keys and the list of filling values as items.
        """
        self.logger = getLogger( loggerTitle )
        self.multiBlockDataSet: vtkMultiBlockDataSet = multiBlockDataSet
        self.dictAttributesValues: dict[ str, Union[ list[ Any ], None ] ] = dictAttributesValues

    def applyFilter( self: Self ) -> bool:
        """Create a constant attribute per region in the mesh.

        Raise:
            AttributeError: Error with attributes to fill.
            ValueError: Error during the filling of the attribute.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        piece: Piece
        mess: str = ""
        for attributeName, values in self.dictAttributesValues.items():
            piece = getAttributePieceInfo( self.multiBlockDataSet, attributeName )
            if piece == Piece.NONE:
                raise AttributeError( f"The attribute { attributeName } is not in the mesh." )
            elif piece == Piece.BOTH:
                raise AttributeError(
                    f"There is two attribute named { attributeName }, one on points and the other on cells. The attribute name must be unique."
                )

            fillPartialAttributes( self.multiBlockDataSet,
                                   attributeName,
                                   piece=piece,
                                   listValues=values,
                                   logger=self.logger )
            if values is None:
                values = [ "the default value" ]
            mess = f"{ mess }The attribute { attributeName } has been filled with { values }.\n"

        # Log the output message.
        self.logger.info( mess )

        result: str = f"The filter { self.logger.name } succeeded"
        if self.counter.warningCount > 0:
            self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
        else:
            self.logger.info( f"{ result }." )

        # Keep number of warnings logged during the filter application and reset the warnings count in case the filter is applied again.
        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        return
