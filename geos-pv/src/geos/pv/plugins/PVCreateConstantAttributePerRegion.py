# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path

from typing import Union, Any
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smhint, smproperty, smproxy,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

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

from geos.mesh.processing.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion, vnp, np

__doc__ = """
PVCreateConstantAttributePerRegion is a Paraview plugin that allows to create an attribute
with constant values per components for each chosen indexes of a reference/region attribute.
If other region indexes exist values are set to nan for float type, -1 for int type or 0 for uint type.

Input mesh is either vtkMultiBlockDataSet or vtkDataSet and the region attribute must have one component.
The relation index/values is given by a dictionary. Its keys are the indexes and its items are the list of values for each component.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVCreateConstantAttributePerRegion.
* Select the mesh you want to create the attributes and containing a region attribute.
* Select the filter Create Constant Attribute Per Region in filter|0- Geos Pre-processing.
* Choose the region attribute, the relation index/values, the new attribute name, the type of the value, the number of components and their names.
* Apply.

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
        
        self.clearDictRegionValues: bool = True

        # Region attribute settings.
        self.regionName: str = ""
        self.dictRegionValues: dict[ Any, Any ] = {}

        # New attribute settings.
        self.newAttributeName: str = "newAttribute"
        self.valueNpType: type = np.float32
        self.nbComponents: int = 1
        self.componentNames: tuple[ str, ... ] = ()

        # Use the handler of paraview for the log.
        self.speHandler: bool = True

    
    # Settings of the attribute with the region indexes:
    @smproperty.stringvector(
        name="ChooseRegionAttribute",
        label="Attribute with region indexes",
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
            Select the attribute to consider as the region attribute containing the indexes of the regions.
        </Documentation>
        <Hints>
            <NoDefault />
        </Hints>
    """ )
    def _setRegionAttributeName( self: Self, regionName: str ) -> None:
        """Set region attribute name.
        
        Args:
            regionName (str): The name of the attribute to consider as the region attribute.
        """
        self.regionName = regionName
        self.Modified()


    @smproperty.xml("""
        <StringVectorProperty
            name="AttributeTable"
            number_of_elements="2"
            command="_setDictRegionValues"
            repeat_command="1"
            number_of_elements_per_command="2">
            <Documentation>
                Set the value of the new attribute for each region indexes, use a space between the value of each components:\n
                    valueRegionIndex | valueComponent1 valueComponent2 ...\n
                If the region attribute has other indexes than those given, a default value is use:\n
                    0 for uint type, -1 for int type and nan for float type.
            </Documentation>     
            <Hints>
                <AllowRestoreDefaults />
                <ShowComponentLabels>
                    <ComponentLabel component="0" label="Region Indexes"/>
                    <ComponentLabel component="1" label="New Attribute Values"/>
                </ShowComponentLabels>
            </Hints>
        </StringVectorProperty>
    """ )
    def _setDictRegionValues( self: Self, regionIndex: str, value: str ) -> None:
        """Set the the dictionary with the region indexes and its corresponding list of value for each components.

        Args:
            regionIndex (str): Region index of the region attribute to consider.
            value (str): List of value to use for the regionIndex. If multiple components use a coma between the value of each component.
        """
        if self.clearDictRegionValues:
            self.dictRegionValues = {}
            self.clearDictRegionValues = False
        
        if regionIndex != None and value != None :
            self.dictRegionValues[ regionIndex ] = list( value.split( "," ) )
 
        self.Modified()


    @smproperty.xml( """
        <PropertyGroup 
            label="Settings of the attribute with the region indexes"
            panel_visibility="default">
            <Property name="ChooseRegionAttribute"/>
            <Property name="AttributeTable"/>
        </PropertyGroup>""" )
    def _groupeRegionAttributeSettingsWidgets( self: Self ) -> None:
        """Group the widgets to set the settings of the region attribute."""
        self.Modified()


    # Settings of the new attribute:
    @smproperty.xml( """
        <StringVectorProperty
            name="AttributeName"
            label="The name of the new attribute:"
            default_values="newAttribute"
            number_of_elements="1"
            element_types="2">
            <Documentation>
                Name of the new attribute to create.
            </Documentation>
        </StringVectorProperty>
    """ )
    def _setAttributeName( self: Self, newAttributeName: str ) -> None:
        """Set attribute name.

        Args:
            newAttributeName (str): Name of the new attribute to create.
        """
        self.newAttributeName = newAttributeName
        self.Modified()


    @smproperty.intvector(
        name="ValueType",
        label="The type of the values:",
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
        </EnumerationDomain>
        <Documentation>
            The wanted numpy scalar type for values of the new attribute.
        </Documentation>
    """ )
    def _setValueType( self: Self, valueType: int ) -> None:
        """Set the type for the value used to create the new attribute.

        Args:
            valueType (int): The type for the value encoding with the vtk typecode.
        """
        dictType: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
        self.valueNpType: type = dictType[ valueType ]
        self.Modified()


    @smproperty.intvector(
        name="NumberOfComponents",
        label="Number of components:",
        number_of_elements=1,
        default_values=1,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            The number of components for the new attribute to create.
        </Documentation>
    """ )
    def _setNbComponent( self: Self, nbComponents: int ) -> None:
        """Set the number of components of the attribute to create.

        Args:
            nbComponents (int): Number of components for the new attribute.
        """
        self.nbComponents = nbComponents
        self.Modified()


    @smproperty.stringvector(
        name="ComponentNames",
        label="Names of components:",
        number_of_elements=1,
        default_values="Change if multiple components",
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            Names of components if multiple for the new attribute to create.
            Use the coma and a space between each component name:\n
                Names of components: X Y Z
        </Documentation>
        """ )
    def _setComponentNames( self: Self, componentNames: str ) -> None:
        """Set the names of the components of the attribute to create.

        Args:
            componentNamesStr (str): Names of component for the new attribute. Use a coma between each component names.
        """
        if componentNames == "" or componentNames == "Change if multiple components" or self.nbComponents == 1:
            self.componentNames = ()
        else:
            self.componentNames = tuple( componentNames.split( "," ) )
        
        self.Modified()


    @smproperty.xml( """
        <PropertyGroup 
            label="Settings of the new attribute"
            panel_visibility="default">
            <Property name="AttributeName"/>
            <Property name="ValueType"/>
            <Property name="NumberOfComponents"/>
            <Property name="ComponentNames"/>
        </PropertyGroup>""" )
    def _groupNewAttributeSettingsWidgets( self: Self ) -> None:
        """Group the widgets to set the settings of the new attribute."""
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
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inputMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = ( self.GetInputData( inInfoVec, 0, 0 ) )
        outputMesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = ( self.GetOutputData( outInfoVec, 0 ) )

        assert inputMesh is not None, "Input Surface is null."
        assert outputMesh is not None, "Output pipeline is null."

        outputMesh.ShallowCopy( inputMesh )
        filter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion( outputMesh,
                                                                                     self.regionName,
                                                                                     self.dictRegionValues,
                                                                                     self.newAttributeName,
                                                                                     self.valueNpType,
                                                                                     self.nbComponents,
                                                                                     self.componentNames,
                                                                                     self.speHandler,
        )

        if not filter.logger.hasHandlers():
            filter.setLoggerHandler( VTKHandler() )
        
        filter.applyFilter()

        self.clearDictRegion = True

        return 1
