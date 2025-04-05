# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
import numpy as np
import numpy.typing as npt
from typing_extensions import Self

from geos_posp.processing.geomechanicsCalculatorFunctions import (
    computeStressPrincipalComponentsFromStressVector, )

__doc__ = """
MohrCircle module define the Mohr's circle parameters.

Inputs are a 6 component stress vector, a circle id, and the mechanical
convention used for compression.
The class computes principal components from stress vector during initialization.
Accessors get access to these 3 principal components as well as circle center
and radius.

To use the object:

.. code-block:: python

    from processing.MohrCircle import MohrCircle

    # create the object
    stressVector :npt.NDArray[np.float64]
    circleId :str
    mohrCircle :MohrCircle = MohrCircle(circleId)

    # either directly set principal components (p3 <= p2 <= p1)
    mohrCircle.SetPrincipalComponents(p3, p2, p1)
    # or compute them from stress vector
    mohrCircle.computePrincipalComponents(stressVector)

    # access to members
    id :str = mohrCircle.getCircleId()
    p1, p2, p3 :float = mohrCircle.getPrincipalComponents()
    radius :float = mohrCircle.getCircleRadius()
    center :float = mohrCircle.getCircleCenter()
"""


class MohrCircle:

    def __init__( self: Self, circleId: str ) -> None:
        """Compute Mohr's Circle from input stress.

        Args:
            circleId (str): Mohr's circle id.
        """
        self.m_circleId: str = circleId

        self.m_p1: float = 0.0
        self.m_p2: float = 0.0
        self.m_p3: float = 0.0

    def __str__( self: Self ) -> str:
        """Overload of __str__ method."""
        return self.m_circleId

    def __repr__( self: Self ) -> str:
        """Overload of __repr__ method."""
        return self.m_circleId

    def setCircleId( self: Self, circleId: str ) -> None:
        """Set circle Id variable.

        Args:
            circleId (str): circle Id.
        """
        self.m_circleId = circleId

    def getCircleId( self: Self ) -> str:
        """Access the Id of the Mohr circle.

        Returns:
            str: Id of the Mohr circle
        """
        return self.m_circleId

    def getCircleRadius( self: Self ) -> float:
        """Compute and return Mohr's circle radius from principal components."""
        return ( self.m_p1 - self.m_p3 ) / 2.0

    def getCircleCenter( self: Self ) -> float:
        """Compute and return Mohr's circle center from principal components."""
        return ( self.m_p1 + self.m_p3 ) / 2.0

    def getPrincipalComponents( self: Self ) -> tuple[ float, float, float ]:
        """Get Moh's circle principal components."""
        return ( self.m_p3, self.m_p2, self.m_p1 )

    def setPrincipalComponents( self: Self, p3: float, p2: float, p1: float ) -> None:
        """Set principal components.

        Args:
            p3 (float): first component. Must be the lowest.
            p2 (float): second component.
            p1 (float): third component. Must be the greatest.
        """
        assert ( p3 <= p2 ) and ( p2 <= p1 ), "Component order is wrong."
        self.m_p3 = p3
        self.m_p2 = p2
        self.m_p1 = p1

    def computePrincipalComponents( self: Self, stressVector: npt.NDArray[ np.float64 ] ) -> None:
        """Calculate principal components.

        Args:
            stressVector (npt.NDArray[np.float64]): 6 components stress vector
                Stress vector must follow GEOS convention (XX, YY, ZZ, YZ, XZ, XY)
        """
        # get stress principal components
        self.m_p3, self.m_p2, self.m_p1 = ( computeStressPrincipalComponentsFromStressVector( stressVector ) )
