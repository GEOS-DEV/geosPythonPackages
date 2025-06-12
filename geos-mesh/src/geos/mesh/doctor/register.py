import argparse
import importlib
from typing import Dict, Callable, Any, Tuple
import geos.mesh.doctor.parsing as parsing
from geos.mesh.doctor.parsing import ActionHelper, cli_parsing
from geos.mesh.doctor.parsing.cli_parsing import setup_logger

__HELPERS: Dict[ str, Callable[ [ None ], ActionHelper ] ] = dict()
__ACTIONS: Dict[ str, Callable[ [ None ], Any ] ] = dict()


def __load_module_action( module_name: str, action_fct="action" ):
    module = importlib.import_module( "geos.mesh.doctor.actions." + module_name )
    return getattr( module, action_fct )


def __load_module_action_helper( module_name: str, parsing_fct_suffix="_parsing" ):
    module = importlib.import_module( "geos.mesh.doctor.parsing." + module_name + parsing_fct_suffix )
    return ActionHelper( fill_subparser=module.fill_subparser,
                         convert=module.convert,
                         display_results=module.display_results )


def __load_actions() -> Dict[ str, Callable[ [ str, Any ], Any ] ]:
    """
    Loads all the actions.
    This function acts like a protection layer if a module fails to load.
    A action that fails to load won't stop the process.
    :return: The actions.
    """
    loaded_actions: Dict[ str, Callable[ [ str, Any ], Any ] ] = dict()
    for action_name, action_provider in __ACTIONS.items():
        try:
            loaded_actions[ action_name ] = action_provider()
            setup_logger.debug( f"Action \"{action_name}\" is loaded." )
        except Exception as e:
            setup_logger.warning( f"Could not load module \"{action_name}\": {e}" )
    return loaded_actions


def register_parsing_actions(
) -> Tuple[ argparse.ArgumentParser, Dict[ str, Callable[ [ str, Any ], Any ] ], Dict[ str, ActionHelper ] ]:
    """
    Register all the parsing actions. Eventually initiate the registration of all the actions too.
    :return: The actions and the actions helpers.
    """
    parser = cli_parsing.init_parser()
    subparsers = parser.add_subparsers( help="Modules", dest="subparsers" )

    def closure_trick( cn: str ):
        __HELPERS[ action_name ] = lambda: __load_module_action_helper( cn )
        __ACTIONS[ action_name ] = lambda: __load_module_action( cn )

    # Register the modules to load here.
    for action_name in ( parsing.ALL_CHECKS, parsing.COLLOCATES_NODES, parsing.ELEMENT_VOLUMES,
                         parsing.FIX_ELEMENTS_ORDERINGS, parsing.GENERATE_CUBE, parsing.GENERATE_FRACTURES,
                         parsing.GENERATE_GLOBAL_IDS, parsing.NON_CONFORMAL, parsing.SELF_INTERSECTING_ELEMENTS,
                         parsing.SUPPORTED_ELEMENTS ):
        closure_trick( action_name )
    loaded_actions: Dict[ str, Callable[ [ str, Any ], Any ] ] = __load_actions()
    loaded_actions_helpers: Dict[ str, ActionHelper ] = dict()
    for action_name in loaded_actions.keys():
        h = __HELPERS[ action_name ]()
        h.fill_subparser( subparsers )
        loaded_actions_helpers[ action_name ] = h
        setup_logger.debug( f"Parsing for action \"{action_name}\" is loaded." )
    return parser, loaded_actions, loaded_actions_helpers
