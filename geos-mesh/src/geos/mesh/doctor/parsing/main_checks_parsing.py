import argparse
from copy import deepcopy
from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import ( CheckFeature, convert as sharedConvert,
                                                                    fillSubparser as sharedFillSubparser )

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
                  optionsCls=cn_parser.Options,
                  resultCls=cn_parser.Result,
                  defaultParams=deepcopy( cn_parser.__COLLOCATED_NODES_DEFAULT ),
                  display=cn_parser.displayResults ),
    ELEMENT_VOLUMES:
    CheckFeature( name=ELEMENT_VOLUMES,
                  optionsCls=ev_parser.Options,
                  resultCls=ev_parser.Result,
                  defaultParams=deepcopy( ev_parser.__ELEMENT_VOLUMES_DEFAULT ),
                  display=ev_parser.displayResults ),
    SELF_INTERSECTING_ELEMENTS:
    CheckFeature( name=SELF_INTERSECTING_ELEMENTS,
                  optionsCls=sie_parser.Options,
                  resultCls=sie_parser.Result,
                  defaultParams=deepcopy( sie_parser.__SELF_INTERSECTING_ELEMENTS_DEFAULT ),
                  display=sie_parser.displayResults ),
}


def fillSubparser( subparsers: argparse._SubParsersAction ) -> None:
    """Fills the subparser by calling the shared logic with the specific 'main_checks' configuration."""
    sharedFillSubparser( subparsers=subparsers,
                         subparserName=MAIN_CHECKS,
                         helpMessage="Perform a curated set of main mesh-doctor checks.",
                         orderedCheckNames=ORDERED_CHECK_NAMES,
                         checkFeaturesConfig=CHECK_FEATURES_CONFIG )


def convert( parsedArgs: argparse.Namespace ) -> AllChecksOptions:
    """Converts arguments by calling the shared logic with the 'main_checks' configuration."""
    return sharedConvert( parsedArgs=parsedArgs,
                          orderedCheckNames=ORDERED_CHECK_NAMES,
                          checkFeaturesConfig=CHECK_FEATURES_CONFIG )


# The displayResults function is imported directly as it needs no special configuration.
