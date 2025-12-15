# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from pathlib import Path
from typing import Any

from trame.app import get_server  # type: ignore
from trame_server import Server

import sys

sys.path.insert( 0, "/data/pau901/SIM_CS/users/jfranc/geosPythonPackages/geos-trame/src" )

from geos.trame.app.core import GeosTrame


def main( server: Server = None, **kwargs: Any ) -> None:
    """Main function."""
    # Get or create server
    if server is None:
        server = get_server()
    server.clear_state_client_cache()

    if isinstance( server, str ):
        server = get_server( server )

    # Set client type
    server.client_type = "vue3"

    # parse args
    parser = server.cli
    parser.add_argument( "-I", "--input", help="Input file (.xml)" )

    ( args, _unknown ) = parser.parse_known_args()

    if args.input is None:
        print( "Usage: \n\tgeos-trame -I /path/to/input/file" )
        return

    file_name = str( Path( args.input ).absolute() )

    app = GeosTrame( server, file_name )
    app.server.start( **kwargs )


if __name__ == "__main__":
    main()
