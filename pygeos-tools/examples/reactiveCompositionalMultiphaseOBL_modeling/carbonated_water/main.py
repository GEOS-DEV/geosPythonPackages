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


def run_darts_model( domain: str, 
                     xml_name: str, 
                     darts_model=None, 
                     dt_multiplier: float = 1.0, 
                     vtk_output: bool = True):
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
    solver.setDt( 8.64 * dt_multiplier )

    while time < solver.maxTime:
        # choose new timestep
        if domain == '1D':
            if time < 48:
                solver.setDt( 4.0 * dt_multiplier )
            elif time < 240:
                solver.setDt( 8.64 * dt_multiplier )
            elif time < 3600:
                solver.setDt( 86.4 * dt_multiplier )
            elif time < 6 * 8640:
                solver.setDt( 240.0 * dt_multiplier )
            elif time < 2 * 86400:
                solver.setDt( 900.0 * dt_multiplier )
            else:
                solver.setDt( 3600.0 * dt_multiplier )
        elif domain == '2D':
            if time < 24:
                solver.setDt( 4.0 * dt_multiplier )
            elif time < 120:
                solver.setDt( 8.64 * dt_multiplier )
            elif time < 300:
                solver.setDt( 2 * 8.64 * dt_multiplier )
            elif time < 1400:
                solver.setDt( 60.0 * dt_multiplier )
            elif time < 4 * 3600:
                solver.setDt( 300.0 * dt_multiplier )
            elif time < 9 * 3600:
                solver.setDt( 200.0 * dt_multiplier )
            else:
                solver.setDt( 100.0 * dt_multiplier )
        if rank == 0:
            print( f"time = {time:.3f}s, dt = {solver.getDt():.4f}, step = {cycle + 1}" )

        if vtk_output and cycle % 10 == 0:
            solver.outputVtk( time, cycle )

        solver.execute( time, cycle )

        time += solver.getDt()
        cycle += 1

    if vtk_output:
        solver.outputVtk( time, cycle )
    solver.cleanup( time )


# To run use the following command:
# nohup mpiexec -n 96 python -m mpi4py main.py -x 8 -y 12 -output 2D_np_96_nx_1600 -t runtime-report,max_column_width=200 > 2D_np_96_nx_1600.txt 2>&1 &

if __name__ == "__main__":
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    comm.Barrier()
    t0 = MPI.Wtime()

    darts_model = Model()
    # Use 2D when running with -x 4 -y 4
    run_darts_model( domain='1D', xml_name="1d_setup.xml", darts_model=darts_model )
    # run_darts_model( domain='2D', xml_name="2d_setup.xml", darts_model=darts_model )
    # run_darts_model( domain='2D', xml_name="2d_setup_800.xml", dt_multiplier= 1.0 / 6.0, darts_model=darts_model )
    # run_darts_model( domain='2D', xml_name="2d_setup_1600.xml", dt_multiplier= 1.0 / 10.0, darts_model=darts_model )

    comm.Barrier()
    elapsed = MPI.Wtime() - t0
    total = comm.reduce(elapsed, op=MPI.MAX, root=0)
    if rank == 0:
        print(f"Total simulation wall time: {total:.3f} s")
