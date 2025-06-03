# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from trame.widgets import matplotlib
from trame.widgets import vuetify3 as vuetify

from geos_trame.app.deck.tree import DeckTree


class DeckPlotting( vuetify.VCard ):

    def __init__( self, source: DeckTree, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__( **kwargs )

        self._source = source
        if source.input_file is None:
            return

        self._filepath = ( source.input_file.path, )

        self.ctrl.permeability = self._permeability
        self.ctrl.figure_size = self._figure_size

        with self:
            vuetify.VCardTitle( "2D View" )
            html_viewX = matplotlib.Figure( figure=self.ctrl.permeability( **self.ctrl.figure_size() ),
                                            # style="position: absolute;left: 20%;top: 30%;",
                                           )
            self.ctrl.update_figure = html_viewX.update

    @property
    def source( self ) -> DeckTree:
        """Getter for source."""
        return self._source

    def _update_view( self ) -> None:
        self.ctrl.view_update( figure=self.ctrl.permeability( **self.ctrl.figure_size() ) )

    def _figure_size( self ) -> dict:

        if self.state.figure_size is None:
            return {}

        dpi = self.state.figure_size.get( "dpi" )
        rect = self.state.figure_size.get( "size" )
        w_inch = rect.get( "width" ) / dpi / 2
        h_inch = rect.get( "height" ) / dpi / 2

        return {
            "figsize": ( w_inch, h_inch ),
            "dpi": dpi,
        }

    @staticmethod
    def _inverse_gaz( x: np.ndarray ) -> np.ndarray:
        return 1 - x

    def _permeability( self, **kwargs: Any ) -> Figure:
        # read data
        assert self.source.input_file is not None
        for f in self.source.plots():
            for t in f.table_function:
                if t.name == "waterRelativePermeabilityTable":
                    fileX = t.coordinate_files.strip( "{(.+)}" ).strip()
                    assert fileX is not None and t.voxel_file is not None
                    self.water_x = np.loadtxt( self.source.input_file.path + "/" + fileX )
                    self.water_y = np.loadtxt( self.source.input_file.path + "/" + t.voxel_file )

                if t.name == "gasRelativePermeabilityTable":
                    fileX = t.coordinate_files.strip( "{(.+)}" ).strip()
                    assert fileX is not None and t.voxel_file is not None

                    gaz_x = np.loadtxt( self.source.input_file.path + "/" + fileX )
                    self.gaz_x = self._inverse_gaz( gaz_x )
                    self.gaz_y = np.loadtxt( self.source.input_file.path + "/" + t.voxel_file )

        # make drawing
        plt.close( "all" )
        fig, ax = plt.subplots( **kwargs )

        if ( self.water_x is not None and self.water_y is not None and self.gaz_x is not None
             and self.gaz_y is not None ):
            np.random.seed( 0 )
            ax.plot( self.water_x, self.water_y, label="water" )
            ax.plot( self.gaz_x, self.gaz_y, label="gaz" )

            ax.set_xlabel( "Water saturation" )
            ax.set_ylabel( "Relative permeability" )
            ax.set_title( "Matplotlib Plot Rendered in D3!", size=14 )
            ax.grid( color="lightgray", alpha=0.7 )
            plt.xlim( [ 0, 1 ] )
            plt.ylim( [ 0, 1 ] )
            plt.legend()

        return fig
