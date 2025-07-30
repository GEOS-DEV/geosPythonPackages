import argparse
from copy import deepcopy
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import ( CheckFeature, convert as shared_convert,
                                                                    fill_subparser as shared_fill_subparser,
                                                                    display_results )
from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions

# Import constants for check names
from geos.mesh.doctor.parsing import (
    ALL_CHECKS,
    COLLOCATES_NODES,
    ELEMENT_VOLUMES,
    NON_CONFORMAL,
    SELF_INTERSECTING_ELEMENTS,
    SUPPORTED_ELEMENTS,
)

# Import module-specific parsing components
from geos.mesh.doctor.parsing import collocated_nodes_parsing as cn_parser
from geos.mesh.doctor.parsing import element_volumes_parsing as ev_parser
from geos.mesh.doctor.parsing import non_conformal_parsing as nc_parser
from geos.mesh.doctor.parsing import self_intersecting_elements_parsing as sie_parser
from geos.mesh.doctor.parsing import supported_elements_parsing as se_parser

# --- Configuration Specific to "All Checks" ---

# Ordered list of check names for this configuration
ORDERED_CHECK_NAMES = [
    COLLOCATES_NODES,
    ELEMENT_VOLUMES,
    NON_CONFORMAL,
    SELF_INTERSECTING_ELEMENTS,
    SUPPORTED_ELEMENTS,
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
    NON_CONFORMAL:
    CheckFeature( name=NON_CONFORMAL,
                  options_cls=nc_parser.Options,
                  result_cls=nc_parser.Result,
                  default_params=deepcopy( nc_parser.__NON_CONFORMAL_DEFAULT ),
                  display=nc_parser.display_results ),
    SELF_INTERSECTING_ELEMENTS:
    CheckFeature( name=SELF_INTERSECTING_ELEMENTS,
                  options_cls=sie_parser.Options,
                  result_cls=sie_parser.Result,
                  default_params=deepcopy( sie_parser.__SELF_INTERSECTING_ELEMENTS_DEFAULT ),
                  display=sie_parser.display_results ),
    SUPPORTED_ELEMENTS:
    CheckFeature( name=SUPPORTED_ELEMENTS,
                  options_cls=se_parser.Options,
                  result_cls=se_parser.Result,
                  default_params=deepcopy( se_parser.__SUPPORTED_ELEMENTS_DEFAULT ),
                  display=se_parser.display_results ),
}


def fill_subparser( subparsers: argparse._SubParsersAction ) -> None:
    """Fills the subparser by calling the shared logic with the specific 'all_checks' configuration."""
    shared_fill_subparser( subparsers=subparsers,
                           subparser_name=ALL_CHECKS,
                           help_message="Perform one or multiple mesh-doctor checks from the complete set available.",
                           ordered_check_names=ORDERED_CHECK_NAMES,
                           check_features_config=CHECK_FEATURES_CONFIG )


def convert( parsed_args: argparse.Namespace ) -> AllChecksOptions:
    """Converts arguments by calling the shared logic with the 'all_checks' configuration."""
    return shared_convert( parsed_args=parsed_args,
                           ordered_check_names=ORDERED_CHECK_NAMES,
                           check_features_config=CHECK_FEATURES_CONFIG )
