import os
import numpy as np
import segyio
import mpi4py
mpi4py.rc.initialize = False
from mpi4py import MPI


class SEGYTraceOutput:
    """
    Class containing methods for the output of seismic traces in SEGY format

    Attributes
    -----------
        format : str
            Output filename extension
        directory : str
            Output directory \
            Default is current dir
        rootname : str
            Output root filename
        data : array-like
            Seismic traces to export
        time : array-like
            Time corresponding to seismic traces \
            Default is None
    """

    def __init__( self, seismo, rootname="seismoTrace_shot", directory="./", **kwargs ):
        """
        Parameters
        -----------
            seismo : array-like
                Seismic traces to export
            rootname : str
                Output root filename
            directory : str
                Output directory \
                Default is current dir
        """
        self.format = ".sgy"
        self.directory = directory
        self.rootname = rootname

        self.filename = os.path.join( self.directory, self.rootname + self.format )

        self.data = seismo
        self.time = None

    def export( self, receiverCoords, sourceCoords, dt=None, comm=MPI.COMM_WORLD, **kwargs ):
        """
        Export the seismic traces to .sgy file

        Parameters
        -----------
            receiverCoords : list of list of float
                Coordinates of the receivers
            sourceCoords : list of list of floats
                Coordinates of the source(s)
            dt : float, optional
                Time step in seconds \
                If None (default), \
                  time step from last column of seismos
            comm : MPI communicator, optional
                MPI communicator
        """
        rank = comm.Get_rank()
        nsamples = self.data.shape[ 0 ]

        if self.data.shape[ 1 ] == len( receiverCoords ) + 1:
            self.data, self.time = self.data[ :, :-1 ], self.data[ :, -1 ]

        if dt is None and self.time is not None:
            dt = self.time[ 1 ] - self.time[ 0 ]

        scalco = float( kwargs.get( "scalco", -100 ) )  # TODO: increase for higher precision
        scalel = float( kwargs.get( "scalel", -100 ) )  # TODO: increase for higher precision

        # Segy header creation
        if rank == 0:
            os.makedirs( self.directory, exist_ok=True )

            spec = segyio.spec()
            spec.tracecount = len( receiverCoords )
            spec.samples = np.arange( nsamples )
            spec.sorting = 2
            spec.format = 1

            with segyio.create( self.filename, spec ) as f:
                for i, rcv in enumerate( receiverCoords ):
                    f.header[ i ] = {
                        segyio.su.scalco: int( scalco ),
                        segyio.su.scalel: int( scalel ),
                        segyio.su.sx: int( sourceCoords[ 0 ] / abs( scalco )**np.sign( scalco ) ),
                        segyio.su.sy: int( sourceCoords[ 1 ] / abs( scalco )**np.sign( scalco ) ),
                        segyio.su.sdepth: int( sourceCoords[ 2 ] / abs( scalel )**np.sign( scalel ) ),
                        segyio.su.gx: int( rcv[ 0 ] / abs( scalco )**np.sign( scalco ) ),
                        segyio.su.gy: int( rcv[ 1 ] / abs( scalco )**np.sign( scalco ) ),
                        segyio.su.gelev: int( rcv[ 2 ] / abs( scalel )**np.sign( scalel ) ),
                        segyio.su.dt: int( dt * 1e6 ),
                        segyio.su.ns: nsamples
                    }
                    f.trace[ i ] = np.zeros( nsamples, dtype=np.float32 )
                f.bin.update( tsort=segyio.TraceSortingFormat.INLINE_SORTING, hdt=int( dt * 1e6 ), dto=int( dt * 1e6 ) )

        comm.Barrier()

        # Save data
        with segyio.open( self.filename, 'r+', ignore_geometry=True ) as f:
            for i in range( len( receiverCoords ) ):
                if any( self.data[ 1:, i ] ) == True:
                    f.trace[ i ] = np.ascontiguousarray( self.data[ :, i ], dtype=np.float32 )

        if rank == 0:
            print( f"Seismic traces saved in {self.filename}" )

        comm.Barrier()
