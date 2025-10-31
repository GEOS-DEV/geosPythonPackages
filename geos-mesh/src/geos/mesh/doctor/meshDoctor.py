import sys
from geos.mesh.doctor.parsing import ActionHelper
from geos.mesh.doctor.parsing.cliParsing import parseAndSetVerbosity, setupLogger
from geos.mesh.doctor.register import registerParsingActions


def main():
    parseAndSetVerbosity( sys.argv )
    mainParser, allActions, allActionsHelpers = registerParsingActions()
    args = mainParser.parse_args( sys.argv[ 1: ] )
    setupLogger.info( f"Working on mesh \"{args.vtkInputFile}\"." )
    actionOptions = allActionsHelpers[ args.subparsers ].convert( vars( args ) )
    try:
        action = allActions[ args.subparsers ]
    except KeyError:
        setupLogger.error( f"Action {args.subparsers} is not a valid action." )
        sys.exit( 1 )
    helper: ActionHelper = allActionsHelpers[ args.subparsers ]
    result = action( args.vtkInputFile, actionOptions )
    helper.displayResults( actionOptions, result )


if __name__ == '__main__':
    main()
