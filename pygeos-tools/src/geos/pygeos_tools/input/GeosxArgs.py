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
import sys
from typing import Dict, List
from typing_extensions import Self


__doc__ = """
GeosxArgs class handles the arguments passed to GEOS to start the simulation.

.. todo::
    If possible, change the name GeosxArgs to GeosArgs when 'pygeosx' will be named 'pygeos'.
"""


class GeosxArgs:
    """
    Class containing the main argument in command line for GEOSX

    Attributes
    ----------
        cmdline : list of str
            List corresponding to a splitted GEOSX submission line
        options : dict
            Dict containing GEOSX main options
    """

    def __init__( self: Self, args=sys.argv.copy() ):
        """
        Parameters
        ----------
            args : list of str
                List corresponding to a splitted submission line with options
        """
        self.cmdline: List[ str ] = args
        self.options: Dict[ str, str ] = self.optionsParser()

    def optionsParser( self: Self, cmdline: List[ str ] = list() ) -> Dict[ str, any ]:
        """
        Return a dict with useful geosx options parsed from a list/submission line.

        Parameters
        ----------
            cmdline : list of str
                List corresponding to a splitted GEOSX submission line

        Returns
        --------
            dict :
                Dict containing GEOSX main options
        """
        if not cmdline:
            cmdline = self.cmdline
        desc: str = "Parser of GEOSX command line"
        parser = argparse.ArgumentParser( "GEOSX command line parser", allow_abbrev=False, description=desc )

        parser.add_argument( "--input", "-i", "--xml", type=str, dest="xml", default=None, help="XML input file" )
        parser.add_argument( "--restart", "-r", dest="restart", type=str, default=None, help="Target restart filename" )
        parser.add_argument( "-x-partitions",
                             "-x",
                             type=int,
                             dest="xpart",
                             default=None,
                             help="Number of partitions in the x direction." )
        parser.add_argument( "-y-partitions",
                             "-y",
                             type=int,
                             dest="ypart",
                             default=None,
                             help="Number of partitions in the y direction." )
        parser.add_argument( "-z-partitions",
                             "-z",
                             type=int,
                             dest="zpart",
                             default=None,
                             help="Number of partitions in the z direction." )
        parser.add_argument( "--output",
                             "-o",
                             type=str,
                             dest="outputdir",
                             default=None,
                             help="Directory to put the output files" )
        parser.add_argument( "--use-nonblocking",
                             "-b",
                             default=None,
                             dest="non_blocking",
                             action="store_true",
                             help="Use non-blocking MPI communication" )
        parser.add_argument( "--name", "-n", dest="name", default=None, help="Name of the problem, used for output" )
        parser.add_argument( "--suppress-pinned",
                             "-s",
                             dest="supp_pinned",
                             action="store_true",
                             default=None,
                             help="Suppress usage of pinned memory for MPI communication buffers" )
        parser.add_argument( "--timers",
                             "-t",
                             type=str,
                             dest="timers",
                             default=None,
                             help="String specifying the type of timer output" )
        parser.add_argument( "--trace-data-migration",
                             dest="trace_data_mig",
                             action="store_true",
                             default=None,
                             help="Trace host-device data migration" )
        parser.add_argument( "--pause-for",
                             dest="pause_for",
                             default=None,
                             help="Pause geosx for a given number of seconds before starting execution" )

        return vars( parser.parse_known_args( cmdline )[ 0 ] )

    def updateArg( self: Self, optionName: str = None, newValue: str = None ) -> bool:
        """
        Update the GEOSX initialization arguments

        Parameters
        ----------
            optionName : str
                Name of the option to update
            newValue : str
                New value for the argument to be updated.

        Returns
        -------
            bool : True if the option has been (found and) updated. False otherwise.
        """
        if optionName is not None:
            if self.options[ optionName ] != newValue:
                self.options.update( { optionName: newValue } )
                return True

        return False

    def getCommandLine( self: Self ) -> List[ str ]:
        """
        Return the command line specific to GEOSX initialization

        Returns
        --------
            cl : list of str
                List containing all the options requested
        """
        cl: List[ str ] = [ "" ]
        for opt, val in self.options.items():
            if val is not None:
                ab = GeosxAbbrevOption().getAbbrv( opt )
                cl += [ ab ]
                if not isinstance( self.options[ opt ], bool ):
                    cl += [ str( self.options[ opt ] ) ]

        return cl


class GeosxAbbrevOption:
    """
    Class containing GEOSX command line options abbreviations

    Attributes
    ----------
        abbrvDict : dict
            Dict containing lists of abbreviations for GEOSX command line options
    """

    def __init__( self: Self ):
        self.abbrvDict = {
            "xml": ( "--input", "-i" ),
            "restart": ( "--restart", "r" ),
            "xpart": ( "-x-partitions", "-x" ),
            "ypart": ( "-y-partitions", "-y" ),
            "zpart": ( "-z-partitions", "-z" ),
            "non_blocking": ( "--use-non-blocking", "-b" ),
            "name": ( "--name", "-n" ),
            "supp_pinned": ( "--suppress-pinned" ),
            "outputdir": ( "--output", "-o" ),
            "timers": ( "--timers", "-t" ),
            "trace_data_mig": ( "--trace-data-migration" ),
            "pause_for": ( "--pause-for" )
        }

    def getAbbrv( self: Self, optionName: str = None ) -> str:
        """
        Returns the abbreviation corresponding to the requested option

        Parameters
        ----------
            optionName : str
                Name of the requested option

        Returns
        -------
            str : Requested abbreviations
        """
        return self.abbrvDict[ optionName ][ -1 ]

    def getAllAbbrv( self: Self, optionName: str = None ) -> List[ str ]:
        """
        Returns the abbreviation corresponding to the requested option

        Parameters
        ----------
            optionName : str
                Name of the requested option

        Returns
        -------
            list of str :
                Requested abbreviations
        """
        try:
            return self.abbrvDict[ optionName ]
        except KeyError:
            return [ "" ]
