# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import numpy
from pathlib import Path
from typing import Union, Any

from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smhint, smproperty, smproxy,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtk import VTK_DOUBLE  # type: ignore[import-untyped]
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkDataSet,
)


# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.processing.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion

__doc__ = """
PVCreateConstantAttributePerRegion is a paraview Plugin that allows to create an attribute
with constant values for each chosen indexes of a reference/region attribute.
The region attribute has to have one component and the created attribute has one component.
Regions indexes, values and values types are choose by the user, for the other region index
values are set to nan or -1 if int type.

Input and output meshes are either vtkMultiBlockDataSet or vtkDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVCreateConstantAttributePerRegion.
* Select the mesh you want to create the attributes and containing a region attribute.
* Select the filter Create Constant Attribute Per Region in filter|0- Geos Pre-processing.
* Set variables (region attribute, value type, attribute name, index and its value) and Apply.

"""

@smproxy.filter(
    name="PVCreateConstantAttributePerRegion",
    label="Create Constant Attribute Per Region",
)
@smhint.xml( """<ShowInMenu category="0- Geos Pre-processing"/>""" )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkMultiBlockDataSet", "vtkDataSet" ],
    composite_data_supported=True,
)
class PVCreateConstantAttributePerRegion( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Create an attribute with constant value per region."""
        super().__init__( nInputPorts=1,
                          nOutputPorts=1,
                          inputType="vtkDataObject",
                          outputType="vtkDataObject" )

        self.dictRegion: dict[ Any, Any ] = {}
        self.clearDictRegion: bool = True
        self.regionName: str = "Region"
        self.newAttributeName: str = "newAttribute"
        self.valueType: int = 10
    
    @smproperty.xml( """
        <StringVectorProperty
            name="AttributeName"
            command="a02SetAttributeName"
            default_values="newAttribute"
            number_of_elements="1"
            element_types="2">
            <Documentation>
                Name of the new attribute
            </Documentation>
        </StringVectorProperty>
        """ )
    def a02SetAttributeName( self: Self, value: str ) -> None:
        """Set attribute name.

        Args:
            value (str): attribute name.
        """
        if self.newAttributeName != value:
            self.newAttributeName = value
            self.Modified()

    @smproperty.intvector(
        name="ValueType",
        label="Values type",
        number_of_elements=1,
        default_values=10,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <EnumerationDomain name="enum">
            <Entry value="2" text="int8"/>
            <Entry value="4" text="int16"/>
            <Entry value="6" text="int32"/>
            <Entry value="16" text="int64"/>
            <Entry value="3" text="uint8"/>
            <Entry value="5" text="uint16"/>
            <Entry value="7" text="uint32"/>
            <Entry value="17" text="uint64"/>
            <Entry value="10" text="float32"/>
            <Entry value="11" text="float64"/>
            <Entry value="12" text="ID_TYPE_CODE ( int32 | int64 )"/>
        </EnumerationDomain>
        <Documentation>
            The values type of the attribute. Each type is encoded by a int using the vtk typecode.
        </Documentation>
        """ )
    def a02IntSingle( self: Self, value: int ) -> None:
        """Define an input int field.

        Args:
            value (int): Input
        """
        if value != self.valueType:
            self.valueType = value
            self.Modified()
    
    @smproperty.xml( """
        <PropertyGroup 
            label="Settings of the new attribute"
            panel_visibility="default">
            <Property name="AttributeName"/>
            <Property name="ValueType"/>
        </PropertyGroup>""" )
    def b02GroupFlow1( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.stringvector(
        name="ChooseRegionAttribute",
        label="Attribute with region indexes",
        command="a01SetRegionAttributeName",
        default_values="Choose an attribute",
        number_of_elements="1",
        element_types="2",
        )
    @smdomain.xml("""
        <ArrayListDomain
            name="array_list"
            attribute_type="Scalars"
            input_domain_name="inputs_array">
            <RequiredProperties>
                <Property name="Input" function="Input"/>
            </RequiredProperties>
        </ArrayListDomain>
        <Documentation>
            Select an attribute containing the indexes of the regions
        </Documentation>
        <Hints>
            <NoDefault />
        </Hints>
    """ )
    def a01SetRegionAttributeName( self: Self, name: str ) -> None:
        """Set region attribute name."""
        if self.regionName != name:
            self.regionName = name
            self.Modified()

    @smproperty.xml("""
        <StringVectorProperty
            name="AttributeTable"
            command="b01SetAttributeValues"
            number_of_elements="2"
            repeat_command="1"
            number_of_elements_per_command="2">
            <Hints>
                <AllowRestoreDefaults />
                <ShowComponentLabels>
                    <ComponentLabel component="0" label="Region Indexes"/>
                    <ComponentLabel component="1" label="New Attribute Constant Values Associated"/>
                </ShowComponentLabels>
            </Hints>
            <Documentation>
                Set the constant value of the new attribute for each region indexes.
            </Documentation>
        </StringVectorProperty>
    """ )
    def b01SetAttributeValues( self: Self, regionIndex: str, value: str ) -> None:
        """Set the constant value of the new attribute for each region indexes.

        Args:
            regionIndex (int): Region index.
            value (float): Attribute constant value for the regionIndex.
        """
        if self.clearDictRegion:
            self.dictRegion = {}
            self.clearDictRegion = False
        
        if regionIndex != None and value != None :
            assert "," not in regionIndex, "Use the '.' not the ',' for decimal numbers"
            assert "," not in value, "Use the '.' not the ',' for decimal numbers"
            regionIndex = float( regionIndex )
            value = float( value )
            if regionIndex not in self.dictRegion.keys():
                self.dictRegion[regionIndex] = value
        self.Modified()

    @smproperty.xml( """
        <PropertyGroup 
            label="Settings of the attribute with the region indexes"
            panel_visibility="default">
            <Property name="ChooseRegionAttribute"/>
            <Property name="AttributeTable"/>
        </PropertyGroup>""" )
    def b02GroupFlow( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

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
        inputMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = ( self.GetInputData( inInfoVec, 0, 0 ) )
        outputMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = ( self.GetOutputData( outInfoVec, 0 ) )

        assert inputMesh is not None, "Input Surface is null."
        assert outputMesh is not None, "Output pipeline is null."
            
        filter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion( self.regionName,
                                                                                     self.newAttributeName,
                                                                                     self.dictRegion,
                                                                                     self.valueType,
                                                                                     True, )
        vtkHandler: VTKHandler = VTKHandler()
        filter.setLoggerHandler( vtkHandler )
        filter.SetInputDataObject( inputMesh )
        
        filter.Update()
        outputMesh.ShallowCopy( filter.GetOutputDataObject( 0 ) )


        self.clearDictRegion = True

        return 1

