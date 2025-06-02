from copy import deepcopy
from geos.mesh.doctor.checks.all_checks import Options, Result
from geos.mesh.doctor.parsing import ( ALL_CHECKS, COLLOCATES_NODES, ELEMENT_VOLUMES, NON_CONFORMAL,
                                       SELF_INTERSECTING_ELEMENTS, SUPPORTED_ELEMENTS )
from geos.mesh.doctor.parsing.collocated_nodes_parsing import ( __COLLOCATED_NODES_DEFAULT, Options as OptionsCN, Result
                                                                as ResultCN )
from geos.mesh.doctor.parsing.element_volumes_parsing import ( __ELEMENT_VOLUMES_DEFAULT, Options as OptionsEV, Result
                                                               as ResultEV )
from geos.mesh.doctor.parsing.non_conformal_parsing import ( __NON_CONFORMAL_DEFAULT, Options as OptionsNC, Result as
                                                             ResultNC )
from geos.mesh.doctor.parsing.self_intersecting_elements_parsing import ( __SELF_INTERSECTING_ELEMENTS_DEFAULT, Options
                                                                          as OptionsSIE, Result as ResultSIE )
from geos.mesh.doctor.parsing.supported_elements_parsing import ( __SUPPORTED_ELEMENTS_DEFAULT, Options as OptionsSE,
                                                                  Result as ResultSE )
from geos.utils.Logger import getLogger

__CHECK_ONLY_FEATURES = [
    COLLOCATES_NODES, ELEMENT_VOLUMES, NON_CONFORMAL, SELF_INTERSECTING_ELEMENTS, SUPPORTED_ELEMENTS
]
__CHECK_ONLY_FEATURES_DEFAULT = {
    COLLOCATES_NODES: __COLLOCATED_NODES_DEFAULT,
    ELEMENT_VOLUMES: __ELEMENT_VOLUMES_DEFAULT,
    NON_CONFORMAL: __NON_CONFORMAL_DEFAULT,
    SELF_INTERSECTING_ELEMENTS: __SELF_INTERSECTING_ELEMENTS_DEFAULT,
    SUPPORTED_ELEMENTS: __SUPPORTED_ELEMENTS_DEFAULT
}
__CHECK_ONLY_FEATURES_OPTIONS = {
    COLLOCATES_NODES: OptionsCN,
    ELEMENT_VOLUMES: OptionsEV,
    NON_CONFORMAL: OptionsNC,
    SELF_INTERSECTING_ELEMENTS: OptionsSIE,
    SUPPORTED_ELEMENTS: OptionsSE
}
__CHECK_ONLY_FEATURES_RESULTS = {
    COLLOCATES_NODES: ResultCN,
    ELEMENT_VOLUMES: ResultEV,
    NON_CONFORMAL: ResultNC,
    SELF_INTERSECTING_ELEMENTS: ResultSIE,
    SUPPORTED_ELEMENTS: ResultSE
}

__CHECKS_TO_DO = "checks"
__CHECKS_TO_DO_DEFAULT = __CHECK_ONLY_FEATURES

__CHECKS_SET_PARAMETERS = "set_parameters"
__CHECKS_SET_PARAMETERS_DEFAULT: list[ str ] = list()
__CHECKS_SET_PARAMETERS_DEFAULT_HELP: str = ""
for feature, default_map in __CHECK_ONLY_FEATURES_DEFAULT.items():
    __CHECKS_SET_PARAMETERS_DEFAULT_HELP += f"For {feature},"
    for name, value in default_map.items():
        __CHECKS_SET_PARAMETERS_DEFAULT.append( name + ":" + str( value ) )
        __CHECKS_SET_PARAMETERS_DEFAULT_HELP += " " + name + ":" + str( value )
    __CHECKS_SET_PARAMETERS_DEFAULT_HELP += ". "

logger = getLogger( "All_checks parsing" )


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser(
        ALL_CHECKS, help="Perform one or multiple mesh-doctor check operation in one command line on a same mesh." )
    p.add_argument(
        '--' + __CHECKS_TO_DO,
        type=float,
        metavar=", ".join( __CHECKS_TO_DO_DEFAULT ),
        default=", ".join( __CHECKS_TO_DO_DEFAULT ),
        required=False,
        help="[list of comma separated str]: Name of the mesh-doctor checks that you want to perform on your mesh."
        f" By default, all the checks will be performed which correspond to this list: \"{','.join(__CHECKS_TO_DO_DEFAULT)}\"."
        f" If only two of these checks are needed, you can only select them by specifying: --{__CHECKS_TO_DO} {__CHECKS_TO_DO_DEFAULT[0]}, {__CHECKS_TO_DO_DEFAULT[1]}"
    )
    p.add_argument(
        '--' + __CHECKS_SET_PARAMETERS,
        type=float,
        metavar=", ".join( __CHECKS_SET_PARAMETERS_DEFAULT ),
        default=", ".join( __CHECKS_SET_PARAMETERS_DEFAULT ),
        required=False,
        help=
        "[list of comma separated str]: Each of the checks that will be performed have some parameters to specify when using them."
        " By default, every of these parameters have been set to default values that will be mostly used in the vast majority of cases."
        f" If you want to change the values, just type the following command: --{__CHECKS_SET_PARAMETERS} parameter0:10, parameter1:25, ..."
        f" The complete list of parameters to change with their default value is the following: {__CHECKS_SET_PARAMETERS_DEFAULT_HELP}"
    )


def convert( parsed_options ) -> Options:
    # first, we need to gather every check that will be performed
    checks_to_do: list[ str ] = parsed_options[ __CHECKS_TO_DO ].replace( " ", "" ).split( "," )
    checks_to_perform = set()
    for check in checks_to_do:
        if check not in __CHECKS_TO_DO_DEFAULT:
            logger.critical( f"The given check '{check}' does not exist. Cannot perform this check. Choose between"
                             f" the available checks: {__CHECKS_TO_DO_DEFAULT}." )
        else:
            checks_to_perform.add( check )
    checks_to_perform = list( checks_to_perform )  # only unique checks because of set
    # then, we need to find the values to set in the Options object of every check
    set_parameters: list[ str ] = parsed_options[ __CHECKS_SET_PARAMETERS ].replace( " ", "" ).split( "," )
    set_parameters_tuple: list[ tuple[ str ] ] = [ p.split( ":" ) for p in set_parameters ]
    checks_parameters = deepcopy( __CHECK_ONLY_FEATURES_DEFAULT )
    for set_param in set_parameters_tuple:
        for default_parameters in checks_parameters.values():
            if set_param[ 0 ] in default_parameters:
                default_parameters[ set_param[ 0 ] ] = float( set_param[ 1 ] )
    # finally, we can create the Options object for every check with the right parameters
    checks_options = list()
    for check_to_perform in checks_to_perform:
        option_to_use = __CHECK_ONLY_FEATURES_OPTIONS[ check_to_perform ]
        options_parameters: dict[ str, float ] = checks_parameters[ check_to_perform ]
        checks_options.append( option_to_use( **options_parameters ) )
    return Options( checks_to_perform=checks_to_perform, checks_options=checks_options )


def display_results( options: Options, result: Result ):
    pass
