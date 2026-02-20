# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging
from pathlib import Path
import numpy as np
from typing_extensions import Self

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smdomain, smproperty  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths
from geos.pv.utils.details import ( SISOFilter, FilterCategory )

update_paths()

from geos.utils.Errors import VTKError
from geos.utils.Logger import ( CountVerbosityHandler, isHandlerInLogger, getLoggerHandlerType )
from geos.utils.PhysicalConstants import ( DEFAULT_FRICTION_ANGLE_DEG, DEFAULT_ROCK_COHESION )
from geos.processing.post_processing.SurfaceGeomechanics import SurfaceGeomechanics
from geos.mesh.utils.multiblockHelpers import ( getBlockElementIndexesFlatten, getBlockFromFlatIndex )

from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkPolyData

__doc__ = f"""
PVSurfaceGeomechanics is a Paraview plugin that allows to compute
additional geomechanical attributes from the input surfaces, such as shear capacity utilization (SCU).

Input and output are vtkMultiBlockDataSet.

.. Important::

    - Please refer to the :ref:`GEOS Extract and Merge Blocks <PVGeosBlockExtractAndMerge_plugin>` plugin to provide the correct input.
    - This filter only works on triangles at the moment. Please apply a triangulation algorithm beforehand if required.


To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/post_processing/PVSurfaceGeomechanics
* Select any pipeline child "Fault" from "GEOS Extract and Merge Blocks" plugin
* Select the filter: Filters > { FilterCategory.GENERIC_PROCESSING.value } > GEOS Surface Geomechanics
* (Optional) Set rock cohesion and/or friction angle
* Apply

"""

loggerTitle: str = "Surface Geomechanics"


@SISOFilter( category=FilterCategory.GEOS_POST_PROCESSING,
             decoratedLabel="GEOS Surface Geomechanics",
             decoratedType="vtkMultiBlockDataSet" )
class PVSurfaceGeomechanics( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Compute additional geomechanical surface outputs.

        Input is a vtkMultiBlockDataSet containing surfaces.
        """
        # rock cohesion (Pa)
        self.rockCohesion: float = DEFAULT_ROCK_COHESION
        # friction angle (°)
        self.frictionAngle: float = DEFAULT_FRICTION_ANGLE_DEG

        self.handler: logging.Handler = VTKHandler()
        self.logger = logging.getLogger( loggerTitle )
        self.logger.setLevel( logging.INFO )
        self.logger.addHandler( self.handler )
        self.logger.propagate = False

        counter: CountVerbosityHandler = CountVerbosityHandler()
        self.counter: CountVerbosityHandler
        self.nbWarnings: int = 0
        self.nbErrors: int = 0
        try:
            self.counter = getLoggerHandlerType( type( counter ), self.logger )
            self.counter.resetWarningCount()
            self.counter.resetErrorCount()
        except ValueError:
            self.counter = counter
            self.counter.setLevel( logging.INFO )

        self.logger.addHandler( self.counter )

    @smproperty.doublevector(
        name="RockCohesion",
        label="Rock Cohesion (Pa)",
        default_values=DEFAULT_ROCK_COHESION,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            Reference rock cohesion to compute critical pore pressure.
            The unit is Pa. Default is fractured case (i.e., 0. Pa).
        </Documentation>
            """ )
    def a01SetRockCohesion( self: Self, value: float ) -> None:
        """Set rock cohesion.

        Args:
            value (float): rock cohesion (Pa)
        """
        self.rockCohesion = value
        self.Modified()

    @smproperty.doublevector(
        name="FrictionAngle",
        label="Friction Angle (°)",
        default_values=DEFAULT_FRICTION_ANGLE_DEG,
        panel_visibility="default",
    )
    @smdomain.xml( """
                    <Documentation>
                        Reference friction angle to compute critical pore pressure.
                        The unit is °. Default is no friction case (i.e., 0.°).
                    </Documentation>
                  """ )
    def a02SetFrictionAngle( self: Self, value: float ) -> None:
        """Set friction angle.

        Args:
            value (float): friction angle (°)
        """
        self.frictionAngle = value
        self.Modified()

    def ApplyFilter( self: Self, inputMesh: vtkMultiBlockDataSet, outputMesh: vtkMultiBlockDataSet ) -> None:
        """Apply SurfaceGeomechanics filter to the mesh.

        Args:
            inputMesh (vtkMultiBlockDataSet): The input multiblock mesh with surfaces.
            outputMesh (vtkMultiBlockDataSet): The output multiblock mesh with converted attributes and SCU.
        """
        self.logger.info( f"Apply plugin { self.logger.name }." )

        outputMesh.ShallowCopy( inputMesh )
        try:
            surfaceBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( inputMesh )
            for blockIndex in surfaceBlockIndexes:
                surfaceBlock: vtkPolyData = vtkPolyData.SafeDownCast( getBlockFromFlatIndex( outputMesh, blockIndex ) )

                loggerName: str = f"Surface geomechanics for the blockIndex { blockIndex }"
                sgFilter: SurfaceGeomechanics = SurfaceGeomechanics( surfaceBlock, loggerName, True )

                if not isHandlerInLogger( self.handler, sgFilter.logger ):
                    sgFilter.SetLoggerHandler( self.handler )

                sgFilter.SetRockCohesion( self._getRockCohesion() )
                sgFilter.SetFrictionAngle( self._getFrictionAngle() )

                try:
                    sgFilter.applyFilter()
                    # Add to the warning counter the number of warning logged with the call of SurfaceGeomechanics filter
                    self.counter.addExternalWarningCount( sgFilter.nbWarnings )

                    outputSurface: vtkPolyData = sgFilter.GetOutputMesh()

                    # add attributes to output surface mesh
                    for attributeName in sgFilter.GetNewAttributeNames():
                        attr: vtkDataArray = outputSurface.GetCellData().GetArray( attributeName )
                        surfaceBlock.GetCellData().AddArray( attr )
                        surfaceBlock.GetCellData().Modified()
                    surfaceBlock.Modified()
                except ( ValueError, VTKError, AttributeError, AssertionError ) as e:
                    sgFilter.logger.error( f"The filter { loggerName } failed due to:\n{ e }" )
                    raise ChildProcessError( f"Error during the processing of: { loggerName }." )
                except Exception as e:
                    mess: str = f"The filter { loggerName } failed due to:\n{ e }"
                    sgFilter.logger.critical( mess, exc_info=True )
                    raise ChildProcessError( f"Critical error during the processing of: { loggerName }." )

            result: str = f"The plugin { self.logger.name } succeeded"
            if self.counter.warningCount > 0:
                self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
            else:
                self.logger.info( f"{ result }." )

        except ChildProcessError as e:
            self.logger.error( f"The plugin { self.logger.name } failed due to:\n{ e }" )
        except Exception as e:
            mess = f"The plugin { self.logger.name } failed due to:\n{ e }"
            self.logger.critical( mess, exc_info=True )

        outputMesh.Modified()
        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        self.nbErrors = self.counter.errorCount
        self.counter.resetErrorCount()

        return

    def _getFrictionAngle( self: Self ) -> float:
        """Get friction angle in radian.

        Returns:
            float: The friction angle.
        """
        return self.frictionAngle * np.pi / 180.0

    def _getRockCohesion( self: Self ) -> float:
        """Get rock cohesion.

        Returns:
            float: rock cohesion.
        """
        return self.rockCohesion
