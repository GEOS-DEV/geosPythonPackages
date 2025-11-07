import multiprocessing
from geos.mesh_doctor.actions.supportedElements import Options, Result
from geos.mesh_doctor.parsing import SUPPORTED_ELEMENTS
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger

__CHUNK_SIZE = "chunkSize"
__NUM_PROC = "nproc"

__CHUNK_SIZE_DEFAULT = 1
__NUM_PROC_DEFAULT = multiprocessing.cpu_count()

__SUPPORTED_ELEMENTS_DEFAULT = { __CHUNK_SIZE: __CHUNK_SIZE_DEFAULT, __NUM_PROC: __NUM_PROC_DEFAULT }


def convert( parsedOptions ) -> Options:
    return Options( chunkSize=parsedOptions[ __CHUNK_SIZE ], nproc=parsedOptions[ __NUM_PROC ] )


def fillSubparser( subparsers ) -> None:
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


def displayResults( options: Options, result: Result ):
    setupLogger.results( getOptionsUsedMessage( options ) )
    if result.unsupportedPolyhedronElements:
        setupLogger.results( f"There is/are {len(result.unsupportedPolyhedronElements)} polyhedra that may not be "
                             f"converted to supported elements." )
        setupLogger.results(
            f"The list of the unsupported polyhedra is\n{tuple(sorted(result.unsupportedPolyhedronElements))}." )
    else:
        setupLogger.results( "All the polyhedra (if any) can be converted to supported elements." )
    if result.unsupportedStdElementsTypes:
        setupLogger.results( f"There are unsupported vtk standard element types. The list of those vtk types is "
                             f"{tuple(sorted(result.unsupportedStdElementsTypes))}." )
    else:
        setupLogger.results( "All the standard vtk element types (if any) are supported." )
