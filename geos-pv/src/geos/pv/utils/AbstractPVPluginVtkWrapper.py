# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Any
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
)

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)


__doc__ = """
AbstractPVPluginVtkWrapper module defines the parent Paraview plugin from which inheritates PV plugins that directly wrap a vtk filter.

To use it, make children PV plugins inherited from AbstractPVPluginVtkWrapper. Output mesh is of same type as input mesh.
If output type needs to be specified, this must be done in the child class.
"""

class AbstractPVPluginVtkWrapper(VTKPythonAlgorithmBase):
    def __init__(self:Self) ->None:
        """Abstract Paraview Plugin class."""
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkPointSet")

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
            inputMesh: Any = self.GetInputData( inInfoVec, 0, 0 )
            outputMesh: Any = self.GetOutputData( outInfoVec, 0 )
            assert inputMesh is not None, "Input server mesh is null."
            assert outputMesh is not None, "Output pipeline is null."

            tmpMesh = self.applyVtkFlilter(inputMesh)
            assert tmpMesh is not None, "Output mesh is null."
            outputMesh.ShallowCopy(tmpMesh)
            print("Filter was successfully applied.")
        except (AssertionError, Exception) as e:
            print(f"Filter failed due to: {e}")
            return 0
        return 1

    def applyVtkFlilter(
        self: Self,
        input: Any,
    ) -> Any:
        """Apply vtk filter.

        Args:
            input (Any): input object

        Returns:
            Any: output mesh
        """
        pass
