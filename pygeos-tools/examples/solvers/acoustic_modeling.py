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
import argparse
import os
from geos.pygeos_tools.input import XML
from geos.pygeos_tools.acquisition_library.EquispacedAcquisition import EQUISPACEDAcquisition
from geos.pygeos_tools.solvers import AcousticSolver
from geos.pygeos_tools.output import SeismicTraceOutput
import mpi4py

mpi4py.rc.initialize = False
from mpi4py import MPI

__doc__ = """
This is an example of how to set and run your GEOS simulation when using the AcousticSolver.
The suggested example with this script could be to use a XML file with the "AcousticSEM" solver.
"""


def parse_args():
    """Get arguments

    Returns:
        argument '--xml': Input xml file for GEOSX
    """
    parser = argparse.ArgumentParser( description="Modeling acquisition example - Acoustic" )
    parser.add_argument( '--xml', type=str, required=True, help="Input xml file for GEOS" )
    parser.add_argument( '--soutdir', required=False, type=str, default="./", help="Path to seismogram output dir" )
    parser.add_argument( '--soutn', required=False, type=str, default="seismo", help="Name of output seismograms" )
    parser.add_argument( '--param_file',
                         type=str,
                         required=False,
                         default="identity",
                         dest="pfile",
                         help="Optional file containing modelling parameters" )

    args, _ = parser.parse_known_args()
    return args


def parse_workflow_parameters( pfile ):
    with open( pfile, "r" ) as f:
        hdrStr = f.read()

    hdrList = list()
    for fl in hdrStr.split( '\n' ):
        elt = fl.split( "#" )[ 0 ]
        if elt:
            # add "--" to facilitate parsing that follows
            elt = "--" + elt
            hdrList += elt.split( "=" )

    parser = argparse.ArgumentParser( "Modelling workflow parser" )
    parser.add_argument( "--mintime", dest="mintime", default=None, type=float, help="Min time for the simulation" )
    parser.add_argument( "--maxtime", dest="maxtime", default=None, type=float, help="Max time for the simulation" )
    parser.add_argument( "--dt", dest="dt", default=None, type=float, help="Time step of simulation" )
    parser.add_argument( "--dtSeismo", dest="dtSeismo", default=None, type=float, help="Time step for " )
    parser.add_argument( "--sourceType", dest="sourceType", type=str, help="Source type" )
    parser.add_argument( "--sourceFreq", dest="sourceFreq", type=float, help="Ricker source central frequency" )

    args, _ = parser.parse_known_args( hdrList )
    return args


def main():

    if not MPI.Is_initialized():
        print( "MPI not initialized. Initializing..." )
        MPI.Init()
        print( "MPI initialized" )

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args = parse_args()
    xmlfile = args.xml

    xml = XML( xmlfile )

    wf_args = parse_workflow_parameters( args.pfile )

    # Time Parameters
    minTime = wf_args.mintime
    maxTime = wf_args.maxtime
    dt = wf_args.dt
    dtSeismo = wf_args.dtSeismo

    # Output parameters
    outdirseis = args.soutdir
    os.makedirs( outdirseis, exist_ok=True )
    outseisname = args.soutn

    # Source parameters
    sourceType = wf_args.sourceType
    sourceFreq = wf_args.sourceFreq

    # Read acquisition
    if rank == 0:
        # acquisition = Acquisition(xml)
        acquisition = EQUISPACEDAcquisition( xml=xml,
                                             startFirstSourceLine=[ 305.01, 305.01, 5.01 ],
                                             endFirstSourceLine=[ 325.01, 305.01, 5.01 ],
                                             startLastSourceLine=[ 305.01, 325.01, 5.01 ],
                                             endLastSourceLine=[ 325.01, 325.01, 5.01 ],
                                             numberOfSourceLines=2,
                                             sourcesPerLine=2,
                                             startFirstReceiversLine=[ 121.02, 255.02, 58.01 ],
                                             endFirstReceiversLine=[ 471.02, 255.02, 58.01 ],
                                             startLastReceiversLine=[ 121.02, 255.02, 58.01 ],
                                             endLastReceiversLine=[ 471.02, 255.02, 58.01 ],
                                             numberOfReceiverLines=1,
                                             receiversPerLine=8 )

    else:
        acquisition = None
    acquisition = comm.bcast( acquisition, root=0 )

    solver = AcousticSolver( solverType="AcousticSEM",
                             dt=dt,
                             minTime=minTime,
                             maxTime=maxTime,
                             dtSeismo=dtSeismo,
                             sourceType=sourceType,
                             sourceFreq=sourceFreq )

    for shot in acquisition.shots:
        xmlshot = shot.xml
        rank = comm.Get_rank()

        solver.initialize( rank, xmlshot )
        solver.applyInitialConditions()

        solver.setSourceAndReceivers( shot.getSourceCoords(), shot.getReceiverCoords() )
        solver.setVtkOutputsName( directory=f"Shot{shot.id}" )

        time: float = 0.0
        cycle: int = 0
        while time < solver.maxTime:
            if rank == 0 and cycle % 100 == 0:
                print( f"time = {time:.3f}s, dt= {solver.dt:.4f}, iter = {cycle + 1}" )
            
            if cycle % 50 == 0:
                solver.outputVtk( time, cycle )

            solver.execute( time, cycle )

            time += solver.dt
            cycle += 1

        solver.outputVtk( time, cycle )

        shot.flag = "Done"
        if rank == 0:
            print( f"Shot {shot.id} done" )
            print( "Gathering and exporting seismos" )

        seismos = solver.getPressureAtReceivers()

        directory = outdirseis
        filename = f"{outseisname}_{shot.id}"

        SeismicTraceOutput( seismos, format="SEP" ).export( directory=directory,
                                                            rootname=filename,
                                                            receiverCoords=shot.getReceiverCoords(),
                                                            sourceCoords=shot.getSourceCoords()[ 0 ],
                                                            dt=solver.dtSeismo )

        solver.resetWaveField()


if __name__ == "__main__":
    main()
