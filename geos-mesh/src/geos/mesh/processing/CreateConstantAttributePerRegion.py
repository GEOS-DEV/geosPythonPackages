# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
import numpy as np
import numpy.typing as npt
from typing import Union, Any
from typing_extensions import Self

import vtkmodules.util.numpy_support as vnp

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
)
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
    vtkDataSet,
)
from geos.utils.Logger import Logger, getLogger

from geos.mesh.utils.arrayHelpers import isAttributeInObject
from geos.mesh.utils.arrayModifiers import createAttribute

__doc__ = """
TO DO

"""



class CreateConstantAttributePerRegion( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Create an attribute with constant value per region."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkMultiBlockDataSet, vtkDataSet" )

        self._SetRegionName()
        self._SetAttributeName()
        self._SetInfoRegion()

        # logger
        self.m_logger: Logger = getLogger( "Create Constant Attribute Per Region Filter" )

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

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
            inInfoVec: list[ vtkInformationVector ],  # noqa: F841
            outInfoVec: vtkInformationVector,  # noqa: F841
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        self.m_logger.info( f"Apply filter {__name__}" )
        try:
            input0: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet ] = ( self.GetInputData( inInfoVec, 0, 0 ) )
            output: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet ] = ( self.GetOutputData( outInfoVec, 0 ) )

            assert input0 is not None, "Input Surface is null."
            assert output is not None, "Output pipeline is null."

            output.ShallowCopy( input0 )

            assert ( len( self.regionName ) > 0 ), "Region attribute is undefined, please select an attribute."

            onPoints: bool
            if isAttributeInObject( input0, self.regionName, False ):
                onPoints = False
            elif isAttributeInObject( input0, self.regionName, True ):
                onPoints = True
            else:
                mess = f"{self.regionName} is not in the mesh."
                self.m_logger.info( mess )
                return 0
            
            regionNpArray: npt.NDArray[ Any ]
            npArray: npt.NDArray[ Any ]
            if isinstance( output, vtkMultiBlockDataSet ):
                nbBlock: int = output.GetNumberOfBlocks()
                for idBlock in range( nbBlock ):
                    dataSetOutput: vtkDataSet = output.GetBlock( idBlock )
                    dataSetInput0: vtkDataSet = input0.GetBlock( idBlock )
                    if onPoints:
                        regionNpArray = vnp.vtk_to_numpy( dataSetInput0.GetPointData().GetArray( self.regionName ) )
                    else:
                        regionNpArray = vnp.vtk_to_numpy( dataSetInput0.GetCellData().GetArray( self.regionName ) )

                    npArray = self.createNpArray( regionNpArray )
                    createAttribute( dataSetOutput, npArray, self.attributeName, onPoints=onPoints )
    
            else:
                if onPoints:
                    regionNpArray = vnp.vtk_to_numpy( input0.GetPointData().GetArray( self.regionName ) )
                else:
                    regionNpArray = vnp.vtk_to_numpy( input0.GetCellData().GetArray( self.regionName ) )

                npArray = self.createNpArray( regionNpArray )
                createAttribute( output, npArray, self.attributeName, onPoints=onPoints )

            mess: str = ( f"The new attribute {self.attributeName} was successfully added." )
            self.Modified()
            self.m_logger.info( mess )
        except AssertionError as e:
            mess1: str = "The new attribute was not added due to:"
            self.m_logger.error( mess1 )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess0: str = "The new attribute was not added due to:"
            self.m_logger.critical( mess0 )
            self.m_logger.critical( e, exc_info=True )
            return 0

        return 1


    def _SetRegionName( self: Self, regionName: str = "" ) -> None:
        self.regionName: str = regionName
    

    def _SetAttributeName( self: Self, attributeName: str = "Attribute" ) -> None:
        self.attributeName: str = attributeName


    def _SetInfoRegion( self: Self, dictRegion: dict[ Any, Any ] = {}, valueType: int = 10, defaultValue: Any = np.nan ) -> None:
        dictType: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
        self.valueType: type = dictType[ valueType ]

        self.dictRegion: dict[ Any, Any ] = dictRegion
        for idRegion in self.dictRegion.keys():
            self.dictRegion[ idRegion ] = self.valueType( self.dictRegion[ idRegion ] )

        if np.isnan( defaultValue ):
            if valueType not in [ 10, 11 ]:
                defaultValue = -1
            
        self.defaultValue = self.valueType(defaultValue)


    def createNpArray( self: Self, regionNpArray: npt.NDArray[ Any ] ) -> npt.NDArray[ Any ]:
        """Create numpy arrays from input data.

        Args:
            regionNpArray (npt.NDArray[ Any ]): Region attribute

        Returns:
            npt.NDArray[np.float64]: numpy array of the new attribute.
        """
        nbElements: int = len ( regionNpArray )
        npArray: npt.NDArray[ Any ] = np.ones( nbElements, self.valueType )
        for elem in range( nbElements ):
            idRegion: Any = regionNpArray[elem]
            if idRegion in self.dictRegion.keys():
                npArray[elem] = self.dictRegion[idRegion]
            else:
                npArray[elem] = self.defaultValue

        return npArray
