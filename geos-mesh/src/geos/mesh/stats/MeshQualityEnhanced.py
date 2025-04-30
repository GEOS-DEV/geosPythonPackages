# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
import numpy.typing as npt
import pandas as pd
from typing import Optional, Iterable
from typing_extensions import Self
from vtkmodules.vtkFiltersCore import vtkExtractEdges, vtkFeatureEdges
from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
    vtkIdList,
    vtkPoints,
    vtkDataArray,
    vtkIntArray,
    vtkDoubleArray,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkPolyData,
    vtkCellData,
    vtkFieldData,
    vtkCell,
    vtkPolygon,
    vtkTetra,
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON
)
from vtkmodules.util.numpy_support import vtk_to_numpy

from geos.mesh.stats.CellTypeCounter import CellTypeCounter
from geos.mesh.model.CellTypeCounts import CellTypeCounts
from geos.mesh.model.QualityMetricSummary import QualityMetricSummary, StatTypes
from geos.utils.geometryFunctions import computeAngleFromPoints, computeNormalFromPoints, computeAngleFromVectors
from geos.mesh.vtk.helpers import getAttributesFromDataSet
from geos.mesh.processing.meshQualityMetricHelpers import (
    getQualityMeasureNameFromIndex,
    getQualityMeasureIndexFromName,
    qualityMetricsFromCellType,
    QualityMetricEnum,
    getAllCellTypesExtended,
    getAllCellTypes,
    getPolygonCellTypes,
    getPolyhedronCellTypes,
    getCommonPolygonQualityMeasure,
    getCommonPolyhedraQualityMeasure,
    getQualityMeasureFromCellType,
    getChildrenCellTypes,
)
__doc__ = """
MeshQualityEnhanced module is a vtk filter that computes mesh quality stats.

Mesh quality stats include those from vtkMeshQuality as well as .

Filter input is a vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from geos.mesh.stats.MeshQualityEnhanced import MeshQualityEnhanced

    # filter inputs
    input :vtkUnstructuredGrid

    # instanciate the filter
    filter :MeshQualityEnhanced = MeshQualityEnhanced()
    # set input data object
    filter.SetInputDataObject(input)
    # do calculations
    filter.Update()
    # get output mesh quality report
    output :MeshQualityReport = filter.GetMeshQualityReport()
"""

#: name of output quality array from vtkMeshQuality filter
QUALITY_ARRAY_NAME:str = "Quality"

def getQualityMetricArrayName(metric: int) ->str:
    """Get the name of the array from quality metric index.

    Args:
        metric (int): metric index

    Returns:
        str: name of output array
    """
    return QUALITY_ARRAY_NAME + "_" + "".join(getQualityMeasureNameFromIndex(metric).split())

class MeshQualityEnhanced(VTKPythonAlgorithmBase):
    def __init__(self: Self) ->None:
        """Enhanced vtkMeshQuality filter."""
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid")
        self._outputMesh: vtkUnstructuredGrid
        self._cellCounts: CellTypeCounts
        self._qualityMetricSummary: QualityMetricSummary = QualityMetricSummary()

        self._MetricsAll: dict[Optional[set[int]]] = {
            VTK_TRIANGLE: None,
            VTK_QUAD: None,
            VTK_TETRA: None,
            VTK_PYRAMID: None,
            VTK_WEDGE: None,
            VTK_HEXAHEDRON: None,
        }

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

    def SetTriangleMetrics(self :Self, metrics: Optional[set[int]]) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): metrics to compute
        """
        self._MetricsAll[VTK_TRIANGLE] = metrics

    def SetQuadMetrics(self :Self, metrics: Optional[set[int]] = None) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): metrics to compute
        """
        self._MetricsAll[VTK_QUAD] = metrics

    def SetTetraMetrics(self :Self, metrics: Optional[set[int]] = None) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): metrics to compute
        """
        self._MetricsAll[VTK_TETRA] = metrics

    def SetPyramidMetrics(self :Self, metrics: Optional[set[int]] = None) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): metrics to compute
        """
        self._MetricsAll[VTK_PYRAMID] = metrics

    def SetWedgeMetrics(self :Self, metrics: Optional[set[int]] = None) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): metrics to compute
        """
        self._MetricsAll[VTK_WEDGE] = metrics

    def SetHexaMetrics(self :Self, metrics: Optional[set[int]] = None) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): metrics to compute
        """
        self._MetricsAll[VTK_HEXAHEDRON] = metrics

    def SetMeshQualityMetrics(self :Self,
                              triangleMetrics: Optional[set[int]] = None,
                              quadMetrics: Optional[set[int]] = None,
                              tetraMetrics: Optional[set[int]] = None,
                              pyramidMetrics: Optional[set[int]] = None,
                              wedgeMetrics: Optional[set[int]] = None,
                              hexaMetrics: Optional[set[int]] = None,
                             ) -> None:
        """Set all quality metrics to compute.

        Args:
            triangleMetrics (Iterable[int]): triangle metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            quadMetrics (Iterable[int]): quad metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            tetraMetrics (Iterable[int]): tetrahedron metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            pyramidMetrics (Iterable[int]): pyramid metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            wedgeMetrics (Iterable[int]): wedge metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            hexaMetrics (Iterable[int]): hexahedron metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
        """
        self.SetTriangleMetrics(triangleMetrics)
        self.SetQuadMetrics(quadMetrics)
        self.SetTetraMetrics(tetraMetrics)
        self.SetPyramidMetrics(pyramidMetrics)
        self.SetWedgeMetrics(wedgeMetrics)
        self.SetHexaMetrics(hexaMetrics)


    def getComputedMetricsFromCellType(self: Self, cellType: int) -> Optional[set[int]]:
        """Get the set of metrics computed for input cell type.

        Args:
            cellType (int): cell type index

        Returns:
            Optional[set[int]]: set of computed quality metrics
        """
        # child cell type
        if cellType in getAllCellTypes():
            return self._MetricsAll[cellType]
        # for parent cell types, gather children metrics
        metrics: Optional[set[int]] = getQualityMeasureFromCellType(cellType)
        commonComputedMetricsExists: bool = False
        for cellTypeChild in getChildrenCellTypes(cellType):
            computedMetrics: set[int] = self._MetricsAll[cellTypeChild]
            if computedMetrics is None:
                continue
            commonComputedMetricsExists = True
            metrics = metrics.intersection(computedMetrics)
        return metrics if commonComputedMetricsExists else None

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
        self._outputMesh = self.GetOutputData(outInfoVec, 0)
        assert inData is not None, "Input mesh is undefined."
        assert self._outputMesh is not None, "Ouput pipeline is undefined."

        self._outputMesh.ShallowCopy( inData )
        print(f"nb cells Input mesh {inData.GetNumberOfCells()}")

        # compute cell type counts
        self._computeCellTypeCounts()

        # compute metrics and associated attributes
        self._evaluateMeshQualityAll()

        # compute stats summary
        self._updateStatsSummary()

        # create field data
        self._createFieldDataStatsSummary()

        self._outputMesh.Modified()

        # TODO move calculation in _evaluateMeshQuality

        # cellCounter: CellTypeCounter = CellTypeCounter()
        # cellCounter.SetInputDataObject(inData)
        # cellCounter.Update()
        # cellCounts: CellTypeCounts = cellCounter.GetCellTypeCounts()

        # EL_data = [[],[]]
        # VIE_data =[[],[]]
        # self.EdgesLgth_VertexIncidentEdges(inData, EL_data, VIE_data)

        # facesPtsIdsSet: set[tuple[int]] = set()
        # volume_data: tuple[list[float], list[float]] = [[],[]]
        # jacobian_data: tuple[list[float], list[float]] = [[],[]]
        # aspectRatio_data: tuple[list[float], list[float]] = [[],[]]
        # AnglesBetweenEdges_data: tuple[list[float], list[float]] = [[],[]]
        # HexStretch_data: tuple[list[float], list[float]] = [[],[]]
        # EdgeRatio_data: tuple[list[float], list[float]] = [[],[]]

        # points: vtkPoints = inData.GetPoints()
        # for c in range(inData.GetNumberOfCells()):
        #     cell: vtkCell = inData.GetCell(c)
        #     if cell.GetCellDimension() == 3:
        #         self.cellQuality (cell, volume_data, jacobian_data, HexStretch_data, EdgeRatio_data)
        #         self.CellAspectRatio(cell, aspectRatio_data, (2., 3.))
        #         self.AnglesBetweenEdges(cell, points, facesPtsIdsSet, AnglesBetweenEdges_data)
        return 1

    def _computeCellTypeCounts(self: Self) ->None:
        """Compute cell type counts."""
        filter: CellTypeCounter = CellTypeCounter()
        filter.SetInputDataObject( self._outputMesh )
        filter.Update()
        counts: CellTypeCounts = filter.GetCellTypeCounts()
        assert counts is not None, "CellTypeCounts is undefined"
        self._qualityMetricSummary.setCellTypeCounts(counts)

    def _evaluateMeshQualityAll(self: Self)->None:
        """Compute all mesh quality metrics."""
        for cellType, metrics in self._MetricsAll.items():
            if metrics is None:
                continue
            for metricIndex in metrics:
                self._evaluateMeshQuality(metricIndex, cellType)

    def _evaluateMeshQuality(self: Self,
                             metricIndex: int,
                             cellType: int
                            ) ->None:
        """Compute mesh input quality metric for input cell type.

        Args:
            metricIndex (int): quality metric index
            cellType (int): cell type index
        """
        arrayName: str = getQualityMetricArrayName(metricIndex)
        if arrayName in getAttributesFromDataSet(self._outputMesh, False):
            # metric is already computed (by default computed for all cell types if applicable)
            return
        # compute quality metric
        output: vtkUnstructuredGrid = self._applyMeshQualityFilter(metricIndex, cellType)
        # transfer output cell array to input mesh
        self._transferCellAttribute(output, QUALITY_ARRAY_NAME, arrayName, metricIndex)

    def _applyMeshQualityFilter(self: Self,
                                metric: int,
                                cellType: int
                               ) ->vtkUnstructuredGrid:
        """Apply vtkMeshQuality filter.

        Args:
            metric (int): quality metric index
            cellType (int): cell type

        Returns:
            vtkUnstructuredGrid: _description_
        """
        meshQualityFilter = vtkMeshQuality()
        meshQualityFilter.SetInputDataObject(self._outputMesh)
        if cellType == VTK_TRIANGLE:
            meshQualityFilter.SetTriangleQualityMeasure(metric)
        elif cellType == VTK_QUAD:
            meshQualityFilter.SetQuadQualityMeasure(metric)
        elif cellType == VTK_TETRA:
            meshQualityFilter.SetTetQualityMeasure(metric)
        elif cellType == VTK_PYRAMID:
            meshQualityFilter.SetPyramidQualityMeasure(metric)
        elif cellType == VTK_WEDGE:
            meshQualityFilter.SetWedgeQualityMeasure(metric)
        elif cellType == VTK_HEXAHEDRON:
            meshQualityFilter.SetHexQualityMeasure(metric)
        else:
            print("Cell type is not supported.")
        meshQualityFilter.SaveCellQualityOn()
        meshQualityFilter.Update()
        return meshQualityFilter.GetOutputDataObject(0)

    def _transferCellAttribute(self: Self,
                               serverMesh: vtkUnstructuredGrid,
                               serverAttributeName: str,
                               clientAttributeName: str,
                               qualityMetric: int,
                              ) ->bool:
        """Transfer quality attribute to the client mesh.

        The attribute is renamed with quality metric name. Because a default quality
        metric is computed if an element does not support the desired metric, this
        default metric is replaced by nan values.

        Args:
            serverMesh (vtkUnstructuredGrid): server mesh where Quality metric is
            serverAttributeName (str): name of the attribute in the server mesh
            clientAttributeName (str): name of the attribute in the client mesh
            qualityMetric (int): index of quality metric.

        Returns:
            bool: True if the attribute was successfully transfered, False otherwise
        """
        cellArrays: vtkCellData = serverMesh.GetCellData()
        assert cellArrays is not None, "Cell data from vtkMeshQuality output mesh is undefined."
        array: vtkDataArray = cellArrays.GetArray(serverAttributeName)
        assert array is not None, f"{serverAttributeName} attribute is undefined."
        # rename array
        array.SetName(clientAttributeName)
        # replace irrelevant values
        for cellId in range(serverMesh.GetNumberOfCells()):
            cell: vtkCell = serverMesh.GetCell(cellId)
            cellType: int = cell.GetCellType()
            cellTypeQualityMetrics: set[int] = qualityMetricsFromCellType[cellType]()
            if (qualityMetric > -1) and (qualityMetric not in cellTypeQualityMetrics):
                array.SetTuple1(cellId, np.nan)

        # add array to input mesh
        inputCellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert inputCellArrays is not None, "Cell data from input mesh is undefined."
        inputCellArrays.AddArray(array)
        inputCellArrays.Modified()
        return True

    def _updateStatsSummary(self: Self) ->None:
        """Compute quality metric statistics."""
        # stats for each cell types individually
        for cellType, metrics in self._MetricsAll.items():
            count: int = self._qualityMetricSummary.getCellTypeCountsOfCellType(cellType)
            if (count == 0) or (metrics is None):
                continue
            for metricIndex in metrics:
                self._updateStatsSummaryByCellType(metricIndex, cellType)

        # stats for polygons and polyhedra
        for cellType in (VTK_POLYGON, VTK_POLYHEDRON):
            count: int = self._qualityMetricSummary.getCellTypeCountsOfCellType(cellType)
            # get common computed metrics
            metrics: Optional[set[int]] = self.getComputedMetricsFromCellType(cellType)
            if (count == 0) or (metrics is None):
                continue
            for metricIndex in metrics:
                self._updateStatsSummaryByCellType(metricIndex, cellType)

    def _updateStatsSummaryByCellType(self: Self,
                                      metricIndex: int,
                                      cellType: int
                                     ) ->None:
        """Compute input quality metric statistics for input cell types.

        Args:
            metricIndex (int): quality metric index
            cellType (int): cell type index
        """
        cellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert cellArrays is not None, "Cell data from input mesh is undefined."
        arrayName: str = getQualityMetricArrayName(metricIndex)
        array: vtkDataArray = cellArrays.GetArray(arrayName)
        npArray: npt.NDArray[np.float64] = np.empty(0)
        if array is None:
            return

        npArray: npt.NDArray[np.float64] = vtk_to_numpy(array)
        cellTypes: tuple[int,...] = (cellType,)
        if cellType == VTK_POLYGON:
            cellTypes = getPolygonCellTypes()
        elif cellType == VTK_POLYHEDRON:
            cellTypes = getPolyhedronCellTypes
        cellTypeMask: npt.NDArray[np.bool_] = np.array(
            [self._outputMesh.GetCellType(cellId) in cellTypes for cellId in range(self._outputMesh.GetNumberOfCells())],
            dtype=bool
        )

        mean: float = float(np.nanmean(npArray[cellTypeMask]))
        std: float = float(np.nanstd(npArray[cellTypeMask]))
        mini: float = float(np.nanmin(npArray[cellTypeMask]))
        maxi: float = float(np.nanmax(npArray[cellTypeMask]))
        self._qualityMetricSummary.setStatValueToMetricAndCellType(metricIndex, cellType, StatTypes.MEAN, mean)
        self._qualityMetricSummary.setStatValueToMetricAndCellType(metricIndex, cellType, StatTypes.STD_DEV, std)
        self._qualityMetricSummary.setStatValueToMetricAndCellType(metricIndex, cellType, StatTypes.MIN, mini)
        self._qualityMetricSummary.setStatValueToMetricAndCellType(metricIndex, cellType, StatTypes.MAX, maxi)


    def _createFieldDataStatsSummary(self: Self) ->None:
        """Create field data arrays with quality statistics."""
        fieldData: vtkFieldData = self._outputMesh.GetFieldData()
        assert fieldData is not None, "Field data is undefined."
        for cellType in getAllCellTypesExtended():
            count: int = self._qualityMetricSummary.getCellTypeCountsOfCellType(cellType )
            metrics: Optional[set[int]] = self.getComputedMetricsFromCellType(cellType)
            # create count array
            name = "_".join((vtkCellTypes.GetClassNameFromTypeId(cellType), StatTypes.COUNT.getString()))
            array: vtkIntArray = vtkIntArray()
            array.SetName(name)
            array.SetNumberOfValues(1)
            array.SetNumberOfComponents(1)
            array.SetValue(0, count)
            fieldData.AddArray(array)
            if (count == 0) or (metrics is None):
                continue

            # create metric arrays
            for metricIndex in metrics:
                # one array per statistic number except Count (last one)
                for statType in list(StatTypes)[:-1]:
                    value: int = self._qualityMetricSummary.getStatValueToMetricAndCellType(metricIndex, cellType, statType)
                    name = self._createArrayName(cellType, metricIndex, statType)
                    array: vtkDoubleArray = vtkDoubleArray()
                    array.SetName(name)
                    array.SetNumberOfValues(1)
                    array.SetNumberOfComponents(1)
                    array.SetValue(0, value)
                    fieldData.AddArray(array)
        fieldData.Modified()

    def _createArrayName(self: Self, cellType: int, metricIndex: int, statType: StatTypes) ->str:
        """Concatenate cell type, metric name, and statistic name in array name.

        Args:
            cellType (int): cell type index
            metricIndex (int): quality metric index
            statType (StatTypes): statistic type

        Returns:
            str: array name
        """
        return "_".join((vtkCellTypes.GetClassNameFromTypeId(cellType),
                         getQualityMeasureNameFromIndex(metricIndex).replace(" ", ""),
                         statType.getString()))

    def FaceBarycenter(self: Self,
                       points: vtkPoints,
                       cell: vtkCell
                      ) ->npt.NDArray[np.float64]:
        """Get cell barycenter.

        Args:
            points (vtkPoints): mesh points
            cell (vtkCell): cell

        Returns:
            npt.NDArray[np.float64]: _description_
        """
        cellPtsIds: vtkIdList = cell.GetPointIds()
        nbPts: int = cellPtsIds.GetNumberOfIds()
        center: npt.NDArray[np.float64] = np.zeros(0, dtype=float)
        for i in range (nbPts):
            pt = np.zeros(3, dtype=float)
            points.GetPoint(cellPtsIds.GetId(i), pt)
            center += pt
        return center / nbPts

    def GetNormalVector(self: Self,
                        points: vtkPoints,
                        face: vtkCell
                       ) -> npt.NDArray[np.float64]:
        """Get the normal to the input face.

        .. NOTE:: this method consider the faces as planes.

        Args:
            points (vtkPoints): mesh points
            face (vtkCell): face

        Returns:
            npt.NDArray[np.float64]: coordinates of the normal vector
        """
        assert face.GetCellDimension() == 2, "Cell must be a planar polygon."
        facePtsIds: vtkIdList = face.GetPointIds()
        # need only 3 points among all to get the normal of the face
        ptsCoords: npt.NDArray[np.float64] = np.zeros((3, 3), dtype=float)
        for i in range(3):
            points.GetPoint(facePtsIds.GetId(i), ptsCoords[i])
        return computeNormalFromPoints(ptsCoords[0], ptsCoords[1], ptsCoords[2])

    # TODO: add metric that measures the deviation angle from cell center to face center vector versus face normal vector
    # TODO: add metric that computes the deviation of cell volumes

    # As for OpenFOAM's, you have to dig a little in the source code to figure what they are. 
    # OpenFOAM's skewness is a measure of the deviation of the vector connecting the two cell 
    # centers adjacent to a face and the mid-point of that face. OpenFOAM also checks for orthogonality 
    # which it defines to be the deviation angle between the adjacent cell centers vector and the face normal. 
    def KOrtho(self: Self,
               inData: vtkUnstructuredGrid,
               kOrtho: tuple[list[float], list[float]],
               devAngu: tuple[list[float], list[float]]
              ) ->None:
        """Compute cell orthogonality statistics.

        New cell attributes are created.

        ORTHOGONALITY measures the deviation angle between cell centers and face normal.
        Usefull for flow simulations where cells must be the closest possible from orthogonality.
        Created attributes include minimum, mean, and maxium values from all cell neighbors 
        of a given cell.

        d

        Args:
            inData (vtkUnstructuredGrid): input mesh
            kOrtho (tuple[list[float], list[float]]): output results on cell orthogonality from face normal
            devAngu (tuple[list[float], list[float]]): output results on cell orthogonality
        """
        # copy input data to prevent modifications from GetCellNeighbors method
        copyData: vtkUnstructuredGrid = vtkUnstructuredGrid()
        copyData.ShallowCopy(inData)
        points: vtkPoints = copyData.GetPoints()
        for c in range(copyData.GetNumberOfCells()):
            cell: vtkCell = copyData.GetCell(c)
            if cell.GetCellDimension() == 3:
                paramCenter: npt.NDArray[np.float64] = np.zeros(3)
                subId:int = cell.GetParametricCenter(paramCenter)
                cellCenter: npt.NDArray[np.float64] = np.zeros(3)  # cell barycenter
                weights: npt.NDArray[np.float64] = np.zeros(3)
                cell.EvaluateLocation(subId, paramCenter, cellCenter, weights)

                for f in range(cell.GetNumberOfFaces()):
                    face: vtkCell = cell.GetFace(f)
                    faceCenter: npt.NDArray[np.float64] = self.FaceBarycenter(points, face)  # face barycenter
                    NeighborIds = vtkIdList()
                    copyData.GetCellNeighbors(c, face.GetPointIds(), NeighborIds)
                    for j in range(NeighborIds.GetNumberOfIds()):
                        neighborCellId = NeighborIds.GetId(j)
                        neighborCell: vtkCell = copyData.GetCell(neighborCellId)
                        # if neighbor cell is a polyhedron
                        # to avoid to repeat the same operation on cells already treated
                        if (neighborCell.GetCellDimension() == 3) and (c < neighborCellId):
                                paramCenter2: npt.NDArray[np.float64] = np.zeros(3, dtype=float)
                                subId2: int = neighborCell.GetParametricCenter(paramCenter2)
                                neighborCellCenter: npt.NDArray[np.float64] = np.zeros(3, dtype=float)  # cell barycenter
                                weights2: npt.NDArray[np.float64] = np.zeros(3, dtype=float)
                                neighborCell.EvaluateLocation(subId2, paramCenter2, neighborCellCenter, weights2)

                                # deviation angle between cell centers vector and face normal
                                cb: npt.NDArray[np.float64] = cellCenter - neighborCellCenter
                                ba: npt.NDArray[np.float64] = self.GetNormalVector(points, face)
                                devAngu[0].append(computeAngleFromVectors(cb, ba))

                                # deviation angle between cell centers vector and face to cell center vector
                                ba = faceCenter - cellCenter
                                kOrtho[0].append(computeAngleFromVectors(ba, -cb))

    # TODO: still usefull ?
    def CellsNeighborsMatrix(self: Self,
                             inData: vtkUnstructuredGrid
                            ) -> tuple[list[int], list[int]]:
        """Compute cell neighbors maxtrix.

        Args:
            inData (vtkUnstructuredGrid): input mesh

        Returns:
            tuple[list[int], list[int]]: output matrix
        """
        rowInd: list[int]= []
        colInd: list[int] = []
        # copy input data to prevent modifications from GetCellNeighbors method
        copyData: vtkUnstructuredGrid = vtkUnstructuredGrid()
        copyData.ShallowCopy(inData)
        for c in range(inData.GetNumberOfCells()):
            cell: vtkCell= inData.GetCell(c)
            if cell.GetCellDimension() != 3:
                continue

            for f in range(cell.GetNumberOfFaces()):
                cellIds = vtkIdList()
                copyData.GetCellNeighbors(c, cell.GetFace(f).GetPointIds(), cellIds)
                for j in range(cellIds.GetNumberOfIds()):
                    cellId: int = cellIds.GetId(j)
                    # to avoid to repeat the same operation
                    if (copyData.GetCell(cellId).GetCellDimension() == 3) and (c < cellIds.GetId(j)):
                            rowInd.append(cellId)
                            colInd.append(c)
        return rowInd, colInd

    def EdgesLgth_VertexIncidentEdges(self: Self,
                                      inData: vtkUnstructuredGrid,
                                      EL_data: tuple[list[float], list[float]],
                                      VIE_data: tuple[list[float], list[float]],
                                      EL_threshold: tuple[float, float] = (-np.inf, np.inf)
                                     ) ->None:
        """Compute edge length and vertex incident edge number.

        Args:
            inData (vtkUnstructuredGrid): input mesh
            EL_data (tuple[list[float], list[float]]): edge length outputs
            VIE_data (tuple[list[float], list[float]]): vertex incident edge count outputs
            EL_threshold (tuple[float, float], optional): edge length threshold.

                Defaults to (-np.inf, np.inf).
        """
        extractEdges = vtkExtractEdges()
        extractEdges.SetInputData(inData)
        extractEdges.Update()
        polyData: vtkPolyData = extractEdges.GetOutput()
        VIE_list: list[float] = [0.] * inData.GetNumberOfPoints()

        for edg in range(polyData.GetNumberOfCells()):
            if polyData.GetCell(edg).GetCellDimension() == 1:
                # edges length
                length2: float = polyData.GetCell(edg).GetLength2()
                result: float = np.sqrt(length2)
                if EL_threshold[0] <= result <= EL_threshold[1]:
                    EL_data[0].append(result)
                else:
                    EL_data[1].append(result)

                # VertexIncidentEdges
                edgesPointIds: vtkIdList = polyData.GetCell(edg).GetPointIds()
                for i in range(edgesPointIds.GetNumberOfIds()):
                    VIE_list[edgesPointIds.GetId(i)] += 1

            VIE_data[0] = VIE_list

    def AnglesBetweenEdges(self: Self,
                           cell: vtkCell,
                           points: vtkPoints,
                           facesPtsIdsSet: set[tuple[int]],
                           listData: tuple[list[float], list[float]]
                          ) ->None:
        """Get angles between all edges of input cell.

        Args:
            cell (vtkCell): input cell
            points (vtkPoints): mesh points
            facesPtsIdsSet (set[tuple[int]]): output set of face vertex ids. Provided set should be empty.
            listData (tuple[list[float], list[float]]): output results

        Raises:
            ValueError: Face types
        """
        assert len(facesPtsIdsSet) == 0, "facesPtsIdsSet is not empty."
        for f in range(cell.GetNumberOfFaces()):
            cellface: vtkPolygon = cell.GetFace(f)
            facePtsIds: vtkIdList = cellface.GetPointIds()
            facePtsIdsTuple: tuple[int, ...] = tuple([facePtsIds.GetId(i) for i in range(facePtsIds.GetNumberOfIds())].sort())
            if facePtsIdsTuple not in facesPtsIdsSet:
                # get face points
                nbPts: int = facePtsIds.GetNumberOfIds()
                ptsCoords: npt.NDArray[np.float64] = np.zeros((nbPts, 3), dtype=float)
                for p in range(nbPts):
                    points.GetPoint(facePtsIds.GetId(p), ptsCoords[p])
                # compute edge angles
                if nbPts == 3:
                    listData[0].append(computeAngleFromPoints(ptsCoords[0], ptsCoords[1], ptsCoords[2]))
                    listData[0].append(computeAngleFromPoints(ptsCoords[1], ptsCoords[0], ptsCoords[2]))
                    listData[0].append(computeAngleFromPoints(ptsCoords[0], ptsCoords[2], ptsCoords[1]))
                elif nbPts == 4:
                    listData[0].append(computeAngleFromPoints(ptsCoords[3], ptsCoords[0], ptsCoords[1]))
                    listData[0].append(computeAngleFromPoints(ptsCoords[0], ptsCoords[1], ptsCoords[2]))
                    listData[0].append(computeAngleFromPoints(ptsCoords[1], ptsCoords[2], ptsCoords[3]))
                    listData[0].append(computeAngleFromPoints(ptsCoords[2], ptsCoords[3], ptsCoords[0]))
                else:
                    raise TypeError("Faces must be triangles or quads. Other types are currently not managed.")

                facesPtsIdsSet.add(facePtsIdsTuple)

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

    def cellQuality (self: Self,
                     cell: vtkCell,
                     volume: tuple[list[float], list[float]],
                     jacobian: tuple[list[float], list[float]],
                     hexStretch: tuple[list[float], list[float]],
                     edgeRatio: tuple[list[float], list[float]],
                     J_threshold: tuple[float, float] = (-np.inf, np.inf)
                    ) ->None:
        """Compute cell quality.

        Args:
            cell (vtkCell): cell
            volume (tuple[list[float], list[float]]): output volume results
            jacobian (tuple[list[float], list[float]]): output Jacobian results
            hexStretch (tuple[list[float], list[float]]): output hexahedron stretching results
            edgeRatio (tuple[list[float], list[float]]): output edge ratio results
            J_threshold (tuple[float, float], optional): Jacobian threshold.

                Defaults to (-np.inf, np.inf).
        """
        cellType: int = cell.GetCellType()
        vol: float
        edgeRatioVal: float
        jacob: float
        if cellType == VTK_TETRA :
            vol = self._meshQuality.TetVolume(cell)
            edgeRatioVal = self._meshQuality.TetEdgeRatio(cell)
            jacob = self._meshQuality.TetScaledJacobian(cell)
        elif cellType == VTK_HEXAHEDRON:
            vol = self._meshQuality.HexVolume(cell)
            edgeRatioVal = self._meshQuality.HexEdgeRatio(cell)
            jacob = self._meshQuality.HexScaledJacobian(cell)
            hexStretch[0].append(self._meshQuality.HexStretch(cell))
        elif cellType == VTK_WEDGE :
            vol = self._meshQuality.WedgeVolume(cell)
            edgeRatioVal = self._meshQuality.WedgeEdgeRatio(cell)
            jacob = self._meshQuality.WedgeScaledJacobian(cell)
        elif cellType == VTK_PYRAMID:
            vol = self._meshQuality.PyramidVolume(cell)
            lenghtList =[]
            for i in range(cell.GetNumberOfEdges ()):
                lenght2 = cell.GetEdge(i).GetLength2 ()
                lenghtList.append(np.sqrt(lenght2))
            edgeRatioVal = max(lenghtList) / min(lenghtList)
            jacob = self._meshQuality.PyramidScaledJacobian(cell)
        else:
            vol = np.nan
            edgeRatioVal = np.nan
            jacob = np.nan
            print(f"Cell type {vtkCellTypes.GetClassNameFromTypeId(cellType)} is currently not supported.")

        volume[0].append(vol)
        edgeRatio[0].append(edgeRatioVal)
        if J_threshold[0] <= jacob <= J_threshold[1]:
            jacobian[0].append(jacob)
        else:
            jacobian[1].append(jacob)

    def CellAspectRatio(self: Self,
                        cell: vtkCell,
                        listData: tuple[list[float], list[float]],
                        threshold: tuple[float, float] = (-np.inf, np.inf)
                       ) ->None:
        """Compute cell aspect ratio.

        Args:
            cell (vtkCell): cell
            listData (tuple[list[float], list[float]]): output results
            threshold (tuple[float, float], optional): aspect ratio threshold.

                Defaults to (-np.inf, np.inf).
        """
        cellType: int = cell.GetCellType()
        if cellType == VTK_TETRA :
            if threshold is None:
                listData[0].append(self._meshQuality.TetAspectRatio(cell))
            else:
                if threshold[0] <= self._meshQuality.TetAspectRatio(cell) <= threshold[1]:
                    listData[0].append(self._meshQuality.TetAspectRatio(cell))
                else:
                    listData[1].append(self._meshQuality.TetAspectRatio(cell))

        else :
            listSimplexPts = vtkPoints()
            idList = vtkIdList()
            cell.Triangulate(1, idList,listSimplexPts)

            simplexAspectRatio: list[float] = []
            index: int = 0
            while index != listSimplexPts.GetNumberOfPoints() :
                tetra: vtkTetra = vtkTetra()
                tetraPts: vtkPoints = tetra.GetPoints()
                for i in range(4):
                    tetraPts.SetPoint(i,listSimplexPts.GetPoint(index))
                    tetraPts.Modified()
                    index += 1
                simplexAspectRatio.append(self._meshQuality.TetAspectRatio(tetra))

            if threshold is None:
                listData[0].append(max(simplexAspectRatio))
            else:
                if threshold[0] <= max(simplexAspectRatio) <= threshold[1]:
                    listData[0].append(max(simplexAspectRatio))
                else:
                    listData[1].append(max(simplexAspectRatio))

            simplexAspectRatio.clear()
