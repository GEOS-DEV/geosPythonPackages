# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville, Martin Lemay

from typing_extensions import Self
from typing import Union
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase

from geos.utils.Logger import Logger, getLogger
from geos.mesh.utils.arrayModifiers import fillPartialAttributes
from geos.mesh.utils.arrayHelpers import (
    getNumberOfComponents,
    isAttributeInObject,
)

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
)

import numpy as np

__doc__="""
Fill partial arrays of input mesh with values (defaults to nan).
Several attributes can be fill in the same time but with the same value.

Input and output mesh are vtkMultiBlockDataSet.

To use it:

.. code-block:: python

    from geos.mesh.processing.FillPartialArrays import FillPartialArrays

    # filter inputs
    input_mesh: vtkMultiBlockDataSet
    input_attributesNameList: list[str]
    input_valueToFill: float, optional defaults to nan

    # Instanciate the filter
    filter: FillPartialArrays = FillPartialArrays()
    # Set the list of the partial atributes to fill
    filter._SetAttributesNameList( input_attribute )
    # Set the value to fill in the partial attributes if not nan
    filter._SetValueToFill( input_valueToFill )
    # Set the mesh
    filter.SetInputDataObject( input_mesh )
    # Do calculations
    filter.Update()

    # get output object
    output: vtkMultiBlockDataSet = filter.GetOutputDataObject( 0 ) )
"""

class FillPartialArrays( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType="vtkMultiBlockDataSet", outputType="vtkMultiBlockDataSet" )

        # Initialisation of an empty list of the attribute's name
        self._SetAttributesNameList()

        # Initialisation of the value (nan) to fill in the partial attributes
        self._SetValueToFill()

        # Logger
        self.m_logger: Logger = getLogger( "Fill Partial Attributes" )

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

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
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        self.m_logger.info( f"Apply filter {__name__}" )
        try:
            inputMesh: vtkMultiBlockDataSet = self.GetInputData( inInfoVec, 0, 0 )
            outData: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )

            assert inputMesh is not None, "Input mesh is null."
            assert outData is not None, "Output pipeline is null."

            outData.ShallowCopy( inputMesh )
            for attributeName in self._attributesNameList:
                # cell and point arrays
                for onPoints in (False, True):
                    if isAttributeInObject(outData, attributeName, onPoints):
                        nbComponents = getNumberOfComponents( outData, attributeName, onPoints )
                        fillPartialAttributes( outData, attributeName, nbComponents, onPoints, self._valueToFill )
            outData.Modified()

            mess: str = "Fill Partial arrays were successfully completed. " + str(self._attributesNameList) + " filled with value " + str(self._valueToFill)
            self.m_logger.info( mess )
        except AssertionError as e:
            mess1: str = "Partial arrays filling failed due to:"
            self.m_logger.error( mess1 )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess0: str = "Partial arrays filling failed due to:"
            self.m_logger.critical( mess0 )
            self.m_logger.critical( e, exc_info=True )
            return 0

        return 1

    def _SetAttributesNameList( self: Self, attributesNameList: Union[ list[ str ], tuple ]  = () ) -> None:
        """Set the list of the partial attributes to fill.

        Args:
            attributesNameList (Union[list[str], tuple], optional): list of all the attributes name.
                Defaults to a empty list
        """
        self._attributesNameList: Union[ list[ str ], tuple ] = attributesNameList

    def _SetValueToFill( self: Self, valueToFill: float = np.nan ) -> None:
        """Set the value to fill in the partial attribute.

        Args:
            valueToFill (float, optional): value to fill in the partial attribute.
                Defaults to nan.
        """
        self._valueToFill: float = valueToFill

