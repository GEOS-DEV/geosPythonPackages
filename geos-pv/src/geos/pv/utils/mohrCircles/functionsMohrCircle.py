# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
import os
from typing import Any

import numpy as np
import numpy.typing as npt
from geos.geomechanics.model.MohrCircle import MohrCircle
from geos.geomechanics.model.MohrCoulomb import MohrCoulomb

from geos.pv.utils.mohrCircles import (
    MOHR_CIRCLE_ANALYSIS_MAIN,
    MOHR_CIRCLE_PATH,
)

__doc__ = """
functionsMohrCircle module provides a set of utilities to instanciate Mohr's
circles and Mohr-Coulomb failure envelope.
"""


def buildPythonViewScript(
    dir_path: str,
    mohrCircles: list[ MohrCircle ],
    rockCohesion: float,
    frictionAngle: float,
    userChoices: dict[ str, Any ],
) -> str:
    """Builds the Python script used to launch the Python View.

    The script is returned as a string to be then injected in the Python
    View.

    Args:
        dir_path (str): directory path

        mohrCircles (list[MohrCircle]): list of MohrCircle objects

        rockCohesion (float): rock cohesion (Pa)

        frictionAngle (float): friction angle (rad)

        userChoices (dict[str, Any]): dictionnary of user plot parameters
    Returns:
        str: Complete Python View script.
    """
    pathPythonViewScript: str = os.path.join( dir_path, MOHR_CIRCLE_PATH, MOHR_CIRCLE_ANALYSIS_MAIN )

    mohrCircleParams: list[ tuple[ str, float, float,
                                   float ] ] = [ ( mohrCircle.getCircleId(), *( mohrCircle.getPrincipalComponents() ) )
                                                 for mohrCircle in mohrCircles ]

    script: str = ""
    script += f"mohrCircleParams = {mohrCircleParams}\n"
    script += f"rockCohesion = {rockCohesion}\n"
    script += f"frictionAngle = {frictionAngle}\n"
    script += f"userChoices = {userChoices}\n\n\n"
    with open( pathPythonViewScript ) as file:
        fileContents = file.read()
        script += fileContents
    return script


def findAnnotateTuples( mohrCircle: MohrCircle, ) -> tuple[ str, str, tuple[ float, float ], tuple[ float, float ] ]:
    """Get the values and location of min and max normal stress or Mohr's circle.

    Args:
        mohrCircle (MohrCircle): input Mohr's circle

        maxTau (float): max shear stress

    Returns:
        tuple[str, str, tuple[float, float], tuple[float, float]]: labels and
        location of labels.
    """
    p3, p2, p1 = mohrCircle.getPrincipalComponents()
    xMaxDisplay: str = f"{p1:.2E}"
    xMinDisplay: str = f"{p3:.2E}"
    yPosition: float = 0.0
    xyMax: tuple[ float, float ] = ( p1, yPosition )
    xyMin: tuple[ float, float ] = ( p3, yPosition )
    return ( xMaxDisplay, xMinDisplay, xyMax, xyMin )


def getMohrCircleId( cellId: str, timeStep: str ) -> str:
    """Get Mohr's circle ID from cell id and time step.

    Args:
        cellId (str): cell ID

        timeStep (str): time step.

    Returns:
        str: Mohr's circle ID
    """
    return f"Cell_{cellId}@{timeStep}"


def createMohrCircleAtTimeStep(
    stressArray: npt.NDArray[ np.float64 ],
    cellIds: list[ str ],
    timeStep: str,
    convention: bool,
) -> list[ MohrCircle ]:
    """Create MohrCircle object(s) at a given time step for all cell ids.

    Args:
        stressArray (npt.NDArray[np.float64]): stress numpy array

        cellIds (list[str]): list of cell ids

        timeStep (str): time step

        convention (bool): convention used for compression.
        * False is Geos convention (compression is negative)
        * True is usual convention (compression is positive)

    Returns:
        list[MohrCircle]: list of MohrCircle objects.
    """
    assert stressArray.shape[ 1 ] == 6, "Stress vector must be of size 6."
    mohrCircles: list[ MohrCircle ] = []
    sign: float = 1.0 if convention else -1.0
    for i, cellId in enumerate( cellIds ):
        ide: str = getMohrCircleId( cellId, timeStep )
        mohrCircle: MohrCircle = MohrCircle( ide )
        mohrCircle.computePrincipalComponents( stressArray[ i ] * sign )
        mohrCircles.append( mohrCircle )
    return mohrCircles


def createMohrCirclesFromPrincipalComponents(
        mohrCircleParams: list[ tuple[ str, float, float, float ] ] ) -> list[ MohrCircle ]:
    """Create Mohr's circle objects from principal components.

    Args:
        mohrCircleParams (list[tuple[str, float, float, float]]): list of Mohr's
        circle parameters

    Returns:
        list[MohrCircle]: list of Mohr's circle objects.
    """
    mohrCircles: list[ MohrCircle ] = []
    for circleId, p3, p2, p1 in mohrCircleParams:
        mohrCircle: MohrCircle = MohrCircle( circleId )
        mohrCircle.setPrincipalComponents( p3, p2, p1 )
        mohrCircles.append( mohrCircle )
    return mohrCircles


def createMohrCoulombEnvelope( rockCohesion: float, frictionAngle: float ) -> MohrCoulomb:
    """Create MohrCoulomb object from user parameters.

    Args:
        rockCohesion (float): rock cohesion (Pa).

        frictionAngle (float): friction angle in radian.

    Returns:
        MohrCoulomb: MohrCoulomb object.
    """
    return MohrCoulomb( rockCohesion, frictionAngle )
