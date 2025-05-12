from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Set
from vtkmodules.vtkCommonCore import vtkIdList
from geos.mesh.utils.helpers import to_vtk_id_list
from geos.mesh.io.vtkIO import VtkOutput, read_mesh, write_mesh


@dataclass( frozen=True )
class Options:
    vtk_output: VtkOutput
    cell_type_to_ordering: Dict[ int, List[ int ] ]


@dataclass( frozen=True )
class Result:
    output: str
    unchanged_cell_types: FrozenSet[ int ]


def __check( mesh, options: Options ) -> Result:
    # The vtk cell type is an int and will be the key of the following mapping,
    # that will point to the relevant permutation.
    cell_type_to_ordering: Dict[ int, List[ int ] ] = options.cell_type_to_ordering
    unchanged_cell_types: Set[ int ] = set()  # For logging purpose

    # Preparing the output mesh by first keeping the same instance type.
    output_mesh = mesh.NewInstance()
    output_mesh.CopyStructure( mesh )
    output_mesh.CopyAttributes( mesh )

    # `output_mesh` now contains a full copy of the input mesh.
    # We'll now modify the support nodes orderings in place if needed.
    cells = output_mesh.GetCells()
    for cell_idx in range( output_mesh.GetNumberOfCells() ):
        cell_type: int = output_mesh.GetCell( cell_idx ).GetCellType()
        new_ordering = cell_type_to_ordering.get( cell_type )
        if new_ordering:
            support_point_ids = vtkIdList()
            cells.GetCellAtId( cell_idx, support_point_ids )
            new_support_point_ids = []
            for i, v in enumerate( new_ordering ):
                new_support_point_ids.append( support_point_ids.GetId( new_ordering[ i ] ) )
            cells.ReplaceCellAtId( cell_idx, to_vtk_id_list( new_support_point_ids ) )
        else:
            unchanged_cell_types.add( cell_type )
    is_written_error = write_mesh( output_mesh, options.vtk_output )
    return Result( output=options.vtk_output.output if not is_written_error else "",
                   unchanged_cell_types=frozenset( unchanged_cell_types ) )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __check( mesh, options )
