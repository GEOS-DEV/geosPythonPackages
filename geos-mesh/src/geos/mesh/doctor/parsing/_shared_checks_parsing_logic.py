import argparse
from copy import deepcopy
from dataclasses import dataclass
from typing import Type, Any

from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions
from geos.mesh.doctor.actions.all_checks import Result as AllChecksResult
from geos.mesh.doctor.parsing.cli_parsing import parseCommaSeparatedString, setupLogger


# --- Data Structure for Check Features ---
@dataclass( frozen=True )
class CheckFeature:
    """A container for a check's configuration and associated classes."""
    name: str
    optionsCls: Type[ Any ]
    resultCls: Type[ Any ]
    defaultParams: dict[ str, Any ]
    display: Type[ Any ]


# --- Argument Parser Constants ---
CHECKS_TO_DO_ARG = "checksToPerform"
PARAMETERS_ARG = "setParameters"


def _generateParametersHelp( orderedCheckNames: list[ str ], checkFeaturesConfig: dict[ str,
                                                                                              CheckFeature ] ) -> str:
    """Dynamically generates the help text for the setParameters argument."""
    helpText: str = ""
    for checkName in orderedCheckNames:
        config = checkFeaturesConfig.get( checkName )
        if config and config.defaultParams:
            configParams = [ f"{name}:{value}" for name, value in config.defaultParams.items() ]
            helpText += f"For {checkName}: {', '.join(configParams)}. "
    return helpText


def getOptionsUsedMessage( optionsUsed: dataclass ) -> str:
    """Dynamically generates the description of every parameter used when loaching a check.

    Args:
        optionsUsed (dataclass)

    Returns:
        str: A message like "Parameters used: ( param1:value1 param2:value2 )" for as many paramters found.
    """
    optionsMsg: str = "Parameters used: ("
    for attrName in optionsUsed.__dataclass_fields__:
        attrValue = getattr( optionsUsed, attrName )
        optionsMsg += f" {attrName} = {attrValue}"
    return optionsMsg + " )."


# --- Generic Argument Parser Setup ---
def fillSubparser( subparsers: argparse._SubParsersAction, subparserName: str, helpMessage: str,
                   orderedCheckNames: list[ str ], checkFeaturesConfig: dict[ str, CheckFeature ] ) -> None:
    """
    Fills a subparser with arguments for performing a set of checks.

    Args:
        subparsers: The subparsers action from argparse.
        subparser_name: The name for this specific subparser (e.g., 'all-checks').
        help_message: The help message for this subparser.
        ordered_checkNames: The list of check names to be used in help messages.
        check_features_config: The configuration dictionary for the checks.
    """
    parser = subparsers.add_parser( subparserName,
                                    help=helpMessage,
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    parametersHelp: str = _generateParametersHelp( orderedCheckNames, checkFeaturesConfig )

    parser.add_argument( f"--{CHECKS_TO_DO_ARG}",
                         type=str,
                         default="",
                         required=False,
                         help=( "Comma-separated list of checks to perform. "
                                f"If empty, all of the following are run by default: {orderedCheckNames}. "
                                f"Available choices: {orderedCheckNames}. "
                                f"Example: --{CHECKS_TO_DO_ARG} {orderedCheckNames[0]},{orderedCheckNames[1]}" ) )
    parser.add_argument( f"--{PARAMETERS_ARG}",
                         type=str,
                         default="",
                         required=False,
                         help=( "Comma-separated list of parameters to override defaults (e.g., 'param_name:value'). "
                                f"Default parameters are: {parametersHelp}"
                                f"Example: --{PARAMETERS_ARG} parameter_name:10.5,other_param:25" ) )


def convert( parsedArgs: argparse.Namespace, orderedCheckNames: list[ str ],
             checkFeaturesConfig: dict[ str, CheckFeature ] ) -> AllChecksOptions:
    """
    Converts parsed command-line arguments into an AllChecksOptions object based on the provided configuration.
    """
    # 1. Determine which checks to perform
    if not parsedArgs[ CHECKS_TO_DO_ARG ]:  # handles default and if user explicitly provides --checksToPerform ""
        finalSelectedCheckNames: list[ str ] = deepcopy( orderedCheckNames )
        setupLogger.info( "All configured checks will be performed by default." )
    else:
        userChecks = parseCommaSeparatedString( parsedArgs[ CHECKS_TO_DO_ARG ] )
        finalSelectedCheckNames = list()
        for name in userChecks:
            if name not in checkFeaturesConfig:
                setupLogger.warning( f"Check '{name}' does not exist. Choose from: {orderedCheckNames}." )
            elif name not in finalSelectedCheckNames:
                finalSelectedCheckNames.append( name )

        if not finalSelectedCheckNames:
            raise ValueError( "No valid checks were selected. No operations will be configured." )

    # 2. Prepare parameters for the selected checks
    defaultParams = { name: feature.defaultParams.copy() for name, feature in checkFeaturesConfig.items() }
    finalCheckParams = { name: defaultParams[ name ] for name in finalSelectedCheckNames }

    if not parsedArgs[ PARAMETERS_ARG ]:  # handles default and if user explicitly provides --setParameters ""
        setupLogger.info( "Default configuration of parameters adopted for every check to perform." )
    else:
        setParameters = parseCommaSeparatedString( parsedArgs[ PARAMETERS_ARG ] )
        for param in setParameters:
            if ':' not in param:
                setupLogger.warning( f"Parameter '{param}' is not in 'name:value' format. Skipping." )
                continue

            name, _, valueStr = param.partition( ':' )
            name = name.strip()
            valueStr = valueStr.strip()

            if not valueStr:
                setupLogger.warning( f"Parameter '{name}' has no value. Skipping." )
                continue

            try:
                valueFloat = float( valueStr )
            except ValueError:
                setupLogger.warning( f"Invalid value for '{name}': '{valueStr}'. Must be a number. Skipping." )
                continue

            # Apply the parameter override to any check that uses it
            for checkNameKey in finalCheckParams:
                if name in finalCheckParams[ checkNameKey ]:
                    finalCheckParams[ checkNameKey ][ name ] = valueFloat

    # 3. Instantiate Options objects for the selected checks
    individualCheckOptions: dict[ str, Any ] = dict()
    individualCheckDisplay: dict[ str, Any ] = dict()

    for checkName in list( finalCheckParams.keys() ):
        params = finalCheckParams[ checkName ]
        featureConfig = checkFeaturesConfig[ checkName ]
        try:
            individualCheckOptions[ checkName ] = featureConfig.optionsCls( **params )
            individualCheckDisplay[ checkName ] = featureConfig.display
        except Exception as e:
            setupLogger.error( f"Failed to create options for check '{checkName}': {e}. This check will be skipped." )
            finalSelectedCheckNames.remove( checkName )

    return AllChecksOptions( checksToPerform=finalSelectedCheckNames,
                             checksOptions=individualCheckOptions,
                             checkDisplays=individualCheckDisplay )


# Generic display of Results
def displayResults( options: AllChecksOptions, result: AllChecksResult ) -> None:
    """Displays the results of all the checks that have been performed."""
    if not options.checksToPerform:
        setupLogger.results( "No checks were performed or all failed during configuration." )
        return

    maxLength: int = max( len( name ) for name in options.checksToPerform )
    for name, res in result.checkResults.items():
        setupLogger.results( "" )  # Blank line for visibility
        setupLogger.results( f"******** {name:<{maxLength}} ********" )
        displayFunc = options.checkDisplays.get( name )
        opts = options.checksOptions.get( name )
        if displayFunc and opts:
            displayFunc( opts, res )
    setupLogger.results( "" )
