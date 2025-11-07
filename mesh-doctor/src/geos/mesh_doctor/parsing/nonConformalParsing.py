from geos.mesh_doctor.actions.nonConformal import Options, Result
from geos.mesh_doctor.parsing import NON_CONFORMAL
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger

__ANGLE_TOLERANCE = "angleTolerance"
__POINT_TOLERANCE = "pointTolerance"
__FACE_TOLERANCE = "faceTolerance"

__ANGLE_TOLERANCE_DEFAULT = 10.
__POINT_TOLERANCE_DEFAULT = 0.
__FACE_TOLERANCE_DEFAULT = 0.

__NON_CONFORMAL_DEFAULT = {
    __ANGLE_TOLERANCE: __ANGLE_TOLERANCE_DEFAULT,
    __POINT_TOLERANCE: __POINT_TOLERANCE_DEFAULT,
    __FACE_TOLERANCE: __FACE_TOLERANCE_DEFAULT
}


def convert( parsedOptions ) -> Options:
    return Options( angleTolerance=parsedOptions[ __ANGLE_TOLERANCE ],
                    pointTolerance=parsedOptions[ __POINT_TOLERANCE ],
                    faceTolerance=parsedOptions[ __FACE_TOLERANCE ] )


def fillSubparser( subparsers ) -> None:
    p = subparsers.add_parser( NON_CONFORMAL, help="Detects non conformal elements. [EXPERIMENTAL]" )
    p.add_argument( '--' + __ANGLE_TOLERANCE,
                    type=float,
                    metavar=__ANGLE_TOLERANCE_DEFAULT,
                    default=__ANGLE_TOLERANCE_DEFAULT,
                    help=f"[float]: angle tolerance in degrees. Defaults to {__ANGLE_TOLERANCE_DEFAULT}" )
    p.add_argument(
        '--' + __POINT_TOLERANCE,
        type=float,
        metavar=__POINT_TOLERANCE_DEFAULT,
        default=__POINT_TOLERANCE_DEFAULT,
        help=f"[float]: tolerance for two points to be considered collocated. Defaults to {__POINT_TOLERANCE_DEFAULT}" )
    p.add_argument(
        '--' + __FACE_TOLERANCE,
        type=float,
        metavar=__FACE_TOLERANCE_DEFAULT,
        default=__FACE_TOLERANCE_DEFAULT,
        help=f"[float]: tolerance for two faces to be considered \"touching\". Defaults to {__FACE_TOLERANCE_DEFAULT}" )


def displayResults( options: Options, result: Result ):
    setupLogger.results( getOptionsUsedMessage( options ) )
    nonConformalCells: list[ int ] = []
    for i, j in result.nonConformalCells:
        nonConformalCells += i, j
    nonConformalCells: frozenset[ int ] = frozenset( nonConformalCells )
    setupLogger.results( f"You have {len( nonConformalCells )} non conformal cells." )
    setupLogger.results( f"{', '.join( map( str, sorted( nonConformalCells ) ) )}" )
