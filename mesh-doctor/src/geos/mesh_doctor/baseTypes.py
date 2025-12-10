import argparse
from dataclasses import dataclass
from typing import Any, Callable, Protocol, TypeAlias, runtime_checkable

__doc__ = """Base types, constants and protocols for mesh-doctor actions and parsing."""

DefaultParameters: TypeAlias = dict[ str, Any ]  # check parameter name to default value
UserInputs: TypeAlias = dict[ str, str ]  # command line input mapping parameter name to string value
UserParameters: TypeAlias = dict[ str, Any ]  # check parameter name to user-provided value

ALL_CHECKS = "allChecks"
MAIN_CHECKS = "mainChecks"
COLLOCATES_NODES = "collocatedNodes"
ELEMENT_VOLUMES = "elementVolumes"
FIX_ELEMENTS_ORDERINGS = "fixElementsOrderings"
GENERATE_CUBE = "generateCube"
GENERATE_FRACTURES = "generateFractures"
GENERATE_GLOBAL_IDS = "generateGlobalIds"
NON_CONFORMAL = "nonConformal"
SELF_INTERSECTING_ELEMENTS = "selfIntersectingElements"
SUPPORTED_ELEMENTS = "supportedElements"

ACTION_NAMES = [
    ALL_CHECKS, MAIN_CHECKS, COLLOCATES_NODES, ELEMENT_VOLUMES, FIX_ELEMENTS_ORDERINGS, GENERATE_CUBE,
    GENERATE_FRACTURES, GENERATE_GLOBAL_IDS, NON_CONFORMAL, SELF_INTERSECTING_ELEMENTS, SUPPORTED_ELEMENTS
]


@dataclass( frozen=True )
class ActionHelper:
    fillSubparser: Callable[ [ Any ], argparse.ArgumentParser ]
    convert: Callable[ [ Any ], Any ]
    displayResults: Callable[ [ Any, Any ], None ]


@runtime_checkable
class OptionsProtocol( Protocol ):
    """Protocol for Options dataclasses used in mesh-doctor actions.

    All Options dataclasses should be frozen dataclasses that implement this protocol
    by being a dataclass (which provides __dataclass_fields__).

    This allows for structural subtyping - any frozen dataclass can be considered
    a valid Options type for type checking purposes.
    """
    __dataclass_fields__: dict  # type: ignore[misc]


@runtime_checkable
class ResultProtocol( Protocol ):
    """Protocol for Result dataclasses used in mesh-doctor actions.

    All Result dataclasses should be frozen dataclasses that implement this protocol
    by being a dataclass (which provides __dataclass_fields__).

    This allows for structural subtyping - any frozen dataclass can be considered
    a valid Result type for type checking purposes.
    """
    __dataclass_fields__: dict  # type: ignore[misc]
