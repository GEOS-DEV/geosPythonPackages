import sys

min_python_version = ( 3, 7 )
try:
    assert sys.version_info >= min_python_version
except AssertionError:
    print( f"Please update python to at least version {'.'.join(map(str, min_python_version))}." )
    sys.exit( 1 )

import logging
from geos.mesh.doctor.parsing import ActionHelper
from geos.mesh.doctor.parsing.cli_parsing import parse_and_set_verbosity
import geos.mesh.doctor.register as register


def main():
    logging.basicConfig( format='[%(asctime)s][%(levelname)s] %(message)s' )
    parse_and_set_verbosity( sys.argv )
    main_parser, all_actions, all_actions_helpers = register.register()
    args = main_parser.parse_args( sys.argv[ 1: ] )
    logging.info( f"Working on mesh \"{args.vtk_input_file}\"." )
    action_options = all_actions_helpers[ args.subparsers ].convert( vars( args ) )
    try:
        action = all_actions[ args.subparsers ]
    except KeyError:
        logging.critical( f"Action {args.subparsers} is not a valid action." )
        sys.exit( 1 )
    helper: ActionHelper = all_actions_helpers[ args.subparsers ]
    result = action( args.vtk_input_file, action_options )
    helper.display_results( action_options, result )


if __name__ == '__main__':
    main()
