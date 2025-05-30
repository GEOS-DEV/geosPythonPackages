from typing import Any, Optional
from geos.hdf5_wrapper import wrapper as h5w
import matplotlib.pyplot as plt
import os
import argparse

import re


def isiterable( obj: Any ) -> bool:
    """Check if input is iterable."""
    try:
        it = iter( obj )  # noqa: F841
    except TypeError:
        return False
    return True


def getHistorySeries( database: h5w,
                      variable: str,
                      setname: str,
                      indices: Optional[ int | list[ int ] ] = None,
                      components: Optional[ int | list[ int ] ] = None ) -> Optional[ list[ tuple[ Any, ...] ] ]:
    """Retrieve a series of time history structures suitable for plotting in addition to the specific set index and component for the time series.

    Args:
        database (geos.hdf5_wrapper.hdf5_wrapper): database to retrieve time history data from
        variable (str): the name of the time history variable for which to retrieve time-series data
        setname (str): the name of the index set as specified in the geosx input xml for which to query time-series data
        indices (Optional[int | list[ int ]]): the indices in the named set to query for, if None, defaults to all
        components (Optional[int | list[ int ]]): the components in the flattened data types to retrieve, defaults to all

    Returns:
        Optional[list[ tuple[ Any, ...] ]]: list of (time, data, idx, comp) timeseries tuples for each time history data component
    """
    set_regex = re.compile( variable + '(.*?)', re.IGNORECASE )
    if setname is not None:
        set_regex = re.compile( variable + r'\s*' + str( setname ), re.IGNORECASE )
    time_regex = re.compile( 'Time', re.IGNORECASE )  # need to make this per-set, thought that was in already?

    set_match = list( filter( set_regex.match, database.keys() ) )
    time_match = list( filter( time_regex.match, database.keys() ) )

    if len( set_match ) == 0:
        print( f"Error: can't locate time history data for variable/set described by regex {set_regex.pattern}" )
        return None
    if len( time_match ) == 0:
        print( f"Error: can't locate time history data for set time variable described by regex {time_regex.pattern}" )
        return None

    if len( set_match ) > 1:
        print( f"Warning: variable/set specification matches multiple datasets: {', '.join(set_match)}" )
    if len( time_match ) > 1:
        print( f"Warning: set specification matches multiple time datasets: {', '.join(time_match)}" )

    set_match = set_match[ 0 ]
    time_match = time_match[ 0 ]

    data_series = database[ set_match ]
    time_series = database[ time_match ]

    if time_series.shape[ 0 ] != data_series.shape[ 0 ]:
        print(
            f"Error: The length of the time-series {time_match} and data-series {set_match} do not match: {time_series.shape} and {data_series.shape} !"
        )
    indices1: list[ int ] = []
    if indices is not None:
        if type( indices ) is int:
            indices1 = [ indices ]
        elif isiterable( indices ):
            oob_idxs: list[ int ] = list(
                filter(
                    lambda idx: not 0 <= idx < data_series.shape[ 1 ],  # type: ignore[arg-type]
                    indices ) )  # type: ignore[arg-type]
            if len( oob_idxs ) > 0:
                print( f"Error: The specified indices: ({', '.join(map(str, oob_idxs))}) " + "\n\t" +
                       f" are out of the dataset index range: [0,{data_series.shape[1]})" )  # type: ignore[arg-type]
            indices1 = list( set( indices ) - set( oob_idxs ) )  # type: ignore[arg-type]
        else:
            print( f"Error: unsupported indices type: {type(indices)}" )
    else:
        indices1 = list( range( data_series.shape[ 1 ] ) )

    components1: list[ int ] = []
    if components is not None:
        if type( components ) is int:
            components1 = [ components ]
        elif isiterable( components ):
            oob_comps: list[ int ] = list(
                filter(
                    lambda comp: not 0 <= comp < data_series.shape[ 2 ],  # type: ignore[arg-type]
                    components ) )  # type: ignore[arg-type]
            if len( oob_comps ) > 0:
                print( f"Error: The specified components: ({', '.join(map(str, oob_comps))}) " + "\n\t" +
                       " is out of the dataset component range: [0,{data_series.shape[1]})" )
            components1 = list( set( components ) - set( oob_comps ) )  # type: ignore[arg-type]
        else:
            print( f"Error: unsupported components type: {type(components)}" )
    else:
        components1 = list( range( data_series.shape[ 2 ] ) )

    return [ ( time_series[ :, 0 ], data_series[ :, idx, comp ], idx, comp ) for idx in indices1
             for comp in components1 ]


def commandLinePlotGen() -> int:
    """Parse commande line."""
    parser = argparse.ArgumentParser(
        description="A script that parses geosx HDF5 time-history files and produces time-history plots using matplotlib"
    )
    parser.add_argument( "filename", metavar="history_file", type=str, help="The time history file to parse" )

    parser.add_argument( "variable",
                         metavar="variable_name",
                         type=str,
                         help="Which time-history variable collected by GEOSX to generate a plot file for." )

    parser.add_argument(
        "--sets",
        metavar="name",
        type=str,
        action='append',
        default=[ None ],
        nargs="+",
        help=
        "Which index set of time-history data collected by GEOSX to generate a plot file for, may be specified multiple times with different indices/components for each set."
    )

    parser.add_argument( "--indices",
                         metavar="index",
                         type=int,
                         default=[],
                         nargs="+",
                         help="An optional list of specific indices in the most-recently specified set." )

    parser.add_argument( "--components",
                         metavar="int",
                         type=int,
                         default=[],
                         nargs="+",
                         help="An optional list of specific variable components" )

    args = parser.parse_args()
    result = 0

    if not os.path.isfile( args.filename ):
        print( f"Error: file '{args.filename}' not found." )
        result = -1
    else:
        with h5w( args.filename, mode='r' ) as database:
            for setname in args.sets:
                ds = getHistorySeries( database, args.variable, setname, args.indices, args.components )
                if ds is None:
                    result = -1
                    break
                figname = args.variable + ( "_" + setname if setname is not None else "" )
                fig, ax = plt.subplots()
                ax.set_title( figname )
                for d in ds:
                    ax.plot( d[ 0 ], d[ 1 ] )
                fig.savefig( figname + "_history.png" )

    return result


if __name__ == "__main__":
    commandLinePlotGen()
