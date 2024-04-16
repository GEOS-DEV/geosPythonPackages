import ats  # type: ignore[import]
import os
import shutil
import logging
import glob
import inspect
from configparser import ConfigParser
from ats import atsut
from ats import ( PASSED, FAILED, FILTERED, SKIPPED )
from geos_ats.common_utilities import Error, Log, removeLogDirectories
from geos_ats.configuration_record import config, globalTestTimings

test = ats.manager.test
testif = ats.manager.testif
logger = logging.getLogger( 'geos_ats' )

all_test_names = []


class Batch( object ):
    """A class to represent batch options"""

    def __init__( self, enabled=True, duration="1h", ppn=0, altname=None ):

        if enabled not in ( True, False ):
            Error( "enabled must be a boolean" )

        self.enabled = enabled
        self.duration = duration

        try:
            dur = ats.Duration( duration )
            self.durationSeconds = dur.value
        except ats.AtsError as e:
            logger.error( e )
            Error( "bad time specification: %s" % duration )

        self.ppn = ppn  # processor per node
        self.altname = altname  # alternate name to use when launcing the batch job


class TestCase( object ):
    """Encapsulates one test case, which may include many steps"""

    def __init__( self, name, desc, label=None, labels=None, steps=[], **kw ):

        try:
            self.initialize( name, desc, label, labels, steps, **kw )
        except Exception as e:
            # make sure error messages get logged, then get out of here.
            logging.error( e )
            Log( str( e ) )
            raise Exception( e )

    def initialize( self, name, desc, label=None, labels=None, steps=[], batch=Batch( enabled=False ), **kw ):
        # Check for duplicate tests
        if name in all_test_names:
            raise Exception( f'Found multiple tests with the same name ({name})' )
        all_test_names.append( name )

        # Setup the test
        self.name = name
        self.desc = desc
        self.batch = batch

        # Identify the location of the ats test file
        ats_root_dir = ats.tests.AtsTest.getOptions().get( "atsRootDir" )
        self.dirname = ''
        for s in inspect.stack():
            if ats_root_dir in s.filename:
                self.dirname = os.path.dirname( s.filename )
                break

        if not self.dirname:
            logger.warning( 'Could not find the proper test location... defaulting to current dir' )
            self.dirname = os.getcwd()

        # Setup paths
        log_dir = ats.tests.AtsTest.getOptions().get( "logDir" )
        working_relpath = os.path.relpath( self.dirname, ats_root_dir )
        working_root = ats.tests.AtsTest.getOptions().get( "workingDir" )
        working_dir = os.path.abspath( os.path.join( working_root, working_relpath, self.name ) )

        baseline_relpath = working_relpath
        baseline_root = ats.tests.AtsTest.getOptions().get( "baselineDir" )
        baseline_directory = os.path.abspath( os.path.join( baseline_root, baseline_relpath, self.name ) )

        self.path = working_relpath

        try:
            os.makedirs( working_dir, exist_ok=True )
        except OSError as e:
            logger.debug( e )
            raise Exception()

        # Setup other parameters
        self.dictionary = {}
        self.dictionary.update( kw )
        self.nodoc = self.dictionary.get( "nodoc", False )
        self.last_status = None
        self.dictionary[ "name" ] = self.name
        self.dictionary[ "test_directory" ] = self.dirname
        self.dictionary[ "output_directory" ] = working_dir
        self.dictionary[ "baseline_directory" ] = baseline_directory
        self.dictionary[ "log_directory" ] = log_dir
        self.dictionary[ "testcase_name" ] = self.name

        # Check for previous log information
        log_file = os.path.join( log_dir, 'test_results.ini' )
        if os.path.isfile( log_file ):
            previous_config = ConfigParser()
            previous_config.read( log_file )
            for k, v in previous_config[ 'Results' ].items():
                if self.name in v.split( ';' ):
                    self.last_status = atsut.StatusCode( k.upper() )

        # check for independent
        if config.override_np > 0:
            # If number of processors is overridden, prevent independent
            # runs in same directory since some output files key on
            # number of processors.
            self.independent = False
        else:
            self.independent = self.dictionary.get( "independent", False )
        if self.independent not in ( True, False ):
            Error( "independent must be either True or False: %s" % str( self.independent ) )

        # check for depends
        self.depends = self.dictionary.get( "depends", None )
        if self.depends == self.name:
            # This check avoid testcases depending on themselves.
            self.depends = None

        # complete the steps.
        #  1. update the steps with data from the dictionary
        #  2. substeps are inserted into the list of steps (the steps are flattened)
        for step in steps:
            step.update( self.dictionary )

        self.steps = []
        for step in steps:
            step.insertStep( self.steps )

        # Check for explicit skip flag
        action = ats.tests.AtsTest.getOptions().get( "action" )
        if action in ( "run", "rerun", "continue" ):
            if self.dictionary.get( "skip", None ):
                self.status = SKIPPED
                return

        # Filtering tests on maxprocessors
        npMax = self.findMaxNumberOfProcessors()
        if config.filter_maxprocessors != -1:
            if npMax > config.filter_maxprocessors:
                Log( "# FILTER test=%s : max processors(%d > %d)" % ( self.name, npMax, config.filter_maxprocessors ) )
                self.status = FILTERED
                return

        # Filtering tests on maxGPUS
        ngpuMax = self.findMaxNumberOfGPUs()

        # filter based on not enough resources
        if action in ( "run", "rerun", "continue" ):
            tests = [
                not ats.tests.AtsTest.getOptions().get( "testmode" ), not self.batch.enabled,
                hasattr( ats.manager.machine, "getNumberOfProcessors" )
            ]
            if all( tests ):

                totalNumberOfProcessors = getattr( ats.manager.machine, "getNumberOfProcessors" )()
                if npMax > totalNumberOfProcessors:
                    Log( "# SKIP test=%s : not enough processors to run (%d > %d)" %
                         ( self.name, npMax, totalNumberOfProcessors ) )
                    self.status = SKIPPED
                    return

                # If the machine doesn't specify a number of GPUs then it has none.
                totalNumberOfGPUs = getattr( ats.manager.machine, "getNumberOfGPUS", lambda: 1e90 )()
                if ngpuMax > totalNumberOfGPUs:
                    Log( "# SKIP test=%s : not enough gpus to run (%d > %d)" %
                         ( self.name, ngpuMax, totalNumberOfGPUs ) )
                    self.status = SKIPPED
                    return

        # filtering test steps based on action
        if action in ( "run", "rerun", "continue" ):
            checkoption = ats.tests.AtsTest.getOptions().get( "checkoption" )
            if checkoption == "none":
                self.steps = [ step for step in self.steps if not step.isCheck() ]
        elif action == "check":
            self.steps = [ step for step in self.steps if step.isCheck() ]

        # move all the delayed steps to the end
        reorderedSteps = []
        for step in self.steps:
            if not step.isDelayed():
                reorderedSteps.append( step )
        for step in self.steps:
            if step.isDelayed():
                reorderedSteps.append( step )
        self.steps = reorderedSteps

        # Perform the action:
        if action in ( "run", "continue" ):
            Log( "# run test=%s" % ( self.name ) )
            self.testCreate()

        elif action == "rerun":
            Log( "# rerun test=%s" % ( self.name ) )
            self.testCreate()

        elif action == "check":
            Log( "# check test=%s" % ( self.name ) )
            self.testCreate()

        elif action == "commands":
            self.testCommands()

        elif action == "clean":
            Log( "# clean test=%s" % ( self.name ) )
            self.testClean()

        elif action == "veryclean":
            Log( "# veryclean test=%s" % ( self.name ) )
            self.testVeryClean()

        elif action == "rebaseline":
            self.testRebaseline()

        elif action == "rebaselinefailed":
            self.testRebaselineFailed()

        elif action == "list":
            self.testList()

        else:
            Error( "Unknown action?? %s" % action )

    def logNames( self ):
        return sorted( glob.glob( os.path.join( self.dictionary[ "log_directory" ], f'*{self.name}_*' ) ) )

    def resultPaths( self, step=None ):
        """Return the paths to output files for the testcase.  Used in reporting"""
        paths = []
        if step:
            for x in step.resultPaths():
                fullpath = os.path.join( self.path, x )
                if os.path.exists( fullpath ):
                    paths.append( fullpath )

        return paths

    def cleanLogs( self ):
        for f in self.logNames():
            os.remove( f )

    def testClean( self ):
        self.cleanLogs()
        for step in self.steps:
            step.clean()

    def testVeryClean( self ):

        def _remove( path ):
            delpaths = glob.glob( path )
            for p in delpaths:
                if os.path.exists( p ):
                    try:
                        if os.path.isdir( p ):
                            shutil.rmtree( p )
                        else:
                            os.remove( p )
                    except OSError:
                        pass  # so that two simultaneous clean operations don't fail

        # clean
        self.testClean()
        # remove log directories
        removeLogDirectories( os.getcwd() )
        # remove extra files
        if len( self.steps ) > 0:
            _remove( config.report_html_file )
            _remove( self.path )
            _remove( "*.core" )
            _remove( "core" )
            _remove( "core.*" )
            _remove( "vgcore.*" )
            _remove( "*.btr" )
            _remove( "TestLogs*" )
            _remove( "*.ini" )

    def findMaxNumberOfProcessors( self ):
        npMax = 1
        for step in self.steps:
            np = getattr( step.p, "np", 1 )
            npMax = max( np, npMax )
        return npMax

    def findMaxNumberOfGPUs( self ):
        gpuMax = 0
        for step in self.steps:
            ngpu = getattr( step.p, "ngpu", 0 ) * getattr( step.p, "np", 1 )
            gpuMax = max( ngpu, gpuMax )
        return gpuMax

    def testCreate( self ):
        # Remove old logs
        self.cleanLogs()
        maxnp = 1
        for stepnum, step in enumerate( self.steps ):
            np = getattr( step.p, "np", 1 )
            maxnp = max( np, maxnp )

        if config.priority == "processors":
            priority = maxnp
        elif config.priority == "timing":
            priority = max( globalTestTimings.get( self.name, 1 ) * maxnp, 1 )
        else:
            priority = 1

        # Setup a new test group
        atsTest = None
        ats.tests.AtsTest.newGroup( priority=priority, path=self.path )
        for stepnum, step in enumerate( self.steps ):
            np = getattr( step.p, "np", 1 )
            ngpu = getattr( step.p, "ngpu", 0 )
            executable = step.executable()
            args = step.makeArgs()
            label = "%s_%d_%s" % ( self.name, stepnum + 1, step.label() )

            # call either 'test' or 'testif'
            if atsTest is None:
                func = lambda *a, **k: test( *a, **k )
            else:
                func = lambda *a, **k: testif( atsTest, *a, **k )

            # Set the time limit
            kw = {}
            if self.batch.enabled:
                kw[ "timelimit" ] = self.batch.duration
            if ( step.timelimit() and not config.override_timelimit ):
                kw[ "timelimit" ] = step.timelimit()
            else:
                kw[ "timelimit" ] = config.default_timelimit

            atsTest = func( executable=executable,
                            clas=args,
                            np=np,
                            ngpu=ngpu,
                            label=label,
                            serial=( not step.useMPI() and not config.script_launch ),
                            independent=self.independent,
                            batch=self.batch.enabled,
                            **kw )
            atsTest.step_outputs = step.resultPaths()

        # End the group
        ats.tests.AtsTest.endGroup()

    def commandLine( self, step ):
        args = []
        executable = step.executable()
        commandArgs = step.makeArgs()
        assert isinstance( commandArgs, list )
        for a in commandArgs:
            if " " in a:
                args.append( '"%s"' % a )
            else:
                args.append( a )

        argsstr = " ".join( args )
        return executable + " " + argsstr

    def testCommands( self ):
        Log( "\n# commands test=%s" % ( self.name ) )
        for step in self.steps:
            np = getattr( step.p, "np", 1 )
            usempi = step.useMPI()
            stdout = getattr( step.p, "stdout", None )
            commandline = self.commandLine( step ).replace( '%%', '%' )
            if stdout:
                Log( "np=%d %s > %s" % ( np, commandline, stdout ) )
            else:
                Log( "np=%d %s" % ( np, commandline ) )

    def testRebaseline( self ):
        rebaseline = True
        if config.rebaseline_ask:
            while 1:
                if config.rebaseline_undo:
                    logger.info( f"Are you sure you want to undo the rebaseline for TestCase '{self.name}'?" )
                else:
                    logger.info( f"Are you sure you want to rebaseline TestCase '{self.name}'?" )

                x = input( '[y/n] ' )
                x = x.strip()
                if x == "y":
                    break
                if x == "n":
                    rebaseline = False
                    break
        else:
            Log( "\n# rebaseline test=%s" % ( self.name ) )

        if rebaseline:
            for step in self.steps:
                step.rebaseline()

    def testRebaselineFailed( self ):
        config.rebaseline_ask = False
        if self.last_status == FAILED:
            self.testRebaseline()

    def testList( self ):
        Log( "# test=%s : labels=%s" % ( self.name.ljust( 32 ), " ".join( self.labels ) ) )


# Make available to the tests
ats.manager.define( TestCase=TestCase )
ats.manager.define( Batch=Batch )
