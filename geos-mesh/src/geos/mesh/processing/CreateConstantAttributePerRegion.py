# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
import numpy as np
import numpy.typing as npt
import logging
from typing import Union, Any
from typing_extensions import Self

import vtkmodules.util.numpy_support as vnp
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkDataSet,
)

from geos.utils.Logger import getLogger, Logger
from geos.mesh.utils.arrayHelpers import isAttributeInObject, getNumberOfComponents, getArrayInObject, isAttributeGlobal
from geos.mesh.utils.arrayModifiers import createAttribute

__doc__ = """
CreateConstantAttributePerRegion is a vtk filter that allows to create an attribute
with constant values for each chosen indexes of a reference/region attribute.
The region attribute has to have one component and the created attribute has one component.
Regions indexes, values and values types are choose by the user, for the other region index
values are set to nan or -1 if int type.

Input and output meshes are either vtkMultiBlockDataSet or vtkDataSet.
The value type is encoded by a int using the vtk typecode to preserve the coherency
(https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/numpy_support.py).
The relation index/value is given by a dictionary. Its keys are the indexes and its items are values.
If you have a specific handler for your logger you can set the variable speHandler to True and use the
member function addLoggerHandler (useful for paraview for example).

To use it:

.. code-block:: python

    from geos.mesh.processing.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion

    # filter inputs
    input_mesh: Union[vtkMultiBlockDataSet, vtkDataSet]
    regionName: str
    newAttributeName: str
    dictRegion: dict[Any, Any]
    valueType: int, optional defaults to 10 (float32)
    speHandler: bool, optional defaults to False

    # instantiate the filter
    filter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion( regionName,
                                                                                 newAttributeName,
                                                                                 dictRegion,
                                                                                 valueType,
                                                                                 speHandler,
                                                                                )
    # Set your specific handler (only if speHandler is True)
    filter.addLoggerHandler( YourHandler )
    # Set the mesh
    filter.SetInputDataObject( input_mesh )
    # Do calculations
    filter.Update()

    # get output object
    output: Union[vtkMultiBlockDataSet, vtkDataSet] = filter.GetOutputDataObject( 0 )

"""

loggerTitle: str = "Create constant attribute per region"

class CreateConstantAttributePerRegion( VTKPythonAlgorithmBase ):

    def __init__(
            self: Self,
            regionName: str,
            newAttributeName: str,
            dictRegion: dict[ Any, Any ],
            valueType: int = 10,
            speHandler: bool = False,
        ) -> None:
        """Create an attribute with constant value per region.

        If a region is not given, the attribute will be set with a default value:
            0 for uint data.
            -1 for int  data.
            np.nan for float data.

        An intern logger is used in this filter. If you want to personalize it, you can user a handler of yours that will
        be add at the place of the intern handler. The level by fault of the logger is INFO. 
        
        Args:
            regionName (str): The name of the attribute with the region indexes.
            newAttributeName (str): The name of the new attribute to create.
            dictRegion (dict[ Any, Any ]): The dictionary with the region indexes as keys and their values as items.
            valueType (int, optional): The type of the value using the vtk typecode.
                Defaults to 10.
            speHandler (bool, optional): True if you want to use a specific handler of yours, False otherwise.
                Defaults to False.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType="vtkDataObject", outputType="vtkDataObject" )

        self.regionName: str = regionName
        self.newAttributeName: str = newAttributeName
        self.setInfoRegion( dictRegion, valueType )

        # Logger
        if not speHandler:
            self.m_logger: Logger = getLogger( loggerTitle, True )
        else:
            self.m_logger: Logger = logging.getLogger( loggerTitle )
            self.m_logger.setLevel( logging.INFO )

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        self.m_logger.info( f"Apply filter { self.m_logger.name }." )
        mess: str
        try:
            inputMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
            outData: Union[ vtkDataSet, vtkMultiBlockDataSet ] = self.GetOutputData( outInfoVec, 0 )
            assert inputMesh is not None, "Input mesh is null."
            assert outData is not None, "Output pipeline is null."

            outData.ShallowCopy( inputMesh )

            onPoints: bool
            piece: str = ""
            if isAttributeInObject( inputMesh, self.regionName, False ):
                onPoints = False
                piece = "cells"
            if isAttributeInObject( inputMesh, self.regionName, True ):
                if piece == "cells":
                    self.m_logger.warning( f"The attribute { self.regionName } is on both cells and points, by default the new attribute { self.newAttributeName } will be created on points.")

                onPoints = True
                piece = "points"

            assert piece in ( "points", "cells" ), f"{ self.regionName } is not in the mesh."
            
            nbComponents: int = getNumberOfComponents( inputMesh, self.regionName, onPoints )
            assert nbComponents == 1, "The region attribute has to have only one component"

            regionNpArray: npt.NDArray[ Any ]
            npArray: npt.NDArray[ Any ]
            if isinstance( inputMesh, vtkMultiBlockDataSet ):
                assert isAttributeGlobal( inputMesh, self.regionName, onPoints ), "Region attribute has to be global" 
                nbBlock: int = outData.GetNumberOfBlocks()
                for idBlock in range( nbBlock ):
                    dataSetOutput: vtkDataSet = outData.GetBlock( idBlock )
                    dataSetInput0: vtkDataSet = inputMesh.GetBlock( idBlock )
                    regionNpArray = getArrayInObject( dataSetInput0, self.regionName, onPoints )

                    npArray = self.createNpArray( regionNpArray )
                    assert createAttribute( dataSetOutput, npArray, self.newAttributeName, onPoints=onPoints, logger=self.m_logger ), "The function createAttribute failed."
    
            else:
                regionNpArray = getArrayInObject( inputMesh, self.regionName, onPoints )

                npArray = self.createNpArray( regionNpArray )
                assert createAttribute( outData, npArray, self.newAttributeName, onPoints=onPoints, logger=self.m_logger ), "The function createAttribute failed."
            
            regionIndexes: list[ Any ] = self.dictRegion.keys()
            indexValuesMess: str = ""
            for index in regionIndexes:
                value: Any = self.dictRegion[ index ]
                indexValuesMess =  indexValuesMess + "index " + str( index ) + ": " + str( value ) + ", "
            
            if indexValuesMess == "":
                indexValuesMess = f"No index or no value enter, the new attribute is constant with the value {self.defaultValue}."
                self.m_logger.warning( indexValuesMess )
            
            else:            
                indexValuesMess = indexValuesMess + "other indexes: " + str( self.defaultValue ) + "."
    
            mess = f"The attribute { self.regionName } allows to create on { piece } the new attribute { self.newAttributeName } with the following constant values per region indexes: { indexValuesMess }"
            self.Modified()
            self.m_logger.info( mess )
        except AssertionError as e:
            mess = f"The filter { self.m_logger.name } failed due to:"
            self.m_logger.error( mess )
            self.m_logger.error( e, exc_info=True)
            return 1
        except Exception as e:
            mess = f"The filter { self.m_logger.name } failed due to:"
            self.m_logger.critical( mess )
            self.m_logger.critical( e, exc_info=True)
            return 1

        return 1


    def setInfoRegion( self: Self, dictRegion: dict[ Any, Any ], valueType: int ) -> None:
        """Set attributes self.valueType, self.dictRegion and self.defaultValue.
        The type of the constant values and the default value are set with value type read with numpy.
        The default value is set to nan if the type is float or double, -1 otherwise.

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
    
        
    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the logger of the filter.
        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.
        
        Args:
            handler (logging.Handler): The handler to add.        
        """
        if not self.m_logger.hasHandlers():
            self.m_logger.addHandler( handler )
        else:
            self.m_logger.warning( "The logger already has a handler, to use yours set the argument 'speHandler' to True during the filter initialization" )


    def createNpArray( self: Self, regionNpArray: npt.NDArray[ Any ] ) -> npt.NDArray[ Any ]:
        """Create numpy arrays from input data.

        Args:
            regionNpArray (npt.NDArray[Any]): Region attribute.
            regionVTKArrayType (int): The type of the vtk array.

        Returns:
            npt.NDArray[np.float64]: Numpy array of the new attribute.
        """
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
        
        nbElements: int = len( regionNpArray )
        npArray: npt.NDArray[ Any ] = np.ones( nbElements, self.valueType )
        for elem in range( nbElements ):
            idRegion: Any = regionNpArray[ elem ]
            if idRegion in self.dictRegion.keys():
                npArray[ elem ] = self.dictRegion[ idRegion ]
            else:
                npArray[ elem ] = self.defaultValue

        return npArray
