# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
from typing import Optional, Iterable
from typing_extensions import Self
from enum import Enum
from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import (
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON
)


__doc__ = """
Helpers for MeshQuality metrics.
"""

class QualityMetricAbstractEnum(Enum):
    def __init__(self: Self,
                 qualityMeasureTypesIndex: vtkMeshQuality.QualityMeasureTypes,
                 name: str,
                 applicableToCellTypes: tuple[bool, ...]
                ) -> None:
        """Define the enumeration to add attributes to mesh quality measures.

        Args:
            qualityMeasureTypesIndex (vtkMeshQuality.QualityMeasureTypes): index of QualityMeasureTypes
            name (str): name of the metric
            cellTypes (tuple[bool, ...]): tuple defining for each cell type if the
                metric is applicable.
        """
        self.metricIndex: str = int(qualityMeasureTypesIndex)
        self.metricName: int = name
        self.applicableToCellTypes: tuple[bool] = applicableToCellTypes

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

#: from https://vtk.org/doc/nightly/html/vtkMeshQuality_8h_source.html
class QualityMetricEnum(QualityMetricAbstractEnum):
    """Mesh quality metric enumeration.

    The order of boolean is the same as getAllCellTypes method:
    (VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON)

    .. CAUTION:: The order of the enum must follow the one of vtkMeshQuality.QualityMeasureTypes.

    """
    EDGE_RATIO              = (vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,            "Edge Ratio",               (True, True, True, False, True, True))
    ASPECT_RATIO            = (vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO,          "Aspect Ratio",             (True, True, True, False, False, False))
    RADIUS_RATIO            = (vtkMeshQuality.QualityMeasureTypes.RADIUS_RATIO,          "Radius Ratio",             (True, True, True, False, False, False))
    ASPECT_FROBENIUS        = (vtkMeshQuality.QualityMeasureTypes.ASPECT_FROBENIUS,      "Aspect Frobenius",         (True, False, True, False, False, False))
    MEDIAN_ASPECT_FROBENIUS = (vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS,  "Med Aspect Frobenius",     (False, True, False, False, False, True))
    MAXIMUM_ASPECT_FROBENIUS= (vtkMeshQuality.QualityMeasureTypes.MAX_ASPECT_FROBENIUS,  "Maximum Aspect Frobenius", (False, True, False, False, True, True))
    MINIMUM_ANGLE           = (vtkMeshQuality.QualityMeasureTypes.MIN_ANGLE,             "Minimum Angle",            (True, True, True, False, False, False))
    COLLAPSE_RATIO          = (vtkMeshQuality.QualityMeasureTypes.COLLAPSE_RATIO,        "Collapse Ratio",           (False, False, True, False, False, False))
    MAXIMUM_ANGLE           = (vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE,             "Maximum Angle",            (True, True, False, False, False, False))
    CONDITION               = (vtkMeshQuality.QualityMeasureTypes.CONDITION,             "Condition",                (True, True, True, False, True, True))
    SCALED_JACOBIAN         = (vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,       "Scaled Jacobian",          (True, True, True, True, True, True))
    SHEAR                   = (vtkMeshQuality.QualityMeasureTypes.SHEAR,                 "Shear",                    (False, True, False, False, False, True))
    RELATIVE_SIZE_SQUARED   = (vtkMeshQuality.QualityMeasureTypes.RELATIVE_SIZE_SQUARED, "Relative Size Squared",    (True, True, True, False, False, True))
    SHAPE                   = (vtkMeshQuality.QualityMeasureTypes.SHAPE,                 "Shape",                    (True, True, True, True, True, True))
    SHAPE_AND_SIZE          = (vtkMeshQuality.QualityMeasureTypes.SHAPE_AND_SIZE,        "Shape And Size",           (True, True, True, False, False, True))
    DISTORTION              = (vtkMeshQuality.QualityMeasureTypes.DISTORTION,            "Distortion",               (True, True, True, False, True, True))
    MAXIMUM_EDGE_RATIO      = (vtkMeshQuality.QualityMeasureTypes.MAX_EDGE_RATIO,        "Maximum Edge Ratio",       (False, True, False, False, False, True))
    SKEW                    = (vtkMeshQuality.QualityMeasureTypes.SKEW,                  "Skew",                     (False, True, False, False, False, True))
    TAPER                   = (vtkMeshQuality.QualityMeasureTypes.TAPER,                 "Taper",                    (False, True, False, False, False, True))
    VOLUME                  = (vtkMeshQuality.QualityMeasureTypes.VOLUME,                "Volume",                   (False, False, True, True, True, True))
    STRETCH                 = (vtkMeshQuality.QualityMeasureTypes.STRETCH,               "Stretch",                  (False, True, False, False, False, True))
    DIAGONAL                = (vtkMeshQuality.QualityMeasureTypes.DIAGONAL,              "Diagonal",                 (False, False, False, False, False, True))
    DIMENSION               = (vtkMeshQuality.QualityMeasureTypes.DIMENSION,             "Dimension",                (False, False, False, False, False, True))
    ODDY                    = (vtkMeshQuality.QualityMeasureTypes.ODDY,                  "Oddy",                     (False, True, False, False, False, True))
    SHEAR_AND_SIZE          = (vtkMeshQuality.QualityMeasureTypes.SHEAR_AND_SIZE,        "Shear And Size",           (False, True, False, False, False, True))
    JACOBIAN                = (vtkMeshQuality.QualityMeasureTypes.JACOBIAN,              "Jacobian",                 (False, True, True, True, True, True))
    WARPAGE                 = (vtkMeshQuality.QualityMeasureTypes.WARPAGE,               "Warpage",                  (False, True, False, False, False, False))
    ASPECT_GAMMA            = (vtkMeshQuality.QualityMeasureTypes.ASPECT_GAMMA,          "Aspect Gamma",             (False, False, True, False, False, False))
    AREA                    = (vtkMeshQuality.QualityMeasureTypes.AREA,                  "Area",                     (True, True, False, False, False, False))
    EQUIANGLE_SKEW          = (vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,        "Equiangle Skew",           (True, True, True, True, True, True))
    EQUIVOLUME_SKEW         = (vtkMeshQuality.QualityMeasureTypes.EQUIVOLUME_SKEW,       "Equivolume Skew",          (False, False, True, False, False, False))
    MAXIMUM_STRETCH         = (vtkMeshQuality.QualityMeasureTypes.MAX_STRETCH,           "Maximum Stretch",          (False, False, False, False, True, False))
    MEAN_ASPECT_FROBENIUS   = (vtkMeshQuality.QualityMeasureTypes.MEAN_ASPECT_FROBENIUS, "Mean Aspect Frobenius",    (False, False, False, False, True, False))
    MEAN_RATIO              = (vtkMeshQuality.QualityMeasureTypes.MEAN_RATIO,            "Mean Ratio",               (False, False, True, False, False, False))
    NODAL_JACOBIAN_RATIO    = (vtkMeshQuality.QualityMeasureTypes.NODAL_JACOBIAN_RATIO,  "Nodal Jacobian Ratio",     (False, False, False, False, False, True))
    NORMALIZED_INRADIUS     = (vtkMeshQuality.QualityMeasureTypes.NORMALIZED_INRADIUS,   "Normalized Inradius",      (True, False, True, False, False, False))
    SQUISH_INDEX            = (vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX,          "Squish index",             (False, False, True, False, False, False))
    NONE                    = (vtkMeshQuality.QualityMeasureTypes.NONE,                  "None",                     (False, False, False, False, False, False))

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
