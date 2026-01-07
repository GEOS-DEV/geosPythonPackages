# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner, Jacques Franc
from pathlib import Path
from typing import Any
from dotenv import load_dotenv, find_dotenv

from trame.app import get_server  # type: ignore
from trame_server import Server

import sys
sys.path.insert( 0, "/data/pau901/SIM_CS/users/jfranc/geosPythonPackages/geos-trame/src" )

#do not override if existing
assert load_dotenv( dotenv_path=Path( __file__ ).parent.parent / "assets/.env" )
from geos.trame.app.core import GeosTrame


def main( server: Server = None, **kwargs: Any ) -> None:
    """Main function."""
    # Get or create server
    if server is None:
        server = get_server()

    if isinstance( server, str ):
        server = get_server( server )

    # Set client type
    server.client_type = "vue3"

    # parse args
    parser = server.cli
    parser.add_argument( "-I", "--input", help="Input file (.xml)", required=True )
    parser.add_argument( "-e", "--env", help="dot_env file" , required=False )

    ( args, _unknown ) = parser.parse_known_args()

    file_name = str( Path( args.input ).absolute() )

    app = GeosTrame( server, file_name )
    app.server.start( **kwargs )


if __name__ == "__main__":
    main()
