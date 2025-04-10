# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
from typing import Union
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataObjectTreeIterator,
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
root = os.path.dirname(os.path.dirname(os.path.dirname( dir_path )))
print(root)
for m in ("geos-posp", "geos-mesh", "geos-pv"):
    path = os.path.join(root, m, "src")
    if path not in sys.path:
        sys.path.append( path )

from geos.mesh.processing.SplitMesh import SplitMesh

__doc__ = """
Slip each cell of input mesh to smaller cells.

Input and output are vtkUnstructuredGrid.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVSplitMesh.
* Select the input mesh.
* Apply the filter.

"""

@smproxy.filter( name="PVSplitMesh", label="Split Mesh" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid"],
    composite_data_supported=True,
)
class PVSplitMesh(VTKPythonAlgorithmBase):
    def __init__(self:Self):
        """Split mesh cells."""
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid")

    def FillInputPortInformation(self :Self, port: int, info: vtkInformation) ->int:
        """Inherited from VTKPythonAlgorithmBase::FillInputPortInformation.

        Args:
            port (int): port index
            info (vtkInformation): input port Information

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid")

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
        inData = self.GetInputData(inInfoVec, 0, 0)
        outData = self.GetOutputData(outInfoVec, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfoVec, outInfoVec)
        
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
        try:
            inputMesh: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet,
                               vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
            outputMesh: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet,
                            vtkCompositeDataSet ] = self.GetOutputData( outInfoVec, 0 )

            assert inputMesh is not None, "Input server mesh is null."
            assert outputMesh is not None, "Output pipeline is null."

            splittedMesh: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet, vtkCompositeDataSet ]
            if isinstance( inputMesh, vtkUnstructuredGrid ):
                splittedMesh = self.doSplitMesh(inputMesh)
            elif isinstance( inputMesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
                splittedMesh = self.doSplitMeshMultiBlock(inputMesh)
            else:
                raise ValueError( "Input mesh data type is not supported. Use either vtkUnstructuredGrid or vtkMultiBlockDataSet" )
            assert splittedMesh is not None, "Splitted mesh is null."
            outputMesh.ShallowCopy(splittedMesh)
            print("Mesh was successfully splitted.")
        except AssertionError as e:
            print(f"Mesh split failed due to: {e}")
            return 0
        except Exception as e:
            print(f"Mesh split failed due to: {e}")
            return 0
        return 1

    def doSplitMesh(
        self: Self,
        inputMesh: vtkUnstructuredGrid,
    ) -> vtkUnstructuredGrid:
        """Split cells from vtkUnstructuredGrids.

        Args:
            inputMesh (vtkUnstructuredGrid): input mesh

        Returns:
            vtkUnstructuredGrid: mesh where cells where splitted.
        """
        filter :SplitMesh = SplitMesh()
        filter.SetInputDataObject(inputMesh)
        filter.Update()
        return filter.GetOutputDataObject( 0 )

    def doSplitMeshMultiBlock(
        self: Self,
        inputMesh: vtkMultiBlockDataSet,
    ) -> vtkMultiBlockDataSet:
        """Split cells from vtkMultiBlockDataSet.

        Args:
            inputMesh (vtkMultiBlockDataSet): input mesh

        Returns:
            vtkMultiBlockDataSet: mesh where cells where splitted.
        """
        outputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
        iter.SetDataSet( inputMesh )
        iter.VisitOnlyLeavesOn()
        iter.GoToFirstItem()
        blockIndex: int = 0
        while iter.GetCurrentDataObject() is not None:
            block: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( iter.GetCurrentDataObject() )
            splittedBlock: vtkUnstructuredGrid = self.doSplitMesh( block )
            outputMesh.SetBlock(blockIndex, splittedBlock)
            blockIndex += 1
            iter.GoToNextItem()
        return outputMesh
