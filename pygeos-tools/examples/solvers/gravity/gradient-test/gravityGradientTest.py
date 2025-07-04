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
from geos.pygeos_tools.solvers.InversionUtils import gradientTest, plotGradientTestFromFile

__doc__ = """
This is an example of how to set up and run a gradient test for GEOS simulation using the GravitySolver.
"""


def parse_args():
    """
    Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed arguments including XML input, models, and scaling factor.
    """
    parser = argparse.ArgumentParser( description="Run a GEOS gravity simulation and gradient test." )
    parser.add_argument( '--xml', type=str, required=True, help="Input XML file for GEOSX." )
    parser.add_argument( '--m_true', type=str, required=True, help="True model file (.npy)." )
    parser.add_argument( '--m0', type=str, required=True, help="Initial model file (.npy)." )
    parser.add_argument( '--dm', type=str, required=True, help="Perturbation model file (.npy)." )
    parser.add_argument( '--scale', type=float, default=1.0, help="Scaling factor for the loss." )
    parser.add_argument( '--history', type=str, default='grad_test.txt', help="Output file for gradient test history." )
    parser.add_argument( '--plot', action='store_true', help="Plot the gradient test results." )
    return parser.parse_args()


def main():

    rank = MPI.COMM_WORLD.Get_rank()
    verbose = ( rank == 0 )

    args = parse_args()
    xml_file = args.xml
    scale = args.scale

    # Load XML configuration
    xml = XML( xml_file )

    # Load models from .npy files
    try:
        m_true = np.load( args.m_true )
        m0 = np.load( args.m0 )
        dm = np.load( args.dm )
    except FileNotFoundError as e:
        raise RuntimeError( f"Could not load input model file: {e}" )

    # Initialize solver as a linear operator
    solver = GravityLinearOpSolver( rank=rank, xml=xml, nm=m_true.size, scaleData=scale )

    # Generate observed data
    uobs = solver.getData( m_true )

    # Run gradient test
    passed, slope, history = gradientTest( lambda m: solver.getLoss( m, uobs, scale=scale ),
                                           lambda m: solver.getGradient( m, uobs, scale=scale ),
                                           m0,
                                           dm,
                                           history_filename=args.history,
                                           flag_verbose=verbose )

    if verbose:
        print( "\n=== Gradient Test Summary ===" )
        print( f"Passed: {passed}" )
        print( f"Slope: {slope if slope.size > 0 else 'N/A'}" )
        print( f"History saved to: {args.history}" )

        if args.plot:
            plotGradientTestFromFile( args.history, save_path="grad_test.png", style={ "color": "red", "marker": "o" } )

    # Finalize GEOS
    solver.finalize()

    # Exit with non-zero code if test failed
    if not passed:
        sys.exit( 1 )


if __name__ == "__main__":
    main()
