# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
import numpy as np
import numpy.typing as npt
from typing_extensions import Self, Any

from geos.geomechanics.processing.geomechanicsCalculatorFunctions import (
    computeStressPrincipalComponentsFromStressVector, )

__doc__ = """
MohrCircle module define the Mohr's circle parameters.

Inputs are a 6 component stress vector, and a circle id.
The class computes principal components from stress vector during initialization.
Accessors get access to these 3 principal components as well as circle center
and radius.

To use the object:

.. code-block:: python

    from processing.MohrCircle import MohrCircle

    # Create the object
    stressVector: npt.NDArray[np.float64]
    circleId: str
    mohrCircle: MohrCircle = MohrCircle(circleId)

    # Either directly set principal components (p3 <= p2 <= p1)
    mohrCircle.SetPrincipalComponents(p3, p2, p1)
    # Or compute them from stress vector
    mohrCircle.computePrincipalComponents(stressVector)

    # Access to members
    id: str = mohrCircle.getCircleId()
    p1, p2, p3: float = mohrCircle.getPrincipalComponents()
    radius: float = mohrCircle.getCircleRadius()
    center: float = mohrCircle.getCircleCenter()
"""

loggerTitle : str = "MohrCircle"

class MohrCircle:

    def __init__( self: Self, circleId: str ) -> None:
        """Compute Mohr's Circle from input stress.

        Args:
            circleId (str): Mohr's circle id.
        """
        self.circleId: str = circleId

        self.p1: float = 0.0
        self.p2: float = 0.0
        self.p3: float = 0.0

    def __str__( self: Self ) -> str:
        """Overload of __str__ method."""
        return self.circleId

    def __repr__( self: Self ) -> str:
        """Overload of __repr__ method."""
        return self.circleId

    def __eq__( self: Self, other: Any ) -> bool:
        """Overload of __eq__ method."""
        if not isinstance( other, MohrCircle ):
            return NotImplemented
        return self.circleId == other.circleId

    def __hash__( self: Self ) -> int:
        """Overload of hash method."""
        return hash( self.circleId )

    def setCircleId( self: Self, circleId: str ) -> None:
        """Set circle Id variable.

        Args:
            circleId (str): Circle Id.
        """
        self.circleId = circleId

    def getCircleId( self: Self ) -> str:
        """Access the Id of the Mohr circle.

        Returns:
            str: Id of the Mohr circle
        """
        return self.circleId

    def getCircleRadius( self: Self ) -> float:
        """Compute and return Mohr's circle radius from principal components.

        Returns:
            float: Mohr circle radius.
        """
        return ( self.p1 - self.p3 ) / 2.0

    def getCircleCenter( self: Self ) -> float:
        """Compute and return Mohr's circle center from principal components.

        Returns:
            float: Mohr circle center.
        """
        return ( self.p1 + self.p3 ) / 2.0

    def getPrincipalComponents( self: Self ) -> tuple[ float, float, float ]:
        """Get Moh's circle principal components.

        Returns:
            tuple[float, float, float]: Mohr circle principal components.
        """
        return ( self.p3, self.p2, self.p1 )

    def setPrincipalComponents( self: Self, p3: float, p2: float, p1: float ) -> None:
        """Set principal components.

        Args:
            p3 (float): First component. Must be the lowest.
            p2 (float): Second component.
            p1 (float): Third component. Must be the greatest.

        Raises:
            ValueError: Expected p3 <= p2 <= p1.
        """
        if not ( ( p3 <= p2 ) and ( p2 <= p1 ) ):
            raise ValueError( "Component order is wrong. Expected p3 <= p2 <= p1." )
        self.p3 = p3
        self.p2 = p2
        self.p1 = p1

    def computePrincipalComponents( self: Self, stressVector: npt.NDArray[ np.float64 ] ) -> None:
        """Calculate principal components.

        Args:
            stressVector (npt.NDArray[np.float64]): 6 components stress vector
                Stress vector must follow GEOS convention (XX, YY, ZZ, YZ, XZ, XY)
        """
        # Get stress principal components
        self.p3, self.p2, self.p1 = ( computeStressPrincipalComponentsFromStressVector( stressVector ) )
