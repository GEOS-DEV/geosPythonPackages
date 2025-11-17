# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# type: ignore
# ruff: noqa
try:
    import matplotlib.pyplot as plt
    from paraview import python_view

    import geos.pv.utils.mohrCircles.functionsMohrCircle as mcf
    import geos.pv.utils.mohrCircles.plotMohrCircles as pmc

    plt.close()

    # create MohrCircles
    mohrCircles = mcf.createMohrCirclesFromPrincipalComponents( mohrCircleParams  # noqa:F821
                                                               )

    # create Mohr-Coulomb failure envelope
    mohrCoulomb = mcf.createMohrCoulombEnvelope(
        rockCohesion,
        frictionAngle  # noqa:F821
    )

    # plot MohrCircles
    fig = pmc.createMohrCirclesFigure(
        mohrCircles,
        mohrCoulomb,
        userChoices  # noqa:F821
    )

    def setup_data( view ) -> None:  # noqa
        """Setup data."""
        pass

    def render( view, width: int, height: int ):  # noqa
        """Render method."""
        fig.set_size_inches( float( width ) / 100.0, float( height ) / 100.0 )
        return python_view.figure_to_image( fig )

except Exception as e:
    print( e )
