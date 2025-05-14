# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys

import numpy as np
from typing_extensions import Self

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.dirname( dir_path )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

import PVplugins  # noqa: F401

from geos.utils.Logger import Logger, getLogger
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_DEG,
    DEFAULT_ROCK_COHESION,
)
from geos_posp.filters.SurfaceGeomechanics import SurfaceGeomechanics
from geos.mesh.utils.multiblockInspectorTreeFunctions import (
    getBlockElementIndexesFlatten,
    getBlockFromFlatIndex,
)
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkDataObject,
    vtkMultiBlockDataSet,
    vtkPolyData,
)

__doc__ = r"""
PVSurfaceGeomechanics is a Paraview plugin that allows to compute
additional geomechanical attributes from the input surfaces.

Input and output types are vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVSurfaceGeomechanics.
* Select any pipeline child of the second ouput from
    GeosExtractMergeBlocksVolumeSurface* filter.
* Search and Apply PVSurfaceGeomechanics Filter.

"""


@smproxy.filter( name="PVSurfaceGeomechanics", label="Geos Surface Geomechanics" )
@smhint.xml( '<ShowInMenu category="3- Geos Geomechanics"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkMultiBlockDataSet" ], composite_data_supported=True )
class PVSurfaceGeomechanics( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to compute additional geomechanical surface outputs.

        Input is either a vtkMultiBlockDataSet that contains surfaces with
        Normals and Tangential attributes.
        """
        super().__init__(
            nInputPorts=1,
            nOutputPorts=1,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkMultiBlockDataSet",
        )

        # rock cohesion (Pa)
        self.m_rockCohesion: float = DEFAULT_ROCK_COHESION
        # friction angle (°)
        self.m_frictionAngle: float = DEFAULT_FRICTION_ANGLE_DEG
        # logger
        self.m_logger: Logger = getLogger( "Surface Geomechanics Filter" )

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

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
        self.m_rockCohesion = value
        self.Modified()

    def getRockCohesion( self: Self ) -> float:
        """Get rock cohesion.

        Returns:
            float: rock cohesion.
        """
        return self.m_rockCohesion

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
        """Set frition angle.

        Args:
            value (float): friction angle (°)
        """
        self.m_frictionAngle = value
        self.Modified()

    def getFrictionAngle( self: Self ) -> float:
        """Get friction angle in radian.

        Returns:
            float: friction angle.
        """
        return self.m_frictionAngle * np.pi / 180.0

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkMultiBlockDataSet" )
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()  # noqa: F841
        outInfo = outInfoVec.GetInformationObject( 0 )  # noqa: F841
        return 1

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        self.m_logger.info( f"Apply filter {__name__}" )
        try:
            input0: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData( inInfoVec[ 0 ] )
            output: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )

            assert input0 is not None, "Input Surface is null."
            assert output is not None, "Output pipeline is null."

            output.ShallowCopy( input0 )
            self.computeSurfaceGeomecanics( input0, output )
            output.Modified()
            mess: str = ( "Surface geomechanics attributes calculation successfully ended." )
            self.m_logger.info( mess )
        except AssertionError as e:
            mess1: str = "Surface geomechanics attributes calculation failed due to:"
            self.m_logger.error( mess1 )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess0: str = "Surface geomechanics attributes calculation failed due to:"
            self.m_logger.critical( mess0 )
            self.m_logger.critical( e, exc_info=True )
            return 0
        return 1

    def computeSurfaceGeomecanics( self: Self, input: vtkMultiBlockDataSet, output: vtkMultiBlockDataSet ) -> None:
        """Compute surface geomechanics new attributes.

        Args:
            input (vtkMultiBlockDataSet): input multiBlockDataSet
            output (vtkMultiBlockDataSet): output multiBlockDataSet
        """
        surfaceBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( input )
        for blockIndex in surfaceBlockIndexes:
            surfaceBlock0: vtkDataObject = getBlockFromFlatIndex( output, blockIndex )
            assert surfaceBlock0 is not None, "Surface is undefined."
            surfaceBlock: vtkPolyData = vtkPolyData.SafeDownCast( surfaceBlock0 )
            filter: SurfaceGeomechanics = SurfaceGeomechanics()
            filter.AddInputDataObject( surfaceBlock )
            filter.SetRockCohesion( self.getRockCohesion() )
            filter.SetFrictionAngle( self.getFrictionAngle() )
            filter.Update()
            outputSurface: vtkPolyData = filter.GetOutputDataObject( 0 )

            # add attributes to output surface mesh
            for attributeName in filter.GetNewAttributeNames():
                attr: vtkDataArray = outputSurface.GetCellData().GetArray( attributeName )
                surfaceBlock.GetCellData().AddArray( attr )
                surfaceBlock.GetCellData().Modified()
            surfaceBlock.Modified()
        output.Modified()
