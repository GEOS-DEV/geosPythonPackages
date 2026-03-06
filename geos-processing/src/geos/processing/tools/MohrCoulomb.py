# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import logging
import numpy as np
from typing_extensions import Self, Union

from vtkmodules.vtkCommonDataModel import ( vtkDataSet )
from geos.mesh.utils.arrayHelpers import ( getArrayInObject, isAttributeInObject )
from geos.mesh.utils.arrayModifiers import ( createAttribute, updateAttribute )
from geos.utils.pieceEnum import ( Piece )

from geos.utils.Logger import ( Logger, getLogger )

loggerTitle = "MohrCoulomb Analysis"


class MohrCoulombAnalysis:
    """Mohr-Coulomb failure criterion analysis."""

    def __init__( self: Self,
                  surface: vtkDataSet,
                  cohesion: float,
                  frictionAngle: float,
                  logger: Union[ Logger, None ] = None ) -> None:
        """Mohr-Coulomb analyzer.

        Args:
            surface (vtkDataSet): Surface mesh to analyze with stress data
            cohesion (float): Cohesion in bar
            frictionAngle (float): Friction angle in degrees
            logger (Union[Logger, None], optional): A logger to manage the output messages.
                    Defaults to None, an internal logger is used.
        """
        self.surface = surface
        self.cohesion = cohesion
        self.frictionAngle = frictionAngle

        # Logger
        self.logger: Logger
        if logger is None:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( f"{logger.name}" )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def analyze( self: Self ) -> vtkDataSet:
        """Perform Mohr-Coulomb stability analysis.

        Returns:
            vtkDataSet: Mesh containing new/updated arrays.
        """
        mu = np.tan( np.radians( self.frictionAngle ) )

        # Extract stress components
        sigmaN = getArrayInObject( self.surface, "sigmaNEffective", Piece.CELLS )
        tau = getArrayInObject( self.surface, "tauEffective", Piece.CELLS )

        # Mohr-Coulomb failure envelope
        tauCritical = self.cohesion - sigmaN * mu

        # Coulomb Failure Stress
        cfs = tau - mu * sigmaN

        # Shear Capacity Utilization: SCU = τ / τ_crit
        scu = np.divide( tau, tauCritical, out=np.zeros_like( tau ), where=tauCritical != 0 )

        # if "SCUInitial" not in surface.cell_data:
        if not isAttributeInObject( self.surface, "SCUInitial", Piece.CELLS ):
            # First timestep: store as initial reference
            scuInitial = scu.copy()
            cfsInitial = cfs.copy()
            deltaSCU = np.zeros_like( scu )
            deltaCFS = np.zeros_like( cfs )

            createAttribute( self.surface, scuInitial, "SCUInitial" )
            createAttribute( self.surface, cfsInitial, "CFSInitial" )

            isInitial = True
        else:
            # Subsequent timesteps: calculate change from initial
            scuInitial = getArrayInObject( self.surface, "SCUInitial", Piece.CELLS )
            cfsInitial = getArrayInObject( self.surface, "CFSInitial", Piece.CELLS )
            deltaSCU = scu - scuInitial
            deltaCFS = cfs - cfsInitial
            isInitial = False

        # Stability classification
        stability = np.zeros_like( tau, dtype=int )
        stability[ scu >= 0.8 ] = 1  # Critical
        stability[ scu >= 1.0 ] = 2  # Unstable

        # Failure probability (sigmoid)
        k = 10.0
        failureProba = 1.0 / ( 1.0 + np.exp( -k * ( scu - 1.0 ) ) )

        # Safety margin
        safety = tauCritical - tau

        # Store results
        attributes = {
            "mohrCohesion": np.full( self.surface.GetNumberOfCells(), self.cohesion ),
            "mohrFrictionAngle": np.full( self.surface.GetNumberOfCells(), self.frictionAngle ),
            "mohrFrictionCoefficient": np.full( self.surface.GetNumberOfCells(), mu ),
            "mohrCriticalShearStress": tauCritical,
            "SCU": scu,
            "deltaSCU": deltaSCU,
            "CFS": cfs,
            "deltaCFS": deltaCFS,
            "safetyMargin": safety,
            "stabilityState": stability,
            "failureProbability": failureProba
        }

        for attributeName, value in attributes.items():
            updateAttribute( self.surface, value, attributeName, Piece.CELLS )

        nStable = np.sum( stability == 0 )
        nCritical = np.sum( stability == 1 )
        nUnstable = np.sum( stability == 2 )

        # Additional info on deltaSCU
        if not isInitial:
            meanDelta = np.mean( np.abs( deltaSCU ) )
            maxIncrease = np.max( deltaSCU )
            maxDecrease = np.min( deltaSCU )
            self.logger.info( f"  ✅ Mohr-Coulomb: {nUnstable} unstable, {nCritical} critical,\n"
                              f"{nStable} stable cells\n"
                              f"     ΔSCU: mean={meanDelta:.3f}, maxIncrease={maxIncrease:.3f}, \n"
                              f"maxDecrease={maxDecrease:.3f}" )
        else:
            self.logger.info( f"  ✅ Mohr-Coulomb (initial): {nUnstable} unstable, {nCritical} critical, \n"
                              f"{nStable} stable cells" )

        return self.surface
