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
import os
import sys
import glob
import numpy as np
import segyio
from typing import List
from typing_extensions import Self
from geos.pygeos_tools.acquisition_library.Acquisition import Acquisition
from geos.pygeos_tools.acquisition_library.Shot import Source, SourceSet, Receiver, ReceiverSet, Shot


class SEGYAcquisition( Acquisition ):
    """
    Acquisition defined from the reading of segy files containing the positions of the sources and receivers
    """

    def __init__( self: Self, xml, dt: float = None, **kwargs ):
        """
        Parameters
        -----------
            xml : XML
                XML object corresponding to the GEOS formatted .xml input file
            dt : float
                Timestep
            **kwargs : keyword arguments
                segdir : str
                    Folder containing the .sgy traces
        """
        super().__init__( xml, dt, **kwargs )
        self.type = "segyAcquisition"

    def acquisition_method( self: Self, segdir: str, **kwargs ):
        """
        Set the shots configurations

        Parameters
        -----------
            segdir : str
                Folder containing the .sgy traces
            kwargs :
                sbit : tuple of int
                    source bit position in header \
                    for x, y and z coordinates \
                    Default is (73, 77, 49)
                rbit : tuple of int
                    receiver bit position in header \
                    for x, y, z coordinates \
                    Default is (81, 85, 41)
        """
        sbit = kwargs.get( "sbit", ( 73, 77, 49 ) )
        rbit = kwargs.get( "rbit", ( 81, 85, 41 ) )

        assert all( isinstance( s, int ) for s in sbit )
        assert all( isinstance( r, int ) for r in rbit )

        notEmpty = False
        i = 0
        ext = ( "*.sgy", "*.segy" )
        filesToIgnore = kwargs.get( "ignore", () )

        while notEmpty is not True and i <= len( ext ):
            segfiles = glob.glob( os.path.join( segdir, ext[ i ] ) )

            if segfiles != []:
                notEmpty = True
            else:
                if i == 1:
                    print( f"No SEG found in {segdir}" )
                    sys.exit( 1 )
            i += 1

        if len( filesToIgnore ):
            for f in filesToIgnore:
                if os.path.join( segdir, f ) in segfiles:
                    segfiles.remove( os.path.join( segdir, f ) )

        ishot: int = 1
        shots: List[ Shot ] = list()
        for segfile in sorted( segfiles ):
            receiverList = list()

            with segyio.open( segfile, 'r', ignore_geometry=True ) as f:
                scalarXY = float( f.header[ 0 ][ 71 ] )
                scalarZ = float( f.header[ 0 ][ 69 ] )

                sourceX = f.header[ 0 ][ sbit[ 0 ] ] * abs( scalarXY )**np.sign( scalarXY )
                sourceY = f.header[ 0 ][ sbit[ 1 ] ] * abs( scalarXY )**np.sign( scalarXY )
                sourceZ = f.header[ 0 ][ sbit[ 2 ] ] * abs( scalarZ )**np.sign( scalarZ )

                source = Source( sourceX, sourceY, sourceZ )

                for n in range( len( f.trace ) ):
                    receiverX = f.header[ n ][ rbit[ 0 ] ] * abs( scalarXY )**np.sign( scalarXY )
                    receiverY = f.header[ n ][ rbit[ 1 ] ] * abs( scalarXY )**np.sign( scalarXY )
                    receiverZ = f.header[ n ][ rbit[ 2 ] ] * abs( scalarZ )**np.sign( scalarZ )

                    receiverList.append( Receiver( receiverX, receiverY, receiverZ ) )

                sourceSet = SourceSet()

                shotId = f"{ishot:05d}"

                sourceSet.append( source )
                receiverSet = ReceiverSet( receiverList )

                shots.append( Shot( sourceSet, receiverSet, shotId ) )

            ishot += 1

        self.shots: List[ Shot ] = shots
