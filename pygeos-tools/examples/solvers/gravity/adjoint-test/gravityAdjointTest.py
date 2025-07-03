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
import numpy as np
import sys
from mpi4py import MPI

from geos.pygeos_tools.input import XML
from geos.pygeos_tools.solvers import GravityLinearOpSolver

__doc__ = """
This is an example of how to set up and run an adjoint test for GEOS simulation using the GravitySolver.
"""


def parse_args():
    """
    Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed arguments including XML input, dimensions and scaling factor.
    """
    parser = argparse.ArgumentParser( description="Run a GEOS gravity adjoint test." )
    parser.add_argument( '--xml', type=str, required=True, help="Input XML file for GEOSX." )
    parser.add_argument( '--n_model', type=int, required=True, help="Number of model samples." )
    parser.add_argument( '--n_data', type=int, required=True, help="Number of data samples." )
    parser.add_argument( '--scale', type=float, default=1.0, help="Scaling factor." )
    return parser.parse_args()


def main():
    rank = MPI.COMM_WORLD.Get_rank()
    verbose = ( rank == 0 )

    args = parse_args()
    xml_file = args.xml
    scale = args.scale
    nm = args.n_model
    nd = args.n_data

    # Load XML configuration
    xml = XML( xml_file )

    if rank == 0:
        x = np.random.rand( nm )
        y = np.random.rand( nd )
    else:
        x = None
        y = None

    x = MPI.COMM_WORLD.bcast( x, root=0 )
    y = MPI.COMM_WORLD.bcast( y, root=0 )

    # Initialize solver as a linear operator
    solver = GravityLinearOpSolver( rank=rank, xml=xml, nm=args.n_model, nd=args.n_data, scaleData=scale )

    Ax = solver._matvec( x )
    ATy = solver._rmatvec( y )

    IP1 = np.dot( Ax.T, y )
    IP2 = np.dot( x.T, ATy )

    nAx = np.linalg.norm( Ax, 2 )
    nx = np.linalg.norm( x, 2 )
    nATy = np.linalg.norm( ATy, 2 )
    ny = np.linalg.norm( y, 2 )

    e = abs( IP1 - IP2 ) / np.max( [ nAx * ny, nATy * nx ] )

    if verbose:
        print( "\n=== Adjoint Test Summary ===" )
        print( f"IP1 = {IP1}" )
        print( f"IP2 = {IP2}" )
        print( f"Passed: {e < 1e-13}" )
        print( f"Error: {e}" )

    solver.finalize()

    if e >= 1e-13:
        sys.exit( 1 )


if __name__ == "__main__":
    main()
