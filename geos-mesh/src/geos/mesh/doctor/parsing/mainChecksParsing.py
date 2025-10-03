import argparse
from copy import deepcopy
from geos.mesh.doctor.actions.allChecks import Options as AllChecksOptions
from geos.mesh.doctor.parsing._sharedChecksParsingLogic import ( CheckFeature, convert as sharedConvert,
                                                                 fillSubparser as sharedFillSubparser,
                                                                 displayResults )
from geos.mesh.doctor.parsing import (
    MAIN_CHECKS,
    COLLOCATES_NODES,
    ELEMENT_VOLUMES,
    SELF_INTERSECTING_ELEMENTS,
)
from geos.mesh.doctor.parsing import collocatedNodesParsing as cnParser
from geos.mesh.doctor.parsing import elementVolumesParsing as evParser
from geos.mesh.doctor.parsing import selfIntersectingElementsParsing as sieParser

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
    SELF_INTERSECTING_ELEMENTS:
    CheckFeature( name=SELF_INTERSECTING_ELEMENTS,
                  optionsCls=sieParser.Options,
                  resultCls=sieParser.Result,
                  defaultParams=deepcopy( sieParser.__SELF_INTERSECTING_ELEMENTS_DEFAULT ),
                  display=sieParser.displayResults ),
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
