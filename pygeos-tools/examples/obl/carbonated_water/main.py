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

# ---------------------------------------- README ----------------------------------------
# Requires 'python -m pip install open-darts phreeqpy coolprop' 
# and GEOS branch feature/anovikov/adaptive_obl to run this example.
# In this model, carbonated water is injected into a core-scale domain,
# associated geochemistry is resolved by PHREEQC.

import numpy as np
from mpi4py import MPI

from geos.pygeos_tools.input import XML
from geos.pygeos_tools.solvers import ReservoirSolver

from model import Model


def run_darts_model( domain: str, xml_name: str, darts_model=None ):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    xml = XML( xml_name )

    solver = ReservoirSolver( solverType="ReactiveCompositionalMultiphaseOBL" )
    solver.initialize( rank=rank, xml=xml )

    functions = solver.geosx.get_group( "/Functions" ).groups()
    for func in functions:
        if hasattr( func, 'setAxes' ) and darts_model is not None:
            func.setAxes( darts_model.physics.n_vars, darts_model.physics.n_ops, list( darts_model.physics.axes_min ),
                          list( darts_model.physics.axes_max ), list( darts_model.physics.n_axes_points ) )
            func.setEvaluateFunction( darts_model.physics.reservoir_operators[ 0 ].evaluate )
            print( "Adaptive OBL interpolator is configured." )

    solver.applyInitialConditions()
    solver.setMaxTime( solver.getTimeVariables()[ "maxTime" ] )

    time: float = 0
    cycle: int = 0
    solver.setDt( 8.64 )

    solver.outputVtk( time )
    while time < solver.maxTime:
        # choose new timestep
        if domain == '1D':
            if time < 48:
                solver.setDt( 4.0 )
            elif time < 240:
                solver.setDt( 8.64 )
            elif time < 3600:
                solver.setDt( 86.4 )
            elif time < 6 * 8640:
                solver.setDt( 240.0 )
            elif time < 2 * 86400:
                solver.setDt( 900.0 )
            else:
                solver.setDt( 3600.0 )
        elif domain == '2D':
            if time < 24:
                solver.setDt( 4.0 )
            elif time < 120:
                solver.setDt( 8.64 )
            elif time < 300:
                solver.setDt( 2 * 8.64 )
            elif time < 1400:
                solver.setDt( 60.0 )
            elif time < 4 * 3600:
                solver.setDt( 300.0 )
            elif time < 9 * 3600:
                solver.setDt( 200.0 )
            else:
                solver.setDt( 100.0 )
        if rank == 0:
            print( f"time = {time:.3f}s, dt = {solver.getDt():.4f}, step = {cycle + 1}" )
        # run simulation
        solver.execute( time )
        time += solver.getDt()
        if cycle % 5 == 0:
            solver.outputVtk( time )
        cycle += 1
    solver.cleanup( time )


if __name__ == "__main__":
    darts_model = Model()
    # run_darts_model( domain='1D', xml_name="1d_setup.xml", darts_model=darts_model )
    run_darts_model( domain='2D', xml_name="2d_setup.xml", darts_model=darts_model )
