# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto, Jacques Franc
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkHexahedron, vtkUnstructuredGrid, VTK_HEXAHEDRON
from geos.mesh_doctor.actions.selfIntersectingElements import Options, meshAction
from .helpers import build_mesh_with_negative_volume


def test_jumbledHex() -> None:
    """Tests that a hexahedron with intersecting faces is detected."""
    # creating a simple hexahedron
    points = vtkPoints()
    points.SetNumberOfPoints( 8 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 1, 1, 0 ) )
    points.SetPoint( 3, ( 0, 1, 0 ) )
    points.SetPoint( 4, ( 0, 0, 1 ) )
    points.SetPoint( 5, ( 1, 0, 1 ) )
    points.SetPoint( 6, ( 1, 1, 1 ) )
    points.SetPoint( 7, ( 0, 1, 1 ) )

    cellTypes = [ VTK_HEXAHEDRON ]
    cells = vtkCellArray()
    cells.AllocateExact( 1, 8 )

    hex = vtkHexahedron()
    hex.GetPointIds().SetId( 0, 0 )
    hex.GetPointIds().SetId( 1, 1 )
    hex.GetPointIds().SetId( 2, 3 )  # Intentionally wrong
    hex.GetPointIds().SetId( 3, 2 )  # Intentionally wrong
    hex.GetPointIds().SetId( 4, 4 )
    hex.GetPointIds().SetId( 5, 5 )
    hex.GetPointIds().SetId( 6, 6 )
    hex.GetPointIds().SetId( 7, 7 )
    cells.InsertNextCell( hex )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cellTypes, cells )

    result = meshAction( mesh, Options( minDistance=0. ) )

    assert len( result.invalidCellIds[ "intersectingFacesElements" ] ) == 1
    assert result.invalidCellIds[ "intersectingFacesElements" ][ 0 ] == 0


def test_inverted_hex_orientation_from_gen_mesh() -> None:
    """Inverted hex (top/bottom node groups swapped) is caught by orientation checks.

    ``build_mesh_with_negative_volume()`` contains two hexes:
      - cell 0: correctly oriented unit cube
      - cell 1: top and bottom face groups swapped → non-convex + wrong face orientation

    ``vtkCellValidator`` flags cell 1 via:
      - ``nonConvexElements``              (concavity caused by the inversion)
      - ``facesOrientedIncorrectlyElements`` (inward-pointing normals)

    Cell 0 must NOT appear in either of those categories.
    """
    mesh = build_mesh_with_negative_volume()
    result = meshAction( mesh, Options( minDistance=0. ) )

    assert result.invalidCellIds[ "nonConvexElements" ] == [ 1 ]
    assert result.invalidCellIds[ "facesOrientedIncorrectlyElements" ] == [ 1 ]
