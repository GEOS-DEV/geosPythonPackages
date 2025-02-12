import os
import sys
import glob
import numpy as np
import segyio

from geos.pygeos_tools.utilities.acquisition import Acquisition
from geos.pygeos_tools.utilities.acquisition.Shot import Source, SourceSet, Receiver, ReceiverSet, Shot


class SEGYAcquisition( Acquisition ):
    """
    Acquisition defined from the reading of segy files containing the positions of the sources and receivers
    """

    def __init__( self, xml, dt=None, **kwargs ):
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

    def acquisition( self, segdir, **kwargs ):
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

        while notEmpty != True and i <= len( ext ):
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

        ishot = 1
        shots = []
        for segfile in sorted( segfiles ):
            receiverList = []

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

        self.shots = shots
