import argparse
from copy import deepcopy
from dataclasses import dataclass
from typing import Type, Any

from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions
from geos.mesh.doctor.actions.all_checks import Result as AllChecksResult
from geos.mesh.doctor.parsing.cli_parsing import parse_comma_separated_string, setup_logger


# --- Data Structure for Check Features ---
@dataclass( frozen=True )
class CheckFeature:
    """A container for a check's configuration and associated classes."""
    name: str
    options_cls: Type[ Any ]
    result_cls: Type[ Any ]
    default_params: dict[ str, Any ]
    display: Type[ Any ]


# --- Argument Parser Constants ---
CHECKS_TO_DO_ARG = "checks_to_perform"
PARAMETERS_ARG = "set_parameters"


def _generate_parameters_help( ordered_check_names: list[ str ], check_features_config: dict[ str,
                                                                                              CheckFeature ] ) -> str:
    """Dynamically generates the help text for the set_parameters argument."""
    help_text: str = ""
    for check_name in ordered_check_names:
        config = check_features_config.get( check_name )
        if config and config.default_params:
            config_params = [ f"{name}:{value}" for name, value in config.default_params.items() ]
            help_text += f"For {check_name}: {', '.join(config_params)}. "
    return help_text


def get_options_used_message( options_used: dataclass ) -> str:
    """Dynamically generates the description of every parameter used when loaching a check.

    Args:
        options_used (dataclass)

    Returns:
        str: A message like "Parameters used: ( param1:value1 param2:value2 )" for as many paramters found.
    """
    options_msg: str = "Parameters used: ("
    for attr_name in options_used.__dataclass_fields__:
        attr_value = getattr( options_used, attr_name )
        options_msg += f" {attr_name} = {attr_value}"
    return options_msg + " )."


# --- Generic Argument Parser Setup ---
def fill_subparser( subparsers: argparse._SubParsersAction, subparser_name: str, help_message: str,
                    ordered_check_names: list[ str ], check_features_config: dict[ str, CheckFeature ] ) -> None:
    """
    Fills a subparser with arguments for performing a set of checks.

    Args:
        subparsers: The subparsers action from argparse.
        subparser_name: The name for this specific subparser (e.g., 'all-checks').
        help_message: The help message for this subparser.
        ordered_check_names: The list of check names to be used in help messages.
        check_features_config: The configuration dictionary for the checks.
    """
    parser = subparsers.add_parser( subparser_name,
                                    help=help_message,
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    parameters_help: str = _generate_parameters_help( ordered_check_names, check_features_config )

    parser.add_argument( f"--{CHECKS_TO_DO_ARG}",
                         type=str,
                         default="",
                         required=False,
                         help=( "Comma-separated list of checks to perform. "
                                f"If empty, all of the following are run by default: {ordered_check_names}. "
                                f"Available choices: {ordered_check_names}. "
                                f"Example: --{CHECKS_TO_DO_ARG} {ordered_check_names[0]},{ordered_check_names[1]}" ) )
    parser.add_argument( f"--{PARAMETERS_ARG}",
                         type=str,
                         default="",
                         required=False,
                         help=( "Comma-separated list of parameters to override defaults (e.g., 'param_name:value'). "
                                f"Default parameters are: {parameters_help}"
                                f"Example: --{PARAMETERS_ARG} parameter_name:10.5,other_param:25" ) )


def convert( parsed_args: argparse.Namespace, ordered_check_names: list[ str ],
             check_features_config: dict[ str, CheckFeature ] ) -> AllChecksOptions:
    """
    Converts parsed command-line arguments into an AllChecksOptions object based on the provided configuration.
    """
    # 1. Determine which checks to perform
    if not parsed_args[ CHECKS_TO_DO_ARG ]:  # handles default and if user explicitly provides --checks_to_perform ""
        final_selected_check_names: list[ str ] = deepcopy( ordered_check_names )
        setup_logger.info( "All configured checks will be performed by default." )
    else:
        user_checks = parse_comma_separated_string( parsed_args[ CHECKS_TO_DO_ARG ] )
        final_selected_check_names = list()
        for name in user_checks:
            if name not in check_features_config:
                setup_logger.warning( f"Check '{name}' does not exist. Choose from: {ordered_check_names}." )
            elif name not in final_selected_check_names:
                final_selected_check_names.append( name )

        if not final_selected_check_names:
            raise ValueError( "No valid checks were selected. No operations will be configured." )

    # 2. Prepare parameters for the selected checks
    default_params = { name: feature.default_params.copy() for name, feature in check_features_config.items() }
    final_check_params = { name: default_params[ name ] for name in final_selected_check_names }

    if not parsed_args[ PARAMETERS_ARG ]:  # handles default and if user explicitly provides --set_parameters ""
        setup_logger.info( "Default configuration of parameters adopted for every check to perform." )
    else:
        set_parameters = parse_comma_separated_string( parsed_args[ PARAMETERS_ARG ] )
        for param in set_parameters:
            if ':' not in param:
                setup_logger.warning( f"Parameter '{param}' is not in 'name:value' format. Skipping." )
                continue

            name, _, value_str = param.partition( ':' )
            name = name.strip()
            value_str = value_str.strip()

            if not value_str:
                setup_logger.warning( f"Parameter '{name}' has no value. Skipping." )
                continue

            try:
                value_float = float( value_str )
            except ValueError:
                setup_logger.warning( f"Invalid value for '{name}': '{value_str}'. Must be a number. Skipping." )
                continue

            # Apply the parameter override to any check that uses it
            for check_name_key in final_check_params:
                if name in final_check_params[ check_name_key ]:
                    final_check_params[ check_name_key ][ name ] = value_float

    # 3. Instantiate Options objects for the selected checks
    individual_check_options: dict[ str, Any ] = dict()
    individual_check_display: dict[ str, Any ] = dict()

    for check_name in list( final_check_params.keys() ):
        params = final_check_params[ check_name ]
        feature_config = check_features_config[ check_name ]
        try:
            individual_check_options[ check_name ] = feature_config.options_cls( **params )
            individual_check_display[ check_name ] = feature_config.display
        except Exception as e:
            setup_logger.error( f"Failed to create options for check '{check_name}': {e}. This check will be skipped." )
            final_selected_check_names.remove( check_name )

    return AllChecksOptions( checks_to_perform=final_selected_check_names,
                             checks_options=individual_check_options,
                             check_displays=individual_check_display )


# Generic display of Results
def display_results( options: AllChecksOptions, result: AllChecksResult ) -> None:
    """Displays the results of all the checks that have been performed."""
    if not options.checks_to_perform:
        setup_logger.results( "No checks were performed or all failed during configuration." )
        return

    max_length: int = max( len( name ) for name in options.checks_to_perform )
    for name, res in result.check_results.items():
        setup_logger.results( "" )  # Blank line for visibility
        setup_logger.results( f"******** {name:<{max_length}} ********" )
        display_func = options.check_displays.get( name )
        opts = options.checks_options.get( name )
        if display_func and opts:
            display_func( opts, res )
    setup_logger.results( "" )
