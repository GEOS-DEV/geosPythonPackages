# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
import argparse
import importlib
from typing import Callable
from geos.mesh_doctor.baseTypes import ( ActionHelper, ResultProtocol, ACTION_NAMES )
from geos.mesh_doctor.parsing import cliParsing
from geos.mesh_doctor.parsing.cliParsing import setupLogger

__HELPERS: dict[ str, str ] = {}
__ACTIONS: dict[ str, str ] = {}


def __loadModuleAction( moduleName: str, actionFct: str = "action" ) -> Callable[..., ResultProtocol ]:
    module = importlib.import_module( "geos.mesh_doctor.actions." + moduleName )
    return getattr( module, actionFct )


def __loadModuleActionHelper( moduleName: str, parsingFctSuffix: str = "Parsing" ) -> ActionHelper:
    module = importlib.import_module( "geos.mesh_doctor.parsing." + moduleName + parsingFctSuffix )
    return ActionHelper( fillSubparser=module.fillSubparser,
                         convert=module.convert,
                         displayResults=module.displayResults )


def __loadActions() -> dict[ str, Callable[..., ResultProtocol ] ]:
    """Loads all the actions.

    This function acts like a protection layer if a module fails to load.
    A action that fails to load won't stop the process.

    Returns:
        dict[ str, Callable[ ..., ResultProtocol ] ]: The actions.
    """
    loadedActions: dict[ str, Callable[..., ResultProtocol ] ] = {}
    for actionName, moduleName in __ACTIONS.items():
        try:
            loadedActions[ actionName ] = __loadModuleAction( moduleName )
            setupLogger.debug( f"Action \"{actionName}\" is loaded." )
        except Exception as e:
            setupLogger.warning( f"Could not load module \"{actionName}\": {e}" )
    return loadedActions


def registerParsingActions(
) -> tuple[ argparse.ArgumentParser, dict[ str, Callable[..., ResultProtocol ] ], dict[ str, ActionHelper ] ]:
    """Register all the parsing actions. Eventually initiate the registration of all the actions too.

    Returns:
        tuple[ argparse.ArgumentParser, dict[ str, Callable[ ..., ResultProtocol ] ], dict[ str, ActionHelper ] ]:
        The parser, actions and helpers.
    """
    parser = cliParsing.initParser()
    subparsers = parser.add_subparsers( help="Modules", dest="subparsers" )

    # Register the modules to load here.
    for actionName in ( ACTION_NAMES ):
        __HELPERS[ actionName ] = actionName
        __ACTIONS[ actionName ] = actionName

    loadedActions: dict[ str, Callable[..., ResultProtocol ] ] = __loadActions()
    loadedActionsHelpers: dict[ str, ActionHelper ] = {}
    for actionName in loadedActions:
        moduleName = __HELPERS[ actionName ]
        try:
            h = __loadModuleActionHelper( moduleName )
            h.fillSubparser( subparsers )
            loadedActionsHelpers[ actionName ] = h
            setupLogger.debug( f"Parsing for action \"{actionName}\" is loaded." )
        except Exception as e:
            setupLogger.warning( f"Could not load parsing for action \"{actionName}\": {e}" )
    return parser, loadedActions, loadedActionsHelpers
