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
import numpy.typing as npt
from typing import Dict, List
from typing_extensions import Self
from geos.pygeos_tools.solvers.Solver import Solver

__doc__ = """
AcousticSolver class inherits from Solver class.

This adds accessor methods for stresses, displacements and geomechanics parameters.
"""


class GeomechanicsSolver( Solver ):
    """
    Geomechanics solver object containing methods to run geomechanics simulations in GEOS

    Attributes
    -----------
        The ones inherited from Solver class
    """

    def __init__( self: Self, solverType: str = "solid", dt: float = None, maxTime: float = None, **kwargs ):
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
        self.dt = dt
        self.maxTime = maxTime

    def initialize( self: Self, rank: int = 0, xml=None ) -> None:
        super().initialize( rank, xml )

    """
    Accessors
    """

    def getConstitutiveModelData( self: Self, modelName: str ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local constitutive model data for each CellElementRegion and its cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each. The first 2 regions are using the constituve
            "model1", the last region uses "model2", the result is:
            { "region1/block1/model1": npt.NDArray, "region1/block1/model1": npt.NDArray,
              "region1/block2/model1": npt.NDArray, "region1/block1/model1": npt.NDArray,
              "region2/block3/model1": npt.NDArray, "region2/block1/model1": npt.NDArray,
              "region2/block4/model1": npt.NDArray, "region2/block1/model1": npt.NDArray,
              "region3/block5/model2": npt.NDArray, "region3/block1/model2": npt.NDArray,
              "region3/block6/model2": npt.NDArray, "region3/block1/model2": npt.NDArray }
        """
        model_paths = self.getAllGeosWrapperByName(
            modelName,
            filters=[ self.discretization, "elementRegionsGroup", "elementSubRegions", "ConstitutiveModels" ] )
        all_data: Dict[ str, any ] = dict()
        for path, model in model_paths.items():
            elts: List[ str ] = path.split( "/" )
            try:
                position_elementRegionsGroup: int = elts.index( "elementRegionsGroup" )
                position_elementSubRegions: int = elts.index( "elementSubRegions" )
                position_rockType: int = elts.index( "ConstitutiveModels" )
                regionName: str = elts[ position_elementRegionsGroup + 1 ]
                cellBlock: str = elts[ position_elementSubRegions + 1 ]
                rockType: str = elts[ position_rockType + 1 ]
                all_data[ regionName + "/" + cellBlock + "/" + rockType ] = model
            except Exception:
                all_data[ path ] = model
        return all_data

    def getBulkModulus( self: Self ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local bulk modulus for each CellElementRegion and its cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each. The first 2 regions are using "shale",
            the last region uses "sand", the result is:
            { "region1/block1/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region1/block2/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region2/block3/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region2/block4/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region3/block5/sand": npt.NDArray, "region3/block1/sand": npt.NDArray,
              "region3/block6/sand": npt.NDArray, "region3/block1/sand": npt.NDArray }
        """
        return self.getConstitutiveModelData( "bulkModulus" )

    def getDensities( self: Self ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local density for each CellElementRegion and its cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each. The first 2 regions are using "shale",
            the last region uses "sand", the result is:
            { "region1/block1/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region1/block2/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region2/block3/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region2/block4/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region3/block5/sand": npt.NDArray, "region3/block1/sand": npt.NDArray,
              "region3/block6/sand": npt.NDArray, "region3/block1/sand": npt.NDArray }
        """
        return self.getConstitutiveModelData( "density" )

    def getShearModulus( self: Self ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local shear modulus for each CellElementRegion and its cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each. The first 2 regions are using "shale",
            the last region uses "sand", the result is:
            { "region1/block1/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region1/block2/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region2/block3/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region2/block4/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region3/block5/sand": npt.NDArray, "region3/block1/sand": npt.NDArray,
              "region3/block6/sand": npt.NDArray, "region3/block1/sand": npt.NDArray }
        """
        return self.getConstitutiveModelData( "shearModulus" )

    def getStresses( self: Self ) -> Dict[ str, npt.NDArray ]:
        """
        Get the local stresses for each CellElementRegion and its cellBlocks of the mesh.

        Returns
        --------
            Dict[ str, npt.NDArray ]
            If your mesh contains 3 regions with 2 cellBlocks in each. The first 2 regions are using "shale",
            the last region uses "sand", the result is:
            { "region1/block1/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region1/block2/shale": npt.NDArray, "region1/block1/shale": npt.NDArray,
              "region2/block3/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region2/block4/shale": npt.NDArray, "region2/block1/shale": npt.NDArray,
              "region3/block5/sand": npt.NDArray, "region3/block1/sand": npt.NDArray,
              "region3/block6/sand": npt.NDArray, "region3/block1/sand": npt.NDArray }
        """
        return self.getConstitutiveModelData( "stress" )

    def getTotalDisplacement( self: Self ) -> npt.NDArray:
        """
        Get the local totalDipslacements from the nodes.

        Returns
        --------
            npt.NDArray of totalDipslacements, shape = ( number of nodes, 3 )

        """
        return self.getGeosWrapperByName( "totalDisplacement", filters=[ self.discretization ] )
