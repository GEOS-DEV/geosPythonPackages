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
from geos.mesh.utils.arrayHelpers import getAttributeSet

from geos.pv.utils.checkboxFunction import createModifiedCallback
from geos.pv.utils.paraviewTreatments import getArrayChoices
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

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
AttributeMapping is a paraview plugin that transfer attributes from a source mesh to the working mesh for each
cell of the two meshes with the same coordinates.
Input and output meshes can be vtkDataSet or vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVAttributeMapping.
* Select the working mesh.
* Search and Select Attribute Mapping Filter.
* Select the source mesh.
* Select attributes to transfer from the source mesh to the working mesh.
* Apply.

"""


@smproxy.filter( name="PVAttributeMapping", label="Attribute Mapping" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Source", port_index=1, label="Source mesh" )
@smdomain.datatype(
    dataTypes=[ "vtkDataSet", "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
@smproperty.input( name="Working", port_index=0, label="Working mesh" )
@smdomain.datatype(
    dataTypes=[ "vtkDataSet", "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
class PVAttributeMapping( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map attributes of the source mesh to the working mesh."""
        super().__init__( nInputPorts=2, nOutputPorts=1, inputType="vtkObject", outputType="vtkObject" )

        # boolean to check if first use of the filter for attribute list initialization
        self.m_firstUse = True

        # list of attribute names to transfer
        self.m_attributes: vtkDataArraySelection = vtkDataArraySelection()
        self.m_attributes.AddObserver( 0, createModifiedCallback( self ) )

    @smproperty.dataarrayselection( name="AttributesToTransfer" )
    def a02GetAttributeToTransfer( self: Self ) -> vtkDataArraySelection:
        """Get selected attribute names to transfer.

        Returns:
            vtkDataArraySelection: selected attribute names.
        """
        self.Modified()
        return self.m_attributes

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        # only at initialization step, no change later
        if self.m_firstUse:
            # get cell ids
            inData = self.GetInputData( inInfoVec, 1, 0 )
            assert isinstance( inData, ( vtkDataSet, vtkMultiBlockDataSet ) ), "Working mesh type is not supported."

            # update vtkDAS
            attributeNames: set[ str ] = getAttributeSet( inData, False )
            for attributeName in attributeNames:
                if not self.m_attributes.ArrayExists( attributeName ):
                    self.m_attributes.AddArray( attributeName, False )

            self.m_firstUse = False
        return 1

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
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        workingMesh: Union[ vtkDataSet, vtkMultiBlockDataSet,
                            vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
        sourceMesh: Union[ vtkDataSet, vtkMultiBlockDataSet,
                            vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 1, 0 )
        outData: Union[ vtkDataSet, vtkMultiBlockDataSet,
                        vtkCompositeDataSet ] = self.GetOutputData( outInfoVec, 0 )

        assert workingMesh is not None, "Input working mesh is null."
        assert sourceMesh is not None, "Input source mesh is null."
        assert outData is not None, "Output pipeline is null."

        outData.ShallowCopy( workingMesh )

        attributeNames: set[ str ] = set( getArrayChoices( self.a02GetAttributeToTransfer() ) )
        
        filter: AttributeMapping = AttributeMapping( sourceMesh, outData, attributeNames, True )
        if not filter.logger.hasHandlers():
            filter.setLoggerHandler( VTKHandler() )

        filter.applyFilter()

        return 1

