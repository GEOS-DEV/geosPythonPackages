# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# type: ignore
# ruff: noqa
from logging import Logger, getLogger, INFO
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

logger: Logger = getLogger( "Python View Configurator" )
logger.setLevel( INFO )
vtkHandler: VTKHandler = VTKHandler()
logger.addHandler( vtkHandler )

try:
    import matplotlib.pyplot as plt
    from paraview import python_view

    import geos.pv.utils.paraviewTreatments as pvt
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
    obj_figure = Figure2DGenerator( dataframe, userChoices, logger )  # noqa: F821
    fig = obj_figure.getFigure()

    def setup_data( view ) -> None:  # noqa
        pass

    def render( view, width: int, height: int ):  # noqa
        fig.set_size_inches( float( width ) / 100.0, float( height ) / 100.0 )
        imageToReturn = python_view.figure_to_image( fig )
        return imageToReturn

except Exception as e:
     logger.critical( e, exc_info=True )
