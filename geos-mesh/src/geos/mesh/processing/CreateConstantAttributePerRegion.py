# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
import numpy as np
import numpy.typing as npt

from typing import Union, Any
from typing_extensions import Self

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkDataSet,
)

from geos.utils.Logger import getLogger, Logger, logging, CountWarningHandler
from geos.mesh.utils.arrayHelpers import ( getArrayInObject, getComponentNames, getNumberOfComponents, getVtkDataTypeInObject, isAttributeGlobal, isAttributeInObject )
from geos.mesh.utils.arrayModifiers import createAttribute, createConstantAttributeDataSet, createConstantAttributeMultiBlock

__doc__ = """
CreateConstantAttributePerRegion is a vtk filter that allows to create an attribute
with constant values per components for each chosen indexes of a reference/region attribute.
If other region indexes exist values are set to nan for float type, -1 for int type or 0 for uint type.

Input mesh is either vtkMultiBlockDataSet or vtkDataSet and the region attribute must have one component.
The relation index/values is given by a dictionary. Its keys are the indexes and its items are the list of values for each component.
To use a specific handler for the logger, set the variable 'speHandler' to True and use the member function addLoggerHandler.

To use it:

.. code-block:: python

    from geos.mesh.processing.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion

    # filter inputs
    mesh: Union[vtkMultiBlockDataSet, vtkDataSet]
    regionName: str
    dictRegionValues: dict[ Any, Any ]
    newAttributeName: str
    valueNpType: type, optional defaults to numpy.float32
    nbComponents: int, optional default to 1.
    componentNames: tuple[ str, ... ], optional defaults to an empty tuple.
    speHandler: bool, optional defaults to False

    # instantiate the filter
    filter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion( mesh,
                                                                                 regionName,
                                                                                 dictRegionValues,
                                                                                 newAttributeName,
                                                                                 valueNpType,
                                                                                 nbComponents,
                                                                                 componentNames,
                                                                                 speHandler,
                                                                                )

    # Set the specific handler (only if speHandler is True).
    specificHandler: logging.Handler
    filter.addLoggerHandler( specificHandler )

    # Do calculations.
    filter.applyFilter()
"""

loggerTitle: str = "Create constant attribute per region"

class CreateConstantAttributePerRegion:

    def __init__(
            self: Self,
            mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ],
            regionName: str,
            dictRegionValues: dict[ Any, Any ],
            newAttributeName: str,
            valueNpType: type = np.float32,
            nbComponents: int = 1,
            componentNames: tuple[ str, ... ] = (), # noqa: C408
            speHandler: bool = False,
        ) -> None:
        """Create an attribute with constant value per region.
        
        Args:
            mesh (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh where to create the constant attribute per region.
            regionName (str): The name of the attribute with the region indexes.
            dictRegionValues (dict[ Any, Any ]): The dictionary with the region indexes as keys and the list of values as items.
            newAttributeName (str): The name of the new attribute to create.
            nbComponents (int, optional): Number of components for the new attribute.
                Defaults to 1.
            componentNames (tuple[str,...], optional): Name of the components for vectorial attributes. If one component, gives an empty tuple.
                Defaults to an empty tuple.
            valueNpType (type, optional): The numpy scalar type for values.
                Defaults to numpy.float32.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = mesh

        # New attribute settings.
        self.newAttributeName: str = newAttributeName
        self.valueNpType: type = valueNpType
        self.nbComponents: int = nbComponents
        self.componentNames: tuple[ str, ... ] = componentNames

        # Region attribute settings.
        self.regionName: str = regionName
        self.dictRegionValues: dict[ Any, Any ] = dictRegionValues

        self.useDefaultValue: bool = False # Check if the new component have default values (information for the output message).

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

        # Check the validity of the attribute region.
        self._setPieceRegionAttribute()
        if self.onPoints is None:
            self.logger.error( f"{ self.regionName } is not in the mesh." )
            self.logger.error( f"The new attribute { self.newAttributeName } has not been add." )
            self.logger.error( f"The filter { self.logger.name } failed.")
            return False
        
        if self.onBoth:
            self.logger.error( f"Their is two attribute named { self.regionName }, one on points and the other on cells. The region attribute must be unique." )
            self.logger.error( f"The new attribute { self.newAttributeName } has not been add." )
            self.logger.error( f"The filter { self.logger.name } failed.")
            return False

        nbComponentsRegion: int = getNumberOfComponents( self.mesh, self.regionName, self.onPoints )
        if nbComponentsRegion != 1:
            self.logger.error( f"The region attribute { self.regionName } has to many components, one is requires." )
            self.logger.error( f"The new attribute { self.newAttributeName } has not been add." )
            self.logger.error( f"The filter { self.logger.name } failed.")
            return False

        self._setInfoRegion()
        # Check if the number of components and number of values for the region indexes are coherent.
        for index in self.dictRegionValues:
            if len( self.dictRegionValues[ index ] ) != self.nbComponents:
                self.logger.error( f"The number of value given for the region index { index } is not correct. You must set a value for each component, in this case { self.nbComponents }." )
                return False
                
        trueIndexes: list[ Any ] = []
        falseIndexes: list[ Any ] = []
        regionNpArray: npt.NDArray[ Any ]
        npArray: npt.NDArray[ Any ]
        if isinstance( self.mesh, vtkMultiBlockDataSet ):
            # Check if the attribute region is global.
            if not isAttributeGlobal( self.mesh, self.regionName, self.onPoints ):
                self.logger.error( f"The region attribute { self.regionName } has to be global." )
                self.logger.error( f"The new attribute { self.newAttributeName } has not been add." )
                self.logger.error( f"The filter { self.logger.name } failed.")
                return False
                
            trueIndexes, falseIndexes = self._getTrueIndexesInMultiBlock( self.mesh )
            if len( trueIndexes ) == 0:
                if len( self.dictRegionValues ) == 0:
                    self.logger.warning( "No region indexes entered." )
                else:
                    self.logger.warning( f"The region indexes entered are not in the region attribute { self.regionName }." )

                if not createConstantAttributeMultiBlock( self.mesh, self.defaultValue, self.newAttributeName, componentNames=self.componentNames, onPoints=self.onPoints, logger=self.logger ):
                    self.logger.error( f"The filter { self.logger.name } failed.")
                    return False

            else:
                if len( falseIndexes ) > 0:
                    self.logger.warning( f"The region indexes { falseIndexes } are not in the region attribute { self.regionName }." )

                # Parse the mesh to add the attribute on each block.
                nbBlock: int = self.mesh.GetNumberOfBlocks()
                for idBlock in range( nbBlock ):
                    dataSet: vtkDataSet = vtkDataSet.SafeDownCast( self.mesh.GetBlock( idBlock ) )

                    regionNpArray = getArrayInObject( dataSet, self.regionName, self.onPoints )
                    npArray = self._createNpArray( regionNpArray )
                    if not createAttribute( dataSet, npArray, self.newAttributeName, componentNames=self.componentNames, onPoints=self.onPoints, logger=self.logger ):
                        self.logger.error( f"The filter { self.logger.name } failed.")
                        return False
    
        else:
            trueIndexes, falseIndexes = self._getTrueIndexesInDataSet( self.mesh )
            if len( trueIndexes ) == 0:
                if len( self.dictRegionValues ) == 0:
                    self.logger.warning( "No region indexes entered." )
                else:
                    self.logger.warning( f"The region indexes entered are not in the region attribute { self.regionName }." )

                if not createConstantAttributeDataSet( self.mesh, self.defaultValue, self.newAttributeName, componentNames=self.componentNames, onPoints=self.onPoints, logger=self.logger ):
                    self.logger.error( f"The filter { self.logger.name } failed.")
                    return False

            else:
                if len( falseIndexes ) > 0:
                    self.logger.warning( f"The region indexes { falseIndexes } are not in the region attribute { self.regionName }." )

                regionNpArray = getArrayInObject( self.mesh, self.regionName, self.onPoints )
                npArray = self._createNpArray( regionNpArray )
                if not createAttribute( self.mesh, npArray, self.newAttributeName, componentNames=self.componentNames, onPoints=self.onPoints, logger=self.logger ):
                    self.logger.error( f"The filter { self.logger.name } failed.")
                    return False

        # Log the output message.
        self._logOutputMessage( trueIndexes )

        return True


    def _setPieceRegionAttribute( self: Self ) -> None:
        """Set the attribute self.onPoints and self.onBoth.

         self.onPoints is True if the region attribute is on points, False if it is on cells, None otherwise.

         self.onBoth is True if a region attribute is on points and on cells, False otherwise.
        """
        self.onPoints: Union[ bool, None ] = None
        self.onBoth: bool = False
        if isAttributeInObject( self.mesh, self.regionName, False ):
            self.onPoints = False
        if isAttributeInObject( self.mesh, self.regionName, True ):
            if self.onPoints == False:
                self.onBoth = True
            self.onPoints = True
        

    def _setInfoRegion( self: Self ) -> None:
        """Update self.dictRegion and set self.defaultValue.
        Values and default value type are set with the numpy type given by self.valueNpType.
        Default value is set to nan for float data, -1 for int data and 0 for uint data.
        """
        # Get the numpy type from the vtk typecode.
        dictType: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
        regionVtkType: int = getVtkDataTypeInObject( self.mesh, self.regionName, self.onPoints )
        regionNpType: type = dictType[ regionVtkType ]

        # Set the correct type of values and region index.
        dictRegionValuesUpdateType: dict[ Any, Any ] = {}
        for idRegion in self.dictRegionValues:
            dictRegionValuesUpdateType[ regionNpType( idRegion ) ] = [ self.valueNpType( value ) for value in self.dictRegionValues[ idRegion ] ]
        self.dictRegionValues = dictRegionValuesUpdateType

        # Set the list of default value for each component depending of the type.
        self.defaultValue: list [ Any ]
        ## Default value for float types is nan.
        if self.valueNpType in ( np.float32, np.float64 ):
            self.defaultValue = [ self.valueNpType( np.nan ) for _ in range( self.nbComponents ) ]
        ## Default value for int types is -1.
        elif self.valueNpType in ( np.int8, np.int16, np.int32, np.int64 ):
            self.defaultValue = [ self.valueNpType( -1 ) for _ in range( self.nbComponents ) ]
        ## Default value for uint types is 0.
        elif self.valueNpType in ( np.uint8, np.uint16, np.uint32, np.uint64 ):
            self.defaultValue = [ self.valueNpType( 0 ) for _ in range( self.nbComponents ) ]
    

    def _getTrueIndexesInMultiBlock( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> tuple[ list[ Any ], list[ Any ] ]:
        """Check for each region index if it is a true index (the index is value of the attribute of at least one block), or a false index.

        Args:
            dataSet (vtkDataSet): The mesh with the attribute to check.
        
        Returns:
            tuple(list[Any], list[Any]): Tuple with the list of the true indexes and the list of the false indexes.
        """
        trueIndexes: list[ Any ] = []
        falseIndexes: list[ Any ] = []
        nbBlock: int = multiBlockDataSet.GetNumberOfBlocks()
        # Parse all blocks to get the true indexes of each block.
        for idBlock in range( nbBlock ):
            block: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSet.GetBlock( idBlock ) )
            # Get the true and false indexes of the block.
            trueIndexesBlock: list[ Any ] = self._getTrueIndexesInDataSet( block )[ 0 ]
            
            # Keep the new true indexes.
            for index in trueIndexesBlock:
                if index not in trueIndexes:
                    trueIndexes.append( index )
        
        # Get the false indexes.
        for index in self.dictRegion:
            if index not in trueIndexes:
                falseIndexes.append( index ) 

        return ( trueIndexes, falseIndexes )


    def _getTrueIndexesInDataSet( self: Self, dataSet: vtkDataSet ) -> tuple[ list[ Any ], list[ Any ] ]:
        """Check for each region index if it is a true index (the index is value of the attribute), or a false index.

        Args:
            dataSet (vtkDataSet): The mesh with the attribute to check.
        
        Returns:
            tuple(list[Any], list[Any]): The tuple with the list of the true indexes and the list of the false indexes.
        """
        regionNpArray = getArrayInObject( dataSet, self.regionName, self.onPoints )
        trueIndexes: list[ Any ] = []
        falseIndexes: list[ Any ] = []
        for index in self.dictRegionValues:
            if index in regionNpArray:
                trueIndexes.append( index )
            else:
                falseIndexes.append( index )

        return ( trueIndexes, falseIndexes )


    def _createNpArray( self: Self, regionNpArray: npt.NDArray[ Any ] ) -> npt.NDArray[ Any ]:
        """Create an array from the input one.
        If the value of the input array is a key of self.dictRegionValues, the corresponding list of value for each component of the created array is its item.
        If their is other indexes than those given, their list of values are self.defaultValue and self.useDefaultValue is set to True.

        Args:
            regionNpArray (npt.NDArray[Any]): The array with the region indexes.

        Returns:
            npt.NDArray[Any]: The array with values instead of indexes.
        """
        nbElements: int = len( regionNpArray )
        npArray: npt.NDArray[ Any ]
        if self.nbComponents == 1:
            npArray = np.ones( nbElements, self.valueNpType )
        else:
            npArray = np.ones( ( nbElements, self.nbComponents ), self.valueNpType )

        for elem in range( nbElements ):
            value: Any = regionNpArray[ elem ]
            if value in self.dictRegionValues:
                if self.nbComponents == 1:
                    npArray[ elem ] = self.dictRegionValues[ value ][ 0 ]
                else:
                    npArray[ elem ] = self.dictRegionValues[ value ]
            else:
                if self.nbComponents == 1:
                    npArray[ elem ] = self.defaultValue[ 0 ]
                    self.useDefaultValue = True
                else:
                    npArray[ elem ] = self.defaultValue
                    self.useDefaultValue = True

        return npArray
    

    def _logOutputMessage( self: Self, trueIndexes: list[ Any ] ) -> None:
        """Create and log result messages of the filter.

        Args:
            trueIndexes (list[Any]): The list of the true region indexes use to create the attribute.      
        """ 
        # The Filter succeed.
        self.logger.info( f"The filter { self.logger.name } succeed." )

        # Info about the created attribute.
        ## The piece where the attribute is created.
        piece: str = "points" if self.onPoints else "cells"
        self.logger.info( f"The new attribute { self.newAttributeName } is created on { piece }." )

        ## The number of component and they names if multiple.
        componentNamesCreated: tuple[ str, ... ] = getComponentNames( self.mesh, self.newAttributeName, self.onPoints )
        if self.nbComponents > 1:
            messComponent: str = f"The new attribute { self.newAttributeName } has { self.nbComponents } components named { componentNamesCreated }."
            if componentNamesCreated != self.componentNames:
                ### Warn the user because other component names than those given have been used.
                self.logger.warning( messComponent )
            else:
                self.logger.info( messComponent )

        ## The values of the attribute.
        messValue: str = f"The new attribute { self.newAttributeName } is constant"
        if len( trueIndexes ) == 0:
            ### Create the message to have the value of each component.
            messValue = f"{ messValue } with"
            if self.nbComponents > 1:
                for idComponent in range( self.nbComponents ):
                    messValue = f"{ messValue } the value { self.defaultValue[ idComponent ] } for the component { componentNamesCreated[ idComponent ] },"
                messValue = f"{ messValue[:-1] }."
            else:
                messValue = f"{ messValue } the value { self.defaultValue[ 0 ] }."
            ### Warn the user because no region index has been used.
            self.logger.warning( messValue )
 
        else:
            ### Create the message to have for each component the value of the region index.
            messValue = f"{ messValue } per region indexes with:\n"
            for index in trueIndexes:
                messValue = f"{ messValue }\tThe value { self.dictRegionValues[ index ][ 0 ] } for the"
                if self.nbComponents > 1:
                    messValue = f"{ messValue } component { componentNamesCreated[ 0 ] },"
                    for idComponent in range( 1, self.nbComponents - 1 ):
                        messValue = f"{ messValue } the value { self.dictRegionValues[ index ][ idComponent ] } for the component { componentNamesCreated[ idComponent ] },"
                    messValue = f"{ messValue[ : -1 ] } and the value { self.dictRegionValues[ index ][ -1 ] } for the component { componentNamesCreated[ -1 ] } for the index { index }.\n"
                else:
                    messValue =  f"{ messValue } index { index }.\n"

            if self.useDefaultValue:
                messValue =  f"{ messValue }\tThe value { self.defaultValue[ 0 ] } for the"
                if self.nbComponents > 1:
                    messValue = f"{ messValue } component { componentNamesCreated[ 0 ] },"
                    for idComponent in range( 1, self.nbComponents - 1 ):
                        messValue = f"{ messValue } the value { self.defaultValue[ idComponent ] } for the component { componentNamesCreated[ idComponent ] },"
                    messValue = f"{ messValue[ : -1 ] } and the value { self.defaultValue[ -1 ] } for the component { componentNamesCreated[ -1 ] } for the other indexes."
                else:
                    messValue =  f"{ messValue } other indexes."
                ### Warn the user because a default value has been used.
                self.logger.warning( messValue )
            else:
                if self.counter.warningCount > 0:
                    ### Warn the user because other component names than those given have been used.
                    self.logger.warning( messValue )
                else:
                    self.logger.info( messValue )
    