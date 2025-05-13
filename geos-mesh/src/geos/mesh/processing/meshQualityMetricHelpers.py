# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
from dataclasses import dataclass
import numpy as np
from typing import Optional
from typing_extensions import Self
from enum import Enum
from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import (
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON
)


__doc__ = """
Helpers for MeshQuality metrics.
"""

@dataclass( frozen=True )
class QualityRange():
    """Defines metric quality ranges."""
    acceptableRange: tuple[float, float]
    normalRange: tuple[float, float]
    fullRange: tuple[float, float]

class QualityMetricAbstractEnum(Enum):
    def __init__(self: Self,
                 qualityMeasureTypesIndex: vtkMeshQuality.QualityMeasureTypes,
                 name: str,
                 applicableToCellTypes: tuple[bool, ...],
                 qualityRanges: tuple[QualityRange | None,...],
                ) -> None:
        """Define the enumeration to add attributes to mesh quality measures.

        Args:
            qualityMeasureTypesIndex (vtkMeshQuality.QualityMeasureTypes): index of QualityMeasureTypes
            name (str): name of the metric
            applicableToCellTypes (tuple[bool, ...]): tuple defining for each cell type if the
                metric is applicable.
            qualityRanges (tuple[QualityRange | None,...]): quality range limits for each cell type
                starting from best to worst quality.
        """
        self.metricIndex: str = int(qualityMeasureTypesIndex)
        self.metricName: int = name
        self.applicableToCellTypes: tuple[bool] = applicableToCellTypes
        self.qualityRanges: tuple[QualityRange | None,...] = qualityRanges

    def isApplicableToCellType(self: Self, cellType: int) ->bool:
        """Return True if the metric is applicable to input cell type, False otherwise.

        Args:
            cellType (int): cell type index

        Returns:
            bool: True if the metric is applicable
        """
        assert cellType in getAllCellTypesExtended(), f"Cell type index {cellType} not in supported cell types."
        cellTypes: tuple[int] = (cellType,)
        if cellType == VTK_POLYGON:
            cellTypes = getPolygonCellTypes()
        if cellType == VTK_POLYHEDRON:
            cellTypes = getPolyhedronCellTypes()
        for cellType in cellTypes:
            cellTypeIndex: int = getAllCellTypes().index(cellType)
            if not self.applicableToCellTypes[cellTypeIndex]:
                return False
        return True

    def getQualityRange(self: Self, cellType: int) -> Optional[QualityRange]:
        """Get quality range for input cell type.

        Args:
            cellType (int): cell type index

        Returns:
            tuple[float, float, float, float, bool] | None: quality range from best to worst. Last element
                yields True if the range is symmetrical to negative values.
        """
        if cellType not in getAllCellTypes():
            return None
        cellTypeIndex: int = getAllCellTypes().index(cellType)
        return self.qualityRanges[cellTypeIndex]

#: from https://vtk.org/doc/nightly/html/vtkMeshQuality_8h_source.html
class QualityMetricEnum(QualityMetricAbstractEnum):
    """Mesh quality metric enumeration.

    The order of boolean is the same as getAllCellTypes method:
    (VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON)

    .. CAUTION:: The order of the enum must follow the one of vtkMeshQuality.QualityMeasureTypes.

    """
    EDGE_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,
        "Edge Ratio",
        (True, True, True, False, True, True),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None, 
         QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)),)
    )
    ASPECT_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO,
        "Aspect Ratio",
        (True, True, True, False, False, False),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None, None, None),
    )
    RADIUS_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.RADIUS_RATIO,
        "Radius Ratio",
        (True, True, True, False, False, False),
        (QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None, None, None),
    )
    ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.ASPECT_FROBENIUS,
        "Aspect Frobenius",
        (True, False, True, False, False, False),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, None),
    )
    MEDIAN_ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS,
        "Med Aspect Frobenius",
        (False, True, False, False, False, True),
        (None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, None, QualityRange((1.0, 3.0), (1.0, 3.0), (9.0, np.inf)))
    )
    MAXIMUM_ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.MAX_ASPECT_FROBENIUS,
        "Maximum Aspect Frobenius",
        (False, True, False, False, True, True),
        (None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)))
    )
    MINIMUM_ANGLE = (
        vtkMeshQuality.QualityMeasureTypes.MIN_ANGLE,
        "Minimum Angle (°)",
        (True, True, True, False, False, False),
        (QualityRange((30.0, 60.0), (0.0, 60.0), (0.0, 360.0)), QualityRange((45.0, 90.0), (0.0, 90.0), (0.0, 360.)),
         QualityRange((40.0, 180./np.pi*np.arccos(1/3)), (0.0, 180./np.pi*np.arccos(1/3)), (0.0, 360.0)), None, None, None)
    )
    COLLAPSE_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.COLLAPSE_RATIO,
        "Collapse Ratio",
        (False, False, True, False, False, False),
        (None, None, QualityRange((0.1, 1.0), (0.0, np.inf), (0.0, np.inf)), None, None, None)
    )
    MAXIMUM_ANGLE = (
        vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE,
        "Maximum Angle (°)",
        (True, True, False, False, False, False),
        (QualityRange((60., 90.0), (60.0, 180.0), (0.0, 180.0)), QualityRange((90.0, 135.0), (90.0, 360.0), (0.0, 360.)), None, None, None, None)
    )
    CONDITION = (
        vtkMeshQuality.QualityMeasureTypes.CONDITION,
        "Condition",
        (True, True, True, False, True, True),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 4.0), (1.0, 12.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None,
         QualityRange((1.0, 4.0), (1.0, 12.0), (1.0, np.inf)), QualityRange((1.0, 4.0), (1.0, 12.0), (1.0, np.inf))),
    )
    SCALED_JACOBIAN = (
        vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
        "Scaled Jacobian",
        (True, True, True, True, True, True),
        (QualityRange((0.5, 2.0*np.sqrt(3)/3.0), (-2.0*np.sqrt(3)/3.0, 2.0*np.sqrt(3)/3.0), (-np.inf, np.inf)), QualityRange((0.30, 1.0), (-1.0, 1.0), (-1.0, np.inf)),
         QualityRange((0.5, 0.5*np.sqrt(2)), (-0.5*np.sqrt(2), 0.5*np.sqrt(2)), (-np.inf, np.inf)), QualityRange((0.50, 1.0), (-1.0, 1.0), (-1.0, np.inf)),
         QualityRange((0.50, 1.0), (-1.0, 1.0), (-1.0, np.inf)), QualityRange((0.50, 1.0), (-1.0, 1.0), (-1.0, np.inf)),),
    )
    SHEAR = (
        vtkMeshQuality.QualityMeasureTypes.SHEAR,
        "Shear",
        (False, True, False, False, False, True),
        (None, QualityRange((0.3, 0.6), (0.0, 1.0), (0.0, 1.0)), None, None, None, QualityRange((0.3, 0.6), (0.0, 1.0), (0.0, 1.0))))
    RELATIVE_SIZE_SQUARED = (
        vtkMeshQuality.QualityMeasureTypes.RELATIVE_SIZE_SQUARED,
        "Relative Size Squared",
        (True, True, True, False, False, True),
        (QualityRange((0.25, 0.50), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.6), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.50), (0.0, 1.0), (0.0, 1.0)), None, None, QualityRange((0.50, 1.0), (0.0, 1.0), (0.0, 1.0))),
    )
    SHAPE = (
        vtkMeshQuality.QualityMeasureTypes.SHAPE,
        "Shape",
        (True, True, True, True, True, True),
        (QualityRange((0.25, 0.50), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)),
         QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)),),
    )
    SHAPE_AND_SIZE = (
        vtkMeshQuality.QualityMeasureTypes.SHAPE_AND_SIZE,
        "Shape And Size",
        (True, True, True, False, False, True),
        (QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)),
         QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)),),
    )
    DISTORTION = (
        vtkMeshQuality.QualityMeasureTypes.DISTORTION,
        "Distortion",
        (True, True, True, False, True, True),
        (QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), None, 
         QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)),),
    )
    MAXIMUM_EDGE_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.MAX_EDGE_RATIO,
        "Maximum Edge Ratio",
        (False, True, False, False, False, True),
        (None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)))
    )
    SKEW = (
        vtkMeshQuality.QualityMeasureTypes.SKEW,
        "Skew",
        (False, True, False, False, False, True),
        (None, QualityRange((0.5, 1.0), (0.0, 1.0), (0.0, 1.0)), None, None, None, QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)))
    )
    TAPER = (
        vtkMeshQuality.QualityMeasureTypes.TAPER,
        "Taper",
        (False, True, False, False, False, True),
        (None, QualityRange((0.0, 0.7), (0.0, 2.0), (0.0, np.inf)), None, None, None, QualityRange((0.0, 0.5), (0.0, 1.5), (0.0, np.inf)))
    )
    VOLUME = (
        vtkMeshQuality.QualityMeasureTypes.VOLUME,
        "Volume (m3)",
        (False, False, True, True, True, True),
        (None, None, QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)),
         QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf))),
    )
    STRETCH = (
        vtkMeshQuality.QualityMeasureTypes.STRETCH,
        "Stretch",
        (False, True, False, False, False, True),
        (None, QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, np.inf)), None, None, None, QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, np.inf)))
    )
    DIAGONAL = (
        vtkMeshQuality.QualityMeasureTypes.DIAGONAL,
        "Diagonal",
        (False, False, False, False, False, True),
        (None, None, None, None, None, QualityRange((0.65, 1.0), (0.0, 1.0), (0.0, np.inf)),)
    )
    # acceptable range is application dependent.
    DIMENSION = (
        vtkMeshQuality.QualityMeasureTypes.DIMENSION,
        "Dimension (m)",
        (False, False, False, False, False, True),
        (None, None, None, None, None, QualityRange((0.0, np.inf), (0.0, np.inf), (0.0, np.inf)),)
    )
    ODDY = (
        vtkMeshQuality.QualityMeasureTypes.ODDY,
        "Oddy",
        (False, True, False, False, False, True),
        (None, QualityRange((0.0, 0.5), (0.0, 1.5), (0.0, np.inf)), None, None, None, QualityRange((0.0, 0.5), (0.0, 1.5), (0.0, np.inf)),)
    )
    SHEAR_AND_SIZE = (
        vtkMeshQuality.QualityMeasureTypes.SHEAR_AND_SIZE,
        "Shear And Size",
        (False, True, False, False, False, True),
        (None, QualityRange((0.2, 0.4), (0.0, 1.0), (0.0, 1.0)), None, None, None, QualityRange((0.2, 0.4), (0.0, 1.0), (0.0, 1.0)))
    )
    JACOBIAN = (
        vtkMeshQuality.QualityMeasureTypes.JACOBIAN,
        "Jacobian",
        (False, True, True, True, True, True),
        (None, QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)),
         QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)),)
    )
    WARPAGE = (
        vtkMeshQuality.QualityMeasureTypes.WARPAGE,
        "Warpage",
        (False, True, False, False, False, False),
        (None, QualityRange((0.0, 0.7), (0.0, 2.0), (0.0, np.inf)), None, None, None, None)
    )
    ASPECT_GAMMA = (
        vtkMeshQuality.QualityMeasureTypes.ASPECT_GAMMA,
        "Aspect Gamma",
        (False, False, True, False, False, False),
        (None, None, QualityRange((1.0, 3.0), (1.0, 9.0), (0.0, np.inf)), None, None, None)
    )
    AREA = (
        vtkMeshQuality.QualityMeasureTypes.AREA,
        "Area (m2)",
        (True, True, False, False, False, False),
        (QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), None, None, None, None),
    )
    EQUIANGLE_SKEW = (
        vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
        "Equiangle Skew",
        (True, True, True, True, True, True),
        (QualityRange((0.0, 0.3), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.3), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.3), (0.0, 1.0), (0.0, 1.0)),
         QualityRange((0.0, 0.3), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.3), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.3), (0.0, 1.0), (0.0, 1.0)),)
    )
    EQUIVOLUME_SKEW = (
        vtkMeshQuality.QualityMeasureTypes.EQUIVOLUME_SKEW,
        "Equivolume Skew",
        (False, False, True, False, False, False),
        (None, None, QualityRange((0.0, 0.3), (0.0, 0.9), (0.0, 1.0)), None, None, None)
    )
    MAXIMUM_STRETCH = (
        vtkMeshQuality.QualityMeasureTypes.MAX_STRETCH,
        "Maximum Stretch",
        (False, False, False, False, True, False),
        (None, None, None, None, QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, np.inf)), None)
    )
    MEAN_ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.MEAN_ASPECT_FROBENIUS,
        "Mean Aspect Frobenius",
        (False, False, False, False, True, False),
        (None, None, None, None, QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None)
    )
    MEAN_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.MEAN_RATIO,
        "Mean Ratio",
        (False, False, True, False, False, False),
        (None, None, QualityRange((0.0, 0.3), (0.0, 0.9), (0.0, 1.0)), None, None, None)
    )
    NODAL_JACOBIAN_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.NODAL_JACOBIAN_RATIO,
        "Nodal Jacobian Ratio",
        (False, False, False, False, False, True),
        (None, None, None, None, None, QualityRange((0.0, np.inf), (0.0, np.inf), (0.0, np.inf)))
    )
    NORMALIZED_INRADIUS = (
        vtkMeshQuality.QualityMeasureTypes.NORMALIZED_INRADIUS,
        "Normalized Inradius",
        (True, False, True, False, False, False),
        (QualityRange((0.15, 0.5), (-1.0, 1.0), (-1.0, 1.0)), None, QualityRange((0.15, 0.5), (-1.0, 1.0), (-1.0, 1.0)), None, None, None)
    )
    SQUISH_INDEX = (
        vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX,
        "Squish index",
        (False, False, True, False, False, False),
        (None, None, QualityRange((0.0, 0.3), (0.0, 0.9), (0.0, 1.0)), None, None, None)
    )
    NONE = (
        vtkMeshQuality.QualityMeasureTypes.NONE,
        "None",
        (False, False, False, False, False, False),
        (None, None, None, None, None, None)
    )


def getAllCellTypesExtended() -> list[int]:
    """Get all cell type ids.

    Returns:
        tuple[int,...]: tuple containing cell type ids.
    """
    return getPolygonCellTypes() + getPolyhedronCellTypes() + [VTK_POLYGON, VTK_POLYHEDRON]

def getAllCellTypes() -> list[int]:
    """Get all cell type ids.

    Returns:
        tuple[int,...]: tuple containing cell type ids.
    """
    return getPolygonCellTypes() + getPolyhedronCellTypes()

def getChildrenCellTypes(parent: int) -> list[int]:
    """Get children cell type ids from parent id.

    Returns:
        tuple[int,...]: tuple containing cell type ids.
    """
    if parent == VTK_POLYGON:
        return getPolygonCellTypes()
    elif parent == VTK_POLYHEDRON:
        return getPolyhedronCellTypes()
    else:
        raise ValueError(f"Cell type {parent} is not supported.")

def getPolygonCellTypes() -> list[int]:
    """Get polygonal cell type ids.

    Returns:
        tuple[int,...]: tuple containing cell type ids.
    """
    return [VTK_TRIANGLE, VTK_QUAD]

def getPolyhedronCellTypes() -> list[int]:
    """Get polyhedra cell type ids.

    Returns:
        tuple[int,...]: tuple containing cell type ids.
    """
    return [VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON]

def getQualityMeasureNameFromIndex(index: int) ->str:
    """Get quality metric name from index.

    Args:
        index (int): index of quality measure

    Returns:
        str: name of quality measure
    """
    return list(QualityMetricEnum)[index].metricName

def getQualityMeasureIndexFromName(name: str) ->int:
    """Get quality metric index from name.

    Args:
        name (str): name of quality measure

    Returns:
        int: index of quality measure
    """
    for metric in list(QualityMetricEnum):
        if metric.metricName == name:
            return metric.metricIndex

def getQualityMeasureFromCellType(cellType: int) -> set[int]:
    """Get the indexes of mesh quality metrics defined for triangles.

    Returns:
        set[int]: set of possible indexes.
    """
    if cellType not in getAllCellTypesExtended():
        raise ValueError(f"Cell type {cellType} not in supported cell types {getAllCellTypesExtended()}.")
    return {metric.metricIndex for metric in list(QualityMetricEnum) if metric.isApplicableToCellType(cellType)}

def getTriangleQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for triangles.

    Returns:
        set[int]: set of possible indexes.
    """
    return getQualityMeasureFromCellType(VTK_TRIANGLE)

def getQuadQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getQualityMeasureFromCellType(VTK_QUAD)

def getCommonPolygonQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for both triangles and quads.

    Returns:
        set[int]: set of possible indexes.
    """
    triangleMetrics: set[int] = getTriangleQualityMeasure()
    quadMetrics: set[int] = getQuadQualityMeasure()
    return triangleMetrics.intersection(quadMetrics)

def getTetQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getQualityMeasureFromCellType(VTK_TETRA)

def getPyramidQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getQualityMeasureFromCellType(VTK_PYRAMID)

def getWedgeQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getQualityMeasureFromCellType(VTK_WEDGE)

def getHexQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getQualityMeasureFromCellType(VTK_HEXAHEDRON)

def getCommonPolyhedraQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for both triangles and quads.

    Returns:
        set[int]: set of possible indexes.
    """
    tetMetrics: set[int] = getTetQualityMeasure()
    pyrMetrics: set[int] = getPyramidQualityMeasure()
    wedgeMetrics: set[int] = getWedgeQualityMeasure()
    hexMetrics: set[int] = getHexQualityMeasure()
    return tetMetrics.intersection(pyrMetrics).intersection(wedgeMetrics).intersection(hexMetrics)

#: functor to get mesh quality metrics set from cell type
qualityMetricsFromCellType: dict[int, callable] = {
    VTK_TRIANGLE: getTriangleQualityMeasure,
    VTK_QUAD: getQuadQualityMeasure,
    VTK_TETRA: getTetQualityMeasure,
    VTK_PYRAMID: getPyramidQualityMeasure,
    VTK_WEDGE: getWedgeQualityMeasure,
    VTK_HEXAHEDRON: getHexQualityMeasure,
}
