# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from pathlib import Path

from trame.app import get_server

from geos_trame.app.core import GeosTrame


def main(server=None, **kwargs):
    # Get or create server
    if server is None:
        server = get_server()

    if isinstance(server, str):
        server = get_server(server)

    # Set client type
    server.client_type = "vue3"

    # parse args
    parser = server.cli
    parser.add_argument("-I", "--input", help="Input file (.xml)")

    (args, _unknown) = parser.parse_known_args()

    if args.input is None:
        print("Usage: \n\tgeos-trame -I /path/to/input/file")
        return

    file_name = str(Path(args.input).absolute())

    app = GeosTrame(server, file_name)
    app.server.start(**kwargs)
