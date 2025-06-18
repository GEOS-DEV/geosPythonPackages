# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self

import numpy as np

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
)

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.processing.FillPartialArrays import FillPartialArrays

__doc__ = """
Fill partial arrays of input mesh.

Input and output are vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVFillPartialArrays.
* Select the input mesh.
* Select the partial arrays to fill.
* Apply.

"""


@smproxy.filter( name="PVFillPartialArrays", label="Fill Partial Arrays" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
class PVFillPartialArrays( VTKPythonAlgorithmBase ):

    def __init__( self: Self,) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__(nInputPorts=1, nOutputPorts=1, inputType="vtkMultiBlockDataSet", outputType="vtkMultiBlockDataSet")

        self._clearSelectedAttributeMulti: bool = True
        self._selectedAttributeMulti: list[ str ] = []

        self._doubleSingle: float = np.nan

    @smproperty.stringvector(
        name="SelectMultipleAttribute",
        label="Select Multiple Attribute",
        repeat_command=1,
        number_of_elements_per_command="1",
        element_types="2",
        default_values="N/A",
        panel_visibility="default",
    )
    @smdomain.xml( """
                <ArrayListDomain
                    name="array_list"
                    attribute_type="Vectors"
                    input_domain_name="cells_vector_array">
                    <RequiredProperties>
                        <Property name="Input" function="Input"/>
                    </RequiredProperties>
                </ArrayListDomain>
                <Documentation>
                    Select a unique attribute from all the scalars cell attributes from input object.
                    Input object is defined by its name Input that must corresponds to the name in @smproperty.input
                    Attribute support is defined by input_domain_name: inputs_array (all arrays) or user defined
                    function from <InputArrayDomain/> tag from filter @smdomain.xml.
                    Attribute type is defined by keyword `attribute_type`: Scalars or Vectors
                </Documentation>
                <Hints>
                    <NoDefault />
                </Hints>
                  """ )
    def a02SelectMultipleAttribute( self: Self, name: str ) -> None:
        """Set selected attribute name.

        Args:
            name (str): Input value
        """
        if self._clearSelectedAttributeMulti:
            self._selectedAttributeMulti.clear()
            self._clearSelectedAttributeMulti = False

        if name != "N/A":
            self._selectedAttributeMulti.append( name )
            self.Modified()

    @smproperty.stringvector(
        name="StringSingle",
        label="Value to fill",
        number_of_elements="1",
        default_values="nan",
        panel_visibility="default",
    )
    def a01StringSingle( self: Self, value: str, ) -> None:
        """Define an input string field.

        Args:
            value (str): Input
        """
        if value == "nan":
            value = np.nan
        else:
            value = float( value )
        
        if value != self._doubleSingle:
            self._doubleSingle = value 
            self.Modified()

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
        inputMesh: vtkMultiBlockDataSet = self.GetInputData( inInfoVec, 0, 0 )
        outputMesh: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )
        assert inputMesh is not None, "Input server mesh is null."
        assert outputMesh is not None, "Output pipeline is null."
        
        filter: FillPartialArrays = FillPartialArrays()
        filter._SetSelectedAttributeMulti( self._selectedAttributeMulti )
        filter._SetValueToFill( self._doubleSingle )
        filter.SetInputDataObject( inputMesh )
        filter.Update()
        outputMesh.ShallowCopy( filter.GetOutputDataObject( 0 ) )

        self._clearSelectedAttributeMulti = True
        return 1
