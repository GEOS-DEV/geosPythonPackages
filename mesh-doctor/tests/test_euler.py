# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
import pytest
from vtkmodules.vtkFiltersCore import vtkFeatureEdges
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from geos.mesh_doctor.actions.euler import Options, meshAction
from .helpers import build_volume_with_non_manifold_edge, build_surface_with_non_manifold_edge

_OPTS = Options()


def test_volume_non_manifold_edge_detected() -> None:
    """Bowtie of two hexes sharing only one edge has a non-manifold boundary.

    ``build_volume_with_non_manifold_edge()`` produces two hexahedra that share
    only the edge (1,1,0)→(1,1,1).  On the extracted boundary surface that edge
    is touched by four faces (two from each hex), making it non-manifold.

    Expected topology (V=14, E=23, F=12, C=2):
      solidEulerCharacteristic = 14 - 23 + 12 - 2 = 1
      numNonManifoldEdges       = 1
      numConnectedComponents    = 1   (hexes share 2 points → same component)
    """
    result = meshAction( build_volume_with_non_manifold_edge(), _OPTS )

    assert result.numNonManifoldEdges == 1
    assert result.solidEulerCharacteristic == 1
    assert result.numConnectedComponents == 1
    assert result.numBoundaryEdges == 0


def test_volume_non_manifold_topology_counts() -> None:
    """Exact V/E/F/C counts for the bowtie configuration."""
    result = meshAction( build_volume_with_non_manifold_edge(), _OPTS )

    assert result.numVertices == 14
    assert result.numEdges == 23
    assert result.numFaces == 12
    assert result.numCells == 2


def test_surface_non_manifold_edge_detected() -> None:
    """Three quads sharing one edge form a non-manifold surface.

    ``build_surface_with_non_manifold_edge()`` returns a vtkUnstructuredGrid of
    3 VTK_QUAD cells.  Edge (1,0,0)→(1,1,0) is shared by all three faces.

    ``euler.meshAction`` requires 3D cells and raises ``RuntimeError`` on a
    pure surface mesh.  The non-manifold edge is verified directly via
    ``vtkFeatureEdges`` — the same filter ``euler.py`` uses internally.
    """
    ugrid = build_surface_with_non_manifold_edge()

    # euler.meshAction cannot handle a mesh with no 3D cells
    with pytest.raises( RuntimeError ):
        meshAction( ugrid, _OPTS )

    # Convert to polydata and run the same vtkFeatureEdges query euler.py uses
    gf = vtkGeometryFilter()
    gf.SetInputData( ugrid )
    gf.Update()
    surface = gf.GetOutput()

    fe = vtkFeatureEdges()
    fe.SetInputData( surface )
    fe.BoundaryEdgesOff()
    fe.ManifoldEdgesOff()
    fe.NonManifoldEdgesOn()
    fe.FeatureEdgesOff()
    fe.Update()

    # The edge (1,0,0)→(1,1,0) is shared by 3 quads → 1 non-manifold edge segment
    assert fe.GetOutput().GetNumberOfCells() > 0
