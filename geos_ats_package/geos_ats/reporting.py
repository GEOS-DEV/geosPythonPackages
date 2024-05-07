import os
import socket
import time
from geos_ats.configuration_record import config
from geos_ats import assets
from configparser import ConfigParser
from tabulate import tabulate
import glob
import logging
import shutil
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
    path: str


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
            group_path = os.path.join( '.', t.options[ 'path' ], test_name )

            # Save data
            if test_name not in self.test_results:
                self.test_results[ test_name ] = TestCaseRecord( steps={},
                                                                 status=EXPECTED,
                                                                 previous_status=t.options[ 'last_status' ],
                                                                 test_number=test_id,
                                                                 elapsed=0.0,
                                                                 current_step=' ',
                                                                 resources=t.np,
                                                                 path=group_path )

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
        self.html_dir = os.path.dirname( self.html_filename )
        self.html_data_name = 'test_data'
        self.html_data = os.path.join( self.html_dir, self.html_data_name )
        os.makedirs( self.html_data, exist_ok=True )

        self.html_assets = 'html_assets'
        assets.create_assets_folder( os.path.join( self.html_dir, self.html_assets ) )

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
        header += f"""  <title>GEOS ATS Results</title>
          <script src="./{self.html_assets}/sorttable.js"></script>
          <link rel="stylesheet" href="./{self.html_assets}/style.css">
          <link rel="stylesheet" href="./{self.html_assets}/lightbox/lightbox2-2.11.4/dist/css/lightbox.css">
          <script src="./{self.html_assets}/lightbox/lightbox2-2.11.4/dist/js/lightbox-plus-jquery.js"></script>
         </head>
        <body>
        <div id="banner"><div id="banner-content"><h1>GEOS ATS Report</h1></div></div>
        </br></br></br>
        <h2>Configuration</h2>
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
        table_html = table_html.replace( '<table>', f'<table class="sortable">' )
        sp.write( table_html )

    def writeTable( self, sp ):
        header = ( "Status", "Name", "TestStep", "Elapsed", "Resources", "Logs", "Output" )

        table = []
        table_filt = []
        file_pattern = "<a href=\"{}\">{}</a>"
        image_pattern = "<a href=\"{}\" data-lightbox=\"curvecheck\" data-title=\"{}\">{}</a>"
        color_pattern = "<p style=\"color: {};\" id=\"{}\"> {} </p>"

        for k, v in self.test_results.items():
            status_str = v.status.name
            status_formatted = color_pattern.format( COLORS[ status_str ], k, status_str )
            step_shortname = v.current_step[ v.current_step.rfind( '_' ) + 1:-1 ]
            elapsed_formatted = hms( v.elapsed )

            # Collect files to include in the table
            output_files = []
            for s in v.steps.values():
                for f in [ s.log, s.log + '.err' ]:
                    if os.path.isfile( f ):
                        output_files.append( f )
                for pattern in s.output:
                    for f in sorted( glob.glob( pattern ) ):
                        if ( 'restart' not in f ):
                            output_files.append( f )

            # Copy files and build links
            if output_files:
                os.makedirs( os.path.join( self.html_data, v.path ), exist_ok=True )

            log_links = []
            other_links = []
            for f in output_files:
                base_fname = os.path.basename( f )
                copy_fname = os.path.join( self.html_data, v.path, base_fname )
                link_fname = os.path.join( '.', self.html_data_name, v.path, base_fname )
                output_fname = base_fname
                if ( '.log' in output_fname ):
                    log_index = base_fname[ :base_fname.find( '.' ) ]
                    log_type = ''.join( base_fname.split( '_' )[ -2: ] )
                    output_fname = f'{log_index}_{log_type}'

                shutil.copyfile( f, copy_fname )
                if os.stat( f ).st_size:
                    if '.log' in output_fname:
                        log_links.append( file_pattern.format( link_fname, output_fname ) )
                    elif '.png' in output_fname:
                        image_caption = os.path.join( k, output_fname[ :-4 ] )
                        other_links.append( image_pattern.format( link_fname, image_caption, output_fname ) )
                    else:
                        other_links.append( file_pattern.format( link_fname, output_fname ) )

            # Write row
            row = [
                status_formatted,
                k.replace( '_', ' ' ), step_shortname, elapsed_formatted, v.resources, ', '.join( log_links ),
                ', '.join( other_links )
            ]
            if status_str == 'FILTERED':
                table_filt.append( row )
            else:
                table.append( row )

        if len( table ):
            sp.write( "\n\n<h1>Active Tests</h1>\n\n" )
            table_html = tabulate( table, headers=header, tablefmt='unsafehtml' )
            table_html = table_html.replace( '<table>', '<table class="sortable">' )
            sp.write( table_html )

        if len( table_filt ):
            sp.write( "\n\n<h1>Filtered Tests</h1>\n\n" )
            table_html = tabulate( table_filt, headers=header, tablefmt='unsafehtml' )
            table_html = table_html.replace( '<table>', '<table class="sortable">' )
            sp.write( table_html )

    def writeFooter( self, sp ):
        footer = """
         </body>
        </html>
        """
        sp.write( footer )
