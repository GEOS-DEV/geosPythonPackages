# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
import pytest
from typing import Iterator, Tuple
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkTetra, vtkUnstructuredGrid, VTK_TETRA
from geos.mesh_doctor.actions.collocatedNodes import Options, meshAction


def getPoints() -> Iterator[ Tuple[ vtkPoints, int ] ]:
    """Generates the data for the cases.

    One case has two nodes at the exact same position. The other has two different nodes.

    Returns:
        Iterator[ Tuple[ vtkPoints, int ] ]: The points and the expected number of buckets of collocated nodes.
    """
    for p0, p1 in ( ( 0, 0, 0 ), ( 1, 1, 1 ) ), ( ( 0, 0, 0 ), ( 0, 0, 0 ) ):
        points = vtkPoints()
        points.SetNumberOfPoints( 2 )
        points.SetPoint( 0, p0 )
        points.SetPoint( 1, p1 )
        numNodesBucket = 1 if p0 == p1 else 0
        yield points, numNodesBucket


@pytest.mark.parametrize( "data", getPoints() )
def test_simpleCollocatedPoints( data: Tuple[ vtkPoints, int ] ) -> None:
    """Tests the detection of collocated nodes for a simple case."""
    points, numNodesBucket = data

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )

    result = meshAction( mesh, Options( tolerance=1.e-12 ) )

    assert len( result.wrongSupportElements ) == 0
    assert len( result.nodesBuckets ) == numNodesBucket
    if numNodesBucket == 1:
        assert len( result.nodesBuckets[ 0 ] ) == points.GetNumberOfPoints()


def test_wrongSupportElements() -> None:
    """Tests that a tetrahedron with two nodes at the same location is detected."""
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
    tet.GetPointIds().SetId( 3, 0 )  # Intentionally wrong
    cells.InsertNextCell( tet )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cellTypes, cells )

    result = meshAction( mesh, Options( tolerance=1.e-12 ) )

    assert len( result.nodesBuckets ) == 0
    assert len( result.wrongSupportElements ) == 1
    assert result.wrongSupportElements[ 0 ] == 0
