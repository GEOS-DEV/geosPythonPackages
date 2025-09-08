# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Union
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.processing.AttributeMapping import AttributeMapping
from geos.mesh.utils.arrayHelpers import ( getAttributeSet, isAttributeGlobal )

from geos.pv.utils.checkboxFunction import createModifiedCallback
from geos.pv.utils.paraviewTreatments import getArrayChoices
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonCore import (
    vtkDataArraySelection,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataSet,
    vtkMultiBlockDataSet,
)

__doc__ = """
AttributeMapping is a paraview plugin that transfer global attributes from a meshFrom to a meshTo for each
cell or point of the two meshes with the same coordinates. For cell, the coordinates of the points in the cell are compared.
Input and output meshes can be vtkDataSet or vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVAttributeMapping.
* Select the mesh to transfer the global attributes (meshTo).
* Search and Select Attribute Mapping Filter.
* Select the mesh with global attributes to transfer (meshFrom).
* Select global attributes to transfer from the meshFrom to the meshTo.
* Apply.

"""


@smproxy.filter( name="PVAttributeMapping", label="Attribute Mapping" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="meshFrom", port_index=1, label="Mesh From" )
@smdomain.datatype(
    dataTypes=[ "vtkDataSet", "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
@smproperty.input( name="meshTo", port_index=0, label="Mesh To" )
@smdomain.datatype(
    dataTypes=[ "vtkDataSet", "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
class PVAttributeMapping( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map attributes of the source mesh (meshFrom) to the other mesh (meshTo)."""
        super().__init__( nInputPorts=2, nOutputPorts=1, inputType="vtkObject", outputType="vtkObject" )

        self.onPoints: bool = False

        self._initArraySelections: bool = True
        self.cellAttributeNames: vtkDataArraySelection = vtkDataArraySelection()
        self.pointAttributeNames: vtkDataArraySelection = vtkDataArraySelection()
        
        self.clearAttributeNames = True
        self.attributeNames: list[ str ] = []

    @smproperty.intvector(
        name="AttributeType",
        default_values=1,
        number_of_elements=1,
    )
    @smdomain.xml( """
        <FieldDataDomain enable_field_data="0" name="enum">
            <RequiredProperties>
                <Property function="Input" name="meshFrom" />
            </RequiredProperties>
        </FieldDataDomain>
    """ )
    def e01SetFieldAssociation( self: Self, value: int ) -> None:
        """Set attribute type.

        Args:
            value  (int): 0 if on points, 1 if on cells.
        """
        self.onPoints = bool( value )
        self.Modified()
        
    @smproperty.stringvector(
        name="SelectAttributeToTransfer",
        label="Select Attribute To Transfer",
        repeat_command=1,
        number_of_elements_per_command="1",
        element_types="2",
        default_values="None",
    )
    @smdomain.xml( """
        <ArrayListDomain name="Attribute_List"
                attribute_type="array"
                input_domain_name="onPiece_Attribute_List">
            <RequiredProperties>
                <Property function="Input" name="meshFrom" />
                <Property function="FieldDataSelection" name="AttributeType" />
            </RequiredProperties>
        </ArrayListDomain>
        <Documentation>
            Select attributes to transfer from the meshFrom To the meshTo.
        </Documentation>
        <Hints>
            <NoDefault />
        </Hints>
            """ )
    def a02SelectMultipleAttribute( self: Self, name: str ) -> None:
        """Set the attribute to transfer from the meshFrom to the meshTo.

        Args:
            name (str): The name of the attribute to transfer.
        """
        if self.clearAttributeNames:
            self.attributeNames = []
            self.clearAttributeNames = False

        if name != "None":
            self.attributeNames.append( name )
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
        inDataTo = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inDataTo is not None
        if outData is None or ( not outData.IsA( inDataTo.GetClassName() ) ):
            outData = inDataTo.NewInstance()
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
        meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
        meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 1, 0 )
        outData: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCompositeDataSet ] = self.GetOutputData( outInfoVec, 0 )

        assert meshTo is not None, "Input mesh (meshTo) to transfer attributed is null."
        assert meshFrom is not None, "Input mesh (meshFrom) with attributes to transfer is null."
        assert outData is not None, "Output pipeline is null."

        outData.ShallowCopy( meshTo )

        filter: AttributeMapping = AttributeMapping( meshFrom, outData, set(self.attributeNames), self.onPoints, True )
        if not filter.logger.hasHandlers():
            filter.setLoggerHandler( VTKHandler() )

        filter.applyFilter()
        self.clearAttributeNames = True

        return 1

