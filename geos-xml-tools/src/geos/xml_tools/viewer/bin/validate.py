# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

import argparse

from xmlschema import XMLSchema


def parsing() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser( description="Validate xsd schema" )

    parser.add_argument(
        "--xsdFilepath",
        type=str,
        default="",
        help="path to xsd file.",
        required=True,
    )
    parser.add_argument(
        "--xmlFilepath",
        type=str,
        default="",
        help="path to xml file.",
    )

    return parser


def main( args: argparse.Namespace ) -> None:
    XMLSchema.meta_schema.validate( args.xsdFilepath )
    obj = XMLSchema.meta_schema.decode( args.xsdFilepath )

    if args.xmlFilepath:
        schema = XMLSchema( args.xsdFilepath )
        schema.validate( args.xmlFilepath )

    else:
        print( "No xml file provided" )


def run() -> None:
    parser = parsing()
    args, unknown_args = parser.parse_known_args()
    main( args )


if __name__ == "__main__":
    run()
