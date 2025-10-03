import argparse
import importlib
from typing import Dict, Callable, Any, Tuple
import geos.mesh.doctor.parsing as parsing
from geos.mesh.doctor.parsing import ActionHelper, cliParsing
from geos.mesh.doctor.parsing.cliParsing import setupLogger

__HELPERS: Dict[ str, Callable[ [ None ], ActionHelper ] ] = dict()
__ACTIONS: Dict[ str, Callable[ [ None ], Any ] ] = dict()


def __loadModuleAction( moduleName: str, actionFct="action" ):
    module = importlib.import_module( "geos.mesh.doctor.actions." + moduleName )
    return getattr( module, actionFct )


def __loadModuleActionHelper( moduleName: str, parsingFctSuffix="Parsing" ):
    module = importlib.import_module( "geos.mesh.doctor.parsing." + moduleName + parsingFctSuffix )
    return ActionHelper( fillSubparser=module.fillSubparser,
                         convert=module.convert,
                         displayResults=module.displayResults )


def __loadActions() -> Dict[ str, Callable[ [ str, Any ], Any ] ]:
    """
    Loads all the actions.
    This function acts like a protection layer if a module fails to load.
    A action that fails to load won't stop the process.
    :return: The actions.
    """
    loadedActions: Dict[ str, Callable[ [ str, Any ], Any ] ] = dict()
    for actionName, actionProvider in __ACTIONS.items():
        try:
            loadedActions[ actionName ] = actionProvider()
            setupLogger.debug( f"Action \"{actionName}\" is loaded." )
        except Exception as e:
            setupLogger.warning( f"Could not load module \"{actionName}\": {e}" )
    return loadedActions


def registerParsingActions(
) -> Tuple[ argparse.ArgumentParser, Dict[ str, Callable[ [ str, Any ], Any ] ], Dict[ str, ActionHelper ] ]:
    """
    Register all the parsing actions. Eventually initiate the registration of all the actions too.
    :return: The actions and the actions helpers.
    """
    parser = cliParsing.initParser()
    subparsers = parser.add_subparsers( help="Modules", dest="subparsers" )

    def closureTrick( cn: str ):
        __HELPERS[ actionName ] = lambda: __loadModuleActionHelper( cn )
        __ACTIONS[ actionName ] = lambda: __loadModuleAction( cn )

    # Register the modules to load here.
    for actionName in ( parsing.ALL_CHECKS, parsing.COLLOCATES_NODES, parsing.ELEMENT_VOLUMES,
                        parsing.FIX_ELEMENTS_ORDERINGS, parsing.GENERATE_CUBE, parsing.GENERATE_FRACTURES,
                        parsing.GENERATE_GLOBAL_IDS, parsing.MAIN_CHECKS, parsing.NON_CONFORMAL,
                        parsing.SELF_INTERSECTING_ELEMENTS, parsing.SUPPORTED_ELEMENTS ):
        closureTrick( actionName )
    loadedActions: Dict[ str, Callable[ [ str, Any ], Any ] ] = __loadActions()
    loadedActionsHelpers: Dict[ str, ActionHelper ] = dict()
    for actionName in loadedActions.keys():
        h = __HELPERS[ actionName ]()
        h.fillSubparser( subparsers )
        loadedActionsHelpers[ actionName ] = h
        setupLogger.debug( f"Parsing for action \"{actionName}\" is loaded." )
    return parser, loadedActions, loadedActionsHelpers
