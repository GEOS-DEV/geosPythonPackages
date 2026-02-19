import numpy as np
from vtkmodules.vtkCommonDataModel import (
    vtkDataSet )
from vtkmodules.util.numpy_support import numpy_to_vtk
from geos.mesh.utils.arrayHelpers import ( getArrayInObject, isAttributeInObject )
from geos.mesh.utils.arrayModifiers import ( createAttribute, updateAttribute )
from geos.utils.pieceEnum import Piece
# ============================================================================
# MOHR COULOMB
# ============================================================================
class MohrCoulomb:
    """Mohr-Coulomb failure criterion analysis."""

    @staticmethod
    def analyze( surface: vtkDataSet, cohesion: float, frictionAngleDeg: float, verbose: bool = True ) -> vtkDataSet:
        """Perform Mohr-Coulomb stability analysis.

        Parameters:
            surface: fault surface with stress data
            cohesion: cohesion in bar
            frictionAngleDeg: friction angle in degrees
            verbose: print statistics
        """
        mu = np.tan( np.radians( frictionAngleDeg ) )

        # Extract stress components
        sigmaN = getArrayInObject( surface, "sigmaNEffective", Piece.CELLS )
        tau = getArrayInObject( surface, "tauEffective", Piece.CELLS )
        deltaSigmaN = getArrayInObject( surface, 'deltaSigmaNEffective', Piece.CELLS )
        deltaTau = getArrayInObject( surface, 'deltaTauEffective', Piece.CELLS )

        # Mohr-Coulomb failure envelope
        tauCritical = cohesion - sigmaN * mu

        # Coulomb Failure Stress
        CFS = tau - mu * sigmaN
        # deltaCFS = deltaTau - mu * deltaSigmaN

        # Shear Capacity Utilization: SCU = τ / τ_crit
        SCU = np.divide( tau, tauCritical, out=np.zeros_like( tau ), where=tauCritical != 0 )

        # if "SCUInitial" not in surface.cell_data:
        if not isAttributeInObject( surface, "SCUInitial", Piece.CELLS ):
            # First timestep: store as initial reference
            SCUInitial = SCU.copy()
            CFSInitial = CFS.copy()
            deltaSCU = np.zeros_like( SCU )
            deltaCFS = np.zeros_like( CFS )

            createAttribute( surface, SCUInitial, "SCUInitial" )
            createAttribute( surface, CFSInitial, "CFSInitial" )

            isInitial = True
        else:
            # Subsequent timesteps: calculate change from initial
            SCUInitial = getArrayInObject( surface, "SCUInitial", Piece.CELLS )
            CFSInitial = getArrayInObject( surface, "CFSInitial", Piece.CELLS )
            deltaSCU = SCU - SCUInitial
            deltaCFS = CFS - CFSInitial
            isInitial = False

        # Stability classification
        stability = np.zeros_like( tau, dtype=int )
        stability[ SCU >= 0.8 ] = 1  # Critical
        stability[ SCU >= 1.0 ] = 2  # Unstable

        # Failure probability (sigmoid)
        k = 10.0
        failureProba = 1.0 / ( 1.0 + np.exp( -k * ( SCU - 1.0 ) ) )

        # Safety margin
        safety = tauCritical - tau

        # Store results
        attributes = { "mohrCohesion": np.full( surface.GetNumberOfCells(), cohesion ),
                       "mohrFrictionAngle": np.full( surface.GetNumberOfCells(), frictionAngleDeg ),
                       "mohrFrictionCoefficient": np.full( surface.GetNumberOfCells(), mu ),
                       "mohr_critical_shear_stress": tauCritical,
                       "SCU": SCU,
                       "deltaSCU": deltaSCU,
                       "CFS": CFS,
                       "deltaCFS": deltaCFS,
                       "safetyMargin": safety,
                       "stabilityState": stability,
                       "failureProbability": failureProba }

        cdata = surface.GetCellData()
        for attributeName, value in attributes.items():
            updateAttribute( surface, value, attributeName, Piece.CELLS )


        if verbose:
            nStable = np.sum( stability == 0 )
            nCritical = np.sum( stability == 1 )
            nUnstable = np.sum( stability == 2 )

            # Additional info on deltaSCU
            if not isInitial:
                meanDelta = np.mean( np.abs( deltaSCU ) )
                maxIncrease = np.max( deltaSCU )
                maxDecrease = np.min( deltaSCU )
                print( f"  ✅ Mohr-Coulomb: {nUnstable} unstable, {nCritical} critical, "
                       f"{nStable} stable cells" )
                print( f"     ΔSCU: mean={meanDelta:.3f}, maxIncrease={maxIncrease:.3f}, "
                       f"maxDecrease={maxDecrease:.3f}" )
            else:
                print( f"  ✅ Mohr-Coulomb (initial): {nUnstable} unstable, {nCritical} critical, "
                       f"{nStable} stable cells" )

        return surface

