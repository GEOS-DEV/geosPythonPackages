# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
from geos.mesh_doctor.actions.orphan2d import Options, meshAction
from .helpers import ( build_hex_mesh, build_hex_mesh_with_fractures, build_tetra_mesh_with_fractures,
                       build_mesh_with_orphan_2d_cells )

_OPTS = Options( orphanVtkOutput=None, cleanVtkOutput=None )


def test_dedicated_orphan_cell() -> None:
    """Mesh with one matched and one orphaned 2D quad is correctly classified.

    ``build_mesh_with_orphan_2d_cells()`` contains:
      - 1 hex (3D)
      - 1 quad that IS the bottom face of the hex   → matched
      - 1 quad at z=2 that is NOT any face of the hex → orphan, cell index 2
      - 1 quad at z=[0,1] that is diagonal to hex and is NOT any face of the hex → orphan, cell index 3
    """
    result = meshAction( build_mesh_with_orphan_2d_cells(), _OPTS )

    assert result.total2dCells == 3
    assert result.total3dCells == 1
    assert result.matched2dCells == 1
    assert result.orphaned2dCells == 2
    assert result.orphaned2dIndices == [ 2, 3 ]


def test_clean_hex_has_no_orphans() -> None:
    """A pure volumetric hex mesh (no 2D cells) reports zero orphans."""
    result = meshAction( build_hex_mesh( 4, 4, 4 ), _OPTS )

    assert result.total2dCells == 0
    assert result.orphaned2dCells == 0


def test_hex_fracture_quads_are_orphans() -> None:
    """Fracture quads appended with MergePointsOff have disjoint point indices.

    ``build_hex_mesh_with_fractures`` combines the volume and fracture sub-meshes
    via ``vtkAppendFilter(MergePointsOff)``.  Because the fracture quad node IDs
    differ from those of the hex faces (even at the same coordinates),
    ``orphan2d.meshAction`` cannot match them → all fracture quads are orphans.

    5×5×5 grid with 1 fracture plane and default trim margins (offx=offy=1)
    produces 4 fracture quads, all orphaned.
    """
    mesh = build_hex_mesh_with_fractures( 5, 5, 5, nfrac=1 )
    result = meshAction( mesh, _OPTS )

    assert result.total3dCells == 64
    assert result.total2dCells == 4
    assert result.matched2dCells == 0
    assert result.orphaned2dCells == 4


def test_tetra_fracture_triangles_are_orphans() -> None:
    """Same MergePointsOff behaviour applies to tetra meshes with tri fractures.

    5×5×5 Delaunay tetra mesh with 1 fracture plane produces 8 triangles,
    all orphaned.
    """
    mesh = build_tetra_mesh_with_fractures( 5, 5, 5, nfrac=1 )
    result = meshAction( mesh, _OPTS )

    assert result.total3dCells > 0
    assert result.total2dCells == 8
    assert result.matched2dCells == 0
    assert result.orphaned2dCells == 8
