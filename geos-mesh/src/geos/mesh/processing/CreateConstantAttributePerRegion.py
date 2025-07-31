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

from geos.utils.Logger import getLogger, Logger, logging
from geos.mesh.utils.arrayHelpers import isAttributeInObject, getNumberOfComponents, getArrayInObject, isAttributeGlobal
from geos.mesh.utils.arrayModifiers import createAttribute, createConstantAttribute, createConstantAttributeDataSet, createConstantAttributeMultiBlock

__doc__ = """
CreateConstantAttributePerRegion is a vtk filter that allows to create an attribute
with constant values for each chosen indexes of a reference/region attribute.
The region attribute has to have one component and the created attribute has one component.
Region indexes, values and values types are choose by the user, if other region indexes exist
values are set to nan for float type, -1 for int type or 0 for uint type.

Input mesh is either vtkMultiBlockDataSet or vtkDataSet.
The value type is encoded by a int using the vtk typecode to preserve the coherency
(https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/numpy_support.py).
The relation index/value is given by a dictionary. Its keys are the indexes and its items are values.
To use a specific handler for the logger, set the variable 'speHandler' to True and use the
member function addLoggerHandler (useful for paraview for example).

To use it:

.. code-block:: python

    from geos.mesh.processing.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion

    # filter inputs
    mesh: Union[vtkMultiBlockDataSet, vtkDataSet]
    regionName: str
    newAttributeName: str
    dictRegion: dict[Any, Any]
    valueType: int, optional defaults to 10 (float32)
    speHandler: bool, optional defaults to False

    # instantiate the filter
    filter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion( mesh,
                                                                                 regionName,
                                                                                 newAttributeName,
                                                                                 dictRegion,
                                                                                 valueType,
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
            newAttributeName: str,
            dictRegion: dict[ Any, Any ],
            valueType: int = 10,
            speHandler: bool = False,
        ) -> None:
        """Create an attribute with constant value per region.
        
        Args:
            mesh (Union[ vtkDataSet, vtkMultiBlockDataSet ]): The mesh where to create the constant attribute per region.
            regionName (str): The name of the attribute with the region indexes.
            newAttributeName (str): The name of the new attribute to create.
            dictRegion (dict[ Any, Any ]): The dictionary with the region indexes as keys and their values as items.
                For other region indexes, the attribute will be filled with a default value:
                0 for uint data.
                -1 for int  data.
                nan for float data.
            valueType (int, optional): The type of the value using the vtk typecode.
                Defaults to 10 (float32).
            speHandler (bool, optional): True To use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = mesh
        self.regionName: str = regionName
        self.newAttributeName: str = newAttributeName
        self.useDefaultValue: bool = False # Check if the new component have default values (information for the output message) 
        self.setInfoRegion( dictRegion, valueType )

        # Logger
        if not speHandler:
            self.logger: Logger = getLogger( loggerTitle, True )
        else:
            self.logger: Logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )


    def applyFilter( self: Self ) -> bool:
        """Create a constant attribute per region in the mesh

        Returns:
            boolean (bool): True if calculation successfully ended, False otherwise.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )

        # Get the piece of the attribute region if it is in the mesh.
        onPoints: bool
        piece: str = ""
        if isAttributeInObject( self.mesh, self.regionName, False ):
            onPoints = False
            piece = "cells"
        if isAttributeInObject( self.mesh, self.regionName, True ):
            # Check if the attribute is on the two pieces.
            if piece == "cells":
                self.logger.warning( f"The attribute { self.regionName } is on both cells and points, by default the new attribute { self.newAttributeName } will be created on points.")

            onPoints = True
            piece = "points"
        
        # Check if the attribute is on points or on cells.
        if piece not in ( "points", "cells" ):
            self.logger.error( f"{ self.regionName } is not in the mesh." )
            self.logger.error( f"The new attribute { self.newAttributeName } has not been add." )
            self.logger.error( f"The filter { self.logger.name } failed.")
            return False
        
        # Check the validity of the attribute region.
        nbComponents: int = getNumberOfComponents( self.mesh, self.regionName, onPoints )
        if nbComponents != 1:
            self.logger.error( f"The region attribute { self.regionName } has to many components, one is requires." )
            self.logger.error( f"The new attribute { self.newAttributeName } has not been add." )
            self.logger.error( f"The filter { self.logger.name } failed.")
            return False
        
        trueIndexes: list[ Any ] = []
        falseIndexes: list[ Any ] = []
        regionNpArray: npt.NDArray[ Any ]
        npArray: npt.NDArray[ Any ]
        if isinstance( self.mesh, vtkMultiBlockDataSet ):
            if not isAttributeGlobal( self.mesh, self.regionName, onPoints ):
                self.logger.error( f"The region attribute { self.regionName } has to be global." )
                self.logger.error( f"The new attribute { self.newAttributeName } has not been add." )
                self.logger.error( f"The filter { self.logger.name } failed.")
                return False
                
            trueIndexes, falseIndexes = self.getTrueIndexesInMultiBlock( self.mesh, onPoints )
            if len( trueIndexes ) == 0:
                if len( self.dictRegion.keys() ) == 0:
                    self.logger.warning( "No region indexes entered." )
                else:
                    self.logger.warning( f"The region indexes entered are not in the region attribute { self.regionName }." )
                if not createConstantAttributeMultiBlock( self.mesh, [ self.defaultValue ], self.newAttributeName, onPoints=onPoints, logger=self.logger ):
                    self.logger.error( f"The filter { self.logger.name } failed.")
                    return False

            else:
                if len( falseIndexes ) > 0:
                    self.logger.warning( f"The region indexes { falseIndexes } are not in the region attribute { self.regionName }." )

                # Parse the mesh to add the attribute on each block.
                nbBlock: int = self.mesh.GetNumberOfBlocks()
                for idBlock in range( nbBlock ):
                    dataSetInput: vtkDataSet = self.mesh.GetBlock( idBlock )

                    regionNpArray = getArrayInObject( dataSetInput, self.regionName, onPoints )
                    npArray = self.createNpArray( regionNpArray )
                    if not createAttribute( dataSetInput, npArray, self.newAttributeName, onPoints=onPoints, logger=self.logger ):
                        self.logger.error( f"The filter { self.logger.name } failed.")
                        return False
    
        else:
            trueIndexes, falseIndexes = self.getTrueIndexesInDataSet( self.mesh, onPoints )
            if len( trueIndexes ) == 0:
                if len( self.dictRegion.keys() ) == 0:
                    self.logger.warning( "No region indexes entered." )
                else:
                    self.logger.warning( f"The region indexes entered are not in the region attribute { self.regionName }." )
                
                if not createConstantAttributeDataSet( self.mesh, [ self.defaultValue ], self.newAttributeName, onPoints=onPoints, logger=self.logger ):
                    self.logger.error( f"The filter { self.logger.name } failed.")
                    return False
                
            else:
                if len( falseIndexes ) > 0:
                    self.logger.warning( f"The region indexes { falseIndexes } are not in the region attribute { self.regionName }." )

                regionNpArray = getArrayInObject( self.mesh, self.regionName, onPoints )
                npArray = self.createNpArray( regionNpArray )
                if not createAttribute( self.mesh, npArray, self.newAttributeName, onPoints=onPoints, logger=self.logger ):
                    self.logger.error( f"The filter { self.logger.name } failed.")
                    return False
        
        # Set the output message.
        self.logger.info( f"The filter { self.logger.name } succeed." )
        self.logger.info( f"The new attribute { self.newAttributeName } is created on { piece }." )

        mess: str = self.setOutputMessage( trueIndexes )
        self.logger.info( mess )
        
        return True
    

    def setOutputMessage( self: Self, trueIndexes: list[ Any ] ) -> str:
        """Create the result message of the filter.

        Args:
            trueIndexes (list[Any]): The list of the region indexes use to create the attribute.
        
        Returns:
            message (str): The result message of the filter with the value per region.
        
        """
        mess: str = f"The new attribute { self.newAttributeName } is constant"
        regionIndexes: list[ Any ] = self.dictRegion.keys()
        if len( regionIndexes ) == 0 or len( trueIndexes ) == 0:
            mess = f"{ mess } with the value { self.defaultValue }."

        else:
            mess = f"{ mess } per region indexes with:"
            for index in regionIndexes:
                mess =  f"{ mess } { self.dictRegion[ index ] } for index { index },"
            
            if self.useDefaultValue:
                mess = f"{ mess } and { self.defaultValue } for the other indexes."
            else:
                mess = f"{ mess[:-1] }."
        
        return mess


    def setInfoRegion( self: Self, dictRegion: dict[ Any, Any ], valueType: int ) -> None:
        """Set attributes self.valueType, self.dictRegion and self.defaultValue.
        The type of the constant values and the default value are set with value type read with numpy.
        The default value is set to nan for float data, -1 for int data and 0 for uint data.

        Args:
            dictRegion (dict[Any, Any]): The dictionary with the indexes and its constant value.
            valueType (int): The type of the constant value with the VTK typecode.
        """
        # Get the numpy type from the vtk typecode.
        dictType: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
        self.valueType: type = dictType[ valueType ]

        # Set the correct type of the items to ensure the coherency.
        self.dictRegion: dict[ Any, Any ] = dictRegion
        for idRegion in self.dictRegion.keys():
            self.dictRegion[ idRegion ] = self.valueType( self.dictRegion[ idRegion ] )

        # Set the default value depending of the type.
        self.defaultValue: Any
        ## Default value for float types is nan.
        if self.valueType().dtype in ( "float32", "float64" ):
            self.defaultValue = self.valueType( np.nan )
        ## Default value for int types is -1.
        elif self.valueType().dtype in ( "int8", "int16", "int32", "int64" ):
            self.defaultValue = self.valueType( -1 )
        ## Default value for uint types is 0.
        elif self.valueType().dtype in ( "uint8", "uint16", "uint32", "uint64" ):
            self.defaultValue = self.valueType( 0 )
    
        
    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the logger of the filter.
        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.
        
        Args:
            handler (logging.Handler): The handler to add.        
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization." )


    def createNpArray( self: Self, regionNpArray: npt.NDArray[ Any ] ) -> npt.NDArray[ Any ]:
        """Create an array from the input one.
        If the value of the input array is a key of self.dictRegion, the corresponding value of the created array is its item.
        If their is other value, the value self.defaultValue is set and the self.useDefaultValue is set to True.

        Args:
            regionNpArray (npt.NDArray[Any]): The array with the region indexes.

        Returns:
            npt.NDArray[Any]: The array with the value instead of the region index.
        """
        nbElements: int = len( regionNpArray )
        npArray: npt.NDArray[ Any ] = np.ones( nbElements, self.valueType )
        for elem in range( nbElements ):
            idRegion: Any = regionNpArray[ elem ]
            if idRegion in self.dictRegion.keys():
                npArray[ elem ] = self.dictRegion[ idRegion ]
            else:
                npArray[ elem ] = self.defaultValue
                self.useDefaultValue = True

        return npArray


    def getTrueIndexesInDataSet( self: Self, dataSet: vtkDataSet, onPoints: bool ) -> tuple[ list[ Any ], list[ Any ]]:
        regionIndexes: list[ Any ] = self.dictRegion.keys()
        regionNpArray = getArrayInObject( dataSet, self.regionName, onPoints )
        trueIndexes: list[ Any ] = []
        falseIndexes: list[ Any ] = []
        for index in regionIndexes:
            if index in regionNpArray:
                trueIndexes.append( index )
            else:
                falseIndexes.append( index )

        return ( trueIndexes, falseIndexes )
    

    def getTrueIndexesInMultiBlock( self: Self, multiBlockDataSet: vtkMultiBlockDataSet, onPoints: bool ) -> tuple[ list[ Any ], list[ Any ]]:
        trueIndexes: list[ Any ] = []
        falseIndexes: list[ Any ] = []
        nbBlock: int = multiBlockDataSet.GetNumberOfBlocks()
        for idBlock in range( nbBlock ):
            dataSetInput: vtkDataSet = multiBlockDataSet.GetBlock( idBlock )
            trueIndexes.extend( self.getTrueIndexesInDataSet( dataSetInput, onPoints )[ 0 ] ) 
            falseIndexes.extend( self.getTrueIndexesInDataSet( dataSetInput, onPoints )[ 1 ] )
            
        return ( list( set( trueIndexes ) ), list( set( falseIndexes ) ) )
    