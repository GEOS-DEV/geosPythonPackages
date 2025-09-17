# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Union
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler, )
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

# Update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.processing.MergeBlockEnhanced import MergeBlockEnhanced

__doc__ = """
Merge Blocks Keeping Partial Attributes is a Paraview plugin filter that allows to merge blocks from a multiblock dataset while keeping partial attributes.

Input is a vtkMultiBlockDataSet and output is a vtkUnstructuredGrid.

.. Note::
    This plugin is intended to be used for GEOS VTK outputs. You may encounter issues if two datasets of the input multiblock dataset have duplicated cell IDs.


To use it:

* Load the module in Paraview: Tools > Manage Plugins... > Load new > PVMergeBlocksEnhanced
* Select the multiblock dataset mesh you want to merge
* Select Filters > 4- Geos Utils > Merge Blocks Keeping Partial Attributes
* Apply


.. Note::
    Partial attributes are filled with default values depending on their types.
    - 0 for uint data.
    - -1 for int data.
    - nan for float data.
"""


@smproxy.filter( name="PVMergeBlocksEnhanced", label="Merge Blocks Keeping Partial Attributes" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Input", port_index=0, label="Input" )
@smdomain.datatype( dataTypes=[ "vtkMultiBlockDataSet" ], composite_data_supported=True )
class PVMergeBlocksEnhanced( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Merge filter that keep partial attributes using default filling values."""
        super().__init__(
            nInputPorts=1,
            nOutputPorts=1,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkUnstructuredGrid",
        )

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
        return super().RequestDataObject( request, inInfoVec, outInfoVec )

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
        inputMesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
        outputMesh: vtkUnstructuredGrid = self.GetOutputData( outInfoVec, 0 )

        assert inputMesh is not None, "Input mesh is null."
        assert outputMesh is not None, "Output pipeline is null."

        filter: MergeBlockEnhanced = MergeBlockEnhanced( inputMesh, True )

        if not filter.logger.hasHandlers():
            filter.setLoggerHandler( VTKHandler() )

        success = filter.applyFilter()

        if success:
            outputMesh.ShallowCopy( filter.getOutput() )
            outputMesh.Modified()

        return 1
