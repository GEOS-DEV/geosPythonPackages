from configparser import ConfigParser
import argparse
import os


def main( fname ):
    log = ConfigParser()
    log.read( os.path.expanduser( fname ) )

    Nfail = 0
    status_fail = [ 'TIMEDOUT', 'HALTED', 'LSFERROR', 'FAILED' ]

    print( '=======================' )
    print( 'Integrated test results' )
    print( '=======================' )
    for status_code, tests in log[ 'Results' ].items():
        N = len( tests )
        print( f'{status_code}: {N}' )
        if status_code in status_fail:
            Nfail += Nfail

    if Nfail:
        print( '\nOverall status: FAILED' )
    else:
        print( '\nOverall status: PASSED' )


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description="GEOS ATS Test Log Check" )
    parser.add_argument( "log_file", type=str, help="Path to the log file" )
    args = parser.parse_args()

    main( args.log_file )
