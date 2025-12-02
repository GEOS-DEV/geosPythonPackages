# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Union
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.processing.generic_processing_tools.AttributeMapping import AttributeMapping

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy )
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkCompositeDataSet, vtkDataSet, vtkMultiBlockDataSet

from geos.pv.utils.details import FilterCategory

__doc__ = f"""
AttributeMapping is a paraview plugin that transfers global attributes from a source mesh to a final mesh with same point/cell coordinates.

Input and output meshes can be vtkDataSet or vtkMultiBlockDataSet.

.. Warning::
    For one application of the plugin, the attributes to transfer should all be located on the same piece (all on points or all on cells).

.. Note::
    For cell, the coordinates of the points in the cell are compared.
    If one of the two meshes is a surface and the other a volume, all the points of the surface must be points of the volume.

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/generic_processing/PVAttributeMapping
* Select the mesh to transfer the global attributes (meshTo)
* Select the filter: Filters > { FilterCategory.GENERIC_PROCESSING.value } > Attribute Mapping
* Select the source mesh with global attributes to transfer (meshFrom)
* Select the on which element (onPoints/onCells) the attributes to transfer are
* Select the global attributes to transfer from the source mesh to the final mesh
* Apply

"""


@smproxy.filter( name="PVAttributeMapping", label="Attribute Mapping" )
@smhint.xml( f'<ShowInMenu category="{ FilterCategory.GENERIC_PROCESSING.value }"/>' )
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
        """Map attributes of the source mesh (meshFrom) to the final mesh (meshTo)."""
        super().__init__( nInputPorts=2, nOutputPorts=1, inputType="vtkObject", outputType="vtkObject" )

        self.onPoints: bool = False
        self.clearAttributeNames = True
        self.attributeNames: list[ str ] = []

    @smproperty.intvector(
        name="AttributePiece",
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
    def setAttributePiece( self: Self, piece: int ) -> None:
        """Set attributes piece (points or cells).

        Args:
            piece (int): 0 if on points, 1 if on cells.
        """
        self.onPoints = not bool( piece )
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
                <Property function="FieldDataSelection" name="AttributePiece" />
            </RequiredProperties>
        </ArrayListDomain>
        <Documentation>
            Select attributes to transfer from the source mesh to the final mesh.
        </Documentation>
        <Hints>
            <NoDefault />
        </Hints>
            """ )
    def selectMultipleAttribute( self: Self, name: str ) -> None:
        """Set the attribute to transfer from the source mesh to the final mesh.

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
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

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
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
        meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 1, 0 )
        outData: Union[ vtkDataSet, vtkMultiBlockDataSet, vtkCompositeDataSet ] = self.GetOutputData( outInfoVec, 0 )

        assert meshTo is not None, "The final mesh (meshTo) where to transfer attributes is null."
        assert meshFrom is not None, "The source mesh (meshFrom) with attributes to transfer is null."
        assert outData is not None, "Output pipeline is null."

        outData.ShallowCopy( meshTo )

        attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, outData, set( self.attributeNames ),
                                                                     self.onPoints, True )

        if len( attributeMappingFilter.logger.handlers ) == 0:
            attributeMappingFilter.setLoggerHandler( VTKHandler() )

        attributeMappingFilter.applyFilter()
        self.clearAttributeNames = True

        return 1
