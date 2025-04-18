# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
from typing_extensions import Self
from vtkmodules.vtkFiltersCore import vtkFeatureEdges
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkCell,
    VTK_VERTEX
)

from geos.mesh.model.MeshIdCard import MeshIdCard

__doc__ = """
ComputeMeshStats module is a vtk filter that computes mesh stats.

Mesh stats include the number of elements of each type.

Filter input is a vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from geos.mesh.stats.ComputeMeshStats import ComputeMeshStats

    # filter inputs
    input :vtkUnstructuredGrid

    # instanciate the filter
    filter :ComputeMeshStats = ComputeMeshStats()
    # set input data object
    filter.SetInputDataObject(input)
    # do calculations
    filter.Update()
    # get output mesh id card
    output :MeshIdCard = filter.GetMeshIdCard()
"""
class ComputeMeshStats(VTKPythonAlgorithmBase):

    def __init__(self) ->None:
        """ComputeMeshStats filter computes mesh stats."""
        super().__init__(nInputPorts=1, nOutputPorts=0)
        self.card: MeshIdCard

    def FillInputPortInformation(self: Self, port: int, info: vtkInformation ) -> int:
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
        assert inData is not None
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
        inData: vtkUnstructuredGrid = self.GetInputData(inInfoVec, 0, 0)
        assert inData is not None, "Input mesh is undefined."

        self.card = MeshIdCard()
        self.card.setTypeCount(VTK_VERTEX, inData.GetNumberOfPoints())
        for i in range(inData.GetNumberOfCells()):
            cell: vtkCell = inData.GetCell(i)
            self.card.addType(cell.GetCellType())
        return 1

    def _computeNumberOfEdges(self :Self, mesh: vtkUnstructuredGrid) ->int:
        """Compute the number of edges of the mesh.

        Args:
            mesh (vtkUnstructuredGrid): input mesh

        Returns:
            int: number of edges
        """
        edges: vtkFeatureEdges = vtkFeatureEdges()
        edges.BoundaryEdgesOn()
        edges.ManifoldEdgesOn()
        edges.FeatureEdgesOff()
        edges.NonManifoldEdgesOff()
        edges.SetInputDataObject(mesh)
        edges.Update()
        return edges.GetOutput().GetNumberOfCells()

    def GetMeshIdCard(self :Self) -> MeshIdCard:
        """Get MeshIdCard object.

        Returns:
            MeshIdCard: MeshIdCard object.
        """
        return self.card
