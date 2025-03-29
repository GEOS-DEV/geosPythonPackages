# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# Copyright (c) 2019-     INRIA project-team Makutu
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------

import numpy as np
from typing import Dict, List
from geos.pygeos_tools.utilities.solvers.Solver import Solver


class ReservoirSolver( Solver ):
    """
    Reservoir solver object containing methods to run reservoir simulations in GEOS

    Attributes
    -----------
        The ones inherited from Solver class
    """

    def __init__( self, solverType: str, initialDt=None, maxTime=None, **kwargs ):
        """
        Parameters
        -----------
            solverType : str
                The solver used in the XML file
            initialDt : float
                Initial time step \
                Default is None
            maxTime : float
                End time of simulation \
                Default is None
        """
        super().__init__( solverType, **kwargs )

        self.initialDt: float = initialDt
        self.maxTime: float = maxTime
        self.isCoupled = kwargs.get( "coupled", False )

    def getDeltaPressures( self ) -> Dict[ str, any ]:
        """
        Get the local delta pressure for each CellElementRegion and each cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, np.array ]
            If your mesh contains 3 regions with 2 cellBlocks in each, the result is:
            { "region1/block1": np.array, "region1/block2": np.array,
              "region2/block3": np.array, "region2/block4": np.array,
              "region3/block5": np.array, "region3/block6": np.array }
        """
        deltaPres_with_paths = self.getAllGeosWrapperByName( "deltaPressure", filters=[ self.discretization ] )
        all_deltaPres: Dict[ str, any ] = dict()
        for path, deltaPres in deltaPres_with_paths.items():
            elts: List[ str ] = path.split( "/" )
            try:
                position_elementRegionsGroup: int = elts.index( "elementRegionsGroup" )
                position_elementSubRegions: int = elts.index( "elementSubRegions" )
                regionName: str = elts[ position_elementRegionsGroup + 1 ]
                cellBlock: str = elts[ position_elementSubRegions + 1 ]
                all_deltaPres[ regionName + "/" + cellBlock ] = deltaPres
            except Exception:
                all_deltaPres[ path ] = deltaPres

        return all_deltaPres

    def getPhaseVolumeFractions( self ) -> Dict[ str, any ]:
        """
        Get the local phaseVolumeFraction for each CellElementRegion and each cellBlocks of the mesh and each phase.

        Returns
        --------
            Dict[ str, np.array ]
            If your mesh contains 3 regions with 2 cellBlocks in each, and two phases 'oil' and 'gas' give the result:
            { "region1/block1/oil": np.array, "region1/block1/gas": np.array,
              "region1/block2/oil": np.array, "region1/block1/gas": np.array,
              "region2/block3/oil": np.array, "region2/block1/gas": np.array,
              "region2/block4/oil": np.array, "region2/block1/gas": np.array,
              "region3/block5/oil": np.array, "region3/block1/gas": np.array,
              "region3/block6/oil": np.array, "region3/block1/gas": np.array }
        """
        phaseNames: List[ str ] = self.xml.getConstitutivePhases()
        if phaseNames is not None:
            all_pvf_paths = self.getAllGeosWrapperByName( "phaseVolumeFraction", filters=[ self.discretization ] )
            all_pvf: Dict[ str, any ] = dict()
            for path, pvf in all_pvf_paths.items():
                elts: List[ str ] = path.split( "/" )
                try:
                    position_elementRegionsGroup: int = elts.index( "elementRegionsGroup" )
                    position_elementSubRegions: int = elts.index( "elementSubRegions" )
                    regionName: str = elts[ position_elementRegionsGroup + 1 ]
                    cellBlock: str = elts[ position_elementSubRegions + 1 ]
                    for i, phaseName in enumerate( phaseNames ):
                        all_pvf[ regionName + "/" + cellBlock + "/" + phaseName ] = np.ascontiguousarray( pvf[ :, i ] )
                except Exception:
                    for i, phaseName in enumerate( phaseNames ):
                        all_pvf[ path + "/" + phaseName ] = np.ascontiguousarray( pvf[ :, i ] )
            return all_pvf
        else:
            print( "getPhaseVolumeFractions: No phases defined in the XML so no phaseVolumeFraction available." )

    def getPorosities( self ):
        """
        Get the local porosity for each CellElementRegion and its cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, np.array ]
            If your mesh contains 3 regions with 2 cellBlocks in each. The first 2 regions are using "burdenPorosity",
            the last region uses "sandPorosity", the result is:
            { "region1/block1/burdenPorosity": np.array, "region1/block1/burdenPorosity": np.array,
              "region1/block2/burdenPorosity": np.array, "region1/block1/burdenPorosity": np.array,
              "region2/block3/burdenPorosity": np.array, "region2/block1/burdenPorosity": np.array,
              "region2/block4/burdenPorosity": np.array, "region2/block1/burdenPorosity": np.array,
              "region3/block5/sandPorosity": np.array, "region3/block1/sandPorosity": np.array,
              "region3/block6/sandPorosity": np.array, "region3/block1/sandPorosity": np.array }
        """
        porosityNames: List[ str ] = self.xml.getPorosityNames()
        if porosityNames is not None:
            all_poro: Dict[ str, any ] = dict()
            for porosityName in porosityNames:
                all_poro_paths = self.getAllGeosWrapperByName( porosityName,
                                                               filters=[ self.discretization, "referencePorosity" ] )
                for path, poro in all_poro_paths.items():
                    elts: List[ str ] = path.split( "/" )
                    try:
                        position_elementRegionsGroup: int = elts.index( "elementRegionsGroup" )
                        position_elementSubRegions: int = elts.index( "elementSubRegions" )
                        regionName: str = elts[ position_elementRegionsGroup + 1 ]
                        cellBlock: str = elts[ position_elementSubRegions + 1 ]
                        all_poro[ regionName + "/" + cellBlock + "/" + porosityName ] = poro
                    except Exception:
                        all_poro[ path + "/" + porosityName ] = poro
            return all_poro
        else:
            print( "getPorosities: No Porosity model defined in the XML." )

    def getPressures( self ) -> Dict[ str, any ]:
        """
        Get the local pressure for each CellElementRegion and each cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, np.array ]
            If your mesh contains 3 regions with 2 cellBlocks in each, the result is:
            { "region1/block1": np.array, "region1/block2": np.array,
              "region2/block3": np.array, "region2/block4": np.array,
              "region3/block5": np.array, "region3/block6": np.array }
        """
        pressures_with_paths = self.getAllGeosWrapperByName( "pressure", filters=[ self.discretization ] )
        all_pressures: Dict[ str, any ] = dict()
        for path, pressure in pressures_with_paths.items():
            elts: List[ str ] = path.split( "/" )
            try:
                position_elementRegionsGroup: int = elts.index( "elementRegionsGroup" )
                position_elementSubRegions: int = elts.index( "elementSubRegions" )
                regionName: str = elts[ position_elementRegionsGroup + 1 ]
                cellBlock: str = elts[ position_elementSubRegions + 1 ]
                all_pressures[ regionName + "/" + cellBlock ] = pressure
            except Exception:
                all_pressures[ path ] = pressure
        return all_pressures
