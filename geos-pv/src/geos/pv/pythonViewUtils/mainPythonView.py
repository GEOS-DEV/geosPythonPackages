# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# type: ignore
# ruff: noqa
try:
    import matplotlib.pyplot as plt
    from paraview import python_view

    import geos_posp.visu.PVUtils.paraviewTreatments as pvt
    from geos.pv.pythonViewUtils.Figure2DGenerator import (
        Figure2DGenerator, )

    plt.close()
    if len( sourceNames ) == 0:  # noqa: F821
        raise ValueError( "No source name was found. Please check at least" + " one source in <<Input Sources>>" )

    dataframes = pvt.getDataframesFromMultipleVTKSources(
        sourceNames,
        variableName  # noqa: F821
    )
    dataframe = pvt.mergeDataframes( dataframes, variableName )  # noqa: F821
    obj_figure = Figure2DGenerator( dataframe, userChoices )  # noqa: F821
    fig = obj_figure.getFigure()

    def setup_data( view ) -> None:  # noqa
        pass

    def render( view, width: int, height: int ):  # noqa
        fig.set_size_inches( float( width ) / 100.0, float( height ) / 100.0 )
        imageToReturn = python_view.figure_to_image( fig )
        return imageToReturn

except Exception as e:
    from geos.utils.Logger import getLogger

    logger = getLogger( "Python View Configurator" )
    logger.critical( e, exc_info=True )
