# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkIntArray,
    vtkInformation,
    vtkInformationVector,
    vtkPoints,
    reference
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, 
    vtkIncrementalOctreePointLocator,
)


__doc__ = """
MergeColocatedPoints module is a vtk filter that merges colocated points from input mesh.

Filter input and output types are vtkUnstructuredGrid.

.. Warning:: This operation uses geometrical tests that may not be accurate in case of very small cells.


To use the filter:

.. code-block:: python

    from geos.mesh.processing.MergeColocatedPoints import MergeColocatedPoints

    # filter inputs
    input :vtkUnstructuredGrid

    # instanciate the filter
    filter :MergeColocatedPoints = MergeColocatedPoints()
    # set input data object
    filter.SetInputDataObject(input)
    # do calculations
    filter.Update()
    # get output object
    output :vtkUnstructuredGrid = filter.GetOutputDataObject(0)
"""

class MergeColocatedPoints(VTKPythonAlgorithmBase):
    def __init__(self: Self ):
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid")

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid")

    def RequestDataObject(self: Self, 
                          request: vtkInformation,  # noqa: F841
                          inInfoVec: list[ vtkInformationVector ],  # noqa: F841
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

    def RequestData(self: Self, 
                    request: vtkInformation,  # noqa: F841
                    inInfoVec: list[ vtkInformationVector ],  # noqa: F841
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
        inData: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
        output: vtkUnstructuredGrid = self.GetOutputData(outInfoVec, 0)
        newPoints: vtkPoints = vtkPoints()
        # use point locator to check for colocated points
        merge_points = vtkIncrementalOctreePointLocator()
        merge_points.InitPointInsertion(newPoints,inData.GetBounds())
        # create an array to count the number of colocated points
        vertexCount: vtkIntArray = vtkIntArray()
        vertexCount.SetName("Count")
        ptId = reference(0)
        countD: int = 0
        for v in range(inData.GetNumberOfPoints()):
            inserted: bool = merge_points.InsertUniquePoint( inData.GetPoints().GetPoint(v), ptId)
            if inserted:
                vertexCount.InsertNextValue(1)
            else:
                vertexCount.SetValue( ptId, vertexCount.GetValue(ptId) + 1)
                countD = countD + 1
            
        output.SetPoints(merge_points.GetLocatorPoints())
        # copy point attributes
        output.GetPointData().DeepCopy(inData.GetPointData())
        # add the array to points data
        output.GetPointData().AddArray(vertexCount)
        # copy cell attributes
        output.GetCellData().DeepCopy(inData.GetCellData())
        return 1