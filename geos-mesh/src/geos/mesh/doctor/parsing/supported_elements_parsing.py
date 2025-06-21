import multiprocessing
from geos.mesh.doctor.actions.supported_elements import Options, Result
from geos.mesh.doctor.parsing import SUPPORTED_ELEMENTS
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import get_options_used_message
from geos.mesh.doctor.parsing.cli_parsing import setup_logger

__CHUNK_SIZE = "chunk_size"
__NUM_PROC = "nproc"

__CHUNK_SIZE_DEFAULT = 1
__NUM_PROC_DEFAULT = multiprocessing.cpu_count()

__SUPPORTED_ELEMENTS_DEFAULT = { __CHUNK_SIZE: __CHUNK_SIZE_DEFAULT, __NUM_PROC: __NUM_PROC_DEFAULT }


def convert( parsed_options ) -> Options:
    return Options( chunk_size=parsed_options[ __CHUNK_SIZE ], nproc=parsed_options[ __NUM_PROC ] )


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( SUPPORTED_ELEMENTS,
                               help="Check that all the elements of the mesh are supported by GEOSX." )
    p.add_argument( '--' + __CHUNK_SIZE,
                    type=int,
                    required=False,
                    metavar=__CHUNK_SIZE_DEFAULT,
                    default=__CHUNK_SIZE_DEFAULT,
                    help=f"[int]: Defaults chunk size for parallel processing to {__CHUNK_SIZE_DEFAULT}" )
    p.add_argument(
        '--' + __NUM_PROC,
        type=int,
        required=False,
        metavar=__NUM_PROC_DEFAULT,
        default=__NUM_PROC_DEFAULT,
        help=f"[int]: Number of threads used for parallel processing. Defaults to your CPU count {__NUM_PROC_DEFAULT}."
    )


def display_results( options: Options, result: Result ):
    setup_logger.results( get_options_used_message( options ) )
    if result.unsupported_polyhedron_elements:
        setup_logger.results(
            f"There is/are {len(result.unsupported_polyhedron_elements)} polyhedra that may not be converted to supported elements."
        )
        setup_logger.results(
            f"The list of the unsupported polyhedra is\n{tuple(sorted(result.unsupported_polyhedron_elements))}." )
    else:
        setup_logger.results( "All the polyhedra (if any) can be converted to supported elements." )
    if result.unsupported_std_elements_types:
        setup_logger.results(
            f"There are unsupported vtk standard element types. The list of those vtk types is {tuple(sorted(result.unsupported_std_elements_types))}."
        )
    else:
        setup_logger.results( "All the standard vtk element types (if any) are supported." )
