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

#: start index of additional cell quality metrics
CELL_QUALITY_METRIC_ADDITIONAL_START_INDEX: int = 100
#: start index of other mesh quality metrics
QUALITY_METRIC_OTHER_START_INDEX: int = 200

@dataclass( frozen=True )
class QualityRange():
    """Defines metric quality ranges."""
    acceptableRange: tuple[float, float]
    normalRange: tuple[float, float]
    fullRange: tuple[float, float]

class MeshQualityMetricEnum(Enum):
    def __init__(self: Self,
                 metricIndex: int,
                 name: str,
                ) -> None:
        """Define the enumeration to add attributes to mesh quality measures.

        Args:
            metricIndex (int): index of QualityMeasureTypes
            name (str): name of the metric
            applicableToCellTypes (tuple[bool, ...]): tuple defining for each cell type if the
                metric is applicable.
        """
        self.metricIndex: int = int(metricIndex)
        self.metricName: str = name

    def getMetricIndex(self: Self) -> int:
        """Get metric index.

        Returns:
            int: metric index
        """
        return self.metricIndex

    def getMetricName(self: Self) ->str:
        """Get metric name.

        Returns:
            str: metric name
        """
        return self.metricName

class CellQualityMetricEnum(MeshQualityMetricEnum):
    def __init__(self: Self,
                 metricIndex: int,
                 name: str,
                 applicableToCellTypes: tuple[bool, ...],
                 qualityRanges: tuple[QualityRange | None,...],
                ) -> None:
        """Define the enumeration to add attributes to mesh quality measures.

        Args:
            metricIndex (int): index of QualityMeasureTypes
            name (str): name of the metric
            applicableToCellTypes (tuple[bool, ...]): tuple defining for each cell type if the
                metric is applicable.
            qualityRanges (tuple[QualityRange | None,...]): quality range limits for each cell type
                starting from best to worst quality.
        """
        super().__init__(metricIndex, name)
        self.applicableToCellTypes: tuple[bool] = applicableToCellTypes
        self.qualityRanges: tuple[QualityRange | None,...] = qualityRanges

    def getApplicableCellTypes(self: Self) -> set[int]:
        """Get the list of cell type indexes the metric applies to.

        Returns:
            set[int]: set of cell type indexes
        """
        cellTypes = set()
        for i, cellType in enumerate(getAllCellTypes()):
            if self.applicableToCellTypes[i]:
                cellTypes.add(cellType)
        return cellTypes

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
class VtkCellQualityMetricEnum(CellQualityMetricEnum):
    """Cell quality metric enumeration.

    The order of boolean is the same as getAllCellTypes method:
    (VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON)

    .. CAUTION:: The order of the enum must follow the one of vtkMeshQuality.QualityMeasureTypes.

    """
    #: ratio of cell longest and shortest edge lengths
    EDGE_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,
        "Edge Ratio",
        (True, True, True, False, True, True),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None, 
         QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)),)
    )
    #: ratio of the maximum edge length to the inradius (for simplicial elements but adapted for quads).
    #: may be adapted for polyhedron other than tet by splitting the polyhedron in tet and computing the
    #: max of aspect ratio of all tet
    ASPECT_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO,
        "Aspect Ratio",
        (True, True, True, False, False, False),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None, None, None),
    )
    #: ratio between the radius of the inscribed circle/sphere to the radius of the circum-circle/sphere
    #: normalized so that the ratio yields 1 for equilateral cell
    RADIUS_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.RADIUS_RATIO,
        "Radius Ratio",
        (True, True, True, False, False, False),
        (QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None, None, None),
    )
    #: sum of the edge lengths squared divided by the area for triangles. Adapted for Tetrahedron.
    #: normalized so that equal to 1 when the element is equilateral triangle
    ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.ASPECT_FROBENIUS,
        "Aspect Frobenius",
        (True, False, True, False, False, False),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, None),
    )
    #: median of Aspect Frobenius over all triangles of quads / tetrahedra of hexahedron
    MEDIAN_ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS,
        "Med Aspect Frobenius",
        (False, True, False, False, False, True),
        (None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, None, QualityRange((1.0, 3.0), (1.0, 3.0), (9.0, np.inf)))
    )
    #: maximum of Aspect Frobenius over all triangles of Quads / tetrahedra of hexahedron
    MAXIMUM_ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.MAX_ASPECT_FROBENIUS,
        "Maximum Aspect Frobenius",
        (False, True, False, False, True, True),
        (None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)))
    )
    #: minimum angle between two neighboring edges for polygons / faces for tetrahedron.
    MINIMUM_ANGLE = (
        vtkMeshQuality.QualityMeasureTypes.MIN_ANGLE,
        "Minimum Angle (°)",
        (True, True, True, False, False, False),
        (QualityRange((30.0, 60.0), (0.0, 60.0), (0.0, 360.0)), QualityRange((45.0, 90.0), (0.0, 90.0), (0.0, 360.)),
         QualityRange((40.0, 180./np.pi*np.arccos(1/3)), (0.0, 180./np.pi*np.arccos(1/3)), (0.0, 360.0)), None, None, None)
    )
    #: the smallest ratio of the height of a vertex above its opposing triangle to
    #: the longest edge of that opposing triangle across all vertices of the tetrahedron
    COLLAPSE_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.COLLAPSE_RATIO,
        "Collapse Ratio",
        (False, False, True, False, False, False),
        (None, None, QualityRange((0.1, 1.0), (0.0, np.inf), (0.0, np.inf)), None, None, None)
    )
    #: maximum angle between two neighboring edges for polygons / faces for tetrahedron.
    MAXIMUM_ANGLE = (
        vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE,
        "Maximum Angle (°)",
        (True, True, False, False, False, False),
        (QualityRange((60., 90.0), (60.0, 180.0), (0.0, 180.0)), QualityRange((90.0, 135.0), (90.0, 360.0), (0.0, 360.)), None, None, None, None)
    )
    #: condition number of the weighted Jacobian matrix.
    CONDITION = (
        vtkMeshQuality.QualityMeasureTypes.CONDITION,
        "Condition",
        (True, True, True, False, True, True),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 4.0), (1.0, 12.0), (1.0, np.inf)), QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None,
         QualityRange((1.0, 4.0), (1.0, 12.0), (1.0, np.inf)), QualityRange((1.0, 4.0), (1.0, 12.0), (1.0, np.inf))),
    )
    #: Jacobian divided by the product of the lengths of the longest edges
    #: normalized so that a unit equilateral triangle has value 1.
    SCALED_JACOBIAN = (
        vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
        "Scaled Jacobian",
        (True, True, True, True, True, True),
        (QualityRange((0.5, 2.0*np.sqrt(3)/3.0), (-2.0*np.sqrt(3)/3.0, 2.0*np.sqrt(3)/3.0), (-np.inf, np.inf)), QualityRange((0.30, 1.0), (-1.0, 1.0), (-1.0, np.inf)),
         QualityRange((0.5, 0.5*np.sqrt(2)), (-0.5*np.sqrt(2), 0.5*np.sqrt(2)), (-np.inf, np.inf)), QualityRange((0.50, 1.0), (-1.0, 1.0), (-1.0, np.inf)),
         QualityRange((0.50, 1.0), (-1.0, 1.0), (-1.0, np.inf)), QualityRange((0.50, 1.0), (-1.0, 1.0), (-1.0, np.inf)),),
    )
    #: same as Scaled Jacobian
    SHEAR = (
        vtkMeshQuality.QualityMeasureTypes.SHEAR,
        "Shear",
        (False, True, False, False, False, True),
        (None, QualityRange((0.3, 0.6), (0.0, 1.0), (0.0, 1.0)), None, None, None, QualityRange((0.3, 0.6), (0.0, 1.0), (0.0, 1.0))))
    #: the minimum of the ratio of cell area/volume to the average area/volume of an ensemble of cells and its inverse.
    RELATIVE_SIZE_SQUARED = (
        vtkMeshQuality.QualityMeasureTypes.RELATIVE_SIZE_SQUARED,
        "Relative Size Squared",
        (True, True, True, False, False, True),
        (QualityRange((0.25, 0.50), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.6), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.50), (0.0, 1.0), (0.0, 1.0)), None, None, QualityRange((0.50, 1.0), (0.0, 1.0), (0.0, 1.0))),
    )
    #: inverse of Condition (Polygons) / Jacobian ratio
    SHAPE = (
        vtkMeshQuality.QualityMeasureTypes.SHAPE,
        "Shape",
        (True, True, True, True, True, True),
        (QualityRange((0.25, 0.50), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)),
         QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.30, 0.60), (0.0, 1.0), (0.0, 1.0)),),
    )
    #: relative size squared times shape
    SHAPE_AND_SIZE = (
        vtkMeshQuality.QualityMeasureTypes.SHAPE_AND_SIZE,
        "Shape And Size",
        (True, True, True, False, False, True),
        (QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)),
         QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.20, 0.4), (0.0, 1.0), (0.0, 1.0)),),
    )
    #: measure of how well-behaved the mapping from parameter space to world coordinates is. ratio of the
    #: minimum of Jacobian determinant to cell area/volume
    DISTORTION = (
        vtkMeshQuality.QualityMeasureTypes.DISTORTION,
        "Distortion",
        (True, True, True, False, True, True),
        (QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), None, 
         QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)), QualityRange((0.5, 1.0), (0.0, 1.0), (-np.inf, np.inf)),),
    )
    #: maximum of edge ratio over all triangles of the cell
    MAXIMUM_EDGE_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.MAX_EDGE_RATIO,
        "Maximum Edge Ratio",
        (False, True, False, False, False, True),
        (None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), None, None, None, QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)))
    )
    #: measures the angle (absolute value of the cosine) between the principal axes.
    SKEW = (
        vtkMeshQuality.QualityMeasureTypes.SKEW,
        "Skew",
        (False, True, False, False, False, True),
        (None, QualityRange((0.5, 1.0), (0.0, 1.0), (0.0, 1.0)), None, None, None, QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)))
    )
    #: maximum ratio of cross derivative magnitude to principal axis magnitude
    TAPER = (
        vtkMeshQuality.QualityMeasureTypes.TAPER,
        "Taper",
        (False, True, False, False, False, True),
        (None, QualityRange((0.0, 0.7), (0.0, 2.0), (0.0, np.inf)), None, None, None, QualityRange((0.0, 0.5), (0.0, 1.5), (0.0, np.inf)))
    )
    #: polyhedron volume
    VOLUME = (
        vtkMeshQuality.QualityMeasureTypes.VOLUME,
        "Volume (m3)",
        (False, False, True, True, True, True),
        (None, None, QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)),
         QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf))),
    )
    #: ratio of minimum edge length to longest diagonal length
    STRETCH = (
        vtkMeshQuality.QualityMeasureTypes.STRETCH,
        "Stretch",
        (False, True, False, False, False, True),
        (None, QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, np.inf)), None, None, None, QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, np.inf)))
    )
    #: ratio of the minimum diagonal length to the maximum diagonal length
    DIAGONAL = (
        vtkMeshQuality.QualityMeasureTypes.DIAGONAL,
        "Diagonal",
        (False, False, False, False, False, True),
        (None, None, None, None, None, QualityRange((0.65, 1.0), (0.0, 1.0), (0.0, np.inf)),)
    )
    # ratio of cell volume to the gradient (divergence?) of cell volumes at the cell. Acceptable range is application dependent.
    DIMENSION = (
        vtkMeshQuality.QualityMeasureTypes.DIMENSION,
        "Dimension (m)",
        (False, False, False, False, False, True),
        (None, None, None, None, None, QualityRange((0.0, np.inf), (0.0, np.inf), (0.0, np.inf)),)
    )
    #: measures the maximum deviation of the metric tensor at the corners of the quadrilateral. Maximum of oddy for hexahedron.
    ODDY = (
        vtkMeshQuality.QualityMeasureTypes.ODDY,
        "Oddy",
        (False, True, False, False, False, True),
        (None, QualityRange((0.0, 0.5), (0.0, 1.5), (0.0, np.inf)), None, None, None, QualityRange((0.0, 0.5), (0.0, 1.5), (0.0, np.inf)),)
    )
    #: relative size squared times shear
    SHEAR_AND_SIZE = (
        vtkMeshQuality.QualityMeasureTypes.SHEAR_AND_SIZE,
        "Shear And Size",
        (False, True, False, False, False, True),
        (None, QualityRange((0.2, 0.4), (0.0, 1.0), (0.0, 1.0)), None, None, None, QualityRange((0.2, 0.4), (0.0, 1.0), (0.0, 1.0)))
    )
    #: minimum determinant of the Jacobian matrix evaluated at each corner and the center of the element
    JACOBIAN = (
        vtkMeshQuality.QualityMeasureTypes.JACOBIAN,
        "Jacobian",
        (False, True, True, True, True, True),
        (None, QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)),
         QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)),)
    )
    #: the cosine of the minimum dihedral angle formed by planes intersecting in diagonals (to the fourth power)
    WARPAGE = (
        vtkMeshQuality.QualityMeasureTypes.WARPAGE,
        "Warpage",
        (False, True, False, False, False, False),
        (None, QualityRange((0.0, 0.7), (0.0, 2.0), (0.0, np.inf)), None, None, None, None)
    )
    #: ratio of root-mean-square edge length to volume.
    #: normalizing the metric to a value of 1 for equilateral tetrahedra
    ASPECT_GAMMA = (
        vtkMeshQuality.QualityMeasureTypes.ASPECT_GAMMA,
        "Aspect Gamma",
        (False, False, True, False, False, False),
        (None, None, QualityRange((1.0, 3.0), (1.0, 9.0), (0.0, np.inf)), None, None, None)
    )
    #: polygon area
    AREA = (
        vtkMeshQuality.QualityMeasureTypes.AREA,
        "Area (m2)",
        (True, True, False, False, False, False),
        (QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), QualityRange((0.0, np.inf), (0.0, np.inf), (-np.inf, np.inf)), None, None, None, None),
    )
    #: maximum of ratio of angular deviation from ideal element
    EQUIANGLE_SKEW = (
        vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
        "Equiangle Skew",
        (True, True, True, True, True, True),
        (QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)),
         QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)), QualityRange((0.0, 0.5), (0.0, 1.0), (0.0, 1.0)),)
    )
    #: maximum of ratio of volume deviation from ideal element
    EQUIVOLUME_SKEW = (
        vtkMeshQuality.QualityMeasureTypes.EQUIVOLUME_SKEW,
        "Equivolume Skew",
        (False, False, True, False, False, False),
        (None, None, QualityRange((0.0, 0.3), (0.0, 0.9), (0.0, 1.0)), None, None, None)
    )
    #: maximum stretch over tetrahedra
    MAXIMUM_STRETCH = (
        vtkMeshQuality.QualityMeasureTypes.MAX_STRETCH,
        "Maximum Stretch",
        (False, False, False, False, True, False),
        (None, None, None, None, QualityRange((0.25, 0.5), (0.0, 1.0), (0.0, np.inf)), None)
    )
    #: mean of Aspect Frobenius over all triangles of Quads / tetrahedra of hexahedron
    MEAN_ASPECT_FROBENIUS = (
        vtkMeshQuality.QualityMeasureTypes.MEAN_ASPECT_FROBENIUS,
        "Mean Aspect Frobenius",
        (False, False, False, False, True, False),
        (None, None, None, None, QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None)
    )
    #: ratio of tetrahedron volume over the volume of an equilateral tetrahedron with the same root mean squared edge length
    MEAN_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.MEAN_RATIO,
        "Mean Ratio",
        (False, False, True, False, False, False),
        (None, None, QualityRange((0.0, 0.3), (0.0, 0.9), (0.0, 1.0)), None, None, None)
    )
    #: ratio between the largest and smallest Jacobian determinant value
    NODAL_JACOBIAN_RATIO = (
        vtkMeshQuality.QualityMeasureTypes.NODAL_JACOBIAN_RATIO,
        "Nodal Jacobian Ratio",
        (False, False, False, False, False, True),
        (None, None, None, None, None, QualityRange((0.0, np.inf), (0.0, np.inf), (0.0, np.inf)))
    )
    #: ratio of the minimum sub-triangle inner radius to the outer triangle radius
    NORMALIZED_INRADIUS = (
        vtkMeshQuality.QualityMeasureTypes.NORMALIZED_INRADIUS,
        "Normalized Inradius",
        (True, False, True, False, False, False),
        (QualityRange((0.15, 0.5), (-1.0, 1.0), (-1.0, 1.0)), None, QualityRange((0.15, 0.5), (-1.0, 1.0), (-1.0, 1.0)), None, None, None)
    )
    #: measure used to quantify how far a cell deviates from orthogonality with respect to its face
    #: maximum of sinus of the angle between the vector from polyhedron center and face center and face normal
    #: yields 0 if vectors are parallel, 1 if they are orthogonal
    SQUISH_INDEX = (
        vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX,
        "Squish Index",
        (False, False, True, True, True, True),
        (None, None, QualityRange((0.0, 0.3), (0.0, 0.9), (0.0, 1.0)), None, None, None)
    )
    #: no metric
    NONE = (
        vtkMeshQuality.QualityMeasureTypes.NONE,
        "None",
        (False, False, False, False, False, False),
        (None, None, None, None, None, None)
    )

class CellQualityMetricAdditionalEnum(CellQualityMetricEnum):
    """Additional cell quality metric enumeration.

    The order of boolean is the same as getAllCellTypes method:
    (VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON)

    Metric index starts at 100 to prevent from conflicts with basic metrics and is incremented
    in the order of the enumeration.

    """
    #: maximum of aspect ratio over all tets .
    MAXIMUM_ASPECT_RATIO = (
        100,
        "Maximum Aspect Ratio",
        (False, False, False, True, True, True),
        (QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)), QualityRange((1.0, 1.3), (1.0, 3.0), (1.0, np.inf)),
         QualityRange((1.0, 3.0), (1.0, 9.0), (1.0, np.inf)), None, None, None),
    )
    # other metrics can be defined the same way such as RADIUS_RATIO, EDGE_RATIO, ASPECT_GAMMA, EQUIVOLUME_SKEW,
    # NORMALIZED_INRADIUS, (MAXIMUM_)ASPECT_FROBENIUS for pyramids, (MAXIMUM_)STRETCH for pyramids

class QualityMetricOtherEnum(MeshQualityMetricEnum):
    """Additional metrics that apply to the mesh, not to specific cell type.

    Metric index starts at 200 to prevent from conflicts with other metrics and is incremented
    in the order of the enumeration.
    """
    #: number of incident edges for each vertex
    INCIDENT_VERTEX_COUNT = (200, "Incident Vertex Count")


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

def getQualityMetricFromIndex(metricIndex: int) -> Optional[MeshQualityMetricEnum]:
    """Get quality metric from its index.

    Args:
        metricIndex (int): metric index

    Raises:
        IndexError: Metric index is out of range

    Returns:
        MeshQualityMetricEnum | None: quality metric
    """
    if metricIndex < CELL_QUALITY_METRIC_ADDITIONAL_START_INDEX:
        return list(VtkCellQualityMetricEnum)[metricIndex]
    elif metricIndex < QUALITY_METRIC_OTHER_START_INDEX:
        return list(CellQualityMetricAdditionalEnum)[metricIndex - CELL_QUALITY_METRIC_ADDITIONAL_START_INDEX]
    elif metricIndex < QUALITY_METRIC_OTHER_START_INDEX + len(list(QualityMetricOtherEnum)):
        return list(QualityMetricOtherEnum)[metricIndex - QUALITY_METRIC_OTHER_START_INDEX]
    return None

def getQualityMeasureNameFromIndex(metricIndex: int) ->str:
    """Get quality metric name from index.

    Args:
        metricIndex (int): index of quality measure

    Returns:
        str: name of quality measure
    """
    metric = getQualityMetricFromIndex(metricIndex)
    if metric is None:
        return None
    return metric.getMetricName()

def getQualityMeasureIndexFromName(name: str) ->int:
    """Get quality metric index from name.

    Args:
        name (str): name of quality measure

    Returns:
        int: index of quality measure
    """
    for metric in list(VtkCellQualityMetricEnum) + list(CellQualityMetricAdditionalEnum) + list(QualityMetricOtherEnum):
        if metric.getMetricName() == name:
            return metric.getMetricIndex()
    return ""

def getCellQualityMeasureFromCellType(cellType: int) -> set[int]:
    """Get the indexes of mesh quality metrics defined for triangles.

    Returns:
        set[int]: set of possible indexes.
    """
    if cellType not in getAllCellTypesExtended():
        raise ValueError(f"Cell type {cellType} not in supported cell types {getAllCellTypesExtended()}.")
    return {metric.metricIndex for metric in list(VtkCellQualityMetricEnum) + list(CellQualityMetricAdditionalEnum) if metric.isApplicableToCellType(cellType)}

def getTriangleQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for triangles.

    Returns:
        set[int]: set of possible indexes.
    """
    return getCellQualityMeasureFromCellType(VTK_TRIANGLE)

def getQuadQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getCellQualityMeasureFromCellType(VTK_QUAD)

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
    return getCellQualityMeasureFromCellType(VTK_TETRA)

def getPyramidQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getCellQualityMeasureFromCellType(VTK_PYRAMID)

def getWedgeQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getCellQualityMeasureFromCellType(VTK_WEDGE)

def getHexQualityMeasure() -> set[int]:
    """Get the indexes of mesh quality metrics defined for quads.

    Returns:
        set[int]: set of possible indexes.
    """
    return getCellQualityMeasureFromCellType(VTK_HEXAHEDRON)

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

def getQualityMetricsOther() ->set[int]:
    """Get the set of indexes of other mesh quality metric.

    Returns:
        set[int]: other mesh quality metric indexes
    """
    return {metric.getMetricIndex() for metric in list(QualityMetricOtherEnum)}

#: dictionary of cell quality metrics set from cell type
cellQualityMetricsFromCellType: dict[int, set[int]] = {
    VTK_TRIANGLE: getTriangleQualityMeasure(),
    VTK_QUAD: getQuadQualityMeasure(),
    VTK_TETRA: getTetQualityMeasure(),
    VTK_PYRAMID: getPyramidQualityMeasure(),
    VTK_WEDGE: getWedgeQualityMeasure(),
    VTK_HEXAHEDRON: getHexQualityMeasure(),
}
