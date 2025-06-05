import argparse
from copy import deepcopy
from dataclasses import dataclass
from typing import Type
from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions
from geos.mesh.doctor.actions.all_checks import Result as AllChecksResult
# Import constants for check names
from geos.mesh.doctor.parsing import (
    ALL_CHECKS,  # Name for the subparser
    COLLOCATES_NODES,
    ELEMENT_VOLUMES,
    NON_CONFORMAL,
    SELF_INTERSECTING_ELEMENTS,
    SUPPORTED_ELEMENTS,
)
# Import module-specific Options, Result, and defaults
# Using module aliases for clarity
from geos.mesh.doctor.parsing import collocated_nodes_parsing as cn_parser
from geos.mesh.doctor.parsing import element_volumes_parsing as ev_parser
from geos.mesh.doctor.parsing import non_conformal_parsing as nc_parser
from geos.mesh.doctor.parsing import self_intersecting_elements_parsing as sie_parser
from geos.mesh.doctor.parsing import supported_elements_parsing as se_parser
from geos.mesh.doctor.parsing.cli_parsing import parse_comma_separated_string
from geos.utils.Logger import getLogger

logger = getLogger( "All_checks_parsing" )

# --- Centralized Configuration for Check Features ---
# This structure makes it easier to manage checks and their properties.


@dataclass( frozen=True )  # Consider using dataclass if appropriate, or a simple dict
class CheckFeature:
    name: str
    options_cls: Type[ any ]  # Specific Options class (e.g., cn_parser.Options)
    result_cls: Type[ any ]  # Specific Result class (e.g., cn_parser.Result)
    default_params: dict[ str, any ]  # Parser keywords with default values
    display: Type[ any ]  # Specific display function for results


# Deepcopy to prevent accidental modification of originals default parameters
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

# Ordered list of check names, defining the default order and for consistent help messages
ORDERED_CHECK_NAMES: list[ str ] = [
    COLLOCATES_NODES,
    ELEMENT_VOLUMES,
    NON_CONFORMAL,
    SELF_INTERSECTING_ELEMENTS,
    SUPPORTED_ELEMENTS,
]
DEFAULT_PARAMS: dict[ str, dict[ str, float ] ] = {
    name: feature.default_params.copy() for name, feature in CHECK_FEATURES_CONFIG.items()
}

# --- Argument Parser Constants ---
CHECKS_TO_DO_ARG = "checks_to_perform"
PARAMETERS_ARG = "set_parameters"

# Generate help text for set_parameters dynamically
PARAMETERS_ARG_HELP: str = ""
for check_name in ORDERED_CHECK_NAMES:
    config = CHECK_FEATURES_CONFIG[ check_name ]
    if config.default_params:
        config_params: list[ str ] = list()
        for name, value in config.default_params.items():
            config_params.append( f"{name}:{value}" )
        PARAMETERS_ARG_HELP += f"For {check_name}: {', '.join( config_params )}. "


# --- Argument Parser Setup ---
def fill_subparser( subparsers: argparse._SubParsersAction ) -> None:
    """Fills the subparser for 'ALL_CHECKS' with its arguments."""
    parser = subparsers.add_parser(
        ALL_CHECKS,
        help="Perform one or multiple mesh-doctor check operations in one command line on the same mesh.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter  # Shows defaults in help
    )
    parser.add_argument( f"--{CHECKS_TO_DO_ARG}",
                         type=str,
                         default="",
                         required=False,
                         help=( "Comma-separated list of mesh-doctor checks to perform. If no input was given, all of"
                                f" the following checks will be executed by default: {ORDERED_CHECK_NAMES}. If you want"
                                " to choose only certain of them, you can name them individually."
                                f" Example: --{CHECKS_TO_DO_ARG} {ORDERED_CHECK_NAMES[0]},{ORDERED_CHECK_NAMES[1]}" ) )
    parser.add_argument(
        f"--{PARAMETERS_ARG}",
        type=str,
        default="",
        required=False,
        help=( "Comma-separated list of parameters to set for the checks (e.g., 'param_name:value'). "
               "These parameters override the defaults. Default parameters are:"
               f" {PARAMETERS_ARG_HELP} Example: --{PARAMETERS_ARG} parameter_name:10.5,other_param:25" ) )


def convert( parsed_args: argparse.Namespace ) -> AllChecksOptions:
    """
    Converts parsed command-line arguments into an AllChecksOptions object.
    """
    # 1. Determine which checks to perform
    final_selected_check_names: list[ str ] = deepcopy( ORDERED_CHECK_NAMES )
    if not parsed_args[ CHECKS_TO_DO_ARG ]:  # handles default and if user explicitly provides --checks_to_perform ""
        logger.info( "All current available checks in mesh-doctor will be performed." )
    else:  # the user specifically entered check names to perform
        checks_to_do: list[ str ] = parse_comma_separated_string( parsed_args[ CHECKS_TO_DO_ARG ] )
        final_selected_check_names = list()
        for name in checks_to_do:
            if name not in CHECK_FEATURES_CONFIG:
                logger.warning( f"The given check '{name}' does not exist. Cannot perform this check."
                                f" Choose from: {ORDERED_CHECK_NAMES}." )
            elif name not in final_selected_check_names:  # Add if valid and not already added
                final_selected_check_names.append( name )

        # If after parsing, no valid checks are selected (e.g., all inputs were invalid)
        if not final_selected_check_names:
            logger.error( "No valid checks selected based on input. No operations will be configured." )
            raise ValueError( "No valid checks selected based on input. No operations will be configured." )

    # 2. Prepare parameters of Options for every check feature that will be used
    final_selected_check_params: dict[ str, dict[ str, float ] ] = deepcopy( DEFAULT_PARAMS )
    for name in list( final_selected_check_params.keys() ):
        if name not in final_selected_check_names:
            del final_selected_check_params[ name ]  # Remove non-used check features

    if not parsed_args[ PARAMETERS_ARG ]:  # handles default and if user explicitly provides --set_parameters ""
        logger.info( "Default configuation of parameters adopted for every check to perform." )
    else:
        set_parameters = parse_comma_separated_string( parsed_args[ PARAMETERS_ARG ] )
        for param in set_parameters:
            if ':' not in param:
                logger.warning( f"Parameter '{param}' in --{PARAMETERS_ARG} is not in 'name:value' format. Skipping." )
                continue
            name, *value = param.split( ':', 1 )
            name = name.strip()
            if value:  # Check if there is anything after the first colon
                value_str = value[ 0 ].strip()
            else:
                # Handle cases where there's nothing after the colon, if necessary
                logger.warning( f"Parameter '{name}' has no value after the colon. Skipping or using default." )
                continue
            try:
                value_float = float( value_str )
            except ValueError:
                logger.warning(
                    f"Invalid value for parameter '{name}': '{value_str}'. Must be a number. Skipping this override." )
                continue

            for check_name_key in final_selected_check_params.keys():  # Iterate through all possible checks
                if name in final_selected_check_params[ check_name_key ]:
                    final_selected_check_params[ check_name_key ][ name ] = value_float
                    break

    # 3. Instantiate the Options objects for the selected checks using their effective parameters
    individual_check_options: dict[ str, any ] = dict()
    individual_check_display: dict[ str, any ] = dict()
    for check_name in list( final_selected_check_params.keys() ):
        options_constructor_params = final_selected_check_params[ check_name ]
        feature_config = CHECK_FEATURES_CONFIG[ check_name ]
        try:
            individual_check_options[ check_name ] = feature_config.options_cls( **options_constructor_params )
            individual_check_display[ check_name ] = feature_config.display
        except Exception as e:  # Catch potential errors during options instantiation
            logger.error(
                f"Failed to create options for check '{check_name}' with params {options_constructor_params}: {e}."
                f" Therefore the check '{check_name}' will not be performed." )
            final_selected_check_names.remove( check_name )

    return AllChecksOptions( checks_to_perform=final_selected_check_names,
                             checks_options=individual_check_options,
                             check_displays=individual_check_display )


# --- Display Results ---
def display_results( options: AllChecksOptions, result: AllChecksResult ) -> None:
    """Displays the results of the checks."""
    # Implementation for displaying results based on the structured options and results.
    logger.info( f"Displaying results for checks: {options.checks_to_perform}" )
    for name, res in result.check_results.items():
        options.check_displays[ name ]( options.checks_options[ name ], res )
