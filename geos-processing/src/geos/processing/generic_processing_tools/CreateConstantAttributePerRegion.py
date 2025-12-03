# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
import numpy as np
import logging

import numpy.typing as npt
from typing import Union, Any
from typing_extensions import Self

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet

from geos.utils.Logger import ( getLogger, Logger, CountWarningHandler )
from geos.mesh.utils.arrayHelpers import ( getArrayInObject, getComponentNames, getNumberOfComponents,
                                           getVtkDataTypeInObject, isAttributeGlobal, getAttributePieceInfo,
                                           checkValidValuesInDataSet, checkValidValuesInMultiBlock )
from geos.mesh.utils.arrayModifiers import ( createAttribute, createConstantAttributeDataSet,
                                             createConstantAttributeMultiBlock )
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten

__doc__ = """
CreateConstantAttributePerRegion is a vtk filter that allows to create an attribute
with constant values per components for each chosen indexes of a reference/region attribute.
If other region indexes exist values are set to nan for float type, -1 for int type or 0 for uint type.

Input mesh is either vtkMultiBlockDataSet or vtkDataSet and the region attribute must have one component.
The relation index/values is given by a dictionary.
Its keys are the indexes and its items are the list of values for each component.
To use a handler of yours, set the variable 'speHandler' to True and add it using the member function addLoggerHandler.

By default, the value type is set to float32, their is one component and no name and the logger use an intern handler.

To use it:

.. code-block:: python

    from geos.processing.generic_processing_tools.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion

    # Filter inputs.
    mesh: Union[vtkMultiBlockDataSet, vtkDataSet]
    regionName: str
    dictRegionValues: dict[ Any, Any ]
    newAttributeName: str

    # Optional inputs.
    valueNpType: type
    nbComponents: int
    componentNames: tuple[ str, ... ]
    speHandler: bool

    # Instantiate the filter
    createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
        mesh,
        regionName,
        dictRegionValues,
        newAttributeName,
        valueNpType,
        nbComponents,
        componentNames,
        speHandler,
    )

    # Set your handler (only if speHandler is True).
    yourHandler: logging.Handler
    createConstantAttributePerRegionFilter.addLoggerHandler( yourHandler )

    # Do calculations.
    createConstantAttributePerRegionFilter.applyFilter()
"""

loggerTitle: str = "Create Constant Attribute Per Region"


class CreateConstantAttributePerRegion:

    def __init__(
            self: Self,
            mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ],
            regionName: str,
            dictRegionValues: dict[ Any, Any ],
            newAttributeName: str,
            valueNpType: type = np.float32,
            nbComponents: int = 1,
            componentNames: tuple[ str, ...] = (),  # noqa: C408
            speHandler: bool = False,
    ) -> None:
        """Create an attribute with constant value per region.

        Args:
            mesh (Union[ vtkDataSet, vtkMultiBlockDataSet ]): Mesh where to create the constant attribute per region.
            regionName (str): Name of the attribute with the region indexes.
            dictRegionValues (dict[ Any, Any ]): Dictionary with the region ids as keys and the list of values as items.
            newAttributeName (str): Name of the new attribute to create.
            valueNpType (type, optional): Numpy scalar type for values.
                Defaults to numpy.float32.
            nbComponents (int, optional): Number of components for the new attribute.
                Defaults to 1.
            componentNames (tuple[str,...], optional): Name of the components for vectorial attributes.
                If one component, gives an empty tuple.
                Defaults to an empty tuple.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = mesh

        # New attribute settings.
        self.newAttributeName: str = newAttributeName
        self.valueNpType: type = valueNpType
        self.nbComponents: int = nbComponents
        self.componentNames: tuple[ str, ...] = componentNames

        # Region attribute settings.
        self.regionName: str = regionName
        self.dictRegionValues: dict[ Any, Any ] = dictRegionValues
        self.onPoints: Union[ None, bool ]
        self.onBoth: bool
        self.onPoints, self.onBoth = getAttributePieceInfo( self.mesh, self.regionName )

        # Check if the new component have default values (information for the output message).
        self.useDefaultValue: bool = False

        # Warnings counter.
        self.counter: CountWarningHandler = CountWarningHandler()
        self.counter.setLevel( logging.INFO )

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if len( self.logger.handlers ) == 0:
            self.logger.addHandler( handler )
        else:
            # This warning does not count for the number of warning created during the application of the filter.
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler' to True"
                                 " during the filter initialization." )

    def applyFilter( self: Self ) -> bool:
        """Create a constant attribute per region in the mesh.

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        # Add the handler to count warnings messages.
        self.logger.addHandler( self.counter )

        try:
            # Check the validity of the attribute region.
            if self.onPoints is None:
                raise AttributeError( f"{ self.regionName } is not in the mesh." )

            if self.onBoth:
                raise ValueError(
                    f"There are two attributes named { self.regionName }, one on points and the other on cells. The region attribute must be unique."
                )

            nbComponentsRegion: int = getNumberOfComponents( self.mesh, self.regionName, self.onPoints )
            if nbComponentsRegion != 1:
                raise ValueError( f"The region attribute { self.regionName } has to many components, one is requires." )

            self._setInfoRegion()
            # Check if the number of components and number of values for the region indexes are coherent.
            for index in self.dictRegionValues:
                if len( self.dictRegionValues[ index ] ) != self.nbComponents:
                    raise ValueError(
                        f"The number of value given for the region index { index } is not correct. You must set a value for each component, in this case { self.nbComponents }."
                    )

            listIndexes: list[ Any ] = list( self.dictRegionValues.keys() )
            validIndexes: list[ Any ] = []
            invalidIndexes: list[ Any ] = []
            regionArray: npt.NDArray[ Any ]
            newArray: npt.NDArray[ Any ]
            if isinstance( self.mesh, vtkMultiBlockDataSet ):
                # Check if the attribute region is global.
                if not isAttributeGlobal( self.mesh, self.regionName, self.onPoints ):
                    raise AttributeError( f"The region attribute { self.regionName } has to be global." )

                validIndexes, invalidIndexes = checkValidValuesInMultiBlock( self.mesh, self.regionName, listIndexes,
                                                                             self.onPoints )
                if len( validIndexes ) == 0:
                    if len( self.dictRegionValues ) == 0:
                        self.logger.warning( "No region indexes entered." )
                    else:
                        self.logger.warning(
                            f"The region indexes entered are not in the region attribute { self.regionName }." )

                    createConstantAttributeMultiBlock( self.mesh,
                                                       self.defaultValue,
                                                       self.newAttributeName,
                                                       componentNames=self.componentNames,
                                                       onPoints=self.onPoints,
                                                       logger=self.logger )

                else:
                    if len( invalidIndexes ) > 0:
                        self.logger.warning(
                            f"The region indexes { invalidIndexes } are not in the region attribute { self.regionName }."
                        )

                    # Parse the mesh to add the attribute on each dataset.
                    listFlatIdDataSet: list[ int ] = getBlockElementIndexesFlatten( self.mesh )
                    for flatIdDataSet in listFlatIdDataSet:
                        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( self.mesh.GetDataSet( flatIdDataSet ) )

                        regionArray = getArrayInObject( dataSet, self.regionName, self.onPoints )
                        newArray = self._createArrayFromRegionArrayWithValueMap( regionArray )
                        createAttribute( dataSet,
                                         newArray,
                                         self.newAttributeName,
                                         componentNames=self.componentNames,
                                         onPoints=self.onPoints,
                                         logger=self.logger )

            else:
                validIndexes, invalidIndexes = checkValidValuesInDataSet( self.mesh, self.regionName, listIndexes,
                                                                          self.onPoints )
                if len( validIndexes ) == 0:
                    if len( self.dictRegionValues ) == 0:
                        self.logger.warning( "No region indexes entered." )
                    else:
                        self.logger.warning(
                            f"The region indexes entered are not in the region attribute { self.regionName }." )

                    createConstantAttributeDataSet( self.mesh,
                                                    self.defaultValue,
                                                    self.newAttributeName,
                                                    componentNames=self.componentNames,
                                                    onPoints=self.onPoints,
                                                    logger=self.logger )

                else:
                    if len( invalidIndexes ) > 0:
                        self.logger.warning(
                            f"The region indexes { invalidIndexes } are not in the region attribute { self.regionName }."
                        )

                    regionArray = getArrayInObject( self.mesh, self.regionName, self.onPoints )
                    newArray = self._createArrayFromRegionArrayWithValueMap( regionArray )
                    createAttribute( self.mesh,
                                     newArray,
                                     self.newAttributeName,
                                     componentNames=self.componentNames,
                                     onPoints=self.onPoints,
                                     logger=self.logger )

            # Log the output message.
            self._logOutputMessage( validIndexes )
        except ( ValueError, AttributeError ) as e:
            self.logger.error( f"The filter { self.logger.name } failed.\n{ e }" )
            return False
        except Exception as e:
            mess: str = f"The filter { self.logger.name } failed.\n{ e }"
            self.logger.critical( mess, exc_info=True )
            return False

        return True

    def _setInfoRegion( self: Self ) -> None:
        """Update self.dictRegionValues and set self.defaultValue.

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
            dictRegionValuesUpdateType[ regionNpType( idRegion ) ] = [
                self.valueNpType( value ) for value in self.dictRegionValues[ idRegion ]
            ]
        self.dictRegionValues = dictRegionValuesUpdateType

        # Set the list of default value for each component depending of the type.
        self.defaultValue: list[ Any ]
        # Default value for float types is nan.
        if self.valueNpType in ( np.float32, np.float64 ):
            self.defaultValue = [ self.valueNpType( np.nan ) for _ in range( self.nbComponents ) ]
        # Default value for int types is -1.
        elif self.valueNpType in ( np.int8, np.int16, np.int32, np.int64 ):
            self.defaultValue = [ self.valueNpType( -1 ) for _ in range( self.nbComponents ) ]
        # Default value for uint types is 0.
        elif self.valueNpType in ( np.uint8, np.uint16, np.uint32, np.uint64 ):
            self.defaultValue = [ self.valueNpType( 0 ) for _ in range( self.nbComponents ) ]

    def _createArrayFromRegionArrayWithValueMap( self: Self, regionArray: npt.NDArray[ Any ] ) -> npt.NDArray[ Any ]:
        """Create the array from the regionArray and the valueMap (self.valueMap).

        Giving the relation between the values of the regionArray and the new one.

        For each element (idElement) of the regionArray:
            - If the value (regionArray[idElement]) is mapped (a keys of the valueMap),
                 valueArray[idElement] = self.valueMap[value].
            - If not, valueArray[idElement] = self.defaultValue.

        Args:
            regionArray (npt.NDArray[Any]): The array with the region indexes.

        Returns:
            npt.NDArray[Any]: The new array with values mapped from the regionArray.
        """
        nbElements: int = len( regionArray )
        newArray: npt.NDArray[ Any ]
        if self.nbComponents == 1:
            newArray = np.ones( nbElements, self.valueNpType )
        else:
            newArray = np.ones( ( nbElements, self.nbComponents ), self.valueNpType )

        for idElement in range( nbElements ):
            value: Any = regionArray[ idElement ]
            if value in self.dictRegionValues:
                if self.nbComponents == 1:
                    newArray[ idElement ] = self.dictRegionValues[ value ][ 0 ]
                else:
                    newArray[ idElement ] = self.dictRegionValues[ value ]
            else:
                if self.nbComponents == 1:
                    newArray[ idElement ] = self.defaultValue[ 0 ]
                    self.useDefaultValue = True
                else:
                    newArray[ idElement ] = self.defaultValue
                    self.useDefaultValue = True

        return newArray

    def _logOutputMessage( self: Self, trueIndexes: list[ Any ] ) -> None:
        """Create and log result messages of the filter.

        Args:
            trueIndexes (list[Any]): The list of the true region indexes use to create the attribute.
        """
        # The Filter succeed.
        self.logger.info( f"The filter { self.logger.name } succeeded." )

        # Info about the created attribute.
        # The piece where the attribute is created.
        piece: str = "points" if self.onPoints else "cells"
        self.logger.info( f"The new attribute { self.newAttributeName } is created on { piece }." )

        # The number of component and they names if multiple.
        componentNamesCreated: tuple[ str, ...] = getComponentNames( self.mesh, self.newAttributeName, self.onPoints )
        if self.nbComponents > 1:
            messComponent: str = ( f"The new attribute { self.newAttributeName } has { self.nbComponents } components"
                                   f" named { componentNamesCreated }." )
            if componentNamesCreated != self.componentNames:
                # Warn the user because other component names than those given have been used.
                self.logger.warning( messComponent )
            else:
                self.logger.info( messComponent )

        # The values of the attribute.
        messValue: str = f"The new attribute { self.newAttributeName } is constant"
        if len( trueIndexes ) == 0:
            # Create the message to have the value of each component.
            messValue = f"{ messValue } with"
            if self.nbComponents > 1:
                for idComponent in range( self.nbComponents ):
                    messValue = ( f"{ messValue } the value { self.defaultValue[ idComponent ] } for the component"
                                  f" { componentNamesCreated[ idComponent ] }," )
                messValue = f"{ messValue[:-1] }."
            else:
                messValue = f"{ messValue } the value { self.defaultValue[ 0 ] }."
            # Warn the user because no region index has been used.
            self.logger.warning( messValue )

        else:
            # Create the message to have for each component the value of the region index.
            messValue = f"{ messValue } per region indexes with:\n"
            for index in trueIndexes:
                messValue = f"{ messValue }\tThe value { self.dictRegionValues[ index ][ 0 ] } for the"
                if self.nbComponents > 1:
                    messValue = f"{ messValue } component { componentNamesCreated[ 0 ] },"
                    for idComponent in range( 1, self.nbComponents - 1 ):
                        messValue = ( f"{ messValue } the value { self.dictRegionValues[ index ][ idComponent ] }"
                                      f" for the component { componentNamesCreated[ idComponent ] }," )
                    messValue = ( f"{ messValue[ : -1 ] } and the value { self.dictRegionValues[ index ][ -1 ] }"
                                  f" for the component { componentNamesCreated[ -1 ] } for the index { index }.\n" )
                else:
                    messValue = f"{ messValue } index { index }.\n"

            if self.useDefaultValue:
                messValue = f"{ messValue }\tThe value { self.defaultValue[ 0 ] } for the"
                if self.nbComponents > 1:
                    messValue = f"{ messValue } component { componentNamesCreated[ 0 ] },"
                    for idComponent in range( 1, self.nbComponents - 1 ):
                        messValue = ( f"{ messValue } the value { self.defaultValue[ idComponent ] }"
                                      f" for the component { componentNamesCreated[ idComponent ] }," )
                    messValue = ( f"{ messValue[ : -1 ] } and the value { self.defaultValue[ -1 ] }"
                                  f" for the component { componentNamesCreated[ -1 ] } for the other indexes." )
                else:
                    messValue = f"{ messValue } other indexes."
                # Warn the user because a default value has been used.
                self.logger.warning( messValue )
            else:
                if self.counter.warningCount > 0:
                    # Warn the user because other component names than those given have been used.
                    self.logger.warning( messValue )
                else:
                    self.logger.info( messValue )
