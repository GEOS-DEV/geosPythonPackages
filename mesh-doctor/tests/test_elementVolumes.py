# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto, Jacques Franc
import numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import VTK_TETRA, vtkCellArray, vtkTetra, vtkUnstructuredGrid
from geos.mesh_doctor.actions.elementVolumes import Options, meshAction
from .helpers import build_mesh_with_negative_volume


def test_simpleTet() -> None:
    """Tests the calculation of element volumes for a simple tetrahedron."""
    # creating a simple tetrahedron
    points = vtkPoints()
    points.SetNumberOfPoints( 4 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 0, 1, 0 ) )
    points.SetPoint( 3, ( 0, 0, 1 ) )

    cellTypes = [ VTK_TETRA ]
    cells = vtkCellArray()
    cells.AllocateExact( 1, 4 )

    tet = vtkTetra()
    tet.GetPointIds().SetId( 0, 0 )
    tet.GetPointIds().SetId( 1, 1 )
    tet.GetPointIds().SetId( 2, 2 )
    tet.GetPointIds().SetId( 3, 3 )
    cells.InsertNextCell( tet )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cellTypes, cells )

    result = meshAction( mesh, Options( minVolume=1. ) )

    assert len( result.elementVolumes ) == 1
    assert result.elementVolumes[ 0 ][ 0 ] == 0
    assert abs( result.elementVolumes[ 0 ][ 1 ] - 1. / 6. ) < 10 * numpy.finfo( float ).eps

    result = meshAction( mesh, Options( minVolume=0. ) )

    assert len( result.elementVolumes ) == 0


def test_negative_volume_hex_detected() -> None:
    """Hexahedron with top/bottom node groups swapped has negative signed volume.

    ``build_mesh_with_negative_volume()`` contains two hexes:
      - cell 0: correctly oriented unit cube → positive volume (+1.0)
      - cell 1: top and bottom face groups swapped → negative volume (−1.0)

    With ``minVolume=0`` only cells whose volume ≤ minVolume are reported.
    Cell 1 (volume ≈ −1.0) must appear; cell 0 must not.
    """
    mesh = build_mesh_with_negative_volume()
    result = meshAction( mesh, Options( minVolume=0.0 ) )

    assert len( result.elementVolumes ) == 1
    assert result.elementVolumes[ 0 ][ 0 ] == 1  # second cell
    assert result.elementVolumes[ 0 ][ 1 ] < 0.0  # negative volume


def test_positive_volume_hex_not_reported() -> None:
    """The correctly oriented hex in the same mesh is not flagged."""
    mesh = build_mesh_with_negative_volume()

    # With threshold just below the correct cell volume (+1.0) nothing is reported
    result = meshAction( mesh, Options( minVolume=-0.5 ) )

    flagged_ids = { entry[ 0 ] for entry in result.elementVolumes }
    assert 0 not in flagged_ids  # cell 0 is valid, volume ≈ +1.0
