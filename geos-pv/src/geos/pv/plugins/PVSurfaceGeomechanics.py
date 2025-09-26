# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
import numpy as np
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_DEG,
    DEFAULT_ROCK_COHESION,
)
from geos.processing.post_processing.SurfaceGeomechanics import SurfaceGeomechanics
from geos.mesh.utils.multiblockHelpers import (
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
    vtkMultiBlockDataSet,
    vtkPolyData,
)

__doc__ = """
PVSurfaceGeomechanics is a Paraview plugin that allows to compute
additional geomechanical attributes from the input surfaces, such as shear capacity utilization (SCU).

Input and output are vtkMultiBlockDataSet.
.. Important::
    Please refer to the GeosExtractMergeBlockVolumeSurface* filters to provide the correct input.


To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVSurfaceGeomechanics.
* Select any pipeline child of the second ouput from
    GeosExtractMergeBlocksVolumeSurface* filter.
* Select Filters > 3-Geos Geomechanics > Geos Surface Geomechanics.
* (Optional) Set rock cohesion and/or friction angle.
* Apply.

"""

@smproxy.filter( name="PVSurfaceGeomechanics", label="Geos Surface Geomechanics" )
@smhint.xml( '<ShowInMenu category="3- Geos Geomechanics"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkMultiBlockDataSet" ], composite_data_supported=True )
class PVSurfaceGeomechanics( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Compute additional geomechanical surface outputs.

        Input is a vtkMultiBlockDataSet that contains surfaces with
        Normals and Tangential attributes.
        """
        super().__init__(
            nInputPorts=1,
            nOutputPorts=1,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkMultiBlockDataSet",
        )
        # rock cohesion (Pa)
        self.rockCohesion: float = DEFAULT_ROCK_COHESION
        # friction angle (°)
        self.frictionAngle: float = DEFAULT_FRICTION_ANGLE_DEG

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
        """Set frition angle.

        Args:
            value (float): friction angle (°)
        """
        self.frictionAngle = value
        self.Modified()

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData( inInfoVec[ 0 ] )
        output: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )

        assert inputMesh is not None, "Input surface is null."
        assert output is not None, "Output pipeline is null."

        output.ShallowCopy( inputMesh )

        surfaceBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( inputMesh )
        for blockIndex in surfaceBlockIndexes:
            surfaceBlock: vtkPolyData = vtkPolyData.SafeDownCast( getBlockFromFlatIndex( output, blockIndex ) )

            filter: SurfaceGeomechanics = SurfaceGeomechanics( surfaceBlock, True )
            filter.SetSurfaceName( f"blockIndex {blockIndex}" )
            if not filter.logger.hasHandlers():
                filter.SetLoggerHandler( VTKHandler() )

            filter.SetRockCohesion( self._getRockCohesion() )
            filter.SetFrictionAngle( self._getFrictionAngle() )
            filter.applyFilter()

            outputSurface: vtkPolyData = filter.GetOutputMesh()

            # add attributes to output surface mesh
            for attributeName in filter.GetNewAttributeNames():
                attr: vtkDataArray = outputSurface.GetCellData().GetArray( attributeName )
                surfaceBlock.GetCellData().AddArray( attr )
                surfaceBlock.GetCellData().Modified()
            surfaceBlock.Modified()

        output.Modified()
        return 1

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
