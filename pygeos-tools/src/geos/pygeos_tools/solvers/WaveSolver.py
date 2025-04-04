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
import pygeosx
from scipy.fftpack import fftfreq, ifft, fft
from typing import List, Union
from typing_extensions import Self
from geos.pygeos_tools.solvers.Solver import Solver

__doc__ = """
WaveSolver class which is the base class for every AcousticSolver and ElasticSolver classes, and inherits the Solver
capabilities.

This adds more methods to the Solver class to handle seismic sources and receivers.
"""


class WaveSolver( Solver ):
    """
    WaveSolver Object containing methods useful for simulation using wave solvers in GEOS

    Attributes
    -----------
        The ones herited from Solver class and:

        dtSeismo : float
            Time step to save pressure for seismic trace
        dtWaveField : float
            Time step to save fields
        minTime : float
            Min time to consider
        maxTime : float
            End time to consider
        minTimeSim : float
            Starting time of simulation
        maxTimeSim : float
            End Time of simulation
        sourceType : str
            Type of source
        sourceFreq : float
            Frequency of the source
    """

    def __init__( self: Self,
                  solverType: str,
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
                The solverType targeted in GEOS XML deck
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
        super().__init__( solverType, **kwargs )

        self.dt: float = dt
        self.dtSeismo: float = dtSeismo
        self.dtWaveField: float = dtWaveField
        self.minTime: float = minTime
        self.minTimeSim: float = minTime
        self.maxTime: float = maxTime
        self.maxTimeSim: float = maxTime

        self.sourceType: str = sourceType
        self.sourceFreq: float = sourceFreq

    def __repr__( self: Self ):
        string_list: List[ str ] = list()
        string_list.append( "Solver type : " + self.type + "\n" )
        string_list.append( "dt : " + str( self.dt ) + "\n" )
        string_list.append( "maxTime : " + str( self.maxTime ) + "\n" )
        string_list.append( "dtSeismo : " + str( self.dtSeismo ) + "\n" )
        string_list.append( "Outputs : " + str( self.hdf5Targets ) + "\n" + str( self.vtkTargets ) + "\n" )
        rep = ""
        for string in string_list:
            rep += string

        return rep

    def initialize( self: Self, rank: int = 0, xml=None ) -> None:
        """
        Initialization or reinitialization of GEOSX

        Parameters
        ----------
            rank : int
                Process rank
            xml : XML
                XML object containing parameters for GEOSX initialization.
                Only required if not set in the __init__ OR if different from it
        """
        super().initialize( rank, xml )
        self.updateSourceProperties()

    """
    Accessors
    """

    def getVelocityModel( self: Self, velocityName: str, filterGhost: bool = False, **kwargs ) -> npt.NDArray:
        """
        Get the velocity values
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            velocityName : str
                Name of velocity array in GEOS
            filterGhost : bool
                Filter the ghost ranks

        Returns
        -------
            Numpy Array : Array containing the velocity values
        """
        velocity = self.getSolverFieldWithPrefix( velocityName, **kwargs )

        if velocity is not None:
            if filterGhost:
                velocity_filtered = self.filterGhostRankFor1RegionWith1CellBlock( velocity, **kwargs )
                if velocity_filtered is not None:
                    return velocity_filtered
                else:
                    print( "getVelocityModelFor1RegionWith1CellBlock->filterGhostRank: No ghostRank was found." )
            else:
                return velocity
        else:
            print( "getVelocityModelFor1RegionWith1CellBlock: No velocity was found." )

    """
    Mutators
    """

    def setSourceAndReceivers( self: Self, sourcesCoords: List = [], receiversCoords: List = [] ) -> None:
        """
        Update sources and receivers positions in GEOS

        Parameters
        ----------
            sourcesCoords : list
                List of coordinates for the sources
            receiversCoords : list
                List of coordinates for the receivers
        """
        src_pos_geosx = self.solver.get_wrapper( "sourceCoordinates" ).value()
        src_pos_geosx.set_access_level( pygeosx.pylvarray.RESIZEABLE )

        rcv_pos_geosx = self.solver.get_wrapper( "receiverCoordinates" ).value()
        rcv_pos_geosx.set_access_level( pygeosx.pylvarray.RESIZEABLE )

        src_pos_geosx.resize_all( ( len( sourcesCoords ), 3 ) )
        if len( sourcesCoords ) == 0:
            src_pos_geosx.to_numpy()[ : ] = np.zeros( ( 0, 3 ) )
        else:
            src_pos_geosx.to_numpy()[ : ] = sourcesCoords[ : ]

        rcv_pos_geosx.resize_all( ( len( receiversCoords ), 3 ) )
        if len( receiversCoords ) == 0:
            rcv_pos_geosx.to_numpy()[ : ] = np.zeros( ( 0, 3 ) )
        else:
            rcv_pos_geosx.to_numpy()[ : ] = receiversCoords[ : ]

        self.solver.reinit()

    def setSourceFrequency( self: Self, freq: float ) -> None:
        """
        Overwrite GEOSX source frequency and set self.sourceFreq

        Parameters
        ----------
            freq : float
                Frequency of the source in Hz
        """
        self.setGeosWrapperValueByTargetKey( "/Solvers/" + self.name + "/timeSourceFrequency", freq )
        self.sourceFreq = freq

    def setSourceValue( self: Self, value: Union[ npt.NDArray, List ] ) -> None:
        """
        Set the value of the source in GEOS

        Parameters
        ----------
            value : array/list
                List/array containing the value of the source at each time step
        """
        src_value = self.solver.get_wrapper( "sourceValue" ).value()
        src_value.set_access_level( pygeosx.pylvarray.RESIZEABLE )

        src_value.resize_all( value.shape )
        src_value.to_numpy()[ : ] = value[ : ]

        self.maxTimeSim = ( value.shape[ 0 ] - 1 ) * self.dt
        self.setGeosWrapperValueByTargetKey( "Events/minTime", self.minTime )
        self.sourceValue = value[ : ]

    """
    Update method
    """

    def updateSourceProperties( self: Self ) -> None:
        """
        Updates the frequency and type of source to match the XML
        """
        if self.sourceFreq is None:
            solverdict = self.xml.solvers[ self.type ]
            for k, v in solverdict.items():
                if k == "timeSourceFrequency":
                    self.sourceFreq = v
                    break

        if self.sourceType is None:
            if hasattr( self.xml, "events" ):
                events = self.xml.events
            try:
                for event in events[ "PeriodicEvent" ]:
                    if isinstance( event, dict ):
                        if event[ "target" ] == "/Solvers/" + self.name:
                            self.sourceType = "ricker" + event[ 'rickerOrder' ]
                    else:
                        if event == "target" and events[ "PeriodicEvent" ][ "target" ] == "/Solvers/" + self.name:
                            self.sourceType = "ricker" + events[ "PeriodicEvent" ][ "rickerOrder" ]
            except KeyError:
                self.sourceType = "ricker2"

    """
    Utils
    """

    def evaluateSource( self: Self ) -> None:
        """
        Evaluate source and update on GEOS
        Only ricker order {0 - 4} accepted
        """
        sourceTypes = ( "ricker0", "ricker1", "ricker2", "ricker3", "ricker4" )
        assert self.sourceType in sourceTypes, f"Only {sourceTypes} are allowed"

        f0 = self.sourceFreq
        delay = 1.0 / f0
        alpha = -( f0 * np.pi )**2

        nsamples = int( round( ( self.maxTime - self.minTime ) / self.dt ) ) + 1
        sourceValue = np.zeros( ( nsamples, 1 ) )

        order = int( self.sourceType[ -1 ] )
        sgn = ( -1 )**( order + 1 )

        time = self.minTime
        for nt in range( nsamples ):

            if self.minTime <= -1.0 / f0:
                tmin = -2.9 / f0
                tmax = 2.9 / f0
                time_d = time

            else:
                time_d = time - delay
                tmin = 0.0
                tmax = 2.9 / f0

            if ( time > tmin and time < tmax ) or ( self.minTime < -1 / f0 and time == tmin ):
                gaussian = np.exp( alpha * time_d**2 )

                if order == 0:
                    sourceValue[ nt, 0 ] = sgn * gaussian

                elif order == 1:
                    sourceValue[ nt, 0 ] = sgn * ( 2 * alpha * time_d ) * gaussian

                elif order == 2:
                    sourceValue[ nt, 0 ] = sgn * ( 2 * alpha + 4 * alpha**2 * time_d**2 ) * gaussian

                elif order == 3:
                    sourceValue[ nt, 0 ] = sgn * ( 12 * alpha**2 * time_d + 8 * alpha**3 * time_d**3 ) * gaussian

                elif order == 4:
                    sourceValue[ nt, 0 ] = sgn * ( 12 * alpha**2 + 48 * alpha**3 * time_d**2 +
                                                   16 * alpha**4 * time_d**4 ) * gaussian

            time += self.dt

        self.setSourceFrequency( self.sourceFreq )
        self.setSourceValue( sourceValue )
        self.sourceValue = sourceValue

    def filterSource( self: Self, fmax: Union[ str, float ] ) -> None:
        """
        Filter the source value and give the value to GEOSX. Note that is can also modify the start and end time of
        simulation to avoid discontinuity.

        Parameters
        -----------
            fmax : float/string
                Max frequency of the source wanted. The source then have frequencies in the interval [0,fmax+1]
        """
        if str( fmax ) == "all":
            return

        minTime = self.minTime
        maxTime = self.maxTime
        dt = self.dt
        f0 = self.sourceFreq

        sourceValue = self.sourceValue

        pad = int( round( sourceValue.shape[ 0 ] / 2 ) )
        n = sourceValue.shape[ 0 ] + 2 * pad

        tf = fftfreq( n, dt )
        y_fft = np.zeros( ( n, sourceValue.shape[ 1 ] ), dtype="complex_" )
        y = np.zeros( y_fft.shape, dtype="complex_" )

        for i in range( y_fft.shape[ 1 ] ):
            y_fft[ pad:n - pad, i ] = sourceValue[ :, i ]
            y_fft[ :, i ] = fft( y_fft[ :, i ] )  # Perform fourier transform

        isup = np.where( tf >= fmax )[ 0 ]
        imax = np.where( tf[ isup ] >= fmax + 1 )[ 0 ][ 0 ]
        i1 = isup[ 0 ]
        i2 = isup[ imax ]

        iinf = np.where( tf <= -fmax )[ 0 ]
        imin = np.where( tf[ iinf ] <= -fmax - 1 )[ 0 ][ -1 ]

        i3 = iinf[ imin ]
        i4 = iinf[ -1 ]

        for i in range( y_fft.shape[ 1 ] ):
            y_fft[ i1:i2, i ] = np.cos( ( isup[ 0:imax ] - i1 ) / ( i2 - i1 ) * np.pi / 2 )**2 * y_fft[ i1:i2, i ]
            y_fft[ i3:i4, i ] = np.cos( ( iinf[ imin:-1 ] - i4 ) / ( i3 - i4 ) * np.pi / 2 )**2 * y_fft[ i3:i4, i ]
            y_fft[ i2:i3, i ] = 0

        for i in range( y.shape[ 1 ] ):
            y[ :, i ] = ifft( y_fft[ :, i ] )  # Perform inverse fourier transform

        it0 = int( round( abs( minTime / dt ) ) ) + pad
        d = int( round( 1 / f0 / dt ) )

        i1 = max( it0 - 4 * d, 0 )
        i2 = int( round( i1 + d / 4 ) )

        i4 = min( n, n - pad + 4 * d )
        i3 = int( round( i4 - d / 4 ) )

        for i in range( y.shape[ 1 ] ):
            y[ i1:i2, i ] = np.cos( ( np.arange( i1, i2 ) - i2 ) / ( i2 - i1 ) * np.pi / 2 )**2 * y[ i1:i2, i ]
            y[ i3:i4, i ] = np.cos( ( np.arange( i3, i4 ) - i3 ) / ( i4 - i3 ) * np.pi / 2 )**2 * y[ i3:i4, i ]
            y[ max( i1 - d, 0 ):i1, i ] = 0.0
            y[ i4:min( i4 + d, n ), i ] = 0.0

        t = np.arange( minTime - pad * dt, maxTime + pad * dt + dt / 2, dt )

        self.setSourceValue( np.real( y[ max( i1 - d, 0 ):min( i4 + d, n ), : ] ) )
        self.minTimeSim = t[ max( i1 - d, 0 ) ]
        self.maxTimeSim = t[ min( i4 + d, n - 1 ) ]
        self.setGeosWrapperValueByTargetKey( "Events/minTime", self.minTimeSim )
        self.sourceValue = np.real( y[ max( i1 - d, 0 ):min( i4 + d, n ), : ] )

    def outputWaveField( self: Self, time: float ) -> None:
        """
        Trigger the wavefield output

        Parameters
        ----------
            time : float
                Current time of simulation
        """
        self.collections[ 0 ].collect( time, self.dt )
        self.hdf5Outputs[ 0 ].output( time, self.dt )
