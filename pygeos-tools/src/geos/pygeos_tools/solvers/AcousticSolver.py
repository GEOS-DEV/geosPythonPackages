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
import h5py
import os
import numpy as np
import numpy.typing as npt
import shutil
from typing import Optional
from typing_extensions import Self
from geos.pygeos_tools.solvers.WaveSolver import WaveSolver
from geos.utils.errors_handling.classes import required_attributes
from geos.utils.pygeos.solvers import MODEL_FOR_GRADIENT

__doc__ = """
AcousticSolver class inherits from WaveSolver class.

This adds method to read / set pressures at receiver, compute partial gradients and accessors for Density and Velocity
models.
"""


class AcousticSolver( WaveSolver ):
    """
    AcousticSolver Object containing all methods to run AcousticSEM simulation with GEOSX

    Attributes
    -----------
        The ones inherited from WaveSolver class

        modelForGradient : str
            Gradient model used
    """

    def __init__( self: Self,
                  solverType: str = "AcousticSEM",
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
                The solverType targeted in GEOS XML deck. Defaults to "AcousticSEM"
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
        self.modelForGradient: str = None

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

    """
    Accessors
    """

    def getFullPressureAtReceivers( self: Self, comm ) -> npt.NDArray:
        """
        Return all pressures at receivers values on all ranks
        Note that for a too large 2d array this may not work.

        Parameters:
        -----------
            comm : MPI_COMM
                MPI communicators
        """
        rank = comm.Get_rank()

        allPressure = comm.gather( self.getPressureAtReceivers(), root=0 )
        pressure = np.zeros( self.getPressureAtReceivers().shape )

        if rank == 0:
            for p in allPressure:
                for i in range( p.shape[ 1 ] ):
                    if any( p[ 1:, i ] ):
                        pressure[ :, i ] = p[ :, i ]

        pressure = comm.bcast( pressure, root=0 )
        return pressure

    def getFullWaveFieldAtReceivers( self: Self, comm ) -> npt.NDArray:
        return self.getFullPressureAtReceivers( comm )[ :, :-1 ]

    @required_attributes( "modelForGradient" )
    def getModelForGradient( self: Self ) -> str:
        return self.modelForGradient

    def getPartialGradientFor1RegionWith1CellBlock( self: Self,
                                                    filterGhost=False,
                                                    **kwargs ) -> Optional[ npt.NDArray ]:
        """
        Get the local rank gradient value
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Returns
        --------
            partialGradient : Numpy Array-
                Array containing the element id list for the local rank
        """
        partialGradient = self.getSolverFieldWithPrefix( "partialGradient", **kwargs )

        if partialGradient is not None:
            if filterGhost:
                partialGradient_filtered = self.filterGhostRankFor1RegionWith1CellBlock( partialGradient, **kwargs )
                if partialGradient_filtered is not None:
                    return partialGradient_filtered
                else:
                    print( "getPartialGradientFor1RegionWith1CellBlock->filterGhostRank: Filtering of ghostRank could" +
                           "not be performed. No partialGradient returned." )
            else:
                return partialGradient
        else:
            print( "getPartialGradientFor1RegionWith1CellBlock: No partialGradient was found." )

    def getPressureAtReceivers( self: Self ) -> npt.NDArray:
        """
        Get the pressure values at receivers coordinates

        Returns
        ------
            numpy Array : Array containing the pressure values at all time step at all receivers coordinates
        """
        return self.getGeosWrapperByName( "pressureNp1AtReceivers", [ "Solvers" ] )

    def getWaveField( self: Self ) -> npt.NDArray:
        return self.getPressureAtReceivers()[ :, :-1 ]

    """
    Mutators
    """

    def setModelForGradient( self: Self, modelForGradient: str ) -> None:
        f"""
        Set the model for the gradient

        Parameters
        -----------
            model : str
                Model for the gradients available are:
                {list( MODEL_FOR_GRADIENT.__members__.keys() )}
        """
        if modelForGradient in MODEL_FOR_GRADIENT.__members__:
            self.modelForGradient = MODEL_FOR_GRADIENT[ modelForGradient ]
        else:
            raise ValueError( f"The model for gradient chosen '{modelForGradient}' is not implemented. The available" +
                              f" ones are '{list( MODEL_FOR_GRADIENT.__members__.keys() )}'." )

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
        self.setGeosWrapperValueByName( "acousticDensity", value=density, filters=[ self.discretization ] )

    def updateVelocityModel( self: Self, vel: npt.NDArray ) -> None:
        """
        Update velocity value in GEOS

        Parameters
        ----------
            vel : float/array
                Value(s) for velocity field
        """
        self.setGeosWrapperValueByName( "acousticVelocity", value=vel, filters=[ self.discretization ] )

    def updateVelocityModelFromHDF5( self: Self, filename: str, low: float, high: float, comm, velocityModelName: str,
                                     **kwargs ) -> None:
        """
        Update velocity model
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            filename : str
                .hdf5 file where to get the new model
            low : float
                Min value threshold. All new values < low are set to low
            high : float
                Max value threshold. All new values > high are set to high
            comm : MPI_COMM
               MPI communicators
        """
        root = 0
        rank = comm.Get_rank()

        x = None
        if rank == root:
            with h5py.File( filename, 'r' ) as f:
                x = f[ "velocity" ][ : ]

            imin = np.where( x < low )[ 0 ]
            imax = np.where( x > high )[ 0 ]
            x[ imin ] = low
            x[ imax ] = high

            if self.modelForGradient == MODEL_FOR_GRADIENT.SLOWNESS_SQUARED.value:
                x = np.sqrt( 1 / x )
            elif self.modelForGradient == MODEL_FOR_GRADIENT.SLOWNESS.value:
                x = 1 / x
            elif self.modelForGradient == MODEL_FOR_GRADIENT.VELOCITY.value:
                pass
            else:
                raise ValueError( "Not implemented" )

        startModel = self.bcastFieldFor1RegionWith1CellBlock( x, comm, root, **kwargs )
        self.setGeosWrapperValueByName( velocityModelName, startModel )

    """
    Methods for computation and reset of values
    """

    def computePartialGradientFor1RegionWith1CellBlock( self: Self,
                                                        shotId: int,
                                                        minDepth: float,
                                                        comm,
                                                        velocityName: str,
                                                        gradDirectory="partialGradient",
                                                        filterGhost: bool = False,
                                                        **kwargs ) -> None:
        """
        Compute the partial Gradient
        WARNING: this function aims to work in the specific case of having only 1 CellElementRegion in your XML file
        and that this CellElementRegion contains only one cellBlock.

        Parameters
        -----------
            shotId : string
                Number of the shot as string
            minDepth : float
                Depth at which gradient values are kept, otherwise it is set to 0.
                NOTE : this is done in this routine to avoid storage \
                    of elementCenter coordinates in the .hdf5 \
                    but might be problem for WolfeConditions later on \
                    if minDepth is too large
            comm : MPI_COMM
                MPI communicators
            velocity : str
                Name of the velocity model in GEOS
            gradDirectory : str, optional
                Partial gradient directory \
                Default is `partialGradient`
        """
        rank = comm.Get_rank()
        root = 0

        # Get local gradient
        grad = self.getPartialGradientFor1RegionWith1CellBlock( filterGhost, **kwargs )
        if self.modelForGradient == MODEL_FOR_GRADIENT.SLOWNESS_SQUARED.value:
            x = self.getVelocityModel( velocityName, filterGhost, **kwargs )
            grad = -( x * x * x / 2 ) * grad
        elif self.modelForGradient == MODEL_FOR_GRADIENT.SLOWNESS.value:
            x = self.getVelocityModel( velocityName, filterGhost=True, **kwargs )
            grad = -x * x * grad
        elif self.modelForGradient == MODEL_FOR_GRADIENT.VELOCITY.value:
            pass
        else:
            raise ValueError( "Not implemented" )

        grad = grad.astype( np.float64 )

        zind = np.where( self.getElementCenterFor1RegionWith1CellBlock( filterGhost, **kwargs )[ :,
                                                                                                 2 ] < minDepth )[ 0 ]
        grad[ zind ] = 0.0

        # Gather global gradient
        gradFull, ntot = self.gatherFieldFor1RegionWith1CellBlock( field=grad, comm=comm, root=root, **kwargs )

        if rank == root:
            os.makedirs( gradDirectory, exist_ok=True )

            with h5py.File( f"{gradDirectory}/partialGradient_" + shotId + ".hdf5", 'w' ) as h5p:

                h5p.create_dataset( "partialGradient", data=np.zeros( ntot ), chunks=True, maxshape=( ntot, ) )
                h5p[ "partialGradient" ][ : ] = self.dtWaveField * gradFull

            shutil.move( f"{gradDirectory}/partialGradient_" + shotId + ".hdf5",
                         f"{gradDirectory}/partialGradient_ready_" + shotId + ".hdf5" )

        comm.Barrier()

    def resetWaveField( self: Self, **kwargs ) -> None:
        """
        Reinitialize all pressure values on the Wavefield to zero in GEOSX
        """
        self.setGeosWrapperValueByTargetKey( "Solvers/" + self.name + "/indexSeismoTrace", value=0 )
        nodeManagerPath = f"domain/MeshBodies/{self.meshName}/meshLevels/{self.discretization}/nodeManager/"

        if self.type == "AcousticSEM":
            for ts in ( "nm1", "n", "np1" ):
                self.setGeosWrapperValueByTargetKey( nodeManagerPath + f"pressure_{ts}", value=0.0 )

        elif self.type == "AcousticFirstOrderSEM":
            self.setGeosWrapperValueByTargetKey( nodeManagerPath + "pressure_np1", value=0.0 )

            prefix = self._getPrefixPathFor1RegionWith1CellBlock( **kwargs )
            for component in ( "x", "y", "z" ):
                self.setGeosWrapperValueByTargetKey( prefix + f"velocity_{component}", value=0.0 )

    def resetPressureAtReceivers( self: Self ) -> None:
        """
        Reinitialize pressure values at receivers to 0
        """
        self.setGeosWrapperValueByTargetKey( "/Solvers/" + self.name + "/" + "pressureNp1AtReceivers", value=0.0 )
