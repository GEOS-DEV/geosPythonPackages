# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from dataclasses import dataclass
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid, writeMesh
from geos.mesh.utils.genericHelpers import toVtkIdList


@dataclass( frozen=True )
class Options:
    vtkOutput: VtkOutput
    cellTypeToOrdering: dict[ int, list[ int ] ]


@dataclass( frozen=True )
class Result:
    output: str
    unchangedCellTypes: frozenset[ int ]


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the fix elements orderings on a vtkUnstructuredGrid.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to reorder.
        options (Options): The options for processing.

    Returns:
        Result: The result of the fix elements orderings.
    """
    # The vtk cell type is an int and will be the key of the following mapping,
    # that will point to the relevant permutation.
    cellTypeToOrdering: dict[ int, list[ int ] ] = options.cellTypeToOrdering
    unchangedCellTypes: set[ int ] = set()  # For logging purpose

    # Preparing the output mesh by first keeping the same instance type.
    outputMesh = mesh.NewInstance()
    outputMesh.CopyStructure( mesh )
    outputMesh.CopyAttributes( mesh )

    # `outputMesh` now contains a full copy of the input mesh.
    # We'll now modify the support nodes orderings in place if needed.
    cells = outputMesh.GetCells()
    for cellIdx in range( outputMesh.GetNumberOfCells() ):
        cellType: int = outputMesh.GetCell( cellIdx ).GetCellType()
        newOrdering = cellTypeToOrdering.get( cellType )
        if newOrdering:
            supportPointIds = vtkIdList()
            cells.GetCellAtId( cellIdx, supportPointIds )
            newSupportPointIds = []
            for orderingId in newOrdering:
                newSupportPointIds.append( supportPointIds.GetId( orderingId ) )
            cells.ReplaceCellAtId( cellIdx, toVtkIdList( newSupportPointIds ) )
        else:
            unchangedCellTypes.add( cellType )
    try:
        isWrittenError = writeMesh( outputMesh, options.vtkOutput, options.vtkOutput.canOverwrite )
    except FileExistsError as e:
        from geos.mesh_doctor.parsing.cliParsing import setupLogger
        setupLogger.error( f"{e} Use --canOverwrite to allow overwriting existing files." )
        raise SystemExit( 1 )
    return Result( output=options.vtkOutput.output if not isWrittenError else "",
                   unchangedCellTypes=frozenset( unchangedCellTypes ) )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtu file and performs the fix elements orderings on it.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the fix elements orderings.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
