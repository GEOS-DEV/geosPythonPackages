import argparse
from copy import deepcopy
from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import ( CheckFeature, convert as shared_convert,
                                                                    fill_subparser as shared_fill_subparser,
                                                                    display_results )

# Import constants for check names
from geos.mesh.doctor.parsing import (
    MAIN_CHECKS,
    COLLOCATES_NODES,
    ELEMENT_VOLUMES,
    SELF_INTERSECTING_ELEMENTS,
)

# Import module-specific parsing components
from geos.mesh.doctor.parsing import collocated_nodes_parsing as cn_parser
from geos.mesh.doctor.parsing import element_volumes_parsing as ev_parser
from geos.mesh.doctor.parsing import self_intersecting_elements_parsing as sie_parser

# --- Configuration Specific to "Main Checks" ---

# Ordered list of check names for this configuration
ORDERED_CHECK_NAMES = [
    COLLOCATES_NODES,
    ELEMENT_VOLUMES,
    SELF_INTERSECTING_ELEMENTS,
]

# Centralized configuration for the checks managed by this module
CHECK_FEATURES_CONFIG = {
    COLLOCATES_NODES:
    CheckFeature( name=COLLOCATES_NODES,
                  options_cls=cn_parser.Options,
                  result_cls=cn_parser.Result,
                  default_params=deepcopy( cn_parser.__COLLOCATED_NODES_DEFAULT ),
                  display=cn_parser.display_results ),
    ELEMENT_VOLUMES:
    CheckFeature( name=ELEMENT_VOLUMES,
                  options_cls=ev_parser.Options,
                  result_cls=ev_parser.Result,
                  default_params=deepcopy( ev_parser.__ELEMENT_VOLUMES_DEFAULT ),
                  display=ev_parser.display_results ),
    SELF_INTERSECTING_ELEMENTS:
    CheckFeature( name=SELF_INTERSECTING_ELEMENTS,
                  options_cls=sie_parser.Options,
                  result_cls=sie_parser.Result,
                  default_params=deepcopy( sie_parser.__SELF_INTERSECTING_ELEMENTS_DEFAULT ),
                  display=sie_parser.display_results ),
}


def fill_subparser( subparsers: argparse._SubParsersAction ) -> None:
    """Fills the subparser by calling the shared logic with the specific 'main_checks' configuration."""
    shared_fill_subparser( subparsers=subparsers,
                           subparser_name=MAIN_CHECKS,
                           help_message="Perform a curated set of main mesh-doctor checks.",
                           ordered_check_names=ORDERED_CHECK_NAMES,
                           check_features_config=CHECK_FEATURES_CONFIG )


def convert( parsed_args: argparse.Namespace ) -> AllChecksOptions:
    """Converts arguments by calling the shared logic with the 'main_checks' configuration."""
    return shared_convert( parsed_args=parsed_args,
                           ordered_check_names=ORDERED_CHECK_NAMES,
                           check_features_config=CHECK_FEATURES_CONFIG )


# The display_results function is imported directly as it needs no special configuration.
