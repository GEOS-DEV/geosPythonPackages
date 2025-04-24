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
from geos.pygeos_tools.input import XML
from geos.pygeos_tools.acquisition_library.Acquisition import Acquisition
from geos.pygeos_tools.solvers import ElasticSolver
from geos.pygeos_tools.output import SeismicTraceOutput
import mpi4py

mpi4py.rc.initialize = False
from mpi4py import MPI

__doc__ = """
This is an example of how to set and run your GEOS simulation when using the ElasticSolver.
The suggested example with this script could be to use a XML file with the "ElasticSEM" solver.
"""


def parse_args():
    """Get arguments

    Returns:
        argument '--xml': Input xml file for GEOSX
    """
    parser = argparse.ArgumentParser( description="Modeling acquisition example" )
    parser.add_argument( '--xml', type=str, required=True, help="Input xml file for GEOSX" )

    args, _ = parser.parse_known_args()
    return args


def main():

    if not MPI.Is_initialized():
        print( "MPI not initialized. Initializing..." )
        MPI.Init()
        print( "MPI initialized" )

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args = parse_args()
    print( args )
    xmlfile = args.xml
    xml = XML( xmlfile )

    # Read acquisition
    if rank == 0:
        acqui = Acquisition( xml )
    else:
        acqui = None
    acqui = comm.bcast( acqui, root=0 )

    solver = ElasticSolver()

    for shot in acqui.shots:
        xmlshot = shot.xml
        rank = comm.Get_rank()

        solver.initialize( rank, xmlshot )
        solver.applyInitialConditions()

        solver.setSourceAndReceivers( shot.getSourceCoords(), shot.getReceiverCoords() )
        solver.setVtkOutputsName( directory=f"Shot{shot.id}" )
        solver.setDtFromTimeVariable( "forceDt" )  # because is defined in the XML
        solver.setMaxTime( solver.getTimeVariables()[ "maxTime" ] )

        t: float = 0.0
        cycle: int = 0

        while t < solver.maxTime:
            if rank == 0 and cycle % 100 == 0:
                print( f"time = {t:.3f}s, dt = {solver.dt:.4f}, iter = {cycle + 1}" )
            
            if cycle % 100 == 0:
                solver.outputVtk( t, cycle )
            
            solver.execute( t, cycle )
            
            t += solver.dt
            cycle += 1

        solver.outputVtk( t, cycle )

        shot.flag = "Done"
        if rank == 0:
            print( f"Shot {shot.id} done" )
            print( "Gathering and exporting seismos" )

        seismos = solver.getAllDisplacementAtReceivers()

        directory = './seismoTraces/'
        rootname = f"seismo_{shot.id}_U"

        for i, dir in enumerate( ( 'X', 'Y', 'Z' ) ):
            seismoOut = SeismicTraceOutput( seismos[ i ], format="SEP" )
            seismoOut.export( directory=directory, rootname=rootname + dir, dt=solver.dtSeismo, verbose=True )

        solver.resetWaveField()


if __name__ == "__main__":
    main()
