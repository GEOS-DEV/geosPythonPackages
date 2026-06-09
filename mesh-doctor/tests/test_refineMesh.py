# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Tests for the refineMesh action and its CLI parsing."""

from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path

from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON

from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid, writeMesh
from geos.mesh.utils.genericHelpers import createMultiCellMesh
from geos.mesh_doctor.actions.refineMesh import Options, action
from geos.mesh_doctor.parsing import refineMeshParsing


def __writeTwoHexMesh( path: Path ) -> None:
    """Write a conformal two-hexahedra mesh sharing a face to ``path``."""
    c0 = np.array( [ [ 0., 0., 0. ], [ 1., 0., 0. ], [ 1., 1., 0. ], [ 0., 1., 0. ], [ 0., 0., 1. ], [ 1., 0., 1. ],
                     [ 1., 1., 1. ], [ 0., 1., 1. ] ] )
    c1 = np.array( [ [ 1., 0., 0. ], [ 2., 0., 0. ], [ 2., 1., 0. ], [ 1., 1., 0. ], [ 1., 0., 1. ], [ 2., 0., 1. ],
                     [ 2., 1., 1. ], [ 1., 1., 1. ] ] )
    mesh = createMultiCellMesh( [ VTK_HEXAHEDRON, VTK_HEXAHEDRON ], [ c0, c1 ], sharePoints=True )
    writeMesh( mesh, VtkOutput( output=str( path ), isDataModeBinary=True ), canOverwrite=True )


def test_refineMeshSingleIteration( tmp_path: Path ) -> None:
    """One iteration splits each hex into 8 and keeps the mesh conformal."""
    inputFile = tmp_path / "in.vtu"
    outputFile = tmp_path / "out.vtu"
    __writeTwoHexMesh( inputFile )

    options = Options( outputFile=VtkOutput( output=str( outputFile ), isDataModeBinary=True ), iterations=1 )
    result = action( str( inputFile ), options )

    assert result.inputNumCells == 2
    assert result.outputNumCells == 2 * 8
    assert result.iterations == 1
    assert outputFile.exists()

    # 4x2x2 conformal hex grid -> (5,3,3) = 45 unique points, no duplicates.
    out = readUnstructuredGrid( str( outputFile ) )
    assert out.GetNumberOfCells() == 16
    assert out.GetNumberOfPoints() == 45


def test_refineMeshTwoIterationsConformal( tmp_path: Path ) -> None:
    """Two iterations multiply cells by 8 each time and stay conformal."""
    inputFile = tmp_path / "in.vtu"
    outputFile = tmp_path / "out.vtu"
    __writeTwoHexMesh( inputFile )

    options = Options( outputFile=VtkOutput( output=str( outputFile ), isDataModeBinary=True ), iterations=2 )
    result = action( str( inputFile ), options )

    assert result.outputNumCells == 2 * 8 * 8
    # 8x4x4 conformal hex grid -> (9,5,5) = 225 unique points.
    out = readUnstructuredGrid( str( outputFile ) )
    assert out.GetNumberOfPoints() == 225
    from vtkmodules.util.numpy_support import vtk_to_numpy
    pts = vtk_to_numpy( out.GetPoints().GetData() )
    assert len( np.unique( pts, axis=0 ) ) == out.GetNumberOfPoints(), "Refined mesh has duplicate coincident points."


def test_refineMeshConvertRejectsNonPositiveIterations() -> None:
    """The CLI converter rejects iteration counts below 1."""
    parsed = { "output": "out.vtu", "data_mode": "binary", "iterations": 0 }
    with pytest.raises( ValueError ):
        refineMeshParsing.convert( parsed )
