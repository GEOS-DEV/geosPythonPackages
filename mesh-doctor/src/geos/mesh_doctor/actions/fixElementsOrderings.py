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


def __action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
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
            for i, v in enumerate( newOrdering ):
                newSupportPointIds.append( supportPointIds.GetId( newOrdering[ i ] ) )
            cells.ReplaceCellAtId( cellIdx, toVtkIdList( newSupportPointIds ) )
        else:
            unchangedCellTypes.add( cellType )
    isWrittenError = writeMesh( outputMesh, options.vtkOutput )
    return Result( output=options.vtkOutput.output if not isWrittenError else "",
                   unchangedCellTypes=frozenset( unchangedCellTypes ) )


def action( vtkInputFile: str, options: Options ) -> Result:
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtkInputFile )
    return __action( mesh, options )
