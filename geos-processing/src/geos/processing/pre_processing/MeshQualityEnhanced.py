# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay, Paloma Martinez
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
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkPolyData, vtkCellData, vtkPointData, vtkFieldData,
                                            vtkCell, vtkCell3D, vtkTetra, vtkCellTypes, vtkPolygon, VTK_TRIANGLE,
                                            VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON,
                                            VTK_POLYHEDRON )
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from geos.mesh.stats.CellTypeCounterEnhanced import CellTypeCounterEnhanced
from geos.mesh.model.CellTypeCounts import CellTypeCounts
from geos.mesh.model.QualityMetricSummary import QualityMetricSummary, StatTypes
from geos.mesh.utils.arrayHelpers import getAttributesFromDataSet
from geos.mesh.processing.meshQualityMetricHelpers import (
    getQualityMeasureNameFromIndex,
    getQualityMetricFromIndex,
    VtkCellQualityMetricEnum,
    CellQualityMetricAdditionalEnum,
    QualityMetricOtherEnum,
    MeshQualityMetricEnum,
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

    # Filter inputs
    input :vtkUnstructuredGrid

    # Instanciate the filter
    filter :MeshQualityEnhanced = MeshQualityEnhanced()
    # Set input data object
    filter.SetInputDataObject(input)
    # Set metrics to use
    filter.SetTriangleMetrics(triangleQualityMetrics)
    filter.SetQuadMetrics(quadQualityMetrics)
    filter.SetTetraMetrics(tetraQualityMetrics)
    filter.SetPyramidMetrics(pyramidQualityMetrics)
    filter.SetWedgeMetrics(wedgeQualityMetrics)
    filter.SetHexaMetrics(hexaQualityMetrics)
    filter.SetOtherMeshQualityMetrics(otherQualityMetrics)
    # Do calculations
    filter.Update()
    # Get output mesh quality report
    outputMesh: vtkUnstructuredGrid = filter.GetOutputDataObject(0)
    outputStats: QualityMetricSummary = filter.GetQualityMetricSummary()
"""

#: name of output quality array from vtkMeshQuality filter
QUALITY_ARRAY_NAME: str = "Quality"


def getQualityMetricArrayName( metric: int ) -> str:
    """Get the name of the array from quality metric index.

    Args:
        metric (int): Metric index

    Returns:
        str: Name of output array
    """
    return QUALITY_ARRAY_NAME + "_" + "".join( getQualityMeasureNameFromIndex( metric ).split( " " ) )


class MeshQualityEnhanced( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Enhanced vtkMeshQuality filter."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )
        self._outputMesh: vtkUnstructuredGrid
        self._cellCounts: CellTypeCounts
        self._qualityMetricSummary: QualityMetricSummary = QualityMetricSummary()

        self._MetricsAll: dict[ int, Optional[ set[ int ] ] ] = {
            VTK_TRIANGLE: None,
            VTK_QUAD: None,
            VTK_TETRA: None,
            VTK_PYRAMID: None,
            VTK_WEDGE: None,
            VTK_HEXAHEDRON: None,
        }
        self._otherMetrics: Optional[ set[ QualityMetricOtherEnum ] ] = None
        # For each cell, save cell type for later use
        self._cellTypeMask: dict[ int, npt.NDArray[ np.bool_ ] ] = {}

        # Static members that can be loaded once to save computational times
        self._allCellTypesExtended: tuple[ int, ...] = getAllCellTypesExtended()
        self._allCellTypes: tuple[ int, ...] = getAllCellTypes()

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): Input port
            info (vtkInformationVector): Info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid" )
        return 1

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
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def GetQualityMetricSummary( self: Self ) -> QualityMetricSummary:
        """Get QualityMetricSummary object.

        Returns:
            QualityMetricSummary: QualityMetricSummary object
        """
        return self._qualityMetricSummary

    def SetTriangleMetrics( self: Self, metrics: Optional[ set[ int ] ] ) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): Metrics to compute
        """
        self._MetricsAll[ VTK_TRIANGLE ] = metrics

    def SetQuadMetrics( self: Self, metrics: Optional[ set[ int ] ] = None ) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): Metrics to compute
        """
        self._MetricsAll[ VTK_QUAD ] = metrics

    def SetTetraMetrics( self: Self, metrics: Optional[ set[ int ] ] = None ) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): Metrics to compute
        """
        self._MetricsAll[ VTK_TETRA ] = metrics

    def SetPyramidMetrics( self: Self, metrics: Optional[ set[ int ] ] = None ) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): Metrics to compute
        """
        self._MetricsAll[ VTK_PYRAMID ] = metrics

    def SetWedgeMetrics( self: Self, metrics: Optional[ set[ int ] ] = None ) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): Metrics to compute
        """
        self._MetricsAll[ VTK_WEDGE ] = metrics

    def SetHexaMetrics( self: Self, metrics: Optional[ set[ int ] ] = None ) -> None:
        """Set triangle quality metrics to compute.

        Args:
            metrics (Iterable[int]): Metrics to compute
        """
        self._MetricsAll[ VTK_HEXAHEDRON ] = metrics

    def SetCellQualityMetrics(
        self: Self,
        triangleMetrics: Optional[ set[ int ] ] = None,
        quadMetrics: Optional[ set[ int ] ] = None,
        tetraMetrics: Optional[ set[ int ] ] = None,
        pyramidMetrics: Optional[ set[ int ] ] = None,
        wedgeMetrics: Optional[ set[ int ] ] = None,
        hexaMetrics: Optional[ set[ int ] ] = None,
    ) -> None:
        """Set all quality metrics to compute.

        Args:
            triangleMetrics (Iterable[int]): Triangle metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            quadMetrics (Iterable[int]): Quad metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            tetraMetrics (Iterable[int]): Tetrahedron metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            pyramidMetrics (Iterable[int]): Pyramid metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            wedgeMetrics (Iterable[int]): Wedge metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
            hexaMetrics (Iterable[int]): Hexahedron metrics to compute.

                Defaults to [vtkMeshQuality.QualityMeasureTypes.NONE,].
        """
        self.SetTriangleMetrics( triangleMetrics )
        self.SetQuadMetrics( quadMetrics )
        self.SetTetraMetrics( tetraMetrics )
        self.SetPyramidMetrics( pyramidMetrics )
        self.SetWedgeMetrics( wedgeMetrics )
        self.SetHexaMetrics( hexaMetrics )

    def SetOtherMeshQualityMetrics( self: Self, metrics: set[ QualityMetricOtherEnum ] ) -> None:
        """Set additional metrics unrelated to cell types.

        Args:
            metrics (set[QualityMetricOtherEnum]): Set of QualityMetricOtherEnum
        """
        if len( metrics ) > 0:
            self._otherMetrics = metrics
        else:
            self._otherMetrics = None

    def getComputedMetricsFromCellType( self: Self, cellType: int ) -> Optional[ set[ int ] ]:
        """Get the set of metrics computed for input cell type.

        Args:
            cellType (int): Cell type index

        Returns:
            Optional[set[int]]: Set of computed quality metrics
        """
        # Child cell type
        if cellType in self._allCellTypes:
            return self._MetricsAll[ cellType ]
        # For parent cell types, gather children metrics
        metrics: set[ int ] | None = getCellQualityMeasureFromCellType( cellType )
        if metrics is None:
            return None
        commonComputedMetricsExists: bool = False
        for cellTypeChild in getChildrenCellTypes( cellType ):
            computedMetrics: set[ int ] | None = self._MetricsAll[ cellTypeChild ]
            if computedMetrics is None:
                continue
            commonComputedMetricsExists = True
            metrics = metrics.intersection( computedMetrics )
        return metrics if commonComputedMetricsExists else None

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
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
        inData: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        self._outputMesh = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None, "Input mesh is undefined."
        assert self._outputMesh is not None, "Output pipeline is undefined."
        self._outputMesh.ShallowCopy( inData )

        # Compute cell type counts
        self._computeCellTypeCounts()

        # Compute metrics and associated attributes
        self._evaluateMeshQualityAll()

        # Compute stats summary
        self._updateStatsSummary()

        # Create field data
        self._createFieldDataStatsSummary()

        self._outputMesh.Modified()
        return 1

    def _computeCellTypeCounts( self: Self ) -> None:
        """Compute cell type counts."""
        filter: CellTypeCounterEnhanced = CellTypeCounterEnhanced()
        filter.SetInputDataObject( self._outputMesh )
        filter.Update()
        counts: CellTypeCounts = filter.GetCellTypeCountsObject()
        assert counts is not None, "CellTypeCounts is undefined"
        self._qualityMetricSummary.setCellTypeCounts( counts )

    def _evaluateMeshQualityAll( self: Self ) -> None:
        """Compute all mesh quality metrics."""
        for _cellType, metrics in self._MetricsAll.items():
            if metrics is None:
                continue
            for metricIndex in metrics:
                self._evaluateCellQuality( metricIndex )

        if self._otherMetrics is not None:
            if QualityMetricOtherEnum.INCIDENT_VERTEX_COUNT.getMetricIndex() in self._otherMetrics:
                self._countVertexIncidentEdges()
            else:
                # TODO: add other metrics
                print( "" )

    def _evaluateCellQuality( self: Self, metricIndex: int ) -> None:
        """Compute mesh input quality metric. By default, the metric is computed for all cell types.

        Args:
            metricIndex (int): Quality metric index
        """
        arrayName: str = getQualityMetricArrayName( metricIndex )
        if arrayName in getAttributesFromDataSet( self._outputMesh, False ):
            # Metric is already computed (by default computed for all cell types if applicable )
            return

        # Get the list of cell types the metric applies to and check if these cell types are present
        metric: MeshQualityMetricEnum | None = getQualityMetricFromIndex( metricIndex )
        if metric is None:
            return
        cellTypes: Optional[ set[ int ] ] = metric.getApplicableCellTypes()
        if cellTypes is None:
            return

        cellToApplyTo = []
        for ct in cellTypes:
            if self._qualityMetricSummary.getCellTypeCountsOfCellType( ct ) > 0:
                cellToApplyTo += [ ct ]

        if len( cellToApplyTo ) == 0:
            return

        # Compute quality metric
        output: vtkUnstructuredGrid | None = None
        if ( metricIndex == VtkCellQualityMetricEnum.SQUISH_INDEX.metricIndex ):
            # Redefined Squish index calculation to be computed for any type of polyhedron
            self._computeSquishIndex()
        elif ( metricIndex in ( CellQualityMetricAdditionalEnum.MAXIMUM_ASPECT_RATIO.metricIndex, ) ):
            # Extended metric for any type of cells (other than tetra) from tetra metrics
            self._computeAdditionalMetrics( metricIndex )
        else:
            output = self._applyMeshQualityFilter( metricIndex, cellToApplyTo )

            assert output is not None, "Output mesh from mesh quality calculation is undefined."
            # Transfer output cell array to input mesh
            # TODO: to test if Shallow copy of vtkMeshQualityFilter result and rename "Quality" array is more efficient than what is done here
            self._transferCellAttribute( output, QUALITY_ARRAY_NAME, arrayName, metric )

    def _applyMeshQualityFilter( self: Self, metric: int, cellTypes: list[ int ] ) -> vtkUnstructuredGrid:
        """Apply vtkMeshQuality filter.

        Args:
            metric (int): Quality metric
            cellTypes (list[int]): The cell types that should be considered

        Returns:
            vtkUnstructuredGrid: Filtered mesh
        """
        meshQualityFilter = vtkMeshQuality()
        meshQualityFilter.SetInputDataObject( self._outputMesh )

        for cellType in cellTypes:
            if cellType == VTK_TRIANGLE:
                meshQualityFilter.SetTriangleQualityMeasure( metric )
            elif cellType == VTK_QUAD:
                meshQualityFilter.SetQuadQualityMeasure( metric )
            elif cellType == VTK_TETRA:
                meshQualityFilter.SetTetQualityMeasure( metric )
            elif cellType == VTK_PYRAMID:
                meshQualityFilter.SetPyramidQualityMeasure( metric )
            elif cellType == VTK_WEDGE:
                meshQualityFilter.SetWedgeQualityMeasure( metric )
            elif cellType == VTK_HEXAHEDRON:
                meshQualityFilter.SetHexQualityMeasure( metric )
            else:
                print( "Cell type is not supported." )

        meshQualityFilter.Update()
        return meshQualityFilter.GetOutputDataObject( 0 )

    def _computeAdditionalMetrics( self: Self, metricIndex: int ) -> None:
        """Compute additional metrics from metrics defined for tetrahedron.

        Output is an cell array in output mesh.

        Args:
            metricIndex (int): Metric index
        """
        metric = getQualityMetricFromIndex( metricIndex )
        assert metric is not None, f"Additional cell quality metric index {metricIndex} is undefined."
        # Output array
        name: str = getQualityMetricArrayName( metric.getMetricIndex() )
        newArray: vtkDoubleArray = vtkDoubleArray()
        newArray.SetName( name )
        newArray.SetNumberOfValues( self._outputMesh.GetNumberOfCells() )
        newArray.SetNumberOfComponents( 1 )

        for i in range( self._outputMesh.GetNumberOfCells() ):
            cell: vtkCell = self._outputMesh.GetCell( i )
            val: float = self._computeAdditionalMetricsCell( metricIndex, cell )
            newArray.SetValue( i, val )
        # Add array
        cellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert cellArrays is not None, "Cell data from output mesh is undefined."
        cellArrays.AddArray( newArray )
        cellArrays.Modified()
        self._outputMesh.Modified()
        return

    def _transferCellAttribute(
        self: Self,
        inputMesh: vtkUnstructuredGrid,
        attributeFromName: str,
        attributeToName: str,
        qualityMetric: int,
    ) -> bool:
        """Transfer quality attribute to the client mesh.

        The attribute is renamed with quality metric name. Because a default quality
        metric is computed if an element does not support the desired metric, this
        default metric is replaced by nan values.

        Args:
            inputMesh (vtkUnstructuredGrid): The mesh that contains the quality cell data array
            attributeFromName (str): The name of the quality attribute in initial mesh
            attributeToName (str): Name of the attribute in the final mesh
            qualityMetric (QualityMetricOtherEnum):The quality metric.

        Returns:
            bool: True if the attribute was successfully transferred, False otherwise
        """
        cellArrays: vtkCellData = inputMesh.GetCellData()
        assert cellArrays is not None, "Cell data from vtkMeshQuality output mesh is undefined."
        array: vtkDataArray = cellArrays.GetArray( attributeFromName )
        assert array is not None, f"{attributeFromName} attribute is undefined."

        # Rename array
        array.SetName( attributeToName )

        # Replace irrelevant values
        self._replaceIrrelevantValues( array, inputMesh, qualityMetric )

        # Add array to input mesh
        inputCellArrays: vtkCellData = self._outputMesh.GetCellData()

        assert inputCellArrays is not None, "Cell data from input mesh is undefined."
        inputCellArrays.AddArray( array )
        inputCellArrays.Modified()

        return True

    def _replaceIrrelevantValues( self: Self, array: vtkDataArray, mesh: vtkUnstructuredGrid,
                                  metric: MeshQualityMetricEnum ) -> None:
        """Replace irrelevant values.

        Values are irrelevant when a quality metric is computed
        whereas input metric does not applies to the cell type.

        Args:
            array (vtkDataArray): Array to update
            mesh (vtkUnstructuredGrid): Mesh
            metric (MeshQualityMetricEnum): Quality metric
        """
        cellTypes: Optional[ set[ int ] ] = metric.getApplicableCellTypes()
        if cellTypes is None:
            return
        cellToApplyTo = []
        for ct in cellTypes:
            if self._qualityMetricSummary.getCellTypeCountsOfCellType( ct ) > 0:
                cellToApplyTo += [ ct ]

        for cellId in range( mesh.GetNumberOfCells() ):
            cell: vtkCell = mesh.GetCell( cellId )
            cellType: int = cell.GetCellType()

            if cellType not in cellToApplyTo:
                array.SetTuple1( cellId, np.nan )

    def _updateStatsSummary( self: Self ) -> None:
        """Compute quality metric statistics."""
        # Init cell type masks
        self._initCellTypeMasks()
        # Stats for each cell types individually
        count: int = 0
        metrics: set[ int ] | None
        for cellType, metrics in self._MetricsAll.items():
            count = self._qualityMetricSummary.getCellTypeCountsOfCellType( cellType )
            if ( count == 0 ) or ( metrics is None ):
                continue
            for metricIndex in metrics:
                self._updateStatsSummaryByCellType( metricIndex, cellType )

        # Stats for polygons and polyhedra
        for cellType in ( VTK_POLYGON, VTK_POLYHEDRON ):
            count = self._qualityMetricSummary.getCellTypeCountsOfCellType( cellType )
            # Get common computed metrics
            metrics = self.getComputedMetricsFromCellType( cellType )
            if ( count == 0 ) or ( metrics is None ):
                continue
            for metricIndex in metrics:
                self._updateStatsSummaryByCellType( metricIndex, cellType )

    def _updateStatsSummaryByCellType( self: Self, metricIndex: int, cellType: int ) -> None:
        """Compute input quality metric statistics for input cell types.

        Args:
            metricIndex (int): Quality metric index
            cellType (int): Cell type index
        """
        cellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert cellArrays is not None, "Cell data from input mesh is undefined."
        arrayName: str = getQualityMetricArrayName( metricIndex )
        array: vtkDataArray | None = cellArrays.GetArray( arrayName )

        if array is None:
            return
        npArray: npt.NDArray[ np.float64 ] = vtk_to_numpy( array )
        cellTypeMask: npt.NDArray[ np.bool_ ] = self._cellTypeMask[ cellType ]

        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(
            metricIndex, cellType, StatTypes.MEAN, StatTypes.MEAN.compute( npArray[ cellTypeMask ] ) )
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(
            metricIndex, cellType, StatTypes.STD_DEV, StatTypes.STD_DEV.compute( npArray[ cellTypeMask ] ) )
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(
            metricIndex, cellType, StatTypes.MIN, StatTypes.MIN.compute( npArray[ cellTypeMask ] ) )
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(
            metricIndex, cellType, StatTypes.MAX, StatTypes.MAX.compute( npArray[ cellTypeMask ] ) )
        self._qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(
            metricIndex, cellType, StatTypes.COUNT, StatTypes.COUNT.compute( npArray[ cellTypeMask ] ) )

    def _initCellTypeMasks( self: Self ) -> None:
        """Init _cellTypeMask variable."""
        # Compute cell type masks
        self._cellTypeMask = {
            cellType: np.zeros( self._outputMesh.GetNumberOfCells(), dtype=bool )
            for cellType in self._allCellTypesExtended
        }
        polyhedronCellTypes: tuple[ int, ...] = getPolyhedronCellTypes()
        polygonCellTypes: tuple[ int, ...] = getPolygonCellTypes()
        for cellId in range( self._outputMesh.GetNumberOfCells() ):
            for cellType in self._allCellTypesExtended:
                cellTypes: tuple[ int, ...] = ( cellType, )
                if cellType == VTK_POLYGON:
                    cellTypes = polygonCellTypes
                elif cellType == VTK_POLYHEDRON:
                    cellTypes = polyhedronCellTypes
                self._cellTypeMask[ cellType ][ cellId ] = self._outputMesh.GetCellType( cellId ) in cellTypes

    def _createFieldDataStatsSummary( self: Self ) -> None:
        """Create field data arrays with quality statistics."""
        fieldData: vtkFieldData = self._outputMesh.GetFieldData()
        assert fieldData is not None, "Field data is undefined."
        for cellType in self._allCellTypesExtended:
            count: int = self._qualityMetricSummary.getCellTypeCountsOfCellType( cellType )
            metrics: Optional[ set[ int ] ] = self.getComputedMetricsFromCellType( cellType )
            # Create count array
            name = "_".join( ( vtkCellTypes.GetClassNameFromTypeId( cellType ), StatTypes.COUNT.getString() ) )
            countArray: vtkIntArray = vtkIntArray()
            countArray.SetName( name )
            countArray.SetNumberOfValues( 1 )
            countArray.SetNumberOfComponents( 1 )
            countArray.SetValue( 0, count )
            fieldData.AddArray( countArray )
            if ( count == 0 ) or ( metrics is None ):
                continue

            # Create metric arrays
            for metricIndex in metrics:
                # One array per statistic number except Count (last one)
                for statType in list( StatTypes )[ :-1 ]:
                    value: int = self._qualityMetricSummary.getCellStatValueFromStatMetricAndCellType(
                        metricIndex, cellType, statType )
                    name = self._createArrayName( cellType, metricIndex, statType )
                    metricArray: vtkDoubleArray = vtkDoubleArray()
                    metricArray.SetName( name )
                    metricArray.SetNumberOfValues( 1 )
                    metricArray.SetNumberOfComponents( 1 )
                    metricArray.SetValue( 0, value )
                    fieldData.AddArray( metricArray )
        fieldData.Modified()

    def _createArrayName( self: Self, cellType: int, metricIndex: int, statType: StatTypes ) -> str:
        """Concatenate cell type, metric name, and statistic name in array name.

        Args:
            cellType (int): Cell type index
            metricIndex (int): Quality metric index
            statType (StatTypes): Statistic type

        Returns:
            str: Array name
        """
        return "_".join( ( vtkCellTypes.GetClassNameFromTypeId( cellType ),
                           getQualityMeasureNameFromIndex( metricIndex ).replace( " ", "" ), statType.getString() ) )

    def _computeAdditionalMetricsCell( self: Self, metricIndex: int, cell: vtkCell ) -> float:
        """Compute additional metrics from metrics defined for tetrahedron for a cell.

        Args:
            metricIndex (int): Metric index
            cell (vtkCell): Cell

        Returns:
            float: Output value
        """
        if cell.GetCellDimension() > 2:
            simplexAspectRatio: list[ float ] = []
            meshQualityFilter: vtkMeshQuality = vtkMeshQuality()
            # Triangulate cell faces
            listSimplexPts = vtkPoints()
            idList = vtkIdList()
            cell.Triangulate( 1, idList, listSimplexPts )

            index: int = 0
            while index != listSimplexPts.GetNumberOfPoints():
                # Create tetra
                tetra: vtkTetra = vtkTetra()
                tetraPts: vtkPoints = tetra.GetPoints()

                for i in range( 4 ):
                    tetraPts.SetPoint( i, listSimplexPts.GetPoint( index ) )
                    tetraPts.Modified()
                    index += 1
                # Compute aspect ratio of tetra
                if metricIndex == CellQualityMetricAdditionalEnum.MAXIMUM_ASPECT_RATIO.getMetricIndex():
                    simplexAspectRatio.append( meshQualityFilter.TetAspectRatio( tetra ) )
                else:
                    # Metric is not supported
                    simplexAspectRatio.append( np.nan )

            if any( np.isfinite( simplexAspectRatio ) ):
                return np.nanmax( simplexAspectRatio )
        return np.nan

    def _countVertexIncidentEdges( self: Self ) -> None:
        """Compute edge length and vertex incident edge number."""
        metric: QualityMetricOtherEnum = QualityMetricOtherEnum.INCIDENT_VERTEX_COUNT
        # Edges are extracted as "cell" of dimension 1
        extractEdges = vtkExtractEdges()
        extractEdges.SetInputData( self._outputMesh )
        extractEdges.Update()
        polyData: vtkPolyData = extractEdges.GetOutput()
        incidentCounts: npt.NDArray[ np.int64 ] = np.zeros( self._outputMesh.GetNumberOfPoints(), dtype=int )
        for edg in range( polyData.GetNumberOfCells() ):
            if polyData.GetCell( edg ).GetCellDimension() != 1:
                # Not an edge
                continue

            edgesPointIds: vtkIdList = polyData.GetCell( edg ).GetPointIds()
            for i in range( edgesPointIds.GetNumberOfIds() ):
                incidentCounts[ edgesPointIds.GetId( i ) ] += 1

        # Create point attribute
        pointData: vtkPointData = self._outputMesh.GetPointData()
        assert pointData is not None, "Point data is undefined."
        countArray: vtkIntArray = numpy_to_vtk( incidentCounts, deep=1 )
        metricName: str = metric.getMetricName().replace( " ", "" )
        name: str = QUALITY_ARRAY_NAME + "_" + metricName
        countArray.SetName( name )
        pointData.AddArray( countArray )
        pointData.Modified()

        fieldData: vtkFieldData = self._outputMesh.GetFieldData()
        assert fieldData is not None, "Field data is undefined."
        for statType in list( StatTypes ):
            name = metricName + "_" + statType.getString()
            val: float | int = statType.compute( incidentCounts )
            # Add values to quality summary stats
            self._qualityMetricSummary.setOtherStatValueFromMetric( metric.getMetricIndex(), statType, val )
            metricArray: vtkDoubleArray = vtkDoubleArray()
            metricArray.SetName( name )
            metricArray.SetNumberOfValues( 1 )
            metricArray.SetNumberOfComponents( 1 )
            metricArray.SetValue( 0, val )  # type: ignore[arg-type]
            fieldData.AddArray( metricArray )
        fieldData.Modified()
        self._outputMesh.Modified()

    def _computeSquishIndex( self: Self ) -> None:
        """Compute Squish index for all element type.

        Squish index is the maximum value of the cosine of the deviation angle between
        cell center to face center vector and face normal vector.

        Output is a new cell array.
        """
        # Output array
        name: str = getQualityMetricArrayName( VtkCellQualityMetricEnum.SQUISH_INDEX.getMetricIndex() )
        newArray: vtkDoubleArray = vtkDoubleArray()
        newArray.SetName( name )
        newArray.SetNumberOfValues( self._outputMesh.GetNumberOfCells() )
        newArray.SetNumberOfComponents( 1 )
        # Copy input data to prevent modifications from GetCellNeighbors method
        copyData: vtkUnstructuredGrid = vtkUnstructuredGrid()
        copyData.ShallowCopy( self._outputMesh )
        points: vtkPoints = copyData.GetPoints()
        for c in range( copyData.GetNumberOfCells() ):
            cell: vtkCell = copyData.GetCell( c )
            # Applies only to polyhedra
            if cell.GetCellDimension() != 3:
                continue
            # Get cell center
            cellCenter: npt.NDArray[ np.float64 ] = self._getCellCenter( cell )
            # Compute deviation cosine for each face
            squishIndex: npt.NDArray[ np.float64 ] = np.full( cell.GetNumberOfFaces(), np.nan )
            for f in range( cell.GetNumberOfFaces() ):
                face: vtkCell = cell.GetFace( f )
                # Get face center
                ptsIds: vtkIdTypeArray = vtkIdTypeArray()
                ptsIds.Allocate( face.GetNumberOfPoints() )
                ptsIdsList: vtkIdList = face.GetPointIds()
                for i in range( ptsIdsList.GetNumberOfIds() ):
                    ptsIds.InsertNextValue( ptsIdsList.GetId( i ) )
                faceCenter: npt.NDArray[ np.float64 ] = self._getCellCenter( face, ptsIds, points )
                faceNormal: npt.NDArray[ np.float64 ] = self._getNormalVector( points, face )

                vec: npt.NDArray[ np.float64 ] = cellCenter - faceCenter
                angle: float = vtkMath.AngleBetweenVectors( vec, faceNormal )  # type: ignore[arg-type]
                squishIndex[ f ] = np.sin( angle )
            newArray.InsertValue( c, np.nanmax( squishIndex ) )

        # Add array
        cellArrays: vtkCellData = self._outputMesh.GetCellData()
        assert cellArrays is not None, "Cell data from output mesh is undefined."
        cellArrays.AddArray( newArray )
        cellArrays.Modified()
        self._outputMesh.Modified()

    def _getCellCenter( self: Self,
                        cell: vtkCell,
                        ptsIds: Optional[ vtkIdTypeArray ] = None,
                        points: Optional[ vtkPoints ] = None ) -> npt.NDArray[ np.float64 ]:
        """Compute cell center.

        Args:
            cell (vtkCell): Input cell
            ptsIds (vtkIdTypeArray | None): Cell point ids. Defaults to None.
            points (vtkPoints | None): Mesh point coordinates. Defaults to None.

        Returns:
            npt.NDArray[np.float64]: Output cell center
        """
        cellCenter: npt.NDArray[ np.float64 ] = np.zeros( 3 )
        if cell.GetCellDimension() == 2:
            # Polygonal cell
            assert ptsIds is not None, "Point ids are required for computing polygonal cell center."
            assert points is not None, "Points are required for computing polygonal cell center."
            cell.GetPointIds()
            vtkPolygon.ComputeCentroid( ptsIds, points, cellCenter )  # type: ignore[call-overload]
        elif cell.GetCellDimension() == 3:
            # Volume cell
            cell3D: vtkCell3D = cast( vtkCell3D, cell )
            cell3D.GetCentroid( cellCenter )  # type: ignore[arg-type]
        else:
            raise TypeError( "Cell must be polygonal or volumic." )
        return cellCenter

    def _getNormalVector( self: Self, points: vtkPoints, face: vtkCell ) -> npt.NDArray[ np.float64 ]:
        """Get the normal to the input face.

        .. NOTE:: This method consider the faces as planes.

        Args:
            points (vtkPoints): Mesh points
            face (vtkCell): Face

        Returns:
            npt.NDArray[np.float64]: Coordinates of the normal vector
        """
        assert face.GetCellDimension() == 2, "Cell must be a planar polygon."
        facePtsIds: vtkIdList = face.GetPointIds()
        # Need only 3 points among all to get the normal of the face since we suppose face is a plane
        ptsCoords: npt.NDArray[ np.float64 ] = np.zeros( ( 3, 3 ), dtype=float )
        for i in range( 3 ):
            points.GetPoint( facePtsIds.GetId( i ), ptsCoords[ i ] )
        return geom.computeNormalFromPoints( ptsCoords[ 0 ], ptsCoords[ 1 ], ptsCoords[ 2 ] )
