# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
import numpy as np
import numpy.typing as npt
from typing_extensions import Self, Union

__doc__ = """
MohrCoulomb module define the Mohr-Coulomb failure envelop class.

Inputs are the rock cohesion (Pa) and the friction angle (°).
2 methods allow to compute either shear stress values according to normal stress
values, or the failure envelope including normal stress and corresponding shear
stress values.

To use the object:

.. code-block:: python

    from processing.MohrCoulomb import MohrCoulomb

    # create the object
    rockCohesion :float = 1.5e9 # Pa
    frictionAngle :float = 10 # degree
    mohrCoulomb = MohrCoulomb(rockCohesion, frictionAngle)

    # compute shear stress values according to normal stress values
    normalStress :npt.NDArray[np.float64] = np.linspace(1e9, 1.5e9)
    shearStress :npt.NDArray[np.float64] = mohrCoulomb.computeShearStress(normalStress)

    # compute the failure envelope including normal stress and corresponding shear
    # stress values
    # ones may also define minimum normal stress and the number of points
    normalStressMax :float = 1.5e9
    normalStress, shearStress = mohrCoulomb.computeFailureEnvelop(normalStressMax)
"""


class MohrCoulomb:

    def __init__( self: Self, rockCohesion: float, frictionAngle: float ) -> None:
        """Define Mohr-Coulomb failure envelop.

        Args:
            rockCohesion (float): rock cohesion (Pa).
            frictionAngle (float): friction angle (rad).
        """
        # rock cohesion
        self.m_rockCohesion = rockCohesion
        # failure envelop slope
        self.m_slope: float = np.tan( frictionAngle )
        # intersection of failure envelop and abscissa axis
        self.m_sigmaMin: float = -rockCohesion / self.m_slope

    def computeShearStress(
            self: Self,
            stressNormal0: Union[ float, npt.NDArray[ np.float64 ] ] ) -> Union[ float, npt.NDArray[ np.float64 ] ]:
        """Compute shear stress from normal stress.

        Args:
            stressNormal0 (float | npt.NDArray[np.float64]): normal stress
                value (Pa)

        Returns:
            float | npt.NDArray[np.float64]): shear stress value.
        """
        stressNormal: npt.NDArray[ np.float64 ] = np.array( stressNormal0 )
        tau: npt.NDArray[ np.float64 ] = self.m_slope * stressNormal + self.m_rockCohesion
        return tau

    def computeFailureEnvelop(
        self: Self,
        stressNormalMax: float,
        stressNormalMin: Union[ float, None ] = None,
        n: int = 100,
    ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ] ]:
        """Compute the envelope failure between min and max normal stress.

        Args:
            stressNormalMax (float): Maximum normal stress (Pa)
            stressNormalMin (float | None, optional): Minimum normal stress.
                If it is None, the envelop is computed from the its intersection
                with the abscissa axis.

                Defaults to None.
            n (int, optional): Number of points to define the envelop.
            Defaults to 100.

        Returns:
            tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]: failure
            envelop coordinates where first element is the abscissa and second
            element is the ordinates.
        """
        sigmaMin: float = ( self.m_sigmaMin if stressNormalMin is None else stressNormalMin )
        stressNormal: npt.NDArray[ np.float64 ] = np.linspace( sigmaMin, stressNormalMax, n ).astype( np.float64 )
        return ( stressNormal, np.array( self.computeShearStress( stressNormal ) ) )
