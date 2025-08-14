from dataclasses import dataclass
from typing import Any
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.register import __load_module_action
from geos.mesh.doctor.parsing.cli_parsing import setup_logger


@dataclass( frozen=True )
class Options:
    checks_to_perform: list[ str ]
    checks_options: dict[ str, Any ]
    check_displays: dict[ str, Any ]


@dataclass( frozen=True )
class Result:
    check_results: dict[ str, Any ]


def get_check_results( vtk_input: str | vtkUnstructuredGrid, options: Options ) -> dict[ str, Any ]:
    isFilepath: bool = isinstance( vtk_input, str )
    isVtkUnstructuredGrid: bool = isinstance( vtk_input, vtkUnstructuredGrid )
    assert isFilepath | isVtkUnstructuredGrid, "Invalid input type, should either be a filepath to .vtu file" \
        " or a vtkUnstructuredGrid object"
    check_results: dict[ str, any ] = dict()
    for check_name in options.checks_to_perform:
        if isVtkUnstructuredGrid:  # we need to call the mesh_action function that takes a vtkPointSet as input
            check_action = __load_module_action( check_name, "mesh_action" )
        else:  # because its a filepath, we can call the regular action function
            check_action = __load_module_action( check_name )
        setup_logger.info( f"Performing check '{check_name}'." )
        option = options.checks_options[ check_name ]
        check_result = check_action( vtk_input, option )
        check_results[ check_name ] = check_result
    return check_results


def action( vtk_input_file: str, options: Options ) -> Result:
    check_results: dict[ str, Any ] = get_check_results( vtk_input_file, options )
    return Result( check_results=check_results )
