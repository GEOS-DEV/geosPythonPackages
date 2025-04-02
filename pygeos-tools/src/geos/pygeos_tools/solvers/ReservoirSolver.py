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
import numpy.typing as npt
from typing import Dict, List
from typing_extensions import Self
from geos.pygeos_tools.solvers.Solver import Solver


__doc__ = """
ReservoirSolver class inherits from Solver class.

This adds accessor methods for pressure, phase volume fractions and porosities.
"""


class ReservoirSolver( Solver ):
    """
    Reservoir solver object containing methods to run reservoir simulations in GEOS

    Attributes
    -----------
        The ones inherited from Solver class
    """

    def __init__( self: Self, solverType: str, initialDt: float = None, maxTime: float = None, **kwargs ):
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

    def getDeltaPressures( self: Self ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local delta pressure for each CellElementRegion and each cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each, the result is:
            { "region1/block1": npt.NDArray, "region1/block2": npt.NDArray,
              "region2/block3": npt.NDArray, "region2/block4": npt.NDArray,
              "region3/block5": npt.NDArray, "region3/block6": npt.NDArray }
        """
        deltaPres_with_paths = self.getAllGeosWrapperByName( "deltaPressure", filters=[ self.discretization ] )
        all_deltaPres: Dict[ str, npt.NDArray ] = dict()
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

    def getPhaseVolumeFractions( self: Self ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local phaseVolumeFraction for each CellElementRegion and each cellBlocks of the mesh and each phase.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each, and two phases 'oil' and 'gas' give the result:
            { "region1/block1/oil": npt.NDArray, "region1/block1/gas": npt.NDArray,
              "region1/block2/oil": npt.NDArray, "region1/block1/gas": npt.NDArray,
              "region2/block3/oil": npt.NDArray, "region2/block1/gas": npt.NDArray,
              "region2/block4/oil": npt.NDArray, "region2/block1/gas": npt.NDArray,
              "region3/block5/oil": npt.NDArray, "region3/block1/gas": npt.NDArray,
              "region3/block6/oil": npt.NDArray, "region3/block1/gas": npt.NDArray }
        """
        phaseNames: List[ str ] = self.xml.getConstitutivePhases()
        if phaseNames is not None:
            all_pvf_paths = self.getAllGeosWrapperByName( "phaseVolumeFraction", filters=[ self.discretization ] )
            all_pvf: Dict[ str, npt.NDArray ] = dict()
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

    def getPorosities( self: Self ):
        """
        Get the local porosity for each CellElementRegion and its cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each. The first 2 regions are using "burdenPorosity",
            the last region uses "sandPorosity", the result is:
            { "region1/block1/burdenPorosity": npt.NDArray, "region1/block1/burdenPorosity": npt.NDArray,
              "region1/block2/burdenPorosity": npt.NDArray, "region1/block1/burdenPorosity": npt.NDArray,
              "region2/block3/burdenPorosity": npt.NDArray, "region2/block1/burdenPorosity": npt.NDArray,
              "region2/block4/burdenPorosity": npt.NDArray, "region2/block1/burdenPorosity": npt.NDArray,
              "region3/block5/sandPorosity": npt.NDArray, "region3/block1/sandPorosity": npt.NDArray,
              "region3/block6/sandPorosity": npt.NDArray, "region3/block1/sandPorosity": npt.NDArray }
        """
        porosityNames: List[ str ] = self.xml.getPorosityNames()
        if porosityNames is not None:
            all_poro: Dict[ str, npt.NDArray ] = dict()
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

    def getPressures( self: Self ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local pressure for each CellElementRegion and each cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each, the result is:
            { "region1/block1": npt.NDArray, "region1/block2": npt.NDArray,
              "region2/block3": npt.NDArray, "region2/block4": npt.NDArray,
              "region3/block5": npt.NDArray, "region3/block6": npt.NDArray }
        """
        pressures_with_paths = self.getAllGeosWrapperByName( "pressure", filters=[ self.discretization ] )
        all_pressures: Dict[ str, npt.NDArray ] = dict()
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
