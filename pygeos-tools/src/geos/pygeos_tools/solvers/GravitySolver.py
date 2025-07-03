# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------

import numpy as np
import numpy.typing as npt
from typing import Dict, List
from typing_extensions import Self
from geos.pygeos_tools.solvers.Solver import Solver
from geos.pygeos_tools.wrapper import get_matching_wrapper_path, set_wrapper_to_value, allgather_wrapper
from pygeosx import run, COMPLETED
import copy

__doc__ = """
GravitySolver class inherits from Solver class.

This adds accessor methods for gravity modeling and adjoint.
"""


class GravitySolver( Solver ):
    """
    Gravity solver object containing methods to run gravity simulations in GEOS

    Attributes
    -----------
        The ones inherited from Solver class
    """

    def __init__( self: Self, solverType: str = "GravityFE", **kwargs ):
        """
        Parameters
        -----------
            solverType : str
                The solver used in the XML file
        """
        super().__init__( solverType, **kwargs )

    def getGzAtStations( self: Self ) -> npt.NDArray:
        """
        Get gz values at station coordinates

        Returns
        ------
            numpy Array : Array containing gz values at all stations coordinates
        """
        return self.getGeosWrapperByName( "gzAtStations", [ "Solvers" ] )

    def getDensityModel( self: Self, filterGhost: bool = False, **kwargs ) -> npt.NDArray:
        """
        Get the density values
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            densityName : str
                Name of density array in GEOS
            filterGhost : bool
                Filter the ghost ranks

        Returns
        -------
            Numpy Array : Array containing the density values
        """
        density = self.getSolverFieldWithPrefix( "mediumDensity", **kwargs )

        if density is not None:
            if filterGhost:
                density_filtered = self.filterGhostRankFor1RegionWith1CellBlock( density, **kwargs )
                if density_filtered is not None:
                    return density_filtered
                else:
                    print( "getDensityModel->filterGhostRank: No ghostRank was found.", flush=True )
            else:
                return density
        else:
            print( "getDensityModel: No velocity was found.", flush=True )
            return None

    def updateDensityModel( self: Self, density: npt.NDArray ) -> None:
        """
        Update density values in GEOS

        Parameters
        -----------
            density : array
                New values for the density
        """
        self.setGeosWrapperValueByName( "mediumDensity", value=density, filters=[ self.discretization ] )

    def setMode( self: Self, mode: str ) -> None:
        mode_key = get_matching_wrapper_path( self.geosx, [ 'mode' ] )
        self.geosx.get_wrapper( mode_key ).set_value( mode )

    def modeling( self: Self, model: npt.NDArray, scale_data: float = 1.0 ) -> npt.NDArray:

        # Make sure we are in modeling mode.
        self.setMode( "modeling" )
        self.applyInitialConditions()

        # Send model.
        self.updateDensityModel( model )

        # Run.
        while run() != COMPLETED:
            pass

        # Get vertical component gz at all stations.
        gz = copy.deepcopy( self.getGzAtStations() ) * scale_data

        return gz

    def adjoint( self: Self, nm: int, residue: npt.NDArray ) -> npt.NDArray:

        # Make sure we are in adjoint mode.
        self.setMode( "adjoint" )
        self.applyInitialConditions()

        # Send the residues to Geos.
        self.setGeosWrapperValueByName( "residue", value=residue )

        # Run
        while run() != COMPLETED:
            pass

        # Retrieve adjoint:
        #   * If any, gather all subdomains.
        #   * Make sure to remove ghosts.
        adjoint = np.zeros( nm )

        try:
            localToGlobal_key = get_matching_wrapper_path(
                self.geosx, [ self.discretization, 'elementSubRegions', 'localToGlobalMap' ] )
            ghost_key = get_matching_wrapper_path( self.geosx,
                                                   [ self.discretization, 'elementSubRegions', 'ghostRank' ] )
            adjoint_key = get_matching_wrapper_path( self.geosx,
                                                     [ self.discretization, 'elementSubRegions', 'adjoint' ] )
        except Exception as e:
            raise RuntimeError( f"Failed to resolve wrapper paths: {e}" )

        adjoint_field = copy.deepcopy( allgather_wrapper( self.geosx, adjoint_key, ghost_key=ghost_key ) )

        localToGlobal_noGhost = allgather_wrapper( self.geosx, localToGlobal_key, ghost_key=ghost_key ).astype( int )
        adjoint[ localToGlobal_noGhost ] = adjoint_field

        #print(f'size adjoint {adjoint.shape}', flush=True)
        #localToGlobal_noGhost = self.getLocalToGlobalMapFor1RegionWith1CellBlock(filterGhost=True)
        #print(f'size localToGlobal_noGhost {localToGlobal_noGhost.shape} {np.min(localToGlobal_noGhost)} {np.max(localToGlobal_noGhost)}')

        #        adjoint_field = self.getAdjoint()
        #adjoint_field = self.getSolverFieldWithPrefix("adjoint")
        #adjoint_key = get_matching_wrapper_path(self.geosx, [self.discretization, 'elementSubRegions', 'adjoint'])
        #adjoint_field = allgather_wrapper(self.geosx, adjoint_key)

        #print(f'size adjoint_field {adjoint_field.shape} {np.min(adjoint_field)} {np.max(adjoint_field)}', flush=True)

        #adjoint[localToGlobal_noGhost] = adjoint_field

        return adjoint
