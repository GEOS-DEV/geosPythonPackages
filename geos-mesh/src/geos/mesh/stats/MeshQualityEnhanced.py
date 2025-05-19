# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
import numpy.typing as npt
from typing import Optional, cast
from typing_extensions import Self
from vtkmodules.vtkFiltersCore import vtkExtractEdges
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
    vtkIdTypeArray,
    vtkMath,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkPolyData,
    vtkCellData,
    vtkPointData,
    vtkFieldData,
    vtkCell,
    vtkCell3D,
    vtkTetra,
    vtkCellTypes,
    vtkPolygon,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON
)
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from geos.mesh.stats.CellTypeCounterEnhanced import CellTypeCounterEnhanced
from geos.mesh.model.CellTypeCounts import CellTypeCounts
from geos.mesh.model.QualityMetricSummary import QualityMetricSummary, StatTypes
from geos.mesh.utils.helpers import getArraysFromDataSet
from geos.mesh.processing.meshQualityMetricHelpers import (
    getQualityMeasureNameFromIndex,
    getQualityMetricFromIndex,
    cellQualityMetricsFromCellType,
    VtkCellQualityMetricEnum,
    CellQualityMetricAdditionalEnum,
    QualityMetricOtherEnum,
    getAllCellTypesExtended,
    getAllCellTypes,
    getPolygonCellTypes,
    getPolyhedronCellTypes,
    getCellQualityMeasureFromCellType,
    getChildrenCellTypes,
)

import geos.utils.geometryFunctions as geom

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
    return QUALITY_ARRAY_NAME + "_" + "".join(getQualityMeasureNameFromIndex(metric).split(" "))

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
        self._otherMetrics: Optional[set[QualityMetricOtherEnum]] = None
        # for each cell, save cell type for later use
        self._cellTypeMask: dict[int, npt.NDArray[np.bool_]] = {}

        # static members that can be loaded once to save computational times
        self._allCellTypesExtended: tuple[int,...] = getAllCellTypesExtended()
        self._allCellTypes: tuple[int,...] = getAllCellTypes()

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

    def GetQualityMetricSummary(self :Self)-> QualityMetricSummary:
        """Get QualityMetricSummary object.

        Returns:
            QualityMetricSummary: QualityMetricSummary object
        """
        return self._qualityMetricSummary

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

    def SetCellQualityMetrics(self :Self,
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

    def SetOtherMeshQualityMetrics(self: Self, metrics: set[QualityMetricOtherEnum]) ->None:
        """Set additional metrics unrelated to cell types.

        Args:
            metrics (set[QualityMetricOtherEnum]): set of QualityMetricOtherEnum
        """
        if len(metrics) > 0:
            self._otherMetrics = metrics
        else:
            self._otherMetrics = None

    def getComputedMetricsFromCellType(self: Self, cellType: int) -> Optional[set[int]]:
        """Get the set of metrics computed for input cell type.

        Args:
            cellType (int): cell type index

        Returns:
            Optional[set[int]]: set of computed quality metrics
        """
        # child cell type
        if cellType in self._allCellTypes:
            return self._MetricsAll[cellType]
        # for parent cell types, gather children metrics
        metrics: Optional[set[int]] = getCellQualityMeasureFromCellType(cellType)
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

        # compute cell type counts
        self._computeCellTypeCounts()

        # compute metrics and associated attributes
        self._evaluateMeshQualityAll()

        # compute stats summary
        self._updateStatsSummary()

        # create field data
        self._createFieldDataStatsSummary()

        self._outputMesh.Modified()
        return 1

    def _computeCellTypeCounts(self: Self) ->None:
        """Compute cell type counts."""
        filter: CellTypeCounterEnhanced = CellTypeCounterEnhanced()
        filter.SetInputDataObject( self._outputMesh )
        filter.Update()
        counts: CellTypeCounts = filter.GetCellTypeCountsObject()
        assert counts is not None, "CellTypeCounts is undefined"
        self._qualityMetricSummary.setCellTypeCounts(counts)

    def _evaluateMeshQualityAll(self: Self)->None:
        """Compute all mesh quality metrics."""
        for cellType, metrics in self._MetricsAll.items():
            if metrics is None:
                continue
            for metricIndex in metrics:
                self._evaluateCellQuality(metricIndex, cellType)

        if self._otherMetrics is not None:
            if QualityMetricOtherEnum.INCIDENT_VERTEX_COUNT.getMetricIndex() in self._otherMetrics:
                self._countVertexIncidentEdges()
            else:
                # TODO: add other metrics
                print("")

    def _evaluateCellQuality(self: Self,
                             metricIndex: int,
                             cellType: int
                            ) ->None:
        """Compute mesh input quality metric for input cell type.

        Args:
            metricIndex (int): quality metric index
            cellType (int): cell type index
        """
        arrayName: str = getQualityMetricArrayName(metricIndex)
        if arrayName in getArraysFromDataSet(self._outputMesh, False):
            # metric is already computed (by default computed for all cell types if applicable)
            return

        # get the list of cell types the metric applies to and check if these cell types are present
        metric = getQualityMetricFromIndex(metricIndex)
        cellTypes: Optional[set[int]] = metric.getApplicableCellTypes()
        nbCells: int = 0
        for cellType in cellTypes:
            nbCells += self._qualityMetricSummary.getCellTypeCountsOfCellType(cellType)
        if nbCells == 0:
            return

        # compute quality metric
        output: vtkUnstructuredGrid | None = None
        if (metricIndex == VtkCellQualityMetricEnum.SQUISH_INDEX.metricIndex):
            # redefined Squish index calculation to be computed for any type of polyhedron
            self._computeSquishIndex()
        elif (metricIndex in (CellQualityMetricAdditionalEnum.MAXIMUM_ASPECT_RATIO.metricIndex, )):
            # extended metric for any type of cells (other than tetra) from tetra metrics
            self._computeAdditionalMetrics(metricIndex)
        else:
            output = self._applyMeshQualityFilter(metricIndex, cellType)
            assert output is not None, "Output mesh from mesh quality calculation is undefined."
            # transfer output cell array to input mesh
            # TODO: to test if Shallow copy of vtkMeshQualityFilter result and rename "Quality" array is more efficient than what is done here
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

    def _computeAdditionalMetrics(self: Self, metricIndex: int) -> None:
        """Compute additional metrics from metrics defined for tetrahedron.

        Output is an cell array in output mesh.

        Args:
            metricIndex (int): metric index
        """
        metric = getQualityMetricFromIndex(metricIndex)
        assert metric is not None, f"Additional cell quality metric index {metricIndex} is undefined."
        # output array
        name: str = getQualityMetricArrayName(metric.getMetricIndex())
        newArray: vtkDoubleArray = vtkDoubleArray()
        newArray.SetName(name)
        newArray.SetNumberOfValues(self._outputMesh.GetNumberOfCells())
        newArray.SetNumberOfComponents(1)
        for i in range(self._outputMesh.GetNumberOfCells()):
            cell: vtkCell = self._outputMesh.GetCell(i)
            val: float = self._computeAdditionalMetricsCell(metricIndex, cell)
            newArray.InsertNextValue(val)
        # add array
        cellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert cellArrays is not None, "Cell data from output mesh is undefined."
        cellArrays.AddArray(newArray)
        cellArrays.Modified()
        self._outputMesh.Modified()
        return

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
        self._replaceIrrelevantValues(array, serverMesh, qualityMetric)

        # add array to input mesh
        inputCellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert inputCellArrays is not None, "Cell data from input mesh is undefined."
        inputCellArrays.AddArray(array)
        inputCellArrays.Modified()
        return True

    def _replaceIrrelevantValues(self: Self,
                                 array: vtkDataArray,
                                 mesh: vtkUnstructuredGrid,
                                 qualityMetric: int
                                ) ->None:
        """Replace irrelevant values.

        Values are irrelevant when a quality metric is computed 
        whereas input metric does not applies to the cell type.

        Args:
            array (vtkDataArray): array to update
            mesh (vtkUnstructuredGrid): mesh
            qualityMetric (int): quality metric index
        """
        for cellId in range(mesh.GetNumberOfCells()):
            cell: vtkCell = mesh.GetCell(cellId)
            cellType: int = cell.GetCellType()
            cellTypeQualityMetrics: set[int] = cellQualityMetricsFromCellType[cellType]
            if (qualityMetric > -1) and (qualityMetric not in cellTypeQualityMetrics):
                array.SetTuple1(cellId, np.nan)

    def _updateStatsSummary(self: Self) ->None:
        """Compute quality metric statistics."""
        # init cell type masks
        self._initCellTypeMasks()
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
        if array is None:
            return
        npArray: npt.NDArray[np.float64] = vtk_to_numpy(array)
        cellTypeMask: npt.NDArray[np.bool_] = self._cellTypeMask[cellType]

        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(metricIndex, cellType, StatTypes.MEAN, StatTypes.MEAN.compute(npArray[cellTypeMask]))
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(metricIndex, cellType, StatTypes.STD_DEV, StatTypes.STD_DEV.compute(npArray[cellTypeMask]))
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(metricIndex, cellType, StatTypes.MIN, StatTypes.MIN.compute(npArray[cellTypeMask]))
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(metricIndex, cellType, StatTypes.MAX, StatTypes.MAX.compute(npArray[cellTypeMask]))
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(metricIndex, cellType, StatTypes.COUNT, StatTypes.COUNT.compute(npArray[cellTypeMask]))

    def _initCellTypeMasks(self: Self) ->None:
        """Init _cellTypeMask variable."""
        # compute cell type masks
        self._cellTypeMask = {
            cellType:np.zeros(self._outputMesh.GetNumberOfCells(), dtype=bool) for cellType in self._allCellTypesExtended
        }
        polyhedronCellTypes: tuple[int,...] = getPolyhedronCellTypes()
        polygonCellTypes: tuple[int,...] = getPolygonCellTypes()
        for cellId in range(self._outputMesh.GetNumberOfCells()):
            for cellType in self._allCellTypesExtended:
                cellTypes: tuple[int,...] = (cellType,)
                if cellType == VTK_POLYGON:
                    cellTypes = polygonCellTypes
                elif cellType == VTK_POLYHEDRON:
                    cellTypes = polyhedronCellTypes
                self._cellTypeMask[cellType][cellId] = self._outputMesh.GetCellType(cellId) in cellTypes

    def _createFieldDataStatsSummary(self: Self) ->None:
        """Create field data arrays with quality statistics."""
        fieldData: vtkFieldData = self._outputMesh.GetFieldData()
        assert fieldData is not None, "Field data is undefined."
        for cellType in self._allCellTypesExtended:
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
                    value: int = self._qualityMetricSummary.getCellStatValueFromStatMetricAndCellType(metricIndex, cellType, statType)
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

    def _computeAdditionalMetricsCell(self: Self, metricIndex: int, cell: vtkCell) -> float:
        """Compute additional metrics from metrics defined for tetrahedron for a cell.

        Args:
            metricIndex (int): metric index
            cell (vtkCell): cell

        Returns:
            float: outout value
        """
        meshQualityFilter: vtkMeshQuality = vtkMeshQuality()
        # triangulate cell faces
        listSimplexPts = vtkPoints()
        idList = vtkIdList()
        cell.Triangulate(1, idList,listSimplexPts)

        simplexAspectRatio: list[float] = []
        index: int = 0
        while index != listSimplexPts.GetNumberOfPoints():
            # create tetra
            tetra: vtkTetra = vtkTetra()
            tetraPts: vtkPoints = tetra.GetPoints()
            for i in range(4):
                tetraPts.SetPoint(i, listSimplexPts.GetPoint(index))
                tetraPts.Modified()
                index += 1
            # compute aspect ratio of tetra
            if metricIndex == CellQualityMetricAdditionalEnum.MAXIMUM_ASPECT_RATIO.getMetricIndex():
                simplexAspectRatio.append(meshQualityFilter.TetAspectRatio(tetra))
            else:
                # metric is not supported
                simplexAspectRatio.append(np.nan)
        if any(np.isfinite(simplexAspectRatio)):
            return np.nanmax(simplexAspectRatio)
        return np.nan

    def _countVertexIncidentEdges(self: Self) ->None:
        """Compute edge length and vertex incident edge number."""
        metric: QualityMetricOtherEnum = QualityMetricOtherEnum.INCIDENT_VERTEX_COUNT
        # edge are extracted as "cell" of dimension 1
        extractEdges = vtkExtractEdges()
        extractEdges.SetInputData(self._outputMesh)
        extractEdges.Update()
        polyData: vtkPolyData = extractEdges.GetOutput()
        incidentCounts: npt.NDArray[np.int64] = np.zeros(self._outputMesh.GetNumberOfPoints(), dtype=int)
        for edg in range(polyData.GetNumberOfCells()):
            if polyData.GetCell(edg).GetCellDimension() != 1:
                # not an edge
                continue

            edgesPointIds: vtkIdList = polyData.GetCell(edg).GetPointIds()
            for i in range(edgesPointIds.GetNumberOfIds()):
                incidentCounts[edgesPointIds.GetId(i)] += 1

        # create point attribute
        pointData: vtkPointData = self._outputMesh.GetPointData()
        assert pointData is not None, "Point data is undefined."
        array: vtkIntArray = numpy_to_vtk(incidentCounts, deep=1)
        metricName: str = metric.getMetricName().replace(" ", "")
        name: str = QUALITY_ARRAY_NAME + "_" + metricName
        array.SetName(name)
        pointData.AddArray(array)
        pointData.Modified()

        fieldData: vtkPointData = self._outputMesh.GetFieldData()
        assert fieldData is not None, "Field data is undefined."
        for statType in list(StatTypes):
            name = metricName + "_" +  statType.getString()
            val: float | int = statType.compute(incidentCounts)
            # add values to quality summary stats
            self._qualityMetricSummary.setOtherStatValueFromMetric(metric.getMetricIndex(), statType, val)
            array: vtkDoubleArray = vtkDoubleArray()
            array.SetName(name)
            array.SetNumberOfValues(1)
            array.SetNumberOfComponents(1)
            array.SetValue(0, val)
            fieldData.AddArray(array)
        fieldData.Modified()
        self._outputMesh.Modified()

    def _computeSquishIndex(self: Self) ->None:
        """Compute Squish index for all element type.

        Squish index is the maximum value of the cosine of the deviation angle between
        cell center to face center vector and face normal vector.

        Output is a new cell array.
        """
        # output array
        name: str = getQualityMetricArrayName(VtkCellQualityMetricEnum.SQUISH_INDEX.getMetricIndex())
        newArray: vtkDoubleArray = vtkDoubleArray()
        newArray.SetName(name)
        newArray.SetNumberOfValues(self._outputMesh.GetNumberOfCells())
        newArray.SetNumberOfComponents(1)
        # copy input data to prevent modifications from GetCellNeighbors method
        copyData: vtkUnstructuredGrid = vtkUnstructuredGrid()
        copyData.ShallowCopy(self._outputMesh)
        points: vtkPoints = copyData.GetPoints()
        for c in range(copyData.GetNumberOfCells()):
            cell: vtkCell = copyData.GetCell(c)
            # applies only to polyhedra
            if cell.GetCellDimension() != 3:
                continue
            # get cell center
            cellCenter: npt.NDArray[np.float64] = self._getCellCenter(cell) #self.CellBarycenter(points, cell) #self._getCellCenter(cell)
            # compute deviation cosine for each face
            squishIndex: npt.NDArray[np.float64] = np.full(cell.GetNumberOfFaces(), np.nan)
            for f in range(cell.GetNumberOfFaces()):
                face: vtkCell = cell.GetFace(f)
                # get face center
                # TODO: use _getCellCenter
                ptsIds: vtkIdTypeArray = vtkIdTypeArray()
                ptsIds.Allocate(face.GetNumberOfPoints())
                ptsIdsList: vtkIdList = face.GetPointIds()
                for i in range(ptsIdsList.GetNumberOfIds()):
                    ptsIds.InsertNextValue(ptsIdsList.GetId(i))
                faceCenter: npt.NDArray[np.float64] = self._getCellCenter(face, ptsIds, points) #self.CellBarycenter(points, face)
                faceNormal: npt.NDArray[np.float64] = self._getNormalVector(points, face)

                vec: npt.NDArray[np.float64] = cellCenter - faceCenter
                angle: float = vtkMath.AngleBetweenVectors(vec, faceNormal)
                squishIndex[f] = np.sin(angle)
                #cos: float = geom.computeCosineFromVectors(vec, faceNormal)
                # cos yields 1 or -1 if vectors are parallel (best case), 0 if they are orthogonal (worst case)
                #squishIndex[f] = 1. - cos*cos
            newArray.InsertValue(c, np.nanmax(squishIndex))

        # add array
        cellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert cellArrays is not None, "Cell data from output mesh is undefined."
        cellArrays.AddArray(newArray)
        cellArrays.Modified()
        self._outputMesh.Modified()

    def _getCellCenter(self: Self,
                       cell: vtkCell,
                       ptsIds: Optional[vtkIdTypeArray] = None,
                       points: Optional[vtkPoints] = None
                      ) -> npt.NDArray[np.float64]:
        """Compute cell center.

        Args:
            cell (vtkCell): input cell
            ptsIds (vtkIdTypeArray | None): cell point ids. Defaults to None.
            points (vtkPoints | None): mesh point coordinates. Defaults to None.

        Returns:
            npt.NDArray[np.float64]: output cell center
        """
        cellCenter: npt.NDArray[np.float64] = np.zeros(3)
        if cell.GetCellDimension() == 2:
            # polygonal cell
            assert ptsIds is not None, "Point ids are required for computing polygonal cell center."
            assert points is not None, "Points are required for computing polygonal cell center."
            cell.GetPointIds()
            vtkPolygon.ComputeCentroid(ptsIds, points, cellCenter)
        elif cell.GetCellDimension() == 3:
            # volume cell
            cell3D: vtkCell3D = cast(vtkCell3D, cell)
            cell3D.GetCentroid(cellCenter)
        else:
            raise TypeError("Cell must be polygonal or volumic.")
        # paramCenter: npt.NDArray[np.float64] = np.zeros(3)
        # subId: int = cell.GetParametricCenter(paramCenter)
        # weights: npt.NDArray[np.float64] = np.zeros(3)
        # cell.EvaluateLocation(subId, paramCenter, cellCenter, weights)
        return cellCenter

    def CellBarycenter(self: Self,
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
        center: npt.NDArray[np.float64] = np.zeros(3, dtype=float)
        for i in range (nbPts):
            pt = np.zeros(3, dtype=float)
            points.GetPoint(cellPtsIds.GetId(i), pt)
            center += pt
        return center / nbPts

    def _getNormalVector(self: Self,
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
        # need only 3 points among all to get the normal of the face since we suppose face is a plane
        ptsCoords: npt.NDArray[np.float64] = np.zeros((3, 3), dtype=float)
        for i in range(3):
            points.GetPoint(facePtsIds.GetId(i), ptsCoords[i])
        return geom.computeNormalFromPoints(ptsCoords[0], ptsCoords[1], ptsCoords[2])

    # TODO: add metric that measures the deviation angle from cell center to face center vector versus face normal vector
    # TODO: add metric that computes the deviation of cell volumes versus face normal vector

    # As for OpenFOAM's, you have to dig a little in the source code to figure what they are. 
    # OpenFOAM's skewness is a measure of the deviation of the vector connecting the two cell 
    # centers adjacent to a face and the mid-point of that face. OpenFOAM also checks for orthogonality 
    # which it defines to be the deviation angle between the adjacent cell centers vector and the face normal. 
    # def KOrtho(self: Self,
    #            inData: vtkUnstructuredGrid,
    #            kOrtho: tuple[list[float], list[float]],
    #            devAngu: tuple[list[float], list[float]]
    #           ) ->None:
    #     """Compute cell orthogonality statistics.

    #     New cell attributes are created.

    #     ORTHOGONALITY measures the deviation angle between cell centers and face normal = Squish index
    #     Usefull for flow simulations where cells must be the closest possible from orthogonality.
    #     Created attributes include minimum, mean, and maxium values from all cell neighbors 
    #     of a given cell.

    #     Args:
    #         inData (vtkUnstructuredGrid): input mesh
    #         kOrtho (tuple[list[float], list[float]]): output results on cell orthogonality from face normal
    #         devAngu (tuple[list[float], list[float]]): output results on cell orthogonality
    #     """
    #     # copy input data to prevent modifications from GetCellNeighbors method
    #     copyData: vtkUnstructuredGrid = vtkUnstructuredGrid()
    #     copyData.ShallowCopy(inData)
    #     points: vtkPoints = copyData.GetPoints()
    #     for c in range(copyData.GetNumberOfCells()):
    #         cell: vtkCell = copyData.GetCell(c)
    #         if cell.GetCellDimension() == 3:
    #             paramCenter: npt.NDArray[np.float64] = np.zeros(3)
    #             subId:int = cell.GetParametricCenter(paramCenter)
    #             cellCenter: npt.NDArray[np.float64] = np.zeros(3)  # cell barycenter
    #             weights: npt.NDArray[np.float64] = np.zeros(3)
    #             cell.EvaluateLocation(subId, paramCenter, cellCenter, weights)

    #             for f in range(cell.GetNumberOfFaces()):
    #                 face: vtkCell = cell.GetFace(f)
    #                 faceCenter: npt.NDArray[np.float64] = self.CellBarycenter(points, face)  # face barycenter
    #                 NeighborIds = vtkIdList()
    #                 copyData.GetCellNeighbors(c, face.GetPointIds(), NeighborIds)
    #                 for j in range(NeighborIds.GetNumberOfIds()):
    #                     neighborCellId = NeighborIds.GetId(j)
    #                     neighborCell: vtkCell = copyData.GetCell(neighborCellId)
    #                     # if neighbor cell is a polyhedron
    #                     # to avoid to repeat the same operation on cells already treated
    #                     if (neighborCell.GetCellDimension() == 3) and (c < neighborCellId):
    #                             paramCenter2: npt.NDArray[np.float64] = np.zeros(3, dtype=float)
    #                             subId2: int = neighborCell.GetParametricCenter(paramCenter2)
    #                             neighborCellCenter: npt.NDArray[np.float64] = np.zeros(3, dtype=float)  # cell barycenter
    #                             weights2: npt.NDArray[np.float64] = np.zeros(3, dtype=float)
    #                             neighborCell.EvaluateLocation(subId2, paramCenter2, neighborCellCenter, weights2)

    #                             # deviation angle between cell centers vector and face normal
    #                             cb: npt.NDArray[np.float64] = cellCenter - neighborCellCenter
    #                             ba: npt.NDArray[np.float64] = self.GetNormalVector(points, face)
    #                             devAngu[0].append(geom.computeAngleFromVectors(cb, ba))

    #                             # deviation angle between cell centers vector and face to cell center vector
    #                             ba = faceCenter - cellCenter
    #                             kOrtho[0].append(geom.computeAngleFromVectors(ba, -cb))

    
    # def AnglesBetweenEdges(self: Self,
    #                        cell: vtkCell,
    #                        points: vtkPoints,
    #                        facesPtsIdsSet: set[tuple[int]],
    #                        listData: tuple[list[float], list[float]]
    #                       ) ->None:
    #     """Get angles between all edges of input cell.

    #     Args:
    #         cell (vtkCell): input cell
    #         points (vtkPoints): mesh points
    #         facesPtsIdsSet (set[tuple[int]]): output set of face vertex ids. Provided set should be empty.
    #         listData (tuple[list[float], list[float]]): output results

    #     Raises:
    #         ValueError: Face types
    #     """
    #     assert len(facesPtsIdsSet) == 0, "facesPtsIdsSet is not empty."
    #     for f in range(cell.GetNumberOfFaces()):
    #         cellface: vtkPolygon = cell.GetFace(f)
    #         facePtsIds: vtkIdList = cellface.GetPointIds()
    #         facePtsIdsTuple: tuple[int, ...] = tuple([facePtsIds.GetId(i) for i in range(facePtsIds.GetNumberOfIds())].sort())
    #         if facePtsIdsTuple not in facesPtsIdsSet:
    #             # get face points
    #             nbPts: int = facePtsIds.GetNumberOfIds()
    #             ptsCoords: npt.NDArray[np.float64] = np.zeros((nbPts, 3), dtype=float)
    #             for p in range(nbPts):
    #                 points.GetPoint(facePtsIds.GetId(p), ptsCoords[p])
    #             # compute edge angles
    #             if nbPts == 3:
    #                 listData[0].append(geom.computeAngleFromPoints(ptsCoords[0], ptsCoords[1], ptsCoords[2]))
    #                 listData[0].append(geom.computeAngleFromPoints(ptsCoords[1], ptsCoords[0], ptsCoords[2]))
    #                 listData[0].append(geom.computeAngleFromPoints(ptsCoords[0], ptsCoords[2], ptsCoords[1]))
    #             elif nbPts == 4:
    #                 listData[0].append(geom.computeAngleFromPoints(ptsCoords[3], ptsCoords[0], ptsCoords[1]))
    #                 listData[0].append(geom.computeAngleFromPoints(ptsCoords[0], ptsCoords[1], ptsCoords[2]))
    #                 listData[0].append(geom.computeAngleFromPoints(ptsCoords[1], ptsCoords[2], ptsCoords[3]))
    #                 listData[0].append(geom.computeAngleFromPoints(ptsCoords[2], ptsCoords[3], ptsCoords[0]))
    #             else:
    #                 raise TypeError("Faces must be triangles or quads. Other types are currently not managed.")

    #             facesPtsIdsSet.add(facePtsIdsTuple)

    # def _computeNumberOfEdges(self :Self, mesh: vtkUnstructuredGrid) ->int:
    #     """Compute the number of edges of the mesh.

    #     Args:
    #         mesh (vtkUnstructuredGrid): input mesh

    #     Returns:
    #         int: number of edges
    #     """
    #     edges: vtkFeatureEdges = vtkFeatureEdges()
    #     edges.BoundaryEdgesOn()
    #     edges.ManifoldEdgesOn()
    #     edges.FeatureEdgesOff()
    #     edges.NonManifoldEdgesOff()
    #     edges.SetInputDataObject(mesh)
    #     edges.Update()
    #     return edges.GetOutput().GetNumberOfCells()

    # def cellQuality (self: Self,
    #                  cell: vtkCell,
    #                  volume: tuple[list[float], list[float]],
    #                  jacobian: tuple[list[float], list[float]],
    #                  hexStretch: tuple[list[float], list[float]],
    #                  edgeRatio: tuple[list[float], list[float]],
    #                  J_threshold: tuple[float, float] = (-np.inf, np.inf)
    #                 ) ->None:
    #     """Compute cell quality.

    #     Args:
    #         cell (vtkCell): cell
    #         volume (tuple[list[float], list[float]]): output volume results
    #         jacobian (tuple[list[float], list[float]]): output Jacobian results
    #         hexStretch (tuple[list[float], list[float]]): output hexahedron stretching results
    #         edgeRatio (tuple[list[float], list[float]]): output edge ratio results
    #         J_threshold (tuple[float, float], optional): Jacobian threshold.

    #             Defaults to (-np.inf, np.inf).
    #     """
    #     cellType: int = cell.GetCellType()
    #     vol: float
    #     edgeRatioVal: float
    #     jacob: float
    #     if cellType == VTK_TETRA :
    #         vol = self._meshQuality.TetVolume(cell)
    #         edgeRatioVal = self._meshQuality.TetEdgeRatio(cell)
    #         jacob = self._meshQuality.TetScaledJacobian(cell)
    #     elif cellType == VTK_HEXAHEDRON:
    #         vol = self._meshQuality.HexVolume(cell)
    #         edgeRatioVal = self._meshQuality.HexEdgeRatio(cell)
    #         jacob = self._meshQuality.HexScaledJacobian(cell)
    #         hexStretch[0].append(self._meshQuality.HexStretch(cell))
    #     elif cellType == VTK_WEDGE :
    #         vol = self._meshQuality.WedgeVolume(cell)
    #         edgeRatioVal = self._meshQuality.WedgeEdgeRatio(cell)
    #         jacob = self._meshQuality.WedgeScaledJacobian(cell)
    #     elif cellType == VTK_PYRAMID:
    #         vol = self._meshQuality.PyramidVolume(cell)
    #         lenghtList =[]
    #         for i in range(cell.GetNumberOfEdges ()):
    #             lenght2 = cell.GetEdge(i).GetLength2 ()
    #             lenghtList.append(np.sqrt(lenght2))
    #         edgeRatioVal = max(lenghtList) / min(lenghtList)
    #         jacob = self._meshQuality.PyramidScaledJacobian(cell)
    #     else:
    #         vol = np.nan
    #         edgeRatioVal = np.nan
    #         jacob = np.nan
    #         print(f"Cell type {vtkCellTypes.GetClassNameFromTypeId(cellType)} is currently not supported.")

    #     volume[0].append(vol)
    #     edgeRatio[0].append(edgeRatioVal)
    #     if J_threshold[0] <= jacob <= J_threshold[1]:
    #         jacobian[0].append(jacob)
    #     else:
    #         jacobian[1].append(jacob)

    # def CellAspectRatio(self: Self,
    #                     cell: vtkCell,
    #                     listData: tuple[list[float], list[float]],
    #                     threshold: tuple[float, float] = (-np.inf, np.inf)
    #                    ) ->None:
    #     """Compute cell aspect ratio.

    #     Args:
    #         cell (vtkCell): cell
    #         listData (tuple[list[float], list[float]]): output results
    #         threshold (tuple[float, float], optional): aspect ratio threshold.

    #             Defaults to (-np.inf, np.inf).
    #     """
    #     cellType: int = cell.GetCellType()
    #     if cellType == VTK_TETRA :
    #         if threshold is None:
    #             listData[0].append(self._meshQuality.TetAspectRatio(cell))
    #         else:
    #             if threshold[0] <= self._meshQuality.TetAspectRatio(cell) <= threshold[1]:
    #                 listData[0].append(self._meshQuality.TetAspectRatio(cell))
    #             else:
    #                 listData[1].append(self._meshQuality.TetAspectRatio(cell))

    #     else :
    #         listSimplexPts = vtkPoints()
    #         idList = vtkIdList()
    #         cell.Triangulate(1, idList,listSimplexPts)

    #         simplexAspectRatio: list[float] = []
    #         index: int = 0
    #         while index != listSimplexPts.GetNumberOfPoints() :
    #             tetra: vtkTetra = vtkTetra()
    #             tetraPts: vtkPoints = tetra.GetPoints()
    #             for i in range(4):
    #                 tetraPts.SetPoint(i,listSimplexPts.GetPoint(index))
    #                 tetraPts.Modified()
    #                 index += 1
    #             simplexAspectRatio.append(self._meshQuality.TetAspectRatio(tetra))

    #         if threshold is None:
    #             listData[0].append(max(simplexAspectRatio))
    #         else:
    #             if threshold[0] <= max(simplexAspectRatio) <= threshold[1]:
    #                 listData[0].append(max(simplexAspectRatio))
    #             else:
    #                 listData[1].append(max(simplexAspectRatio))

    #         simplexAspectRatio.clear()
