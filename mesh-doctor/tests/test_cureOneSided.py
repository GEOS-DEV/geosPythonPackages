# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Tests for the cureOneSided action and its CLI parsing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkCellArray, vtkUnstructuredGrid, VTK_HEXAHEDRON, VTK_QUAD )

from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid
from geos.mesh_doctor.actions.cureOneSided import ( FAULT_SIDE_ARRAY, ON_HOLE_ARRAY, Options, action, meshAction )
from geos.mesh_doctor.parsing import cureOneSidedParsing

# The left block holds point ids 0..11, the right block 12..23 (see __buildSplitMesh).
NUM_LEFT_POINTS: int = 12
TAG_ARRAY: str = "FaultMask"


def __leftPoint( i: int, j: int, k: int ) -> int:
    """Return the id of the left-block point at grid position (i, j, k)."""
    return i * 6 + j * 2 + k


def __rightPoint( i: int, j: int, k: int ) -> int:
    """Return the id of the right-block point at grid position (i, j, k)."""
    return NUM_LEFT_POINTS + i * 6 + j * 2 + k


def __buildSplitMesh( leftQuadFirst: bool = True ) -> vtkUnstructuredGrid:
    """Build a 2x2x1 hexahedral mesh split along the x = 1 plane, tagged with two fault quads.

    The two blocks (x in [0, 1] and x in [1, 2]) carry their own copies of the x = 1 nodes, as
    node splitting produces. The fault surface is a deliberate patchwork: one quad sits on the
    left-block copies, the other on the right-block copies.

    Args:
        leftQuadFirst: If True the y in [0, 1] quad is on the left copies and the y in [1, 2] quad
            on the right ones; swapped otherwise.

    Returns:
        The split mesh, with a FaultMask cell array equal to 1 on the two quads and 0 elsewhere.
    """
    points = vtkPoints()
    for xValue in ( 0., 1. ):  # Left block.
        for yValue in ( 0., 1., 2. ):
            for zValue in ( 0., 1. ):
                points.InsertNextPoint( xValue, yValue, zValue )
    for xValue in ( 1., 2. ):  # Right block, with its own copies of the x = 1 nodes.
        for yValue in ( 0., 1., 2. ):
            for zValue in ( 0., 1. ):
                points.InsertNextPoint( xValue, yValue, zValue )

    connectivities: list[ list[ int ] ] = []
    cellTypes: list[ int ] = []
    for corner in ( __leftPoint, __rightPoint ):
        for j in ( 0, 1 ):
            connectivities.append( [
                corner( 0, j, 0 ),
                corner( 1, j, 0 ),
                corner( 1, j + 1, 0 ),
                corner( 0, j + 1, 0 ),
                corner( 0, j, 1 ),
                corner( 1, j, 1 ),
                corner( 1, j + 1, 1 ),
                corner( 0, j + 1, 1 ),
            ] )
            cellTypes.append( VTK_HEXAHEDRON )

    lowerQuadOnLeft = leftQuadFirst
    for j, onLeft in ( ( 0, lowerQuadOnLeft ), ( 1, not lowerQuadOnLeft ) ):
        if onLeft:
            connectivities.append( [
                __leftPoint( 1, j, 0 ),
                __leftPoint( 1, j + 1, 0 ),
                __leftPoint( 1, j + 1, 1 ),
                __leftPoint( 1, j, 1 )
            ] )
        else:
            connectivities.append( [
                __rightPoint( 0, j, 0 ),
                __rightPoint( 0, j + 1, 0 ),
                __rightPoint( 0, j + 1, 1 ),
                __rightPoint( 0, j, 1 )
            ] )
        cellTypes.append( VTK_QUAD )

    cells = vtkCellArray()
    for connectivity in connectivities:
        cells.InsertNextCell( len( connectivity ), connectivity )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cellTypes, cells )

    tags = np.array( [ 0, 0, 0, 0, 1, 1 ], dtype=np.int32 )
    tagArray = numpy_to_vtk( tags, deep=True )
    tagArray.SetName( TAG_ARRAY )
    mesh.GetCellData().AddArray( tagArray )
    return mesh


def __faultQuadPointIds( mesh: vtkUnstructuredGrid, cellId: int ) -> list[ int ]:
    """Return the point ids of the fault quad ``cellId``."""
    pointIds = mesh.GetCell( cellId ).GetPointIds()
    return [ pointIds.GetId( k ) for k in range( pointIds.GetNumberOfIds() ) ]


def __options( outputFile: str = "unused.vtu", tagValues: tuple[ int, ...] = ( 1, ) ) -> Options:
    """Build the cure options for the test mesh."""
    return Options( outputFile=VtkOutput( output=outputFile, isDataModeBinary=True ),
                    tagArray=TAG_ARRAY,
                    tagValues=tagValues,
                    tolerance=1.e-8 )


@pytest.mark.parametrize( "leftQuadFirst", ( True, False ) )
def test_patchworkFaultBecomesSingleSided( leftQuadFirst: bool ) -> None:
    """The two fault quads end up on the same side, whichever side the cure picks as reference."""
    mesh = __buildSplitMesh( leftQuadFirst )
    faultCellIds = ( 4, 5 )
    before = [ __faultQuadPointIds( mesh, cellId ) for cellId in faultCellIds ]
    assert ( min( before[ 0 ] ) < NUM_LEFT_POINTS ) != ( min( before[ 1 ] ) < NUM_LEFT_POINTS )

    result = meshAction( mesh, __options() )

    assert result.numFaultFaces == 2
    assert result.numMovedFaces == 1
    assert result.numDegenerateFaces == 0
    assert result.numSkippedFaces == 0
    assert result.numHoleBorderFaces == 0
    assert len( result.faults ) == 1
    assert result.faults[ 0 ].tagValue == 1
    assert result.faults[ 0 ].numAlreadyCorrectFaces == 1

    after = [ __faultQuadPointIds( mesh, cellId ) for cellId in faultCellIds ]
    sides = [ all( pointId < NUM_LEFT_POINTS for pointId in ids ) for ids in after ]
    assert sides[ 0 ] == sides[ 1 ], "The two fault quads still sit on different node copies."
    # The faces keep their geometry: only the node copy they refer to changes.
    coordinates = vtk_to_numpy( mesh.GetPoints().GetData() )
    for ids in after:
        assert np.allclose( coordinates[ ids ][ :, 0 ], 1. )


def test_curedFaceIsARealCellFace() -> None:
    """Every cured fault quad matches a face of one of its 3D neighbour cells."""
    mesh = __buildSplitMesh()
    meshAction( mesh, __options() )

    for cellId in ( 4, 5 ):
        target = frozenset( __faultQuadPointIds( mesh, cellId ) )
        found = False
        for hexId in range( 4 ):
            hexCell = mesh.GetCell( hexId )
            for faceIndex in range( hexCell.GetNumberOfFaces() ):
                facePointIds = hexCell.GetFace( faceIndex ).GetPointIds()
                ids = frozenset( facePointIds.GetId( k ) for k in range( facePointIds.GetNumberOfIds() ) )
                found = found or ids == target
        assert found, f"Fault quad {cellId} is not a face of any 3D cell."


def test_qcArraysAreAdded() -> None:
    """The faultSide and onHole arrays flag the fault cells and leave no residual hole."""
    mesh = __buildSplitMesh()
    meshAction( mesh, __options() )

    faultSide = vtk_to_numpy( mesh.GetCellData().GetArray( FAULT_SIDE_ARRAY ) )
    onHole = vtk_to_numpy( mesh.GetCellData().GetArray( ON_HOLE_ARRAY ) )
    assert list( faultSide ) == [ 0, 0, 0, 0, 1, 1 ]
    assert onHole.sum() == 0


def test_tagValuesAreDetectedWhenNotGiven() -> None:
    """An empty tagValues cures every distinct non-zero value carried by a 2D cell."""
    mesh = __buildSplitMesh()
    result = meshAction( mesh, __options( tagValues=() ) )
    assert [ fault.tagValue for fault in result.faults ] == [ 1 ]
    assert result.numFaultFaces == 2


def test_unknownTagArrayRaises() -> None:
    """A tag array missing from the mesh is reported as a ValueError."""
    mesh = __buildSplitMesh()
    options = Options( outputFile=VtkOutput( output="unused.vtu", isDataModeBinary=True ),
                       tagArray="notThere",
                       tagValues=( 1, ),
                       tolerance=1.e-8 )
    with pytest.raises( ValueError ):
        meshAction( mesh, options )
