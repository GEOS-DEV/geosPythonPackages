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
from typing import Tuple, Union
from typing_extensions import Self
from geos.pygeos_tools.solvers.WaveSolver import WaveSolver

__doc__ = """
AcousticSolver class inherits from WaveSolver class.

This adds method to read / set displacements at receiver.
"""


class ElasticSolver( WaveSolver ):
    """
    ElasticSolver Object containing all methods to run ElasticSEM simulation with GEOSX

    Attributes
    -----------
        The ones inherited from WaveSolver class
    """

    def __init__( self: Self,
                  solverType: str = "ElasticSEM",
                  dt: float = None,
                  minTime: float = 0.0,
                  maxTime: float = None,
                  dtSeismo: float = None,
                  dtWaveField: float = None,
                  sourceType: str = None,
                  sourceFreq: float = None,
                  **kwargs ):
        """
        Parameters
        ----------
            solverType: str
                The solverType targeted in GEOS XML deck. Defaults to "ElasticSEM"
            dt : float
                Time step for simulation
            minTime : float
                Starting time of simulation
                Default is 0
            maxTime : float
                End Time of simulation
            dtSeismo : float
                Time step to save pressure for seismic trace
            dtWaveField : float
                Time step to save fields
            sourceType : str
                Type of source
                Default is None
            sourceFreq : float
                Frequency of the source
                Default is None
            kwargs : keyword args
                geosx_argv : list
                    GEOSX arguments or command line as a splitted line
        """
        super().__init__( solverType=solverType,
                          dt=dt,
                          minTime=minTime,
                          maxTime=maxTime,
                          dtSeismo=dtSeismo,
                          dtWaveField=dtWaveField,
                          sourceType=sourceType,
                          sourceFreq=sourceFreq,
                          **kwargs )

    def __repr__( self: Self ):
        string_list = []
        string_list.append( "Solver type : " + type( self ).__name__ + "\n" )
        string_list.append( "dt : " + str( self.dt ) + "\n" )
        string_list.append( "maxTime : " + str( self.maxTime ) + "\n" )
        string_list.append( "dtSeismo : " + str( self.dtSeismo ) + "\n" )
        string_list.append( "Outputs : " + str( self.hdf5Targets ) + "\n" + str( self.vtkTargets ) + "\n" )
        rep = ""
        for string in string_list:
            rep += string

        return rep

    def initialize( self: Self, rank: int = 0, xml=None ) -> None:
        super().initialize( rank, xml )
        try:
            useDAS = self.xml.getAttribute( parentElement=self.type, attributeTag="useDAS" )

        except AttributeError:
            useDAS = None

        if useDAS == "none":
            try:
                linearGEO = bool( self.xml.getAttribute( self.type, "linearDASGeometry" ) )
            except AttributeError:
                linearGEO = False

            if linearGEO is True:
                self.useDAS = True

    """
    Accessors
    """

    def getAllDisplacementAtReceivers( self: Self ) -> Tuple[ npt.NDArray, npt.NDArray, npt.NDArray ]:
        """
        Get the displacement for the x, y and z directions at all time step and all receivers coordinates

        Returns
        --------
            displacementX : numpy array
                Component X of the displacement
            displacementY : numpy array
                Component Y of the displacement
            displacementZ : numpy array
                Component Z of the displacement
        """
        displacementX: npt.NDArray = self.getDisplacementAtReceivers( "X" )
        displacementY: npt.NDArray = self.getDisplacementAtReceivers( "Y" )
        displacementZ: npt.NDArray = self.getDisplacementAtReceivers( "Z" )

        return displacementX, displacementY, displacementZ

    def getDASSignalAtReceivers( self: Self ) -> npt.NDArray:
        """
        Get the DAS signal values at receivers coordinates

        Returns
        --------
            dassignal : numpy array
                Array containing the DAS signal values at all time step at all receivers coordinates
        """
        if self.type != "ElasticSEM":
            raise TypeError( f"DAS signal not implemented for solver of type {self.type}." )
        else:
            dassignal: npt.NDArray = self.getGeosWrapperByName( "dasSignalNp1AtReceivers" )

        return dassignal

    def getDisplacementAtReceivers( self: Self, component: str = "X" ) -> npt.NDArray:
        """
        Get the displacement values at receivers coordinates for a given direction

        Returns
        --------
            displacement : numpy array
                Array containing the displacements values at all time step at all receivers coordinates
        """
        assert component.upper() in ( "X", "Y", "Z" )
        if self.type == "ElasticFirstOrderSEM":
            displacement: npt.NDArray = self.getGeosWrapperByName( f"displacement{component.lower()}Np1AtReceivers" )
        elif self.type == "ElasticSEM":
            displacement = self.getGeosWrapperByName( f"displacement{component.upper()}Np1AtReceivers" )

        return displacement

    def getWaveField( self: Self ) -> Union[ npt.NDArray, Tuple[ npt.NDArray, npt.NDArray, npt.NDArray ] ]:
        if self.useDAS:
            return self.getDASSignalAtReceivers()
        else:
            return self.getAllDisplacementAtReceivers()

    # TODO
    # def getFullWaveFieldAtReceivers( self: Self, comm ):
    #     print( "This method is not implemented yet" )
    """
    Update methods
    """

    def updateDensityModel( self: Self, density: npt.NDArray ) -> None:
        """
        Update density values in GEOS

        Parameters
        -----------
            density : array
                New values for the density
        """
        self.setGeosWrapperValueByName( "elasticDensity", value=density, filters=[ self.discretization ] )

    def updateVelocityModel( self: Self, vel: npt.NDArray, component: str ) -> None:
        """
        Update velocity value in GEOS

        Parameters
        ----------
            vel : float/array
                Value(s) for velocity field
            component : str
                Vs or Vp
        """
        assert component.lower() in ( "vs", "vp" ), "Only Vs or Vp component accepted"
        self.setGeosWrapperValueByName( "elasticVelocity" + component.title(), vel, filters=[ self.discretization ] )

    """
    Methods for reset of values
    """

    def resetWaveField( self: Self, **kwargs ) -> None:
        """Reinitialize all displacement values on the Wavefield to zero in GEOSX"""

        self.setGeosWrapperValueByTargetKey( "Solvers/" + self.name + "/indexSeismoTrace", value=0 )
        nodeManagerPath = f"domain/MeshBodies/{self.meshName}/meshLevels/{self.discretization}/nodeManager/"

        if self.type == "ElasticSEM":
            for component in ( "x", "y", "z" ):
                for ts in ( "nm1", "n", "np1" ):
                    self.setGeosWrapperValueByTargetKey( nodeManagerPath + f"displacement{component}_{ts}", value=0.0 )

        elif self.type == "ElasticFirstOrderSEM":
            component = ( "x", "y", "z" )
            for c in component:
                self.setGeosWrapperValueByTargetKey( nodeManagerPath + f"displacement{c}_np1", value=0.0 )

            prefix = self._getPrefixPathFor1RegionWith1CellBlock( **kwargs )
            for i, c in enumerate( component ):
                for j in range( i, len( component ) ):
                    cc = c + component[ j ]
                self.setGeosWrapperValueByTargetKey( prefix + f"stresstensor{cc}", value=0.0 )

    def resetDisplacementAtReceivers( self: Self ) -> None:
        """Reinitialize displacement values at receivers to 0
        """
        for component in ( "X", "Y", "Z" ):
            self.setGeosWrapperValueByTargetKey( f"displacement{component}Np1AtReceivers", value=0.0 )
