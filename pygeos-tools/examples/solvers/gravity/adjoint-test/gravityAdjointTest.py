# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
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
from geos.pygeos_tools.solvers.InversionUtils import adjointTest

__doc__ = """
Example script demonstrating how to configure and run an adjoint test for GEOS gravity simulation using the GravityLinearOpSolver.
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
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    verbose = ( rank == 0 )

    args = parse_args()
    xml_file = args.xml
    scale = args.scale
    nm = args.n_model
    nd = args.n_data

    # Load XML configuration
    xml = XML( xml_file )

    # Generate random fields
    np.random.seed( 42 )  # Set random seed for reproducibility
    if rank == 0:
        x = np.random.rand( nm )
        y = np.random.rand( nd )
    else:
        x = None
        y = None

    x = comm.bcast( x, root=0 )
    y = comm.bcast( y, root=0 )

    # Initialize solver as a linear operator
    solver = GravityLinearOpSolver( rank=rank, xml=xml, nm=args.n_model, nd=args.n_data, scaleData=scale )

    # Run the test
    passed, error = adjointTest( solver._matvec, solver._rmatvec, x, y, flag_verbose=verbose )

    solver.finalize()

    if not passed:
        sys.exit( 1 )


if __name__ == "__main__":
    main()
