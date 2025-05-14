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
from mpi4py import MPI
from geos.pygeos_tools.input import XML
from geos.pygeos_tools.solvers import ReservoirSolver

__doc__ = """
This is an example of how to set and run your GEOS simulation when using the ReservoirSolver.
The suggested example with this script could be the 2 phases 1D test case provided by GEOS:
'/path/to/your/geos/code/inputFiles/compositionalMultiphaseFlow/2ph_cap_1d_ihu.xml'.
"""


def parse_args():
    """Get arguments

    Returns:
        argument '--xml': Input xml file for GEOSX
    """
    parser = argparse.ArgumentParser( description="Reservoir simulation example" )
    parser.add_argument( '--xml', type=str, required=True, help="Input xml file for GEOS" )

    args, _ = parser.parse_known_args()
    return args


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args = parse_args()
    xmlfile = args.xml
    xml = XML( xmlfile )

    solver = ReservoirSolver( "CompositionalMultiphaseFVM" )
    solver.initialize( rank=rank, xml=xml )
    solver.applyInitialConditions()
    solver.setDtFromTimeVariable( "forceDt" )  # because is defined in the XML
    solver.setMaxTime( solver.getTimeVariables()[ "maxTime" ] )

    time: float = 0.0
    cycle: int = 0

    while time < solver.maxTime:
        if rank == 0:
            if solver.dt is not None:
                print( f"time = {time:.3f}s, dt = {solver.dt:.4f}, iter = {cycle + 1}" )
        solver.outputVtk( time, cycle )
        solver.execute( time, cycle )
        pressure = solver.getPressures()
        print( pressure )
        time += solver.dt
        cycle += 1

    solver.outputVtk( time, cycle )
    solver.cleanup( time )


if __name__ == "__main__":
    main()
