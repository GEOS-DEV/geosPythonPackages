# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville, Martin Lemay

from typing_extensions import Self
from typing import Union, Any

from geos.utils.Logger import logging, Logger, getLogger, CountWarningHandler
from geos.mesh.utils.arrayModifiers import fillPartialAttributes
from geos.mesh.utils.arrayHelpers import (
    getNumberOfComponents,
    isAttributeInObject,
)

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet, )

import numpy as np

__doc__ = """
Fill partial attributes of input mesh with constant values per component.

Input mesh is vtkMultiBlockDataSet and the attribute to fill must be partial.
By defaults, attributes are filled with the same constant value for each component:
    0 for uint data.
    -1 for int data.
    nan for float data.
The filling values per attribute is given by a dictionary. Its keys are the attribute names and its items are the list of filling values for each component.
To use a specific handler for the logger, set the variable 'speHandler' to True and use the member function addLoggerHandler.

To use it:

.. code-block:: python

    from geos.mesh.processing.FillPartialArrays import FillPartialArrays

    # Filter inputs.
    multiBlockDataSet: vtkMultiBlockDataSet
    dictAttributesValues: dict[ str, Any ]

    # Instantiate the filter.
    filter: FillPartialArrays = FillPartialArrays( multiBlockDataSet, dictAttributesValues )
   
    # Set the specific handler (only if speHandler is True).
    specificHandler: logging.Handler
    filter.addLoggerHandler( specificHandler )

    # Do calculations.
    filter.applyFilter()
"""


loggerTitle: str = "Fill Partial Attribute"


class FillPartialArrays:

    def __init__( 
            self: Self,
            multiBlockDataSet: vtkMultiBlockDataSet,
            dictAttributesValues: dict[ str, Any ],
            speHandler: bool = False,
        ) -> None:
        """
        Fill a partial attribute with constant value per component. If the list of filling values for an attribute is empty, it will filled with the default value:
            0 for uint data.
            -1 for int data.
            nan for float data. 

        Args:
            multiBlockDataSet (vtkMultiBlockDataSet): The mesh where to fill the attribute.
            dictAttributesValues (dict[str, Any]): The dictionary with the attribute to fill as keys and the list of filling values as items.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.multiBlockDataSet: vtkMultiBlockDataSet = multiBlockDataSet
        self.dictAttributesValues: dict[ str, Any ] = dictAttributesValues

        # Warnings counter.
        self.counter: CountWarningHandler = CountWarningHandler()
        self.counter.setLevel( logging.INFO )

        # Logger.
        if not speHandler:
            self.logger: Logger = getLogger( loggerTitle, True )
        else:
            self.logger: Logger = logging.getLogger( loggerTitle )
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
            # This warning does not count for the number of warning created during the application of the filter.
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization." )


    def applyFilter( self: Self ) -> bool:
        """Create a constant attribute per region in the mesh.

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        # Add the handler to count warnings messages.
        self.logger.addHandler( self.counter )

        for attributeName in self.dictAttributesValues:
            # cell and point arrays
            self._setPieceRegionAttribute( attributeName )
            if self.onPoints is None:
                self.logger.error( f"{ attributeName } is not in the mesh." )
                self.logger.error( f"The attribute { attributeName } has not been filled." )
                self.logger.error( f"The filter { self.logger.name } failed.")
                return False
            
            if self.onBoth:
                self.logger.error( f"Their is two attribute named { attributeName }, one on points and the other on cells. The attribute must be unique." )
                self.logger.error( f"The attribute { attributeName } has not been filled." )
                self.logger.error( f"The filter { self.logger.name } failed.")
                return False
        
            nbComponents: int = getNumberOfComponents( self.multiBlockDataSet, attributeName, self.onPoints )
            if not fillPartialAttributes( self.multiBlockDataSet, attributeName, nbComponents, self.onPoints, self.dictAttributesValues[ attributeName ] ):
                self.logger.error( f"The filter { self.logger.name } failed.")
                return False
            

    def _setPieceRegionAttribute( self: Self, attributeName: str ) -> None:
        """Set the attribute self.onPoints and self.onBoth.

         self.onPoints is True if the region attribute is on points, False if it is on cells, None otherwise.

         self.onBoth is True if a region attribute is on points and on cells, False otherwise.

         Args:
            attributeName (str): The name of the attribute to verify.
        """
        self.onPoints: Union[ bool, None ] = None
        self.onBoth: bool = False
        if isAttributeInObject( self.multiBlockDataSet, attributeName, False ):
            self.onPoints = False
        if isAttributeInObject( self.multiBlockDataSet, attributeName, True ):
            if self.onPoints == False:
                self.onBoth = True
            self.onPoints = True
