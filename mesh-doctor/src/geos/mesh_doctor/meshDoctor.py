# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
import sys
from geos.mesh_doctor.parsing import ActionHelper
from geos.mesh_doctor.parsing.cliParsing import parseAndSetVerbosity, setupLogger
from geos.mesh_doctor.register import registerParsingActions


def main() -> None:
    """Main function for mesh-doctor CLI."""
    parseAndSetVerbosity( sys.argv )
    mainParser, allActions, allActionsHelpers = registerParsingActions()
    args = mainParser.parse_args( sys.argv[ 1: ] )

    # Extract vtuInputFile from parsed arguments
    vtuInputFile = getattr( args, 'vtuInputFile', None )
    if vtuInputFile:
        setupLogger.info( f"Working on mesh \"{vtuInputFile}\"." )

    actionOptions = allActionsHelpers[ args.subparsers ].convert( vars( args ) )
    try:
        action = allActions[ args.subparsers ]
    except KeyError:
        setupLogger.error( f"Action {args.subparsers} is not a valid action." )
        sys.exit( 1 )
    helper: ActionHelper = allActionsHelpers[ args.subparsers ]
    result = action( vtuInputFile, actionOptions )
    helper.displayResults( actionOptions, result )


if __name__ == '__main__':
    main()
