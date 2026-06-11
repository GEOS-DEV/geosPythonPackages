# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Refine a VTU mesh by repeatedly applying edge-midpoint cell splitting."""

from __future__ import annotations

from dataclasses import dataclass

from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid, writeMesh
from geos.mesh.utils.SplitMesh import SplitMesh
from geos.mesh_doctor.parsing.cliParsing import setupLogger


@dataclass( frozen=True )
class Options:
    """Options for mesh refinement.

    Attributes:
        outputFile: VTK output file configuration.
        iterations: Number of times to apply the split filter. Each iteration
            multiplies the cell count by 4 (2D) or 8 (3D hexahedra/tetrahedra).
    """
    outputFile: VtkOutput
    iterations: int


@dataclass( frozen=True )
class Result:
    """Result of mesh refinement.

    Attributes:
        inputNumPoints: Number of points in the input mesh.
        inputNumCells: Number of cells in the input mesh.
        outputNumPoints: Number of points in the refined mesh.
        outputNumCells: Number of cells in the refined mesh.
        iterations: Number of refinement iterations applied.
    """
    inputNumPoints: int
    inputNumCells: int
    outputNumPoints: int
    outputNumCells: int
    iterations: int


def action( vtuInputFile: str, options: Options ) -> Result:
    """Refine a mesh by splitting each cell using edge midpoints.

    Each iteration splits every cell into smaller cells of the same type:
    hexahedra -> 8, tetrahedra -> 8, pyramids -> 10, triangles -> 4, quads -> 4.
    Cell data arrays are propagated to the child cells.

    Args:
        vtuInputFile: Path to the input VTU mesh file.
        options: Refinement options (output path and iteration count).

    Returns:
        Statistics comparing the input and output mesh.

    Raises:
        TypeError: If the mesh contains unsupported cell types (e.g. wedges).
        RuntimeError: If refinement fails for any reason.
    """
    setupLogger.info( f"Reading mesh from \"{vtuInputFile}\"." )
    mesh = readUnstructuredGrid( vtuInputFile )
    inputNumPoints = mesh.GetNumberOfPoints()
    inputNumCells = mesh.GetNumberOfCells()

    current = mesh
    for i in range( options.iterations ):
        setupLogger.info( f"Refinement iteration {i + 1}/{options.iterations}." )
        splitFilter = SplitMesh( current )
        splitFilter.applyFilter()
        current = splitFilter.getOutput()

    setupLogger.info( f"Writing refined mesh to \"{options.outputFile.output}\"." )
    writeMesh( current, options.outputFile )

    return Result(
        inputNumPoints=inputNumPoints,
        inputNumCells=inputNumCells,
        outputNumPoints=current.GetNumberOfPoints(),
        outputNumCells=current.GetNumberOfCells(),
        iterations=options.iterations,
    )
