import numpy as np
import pyvista as pv
# ============================================================================
# MOHR COULOMB
# ============================================================================
class MohrCoulomb:
    """Mohr-Coulomb failure criterion analysis."""

    @staticmethod
    def analyze( surface: pv.DataSet, cohesion: float, frictionAngleDeg: float, verbose: bool = True ) -> pv.DataSet:
        """Perform Mohr-Coulomb stability analysis.

        Parameters:
            surface: fault surface with stress data
            cohesion: cohesion in bar
            frictionAngleDeg: friction angle in degrees
            verbose: print statistics
        """
        mu = np.tan( np.radians( frictionAngleDeg ) )

        # Extract stress components
        sigmaN = surface.cell_data[ "sigmaNEffective" ]
        tau = surface.cell_data[ "tauEffective" ]
        surface.cell_data[ 'deltaSigmaNEffective' ]
        surface.cell_data[ 'deltaTauEffective' ]

        # Mohr-Coulomb failure envelope
        tauCritical = cohesion - sigmaN * mu

        # Coulomb Failure Stress
        CFS = tau - mu * sigmaN
        # deltaCFS = deltaTau - mu * deltaSigmaN

        # Shear Capacity Utilization: SCU = τ / τ_crit
        SCU = np.divide( tau, tauCritical, out=np.zeros_like( tau ), where=tauCritical != 0 )

        if "SCUInitial" not in surface.cell_data:
            # First timestep: store as initial reference
            SCUInitial = SCU.copy()
            CFSInitial = CFS.copy()
            deltaSCU = np.zeros_like( SCU )
            deltaCFS = np.zeros_like( CFS )

            surface.cell_data[ "SCUInitial" ] = SCUInitial
            surface.cell_data[ "CFSInitial" ] = CFSInitial

            isInitial = True
        else:
            # Subsequent timesteps: calculate change from initial
            SCUInitial = surface.cell_data[ "SCUInitial" ]
            CFSInitial = surface.cell_data[ 'CFSInitial' ]
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
        surface.cell_data.update( {
            "mohrCohesion": np.full( surface.n_cells, cohesion ),
            "mohrFrictionAngle": np.full( surface.n_cells, frictionAngleDeg ),
            "mohrFrictionCoefficient": np.full( surface.n_cells, mu ),
            "mohr_critical_shear_stress": tauCritical,
            "SCU": SCU,
            "deltaSCU": deltaSCU,
            "CFS": CFS,
            "deltaCFS": deltaCFS,
            "safetyMargin": safety,
            "stabilityState": stability,
            "failureProbability": failureProba
        } )

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

