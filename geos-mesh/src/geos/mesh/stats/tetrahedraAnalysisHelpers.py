# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Bertrand Denel, Paloma Martinez
import numpy as np
import numpy.typing as npt
from typing_extensions import Any

from vtkmodules.vtkCommonDataModel import vtkDataSet, VTK_TETRA


def getCoordinatesDoublePrecision( mesh: vtkDataSet ) -> npt.NDArray[ np.float64 ]:
    """Get coordinates with double precision.

    Args:
        mesh (vtkDataSet): Input mesh.

    Returns:
        npt.NDArray[np.float64]: Coordinates

    """
    points = mesh.GetPoints()
    npoints = points.GetNumberOfPoints()

    coords = np.zeros( ( npoints, 3 ), dtype=np.float64 )
    for i in range( npoints ):
        point = points.GetPoint( i )
        coords[ i ] = [ point[ 0 ], point[ 1 ], point[ 2 ] ]

    return coords


def extractTetConnectivity( mesh: vtkDataSet ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ] ]:
    """Extract connectivity for all tetrahedra.

    Args:
        mesh (vtkDataSet): Mesh to analyze.

    Returns:
        tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
                Cell IDS corresponding to tetrahedra,
                Connectivity of these cells
    """
    ncells = mesh.GetNumberOfCells()
    tetrahedraIds = []
    tetrahedraConnectivity = []

    for cellID in range( ncells ):
        if mesh.GetCellType( cellID ) == VTK_TETRA:
            cell = mesh.GetCell( cellID )
            pointIds = cell.GetPointIds()
            conn = [ pointIds.GetId( i ) for i in range( 4 ) ]
            tetrahedraIds.append( cellID )
            tetrahedraConnectivity.append( conn )

    return np.array( tetrahedraIds ), np.array( tetrahedraConnectivity )


def analyzeAllTets( n: int, coords: npt.NDArray[ np.float64 ],
                    connectivity: npt.NDArray[ np.float64 ] ) -> dict[ str, dict[ str, Any ] ]:
    """Vectorized analysis of all tetrahedra.

    Args:
        n (int): Mesh id.
        coords (npt.NDArray[np.float64]): Tetrahedra coordinates.
        connectivity (npt.NDArray[np.float64]): Connectivity.

    Returns:
        dict[str, dict[str, Any]]: Dictionary with keys 'volumes', 'aspectRatio', 'radiusRatio', 'flatnessRatio', 'shapeQuality', 'minEdge', 'maxEdge', 'minDihedral', 'maxDihedral', 'dihedralRange'
    """
    # Get coordinates for all vertices
    v0 = coords[ connectivity[ :, 0 ] ]
    v1 = coords[ connectivity[ :, 1 ] ]
    v2 = coords[ connectivity[ :, 2 ] ]
    v3 = coords[ connectivity[ :, 3 ] ]

    # Compute edges
    e01 = v1 - v0
    e02 = v2 - v0
    e03 = v3 - v0
    e12 = v2 - v1
    e13 = v3 - v1
    e23 = v3 - v2

    # Edge lengths
    l01 = np.linalg.norm( e01, axis=1 )
    l02 = np.linalg.norm( e02, axis=1 )
    l03 = np.linalg.norm( e03, axis=1 )
    l12 = np.linalg.norm( e12, axis=1 )
    l13 = np.linalg.norm( e13, axis=1 )
    l23 = np.linalg.norm( e23, axis=1 )

    allEdges = np.stack( [ l01, l02, l03, l12, l13, l23 ], axis=1 )
    minEdge = np.min( allEdges, axis=1 )
    maxEdge = np.max( allEdges, axis=1 )

    # Volumes
    cross_product = np.cross( e01, e02 )
    volumes = np.abs( np.sum( cross_product * e03, axis=1 ) / 6.0 )

    # Face areas
    face012 = 0.5 * np.linalg.norm( np.cross( e01, e02 ), axis=1 )
    face013 = 0.5 * np.linalg.norm( np.cross( e01, e03 ), axis=1 )
    face023 = 0.5 * np.linalg.norm( np.cross( e02, e03 ), axis=1 )
    face123 = 0.5 * np.linalg.norm( np.cross( e12, e13 ), axis=1 )

    allFaces = np.stack( [ face012, face013, face023, face123 ], axis=1 )
    maxFaceArea = np.max( allFaces, axis=1 )
    totalSurfaceArea = np.sum( allFaces, axis=1 )

    # Aspect ratio
    minAltitude = 3.0 * volumes / np.maximum( maxFaceArea, 1e-15 )
    aspectRatio = maxEdge / np.maximum( minAltitude, 1e-15 )
    aspectRatio[ volumes < 1e-15 ] = np.inf

    # Radius ratio
    inradius = 3.0 * volumes / np.maximum( totalSurfaceArea, 1e-15 )
    circumradius = ( maxEdge**3 ) / np.maximum( 24.0 * volumes, 1e-15 )
    radiusRatio = circumradius / np.maximum( inradius, 1e-15 )

    # Flatness ratio
    flatnessRatio = volumes / np.maximum( maxFaceArea * minEdge, 1e-15 )

    # Shape quality
    sumEdgeShapeQuality = np.sum( allEdges**2, axis=1 )
    shapeQuality = 12.0 * ( 3.0 * volumes )**( 2.0 / 3.0 ) / np.maximum( sumEdgeShapeQuality, 1e-15 )
    shapeQuality[ volumes < 1e-15 ] = 0.0

    # Dihedral angles
    def computeDihedralAngle( normal1: npt.NDArray[ np.float64 ],
                              normal2: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
        """Compute dihedral angle between two face normals.

        Args:
            normal1 (npt.NDArray[np.float64]): Normal vector 1
            normal2 (npt.NDArray[np.float64]): Normal vector 2

        Returns:
            npt.NDArray[ np.float64 ]: Dihedral angle

        """
        n1Norm = normal1 / np.maximum( np.linalg.norm( normal1, axis=1, keepdims=True ), 1e-15 )
        n2Norm = normal2 / np.maximum( np.linalg.norm( normal2, axis=1, keepdims=True ), 1e-15 )
        cosAngle = np.sum( n1Norm * n2Norm, axis=1 )
        cosAngle = np.clip( cosAngle, -1.0, 1.0 )
        angle = np.arccos( cosAngle ) * 180.0 / np.pi
        return angle

    # Face normals
    normal012: npt.NDArray[ np.float64 ] = np.cross( e01, e02 )
    normal013: npt.NDArray[ np.float64 ] = np.cross( e01, e03 )
    normal023: npt.NDArray[ np.float64 ] = np.cross( e02, e03 )
    normal123: npt.NDArray[ np.float64 ] = np.cross( e12, e13 )

    # Dihedral angles for each edge
    dihedral01 = computeDihedralAngle( normal012, normal013 )
    dihedral02 = computeDihedralAngle( normal012, normal023 )
    dihedral03 = computeDihedralAngle( normal013, normal023 )
    dihedral12 = computeDihedralAngle( normal012, normal123 )
    dihedral13 = computeDihedralAngle( normal013, normal123 )
    dihedral23 = computeDihedralAngle( normal023, normal123 )

    allDihedrals = np.stack( [ dihedral01, dihedral02, dihedral03, dihedral12, dihedral13, dihedral23 ], axis=1 )

    minDihedral = np.min( allDihedrals, axis=1 )
    maxDihedral = np.max( allDihedrals, axis=1 )
    dihedralRange = maxDihedral - minDihedral

    return {
        'volumes': volumes,
        'aspectRatio': aspectRatio,
        'radiusRatio': radiusRatio,
        'flatnessRatio': flatnessRatio,
        'shapeQuality': shapeQuality,
        'minEdge': minEdge,
        'maxEdge': maxEdge,
        'minDihedral': minDihedral,
        'maxDihedral': maxDihedral,
        'dihedralRange': dihedralRange
    }


# Combined quality score
def computeQualityScore( aspectRatio: npt.NDArray[ np.float64 ], shapeQuality: npt.NDArray[ np.float64 ],
                         edgeRatio: npt.NDArray[ np.float64 ],
                         minDihedralAngle: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    """Compute combined quality score (0-100).

    Args:
        aspectRatio(npt.NDArray[np.float64]): Aspect ratio
        shapeQuality(npt.NDArray[np.float64]): Shape quality
        edgeRatio(npt.NDArray[np.float64]): Edge ratio
        minDihedralAngle(npt.NDArray[np.float64]): Minimal edge ratio

    Returns:
        np.float64: Quality score
    """
    aspectRatioNorm = np.clip( 1.0 / ( aspectRatio / 1.73 ), 0, 1 )
    shapeQualityNorm = shapeQuality
    edgeRatioNorm = np.clip( 1.0 / edgeRatio, 0, 1 )
    dihedralMinNorm = np.clip( minDihedralAngle / 60.0, 0, 1 )
    score = ( 0.3 * aspectRatioNorm + 0.4 * shapeQualityNorm + 0.2 * edgeRatioNorm + 0.1 * dihedralMinNorm ) * 100

    return score
