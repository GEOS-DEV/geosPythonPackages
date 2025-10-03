import argparse
from copy import deepcopy
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import ( CheckFeature, convert as sharedConvert,
                                                                    fillSubparser as sharedFillSubparser )
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
from geos.mesh.doctor.parsing import collocated_nodes_parsing as cnParser
from geos.mesh.doctor.parsing import element_volumes_parsing as evParser
from geos.mesh.doctor.parsing import non_conformal_parsing as ncParser
from geos.mesh.doctor.parsing import self_intersecting_elements_parsing as sieParser
from geos.mesh.doctor.parsing import supported_elements_parsing as seParser

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
                  optionsCls=cnParser.Options,
                  resultCls=cnParser.Result,
                  defaultParams=deepcopy( cnParser.__COLLOCATED_NODES_DEFAULT ),
                  display=cnParser.displayResults ),
    ELEMENT_VOLUMES:
    CheckFeature( name=ELEMENT_VOLUMES,
                  optionsCls=evParser.Options,
                  resultCls=evParser.Result,
                  defaultParams=deepcopy( evParser.__ELEMENT_VOLUMES_DEFAULT ),
                  display=evParser.displayResults ),
    NON_CONFORMAL:
    CheckFeature( name=NON_CONFORMAL,
                  optionsCls=ncParser.Options,
                  resultCls=ncParser.Result,
                  defaultParams=deepcopy( ncParser.__NON_CONFORMAL_DEFAULT ),
                  display=ncParser.displayResults ),
    SELF_INTERSECTING_ELEMENTS:
    CheckFeature( name=SELF_INTERSECTING_ELEMENTS,
                  optionsCls=sieParser.Options,
                  resultCls=sieParser.Result,
                  defaultParams=deepcopy( sieParser.__SELF_INTERSECTING_ELEMENTS_DEFAULT ),
                  display=sieParser.displayResults ),
    SUPPORTED_ELEMENTS:
    CheckFeature( name=SUPPORTED_ELEMENTS,
                  optionsCls=seParser.Options,
                  resultCls=seParser.Result,
                  defaultParams=deepcopy( seParser.__SUPPORTED_ELEMENTS_DEFAULT ),
                  display=seParser.displayResults ),
}


def fillSubparser( subparsers: argparse._SubParsersAction ) -> None:
    """Fills the subparser by calling the shared logic with the specific 'all_checks' configuration."""
    sharedFillSubparser( subparsers=subparsers,
                         subparserName=ALL_CHECKS,
                         helpMessage="Perform one or multiple mesh-doctor checks from the complete set available.",
                         orderedCheckNames=ORDERED_CHECK_NAMES,
                         checkFeaturesConfig=CHECK_FEATURES_CONFIG )


def convert( parsedArgs: argparse.Namespace ) -> AllChecksOptions:
    """Converts arguments by calling the shared logic with the 'all_checks' configuration."""
    return sharedConvert( parsedArgs=parsedArgs,
                          orderedCheckNames=ORDERED_CHECK_NAMES,
                          checkFeaturesConfig=CHECK_FEATURES_CONFIG )
