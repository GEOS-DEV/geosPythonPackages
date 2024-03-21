import os
import socket
import time
from geos_ats.configuration_record import config
from configparser import ConfigParser
from tabulate import tabulate
import glob
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from ats import atsut
from ats.times import hms
from ats import ( PASSED, FAILED, TIMEDOUT, EXPECTED, BATCHED, FILTERED, SKIPPED, CREATED, RUNNING, HALTED, LSFERROR )

# Get the active logger instance
logger = logging.getLogger( 'geos_ats' )

# Status value in priority order
STATUS = ( EXPECTED, CREATED, BATCHED, FILTERED, SKIPPED, RUNNING, PASSED, TIMEDOUT, HALTED, LSFERROR, FAILED )

COLORS: Mapping[ str, str ] = {
    EXPECTED.name: "black",
    CREATED.name: "black",
    BATCHED.name: "black",
    FILTERED.name: "black",
    SKIPPED.name: "orange",
    RUNNING.name: "blue",
    PASSED.name: "green",
    TIMEDOUT.name: "red",
    HALTED.name: "brown",
    LSFERROR.name: "brown",
    FAILED.name: "red",
}


@dataclass
class TestStepRecord:
    status: atsut._StatusCode
    log: str
    output: list
    number: int
    elapsed: float


@dataclass
class TestCaseRecord:
    steps: dict
    status: atsut._StatusCode
    previous_status: atsut._StatusCode
    test_number: int
    elapsed: float
    current_step: str
    resources: int


@dataclass
class TestGroupRecord:
    tests: list
    status: atsut._StatusCode


def max_status( sa, sb ):
    Ia = STATUS.index( sa )
    Ib = STATUS.index( sb )
    return STATUS[ max( Ia, Ib ) ]


class ReportBase( object ):
    """Base class for reporting"""

    def __init__( self, test_steps ):
        self.test_results = {}
        self.test_groups = {}
        self.status_lists = {}

        for t in test_steps:
            # Parse the test step name
            step_name = t.name[ t.name.find( '(' ) + 1:t.name.rfind( '_' ) ]
            test_name = step_name[ :step_name.rfind( '_' ) ]
            test_id = t.group.number
            group_name = test_name[ :test_name.rfind( '_' ) ]

            # Save data
            if test_name not in self.test_results:
                self.test_results[ test_name ] = TestCaseRecord( steps={},
                                                                 status=EXPECTED,
                                                                 previous_status=t.options[ 'last_status' ],
                                                                 test_number=test_id,
                                                                 elapsed=0.0,
                                                                 current_step=' ',
                                                                 resources=t.np )

            # Check elapsed time
            elapsed = 0.0
            if hasattr( t, 'endTime' ):
                elapsed = t.endTime - t.startTime
            self.test_results[ test_name ].elapsed += elapsed

            # Add the step
            self.test_results[ test_name ].steps[ t.name ] = TestStepRecord( status=t.status,
                                                                             log=t.outname,
                                                                             output=t.step_outputs,
                                                                             number=t.groupSerialNumber,
                                                                             elapsed=elapsed )

            # Check the status and the latest step
            if self.test_results[ test_name ].previous_status == PASSED:
                self.test_results[ test_name ].status = PASSED
            else:
                self.test_results[ test_name ].status = max_status( t.status, self.test_results[ test_name ].status )

            if t.status not in ( EXPECTED, CREATED, BATCHED, FILTERED, SKIPPED ):
                self.test_results[ test_name ].current_step = t.name

            if group_name not in self.test_groups:
                self.test_groups[ group_name ] = TestGroupRecord( tests=[], status=EXPECTED )
            self.test_groups[ group_name ].tests.append( test_name )
            self.test_groups[ group_name ].status = max_status( t.status, self.test_groups[ group_name ].status )

        # Collect status names
        for s in STATUS:
            self.status_lists[ s.name ] = [ k for k, v in self.test_results.items() if v.status == s ]

        self.html_filename = config.report_html_file


class ReportIni( ReportBase ):
    """Minimal reporting class"""

    def report( self, fp ):
        configParser = ConfigParser()

        configParser.add_section( "Info" )
        configParser.set( "Info", "Time", time.strftime( "%a, %d %b %Y %H:%M:%S" ) )
        try:
            platform = socket.gethostname()
        except Exception as e:
            logger.debug( str( e ) )
            logger.debug( "Could not get host name" )
            platform = "unknown"
        configParser.set( "Info", "Platform", platform )

        extraNotations = ""
        for line in config.report_notations:
            line_split = line.split( ":" )
            if len( line_split ) != 2:
                line_split = line.split( "=" )
            if len( line_split ) != 2:
                extraNotations += "\"" + line.strip() + "\""
                continue
            configParser.set( "Info", line_split[ 0 ].strip(), line_split[ 1 ].strip() )
        if extraNotations != "":
            configParser.set( "Info", "Extra Notations", extraNotations )

        configParser.add_section( "Results" )
        for k, v in self.status_lists.items():
            configParser.set( "Results", k, ";".join( sorted( v ) ) )

        configParser.write( fp )


class ReportHTML( ReportBase ):
    """HTML Reporting"""

    def report( self, refresh=0 ):
        sp = open( self.html_filename, 'w' )
        self.writeHeader( sp, refresh )
        self.writeSummary( sp )
        self.writeTable( sp )
        self.writeFooter( sp )
        sp.close()

    def writeHeader( self, sp, refresh ):
        gentime = time.strftime( "%a, %d %b %Y %H:%M:%S" )
        header = """
        <html>
         <head>
        """

        if refresh:
            header += f'  <META HTTP-EQUIV="refresh" CONTENT="{refresh}">'

        header += f"""  <title>Test results - generated on {gentime} </title>
          <style type="text/css">
           th, td {{
            font-family: "New Century Schoolbook", Times, serif;
            font-size: smaller ;
            vertical-align: top;
            background-color: #EEEEEE ;
           }}
           body {{
            font-family: "New Century Schoolbook", Times, serif;
            font-size: medium ;
            background-color: #FFFFFF ;
           }}
           table {{
            empty-cells: hide;
           }}

           .lightondark1 {{
               background-color: #888888;
               color:            white;
               font-size:        x-large;
           }}
           .lightondark2 {{
               background-color: #888888;
               color:            white;
               font-size:        large;
           }}
           .lightondark3 {{
               background-color: #888888;
               color:            white;
               font-size:        medium;
           }}

           th,td {{ background-color:#EEEEEE }}
           td.probname {{ background-color: #CCCCCC; font-size: large ; text-align: center}}

           table {{
              font-family: arial, sans-serif;
              border-collapse: collapse;
            }}

            td {{
              border: 1px solid #dddddd;
              text-align: left;
              padding: 8px;
            }}

            th {{
              border: 1px solid #dddddd;
              background-color: #8f8f8f;
              text-align: left;
              padding: 8px;
            }}
          </style>
         </head>
        <body>
        """

        # Notations:
        try:
            platform = socket.gethostname()
        except Exception as e:
            logger.debug( str( e ) )
            logger.debug( "Could not get host name" )
            platform = "unknown"

        if os.name == "nt":
            username = os.getenv( "USERNAME" )
        else:
            username = os.getenv( "USER" )

        header += "<h1>GEOS ATS Report</h1>\n<h2>Configuration</h2>\n"
        table = [ [ 'Test Results', gentime ], [ 'User', username ], [ 'Platform', platform ] ]
        header += tabulate( table, tablefmt='html' )
        header += '\n'
        sp.write( header )

    def writeSummary( self, sp ):
        link_pattern = '<a href="#{}">{}</a>\n'
        color_pattern = "<p style=\"color: {};\"> {} </p>"
        header = [ 'Status', 'Count', 'Tests' ]
        table = []

        for k, v in self.status_lists.items():
            status_formatted = color_pattern.format( COLORS[ k ], k )
            test_links = [ link_pattern.format( t, t ) for t in v ]
            table.append( [ status_formatted, len( v ), ', '.join( test_links ) ] )

        sp.write( "\n\n<h1>Summary</h1>\n\n" )
        table_html = tabulate( table, headers=header, tablefmt='unsafehtml' )
        sp.write( table_html )

    def writeTable( self, sp ):
        header = ( "Status", "Name", "TestStep", "Elapsed", "Resources", "Output" )

        table = []
        table_filt = []
        file_pattern = "<a href=\"file://{}\">{}</a>"
        color_pattern = "<p style=\"color: {};\" id=\"{}\"> {} </p>"

        for k, v in self.test_results.items():
            status_str = v.status.name
            status_formatted = color_pattern.format( COLORS[ status_str ], k, status_str )
            step_shortname = v.current_step
            elapsed_formatted = hms( v.elapsed )
            output_files = []
            for s in v.steps.values():
                if os.path.isfile( s.log ):
                    output_files.append( file_pattern.format( s.log, os.path.basename( s.log ) ) )
                if os.path.isfile( s.log + '.err' ):
                    output_files.append( file_pattern.format( s.log + '.err', os.path.basename( s.log + '.err' ) ) )
                for pattern in s.output:
                    for f in sorted( glob.glob( pattern ) ):
                        if ( ( 'restart' not in f ) or ( '.restartcheck' in f ) ) and os.path.isfile( f ):
                            output_files.append( file_pattern.format( f, os.path.basename( f ) ) )

            row = [ status_formatted, k, step_shortname, elapsed_formatted, v.resources, ', '.join( output_files ) ]
            if status_str == 'FILTERED':
                table_filt.append( row )
            else:
                table.append( row )

        if len( table ):
            sp.write( "\n\n<h1>Active Tests</h1>\n\n" )
            table_html = tabulate( table, headers=header, tablefmt='unsafehtml' )
            sp.write( table_html )

        if len( table_filt ):
            sp.write( "\n\n<h1>Filtered Tests</h1>\n\n" )
            table_html = tabulate( table_filt, headers=header, tablefmt='unsafehtml' )
            sp.write( table_html )

    def writeFooter( self, sp ):
        footer = """
         </body>
        </html>
        """
        sp.write( footer )
