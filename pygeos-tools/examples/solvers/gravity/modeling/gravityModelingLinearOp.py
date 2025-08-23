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
import copy

from mpi4py import MPI

import numpy as np
from geos.pygeos_tools.input import XML
from geos.pygeos_tools.solvers import GravityLinearOpSolver
from pygeosx import run, COMPLETED

__doc__ = """
Example script demonstrating how to configure and run a GEOS gravity simulation using the GravityLinearOpSolver.
"""


def parse_args():
    """
    Parse command-line arguments for the simulation.

    Returns:
        argparse.Namespace: Parsed arguments including:
            --xml (str): Path to the GEOS input XML file (required).
            --model (str, optional): Path to a .npy file containing the density model.
            --nm (int, optional): Number of model elements. Required if --model is not provided.
            --save_gz (str, optional): Path to save the computed gz output as a .npy file.
    """

    parser = argparse.ArgumentParser(description="Gravity modeling example")
    parser.add_argument('--xml', type=str, required=True, help="Input xml file for GEOS")
    parser.add_argument('--model', type=str, default=None,
                        help="Density model file (.npy). If not provided, --nm must be specified")
    parser.add_argument('--nm', type=int, default=None,
                        help="Model size. Required if --model is not provided")
    parser.add_argument("--save_gz", type=str, default=None,
                        help="Optional output file to save gz (.npy)")
    
    args, _ = parser.parse_known_args()
    return args


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args = parse_args()
    xmlfile = args.xml
    xml = XML( xmlfile )

    if args.model is not None:
        model = np.load(args.model)
        print( f"Density min={np.min(model)}, max={np.max(model)}", flush=True )
        if args.nm is not None and model.size != args.nm:
            raise ValueError(f"Mismatch: model has size {model.size}, but nm={args.nm}")
        nm = model.size
    else:
        if args.nm is None:
            raise ValueError("Either --model or --nm must be provided")
        model = None
        nm = args.nm

    # Initialize solver
    solver = GravityLinearOpSolver( rank=rank, xml=xml, nm=nm )

    # Perform modeling
    gz = solver.getData( model )

    # Save output
    if rank == 0:
        print(f"gz min={np.min(gz)}, max={np.max(gz)}")
        if args.save_gz:
            np.save(args.save_gz, gz)
            print(f"gz saved to {args.save_gz}")

    solver.finalize()


if __name__ == "__main__":
    main()
