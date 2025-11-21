# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
import argparse
from dataclasses import dataclass
from typing import Callable, Any

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


@dataclass( frozen=True )
class ActionHelper:
    fillSubparser: Callable[ [ Any ], argparse.ArgumentParser ]
    convert: Callable[ [ Any ], Any ]
    displayResults: Callable[ [ Any, Any ], None ]
