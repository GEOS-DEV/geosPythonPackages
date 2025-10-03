from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Set
from vtkmodules.vtkCommonCore import vtkIdList
from geos.mesh.utils.genericHelpers import toVtkIdList
from geos.mesh.io.vtkIO import VtkOutput, read_mesh, write_mesh


@dataclass( frozen=True )
class Options:
    vtkOutput: VtkOutput
    cellTypeToOrdering: Dict[ int, List[ int ] ]


@dataclass( frozen=True )
class Result:
    output: str
    unchangedCellTypes: FrozenSet[ int ]


def __action( mesh, options: Options ) -> Result:
    # The vtk cell type is an int and will be the key of the following mapping,
    # that will point to the relevant permutation.
    cellTypeToOrdering: Dict[ int, List[ int ] ] = options.cellTypeToOrdering
    unchangedCellTypes: Set[ int ] = set()  # For logging purpose

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
            for i, v in enumerate( newOrdering ):
                newSupportPointIds.append( supportPointIds.GetId( newOrdering[ i ] ) )
            cells.ReplaceCellAtId( cellIdx, toVtkIdList( newSupportPointIds ) )
        else:
            unchangedCellTypes.add( cellType )
    isWrittenError = write_mesh( outputMesh, options.vtkOutput )
    return Result( output=options.vtkOutput.output if not isWrittenError else "",
                   unchangedCellTypes=frozenset( unchangedCellTypes ) )


def action( vtkInputFile: str, options: Options ) -> Result:
    mesh = read_mesh( vtkInputFile )
    return __action( mesh, options )
