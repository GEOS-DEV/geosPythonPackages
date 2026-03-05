# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import os
import logging
from typing_extensions import Self

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkUnstructuredGrid

from geos.mesh.utils.multiblockModifiers import ( mergeBlocks )
from geos.mesh.io.vtkIO import ( PVDReader, createPVD, writeMesh, VtkOutput )

from geos.processing.tools.FaultGeometry import ( FaultGeometry )
from geos.processing.tools.FaultVisualizer import ( Visualizer )
from geos.processing.tools.MohrCoulomb import ( MohrCoulombAnalysis )
from geos.processing.tools.SensitivityAnalyzer import ( SensitivityAnalyzer )
from geos.processing.tools.StressProjector import ( StressProjector, StressProjectorWeightingScheme )

from geos.utils.GeosOutputsConstants import ( GeosMeshOutputsEnum, PostProcessingOutputsEnum )
from geos.utils.Logger import ( getLogger, Logger, CountVerbosityHandler, isHandlerInLogger, getLoggerHandlerType )

__doc__ = """
FaultStabilityAnalysis is a vtk filter that performs an analysis of requested faults in a mesh for several timesteps of simulation.

The pre-simulation mesh containing a fault mask attribute is required to identify the faults.


To use it:

.. code-block:: python

    from geos.processing.post_processing.FaultStabilityAnalysis import FaultStabilityAnalysis

    # Filter inputs.
    inputMesh: vtkDataSet
    faultAttribute: str
    faultValues: list[int]
    pvdFile: str
    speHandler: bool

    # Instantiate the filter
    faultStabilityFilter = FaultStabilityAnalysis( inputMesh, faultAttribute, faultValues, pvdFile, speHandler )

    # Set parameters [optional]

    faultStabilityFilter.setStressName( stressName: str )
    faultStabilityFilter.setBiotCoefficientName( biotName: str )
    faultStabilityFilter.setSensitivityFrictionAngles( list[ float ] )
    faultStabilityFilter.setSensitivityCohesions( list[ float] )
    faultStabilityFilter.setProfileStartPoints( list[ tuple[ np.float64, np.float64, np.float64 ] ] )

    # Set your handler (only if speHandler is True).
    yourHandler: logging.Handler
    faultStabilityFilter.addLoggerHandler( yourHandler )

    # Do calculations
    try:
        faultStabilityFilter.applyFilter()
    except Exception as e:
        mess: str = f"The filter { faultStabilityFilter.logger.name } failed due to: { e }"
        faultStabilityFilter.logger.error( mess, exc_info=True )
"""

loggerTitle: str = "Fault Stability Analysis"


class FaultStabilityAnalysis:

    def __init__(
        self: Self,
        inputMesh: vtkDataSet,
        faultAttribute: str,
        faultValues: list[ int | float ],
        pvdFile: str,
        speHandler: bool = False,
    ) -> None:
        """Fault stability analysis workflow.

        Args:
            inputMesh (vtkDataSet): Pre-simulation mesh
            faultValues (list[ int | float ]): Fault attribute values to consider
            faultAttribute (str): Fault attribute name in the initial mesh
            volumeMeshInitial( vtkDataSet): Output mesh for time t=0
            pvdFile (str): GEOS output PVD filename
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                    Defaults to False.
        """
        self.pvdFile = pvdFile
        self.timeIndexes: list[ int ] | None = None

        self.outputDir: str = "FaultStabilityAnalysis/"

        # Mechanical parameters
        self.frictionAngle: float = 12  # [degrees]
        self.cohesion: float = 0  # [bar]

        # Normal orientation: Rotate normals and tangents from 180°
        self.rotateNormals: bool = False

        # Visualization
        self.savePlots: bool = True
        self.zscale: float = 1.0

        self.nDepthProfiles = 1  # Nombre de lignes verticales
        self.minDepthProfiles = None
        self.maxDepthProfiles = None
        self.saveContributionCells = True  # Save vtu contributive cells
        self.weightingScheme: StressProjectorWeightingScheme = StressProjectorWeightingScheme.ARITHMETIC

        self.computePrincipalStresses = False
        self.profileStartPoints: list[ tuple[ float, float ] ] = []
        self.profileSearchRadius = None

        # Sensitivity analysis
        self.runSensitivity: bool = True
        self.sensitivityFrictionAngles: list[ float ] = []  # degrees
        self.sensitivityCohesions: list[ float ] = []  # bar

        # Variable names
        self.stressName: str = GeosMeshOutputsEnum.AVERAGE_STRESS.value
        self.biotName: str = PostProcessingOutputsEnum.BIOT_COEFFICIENT.value

        # Faults attributes
        self.faultAttribute = faultAttribute
        self.faultValues = faultValues
        self.processFaultsSeparately: bool = True

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

        counter: CountVerbosityHandler = CountVerbosityHandler()
        self.counter: CountVerbosityHandler
        self.nbWarnings: int = 0
        try:
            self.counter = getLoggerHandlerType( type( counter ), self.logger )
            self.counter.resetWarningCount()
        except ValueError:
            self.counter = counter
            self.counter.setLevel( logging.INFO )

        self.logger.addHandler( self.counter )

        self.logger.info( "📐 Initialize fault geometry" )
        self.volumeMeshInitial = self._getInitialMesh()
        self.faultGeometry = FaultGeometry( inputMesh, faultValues, faultAttribute, self.volumeMeshInitial,
                                            self.outputDir, self.logger )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not isHandlerInLogger( handler, self.logger ):
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has this handler, it has not been added." )

    def _getInitialMesh( self: Self ) -> vtkUnstructuredGrid:
        """Get the mesh from timestep 0 in the PVD output file and merge the blocks."""
        reader = PVDReader( self.pvdFile )

        datasetT0 = reader.getDataSetAtTimeIndex( 0 )

        return mergeBlocks( datasetT0, keepPartialAttributes=True )

    def _initializeFaultGeometry( self: Self ) -> None:
        """Extract faults and compute geometric properties such as normals and adjacency topology."""
        self.logger.info( "🔧 Computing normals and adjacency topology" )
        self.faultGeometry.initialize( processFaultsSeparately=self.processFaultsSeparately,
                                       saveContributionCells=self.saveContributionCells )

    def processAllTimeIndexesRequested( self: Self ) -> None:
        """Process all time steps using pre-computed fault geometry.

        Returns:
            vtkUnstructuredGrid: Fault mesh.
        """
        self.logger.info( "Reading PVD file" )
        reader = PVDReader( self.pvdFile )
        timeValues = reader.getAllTimestepsValues()

        if self.timeIndexes:
            timeValues = timeValues[ self.timeIndexes ]

        outputFiles = []
        dataInitial = None

        # Get pre-computed data from faultGeometry
        surface = self.faultGeometry.faultSurface
        adjacencyMapping = self.faultGeometry.adjacencyMapping
        geometricProperties = self.faultGeometry.getGeometricProperties()

        # Initialize projector with pre-computed topology
        self.logger.info( "Initialize projector with pre-computed topology." )
        projector = StressProjector( adjacencyMapping, geometricProperties, self.outputDir )
        projector.setStressName( self.stressName )
        projector.setBiotCoefficientName( self.biotName )

        self.logger.info( "=" * 60 )
        self.logger.info( "TIME SERIES PROCESSING" )
        self.logger.info( "=" * 60 )

        for i, time in enumerate( timeValues ):
            self.logger.info( f"\n→ Step {i+1}/{len(timeValues)}: {time/(365.25*24*3600):.2f} years" )

            # Read time step
            idx = self.timeIndexes[ i ] if self.timeIndexes else i
            dataset = reader.getDataSetAtTimeIndex( idx )

            # Merge blocks
            volumeData = mergeBlocks( dataset, keepPartialAttributes=True )

            if dataInitial is None:
                dataInitial = volumeData

            # -----------------------------------
            # Projection using pre-computed topology
            # -----------------------------------
            # Projection
            surfaceResult, volumeMarked, contributingCells = projector.projectStressToFault(
                volumeData,
                dataInitial,
                surface,
                time=timeValues[ i ],  # Simulation time
                timestep=i,  # Timestep index
                weightingScheme=self.weightingScheme,
                computePrincipalStresses=self.computePrincipalStresses )

            # -----------------------------------
            # Mohr-Coulomb analysis
            # -----------------------------------
            cohesion = self.cohesion  # bar
            frictionAngle = self.frictionAngle  # degrees

            mc = MohrCoulombAnalysis( surfaceResult, cohesion, frictionAngle )
            surfaceResult = mc.analyze()

            # -----------------------------------
            # Visualize
            # -----------------------------------
            self._plotResults( surfaceResult, contributingCells, time )

            # -----------------------------------
            # Sensitivity analysis
            # -----------------------------------
            if self.runSensitivity:
                analyzer = SensitivityAnalyzer( self.outputDir )
                if self.sensitivityFrictionAngles is None or self.sensitivityCohesions is None:
                    raise ValueError(
                        "Sensitivity friction angles and cohesions required if runSensitivity is set to True" )
                analyzer.runAnalysis( surfaceResult, time, self.sensitivityFrictionAngles, self.sensitivityCohesions,
                                      self.profileStartPoints, self.profileSearchRadius )

            # Save
            filename = os.path.join( self.outputDir, f'fault_analysis_{i:04d}.vtu' )
            writeMesh( mesh=surfaceResult, vtkOutput=VtkOutput( filename ), canOverwrite=True )
            outputFiles.append( ( time, filename ) )
            self.logger.info( f"  💾 Saved: {filename}" )

        # Create master PVD
        createPVD( self.outputDir, outputFiles )

        return surfaceResult

    def applyFilter( self: Self ) -> None:
        """Analyze the stability of the fault for all timesteps requested."""
        self._initializeFaultGeometry()
        self.processAllTimeIndexesRequested()

        result: str = f"The filter { self.logger.name } succeeded"
        if self.counter.warningCount > 0:
            self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
        else:
            self.logger.info( f"{ result }." )

        # Keep number of warnings logged during the filter application and reset the warnings count in case the filter is applied again.
        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        return

    def _plotResults( self: Self, surface: vtkUnstructuredGrid, contributingCells: vtkUnstructuredGrid,
                      time: float ) -> None:
        """Plot and save results for one timestep.

        Args:
            surface (vtkUnstructuredGrid): Fault mesh.
            contributingCells (vtkUnstructuredGrid): Cells contributing to the fault.
            time (float): Time
        """
        Visualizer( self.profileSearchRadius, self.minDepthProfiles, self.maxDepthProfiles,
                    savePlots=self.savePlots ).plotMohrCoulombDiagram(
                        surface,
                        time,
                        self.outputDir,
                        save=self.savePlots,
                    )

        visualizer = Visualizer( self.profileSearchRadius,
                                 self.minDepthProfiles,
                                 self.maxDepthProfiles,
                                 savePlots=self.savePlots )

        if self.computePrincipalStresses:
            # Plot principal stress from volume cells
            visualizer.plotVolumeStressProfiles( volumeMesh=contributingCells,
                                                 faultSurface=surface,
                                                 time=time,
                                                 path=self.outputDir,
                                                 profileStartPoints=self.profileStartPoints )

            # Visualize comparison analytical/numerical
            visualizer.plotAnalyticalVsNumericalComparison( volumeMesh=contributingCells,
                                                            faultSurface=surface,
                                                            time=time,
                                                            path=self.outputDir,
                                                            save=self.savePlots,
                                                            profileStartPoints=self.profileStartPoints )

    def setSensitivityFrictionAngles( self: Self, angles: list[ float ] ) -> None:
        """Set the friction angles for sensitivy analysis."""
        self.sensitivityFrictionAngles = angles

    def setSensitivityCohesions( self: Self, cohesions: list[ float ] ) -> None:
        """Set the cohesions for sensitivy analysis."""
        self.sensitivityCohesions = cohesions

    def setOutputDirectory( self: Self, outputDir: str ) -> None:
        """Set the saving output directory.

        Args:
            outputDir (str): Output directory
        """
        if outputDir != "None":
            self.outputDir = outputDir

    def savePlotsOff( self: Self ) -> None:
        """Switch off plot saving option."""
        self.savePlots = False

    def savePlotsOn( self: Self ) -> None:
        """Switch on plot saving option."""
        self.savePlots = True

    def setStressName( self: Self, stressName: str ) -> None:
        """Set the stress attribute name.

        Args:
            stressName (str): Stress attribute name in the input mesh.
        """
        if stressName != "None":
            self.stressName = stressName

    def setBiotCoefficientName( self: Self, biotName: str ) -> None:
        """Set the stress attribute name.

        Args:
            biotName (str): Biot coefficient attribute name in the input mesh.
        """
        if biotName != "None":
            self.biotName = biotName

    def setProfileStartPoints( self: Self, startPoints: list[ tuple[ float, float ] ] ) -> None:
        """Set the profile start points.

        Args:
            startPoints (list[tuple[np.float64, np.float64, np.float64]]): List of starting points coordinates.
        """
        self.profileStartPoints = startPoints
