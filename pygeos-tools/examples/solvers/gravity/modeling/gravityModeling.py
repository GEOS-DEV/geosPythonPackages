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
from geos.pygeos_tools.solvers import GravitySolver
from pygeosx import run, COMPLETED

__doc__ = """
“This is an example of how to set up and run your GEOS simulation using the GravitySolver.
"""


def parse_args():
    """Get arguments

    Returns:
        argument '--xml': Input xml file for GEOSX
    """
    parser = argparse.ArgumentParser( description="Gravity simulation example" )
    parser.add_argument( '--xml', type=str, required=True, help="Input xml file for GEOS" )
    parser.add_argument( '--m_true', type=str, required=True, help="True model (.npy)" )

    args, _ = parser.parse_known_args()
    return args


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args = parse_args()
    xmlfile = args.xml
    xml = XML( xmlfile )

    solver = GravitySolver()
    solver.initialize( rank=rank, xml=xml )

    density = np.load( args.m_true )

    gz = solver.modeling( density )
    print( f"gz min={np.min(gz)}, max={np.max(gz)}" )

    solver.finalize()


if __name__ == "__main__":
    main()
