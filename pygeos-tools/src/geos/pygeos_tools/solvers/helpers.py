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
from enum import Enum
from typing import List
from geos.pygeos_tools.input.Xml import XML


class GEOS_STATE( Enum ):
    """This class needs to be up to date with the implementation of getState in pygeosx.cpp.

    Args:
        Enum (int): GEOS state parameter.
    """
    UNINITIALIZED = 0
    INITIALIZED = 1
    READY_TO_RUN = 2
    COMPLETED = 3


class MODEL_FOR_GRADIENT( Enum ):
    """This class needs to be up to date with the model for gradient available.
    This refers to inversion parameters.
    """
    VELOCITY = "c"
    SLOWNESS = "1/c"
    SLOWNESS_SQUARED = "1/c2"


def automatic_solver_type( xml: XML, prefix: str = "automatic" ) -> str:
    """Given a XML object and a prefix of the solver you are looking for in the XML, returns the associated solver type.
    If "automatic" was the prefix, the first solver type found on the list of solvers in your XML file will be chosen.
    If no solver matches your prefix, defaults to the first solver type found also.

    Args:
        xml (XML): XML object
        prefix (str, optional): Solver name prefix. Can be just a part of the solver name. Defaults to "automatic".

    Returns:
        str: The solver type
    """
    solverTypes: List[ str ] = xml.getSolverTypes()
    if prefix == "automatic":
        return solverTypes[ 0 ]
    for solverType in solverTypes:
        if prefix.lower() in solverType.lower():
            return solverType
    print( "No solver corresponding to your prefix choice was found in the Solvers. We choose the first one found." )
    return solverTypes[ 0 ]


def print_group( group, indent=0 ):
    print( "{}{}".format( " " * indent, group ) )

    indent += 4
    print( "{}wrappers:".format( " " * indent ) )

    for wrapper in group.wrappers():
        print( "{}{}".format( " " * ( indent + 4 ), wrapper ) )
        print_with_indent( str( wrapper.value( False ) ), indent + 8 )

    print( "{}groups:".format( " " * indent ) )

    for subgroup in group.groups():
        print_group( subgroup, indent + 4 )


def print_with_indent( msg, indent ):
    indent_str = " " * indent
    print( indent_str + msg.replace( "\n", "\n" + indent_str ) )


def printGeosx( solver ):
    print_group( solver.geosx )


def printSolver( solver ):
    print_group( solver.solver )


def printGroup( solver, path ):
    print_group( solver.solver.get_group( path ) )