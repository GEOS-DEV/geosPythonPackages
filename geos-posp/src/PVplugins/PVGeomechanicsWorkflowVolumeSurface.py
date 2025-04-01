# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys

import numpy as np
from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
)

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.dirname(dir_path)
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

import PVplugins #required to update sys path

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
    smdomain,
    smhint,
    smproperty,
    smproxy,
)

from geos.utils.Logger import Logger, getLogger
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_DEG,
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_GRAIN_BULK_MODULUS,
    DEFAULT_ROCK_COHESION,
    WATER_DENSITY,
)
from PVplugins.PVExtractMergeBlocksVolumeSurface import (
    PVExtractMergeBlocksVolumeSurface,
)
from PVplugins.PVGeomechanicsAnalysis import PVGeomechanicsAnalysis
from PVplugins.PVSurfaceGeomechanics import PVSurfaceGeomechanics

__doc__ = """
PVGeomechanicsWorkflowVolumeSurface is a Paraview plugin that execute
multiple filters to clean GEOS outputs and compute additional geomechanical
outputs on volume and surface.

Input and output types are vtkMultiBlockDataSet.

This filter results in 2 output pipelines:

* first pipeline contains the volume mesh. If multiple regions were defined in
    the volume mesh, they are preserved as distinct blocks.
* second pipeline contains surfaces. If multiple surfaces were used, they are
    preserved as distinct blocks.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVGeomechanicsWorkflowVolumeSurface.
* Select the Geos output .pvd file loaded in Paraview.
* Search and Apply PVGeomechanicsWorkflowVolumeSurface Filter.

"""


@smproxy.filter(
    name="PVGeomechanicsWorkflowVolumeSurface",
    label="Geos Geomechanics Workflow - Volume/Surface",
)
@smhint.xml(
    """
    <ShowInMenu category="1- Geos Post-Processing Workflows"/>
    <OutputPort index="0" name="VolumeMesh"/>
    <OutputPort index="1" name="Surfaces"/>
    """
)
@smproperty.input(name="Input", port_index=0)
@smdomain.datatype(dataTypes=["vtkMultiBlockDataSet"], composite_data_supported=True)
class PVGeomechanicsWorkflowVolumeSurface(VTKPythonAlgorithmBase):
    def __init__(self: Self) -> None:
        """Paraview plugin to clean and add new outputs Geos output mesh.

        To apply in the case of output ".pvd" file contains Volume and Fault
        elements.
        """
        super().__init__(
            nInputPorts=1,
            nOutputPorts=2,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkMultiBlockDataSet",
        )

        #: ouput volume mesh
        self.m_volumeMesh: vtkMultiBlockDataSet
        #: output surface mesh
        self.m_surfaceMesh: vtkMultiBlockDataSet

        self.m_computeAdvancedOutputs: bool = False
        self.m_grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.m_specificDensity: float = WATER_DENSITY
        self.m_rockCohesion: float = DEFAULT_ROCK_COHESION
        self.m_frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        # set logger
        self.m_logger: Logger = getLogger("Geomechanics Workflow Filter")

    @smproperty.doublevector(
        name="GrainBulkModulus",
        label="Grain bulk modulus (Pa)",
        default_values=DEFAULT_GRAIN_BULK_MODULUS,
        panel_visibility="default",
    )
    @smdomain.xml(
        """
                    <Documentation>
                        Reference grain bulk modulus to compute Biot coefficient.
                        The unit is Pa. Default is Quartz bulk modulus (i.e., 38GPa).
                    </Documentation>
                  """
    )
    def b01SetGrainBulkModulus(self: Self, value: float) -> None:
        """Set grain bulk modulus.

        Args:
            value (float): grain bulk modulus (Pa)
        """
        self.m_grainBulkModulus = value
        self.Modified()

    def getGrainBulkModulus(self: Self) -> float:
        """Access to the grain bulk modulus value.

        Returns:
            float: self.m_grainBulkModulus.
        """
        return self.m_grainBulkModulus

    @smproperty.doublevector(
        name="SpecificDensity",
        label="Specific Density (kg/m3)",
        default_values=WATER_DENSITY,
        panel_visibility="default",
    )
    @smdomain.xml(
        """
                    <Documentation>
                        Reference density to compute specific gravity.
                        The unit is kg/m3. Default is fresh water density (i.e., 1000 kg/m3).
                    </Documentation>
                  """
    )
    def b02SetSpecificDensity(self: Self, value: float) -> None:
        """Set specific density.

        Args:
            value (float): Reference specific density (kg/m3)
        """
        self.m_specificDensity = value
        self.Modified()

    def getSpecificDensity(self: Self) -> float:
        """Access the specific density value.

        Returns:
            float: self.m_specificDensity.
        """
        return self.m_specificDensity

    @smproperty.xml(
        """
                <PropertyGroup label="Basic output parameters">
                    <Property name="GrainBulkModulus"/>
                    <Property name="SpecificDensity"/>
                </PropertyGroup>
                """
    )
    def b09GroupBasicOutputParameters(self: Self) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.doublevector(
        name="RockCohesion",
        label="Rock Cohesion (Pa)",
        default_values=DEFAULT_ROCK_COHESION,
        panel_visibility="default",
    )
    @smdomain.xml(
        """
                    <Documentation>
                        Reference rock cohesion to compute critical pore pressure.
                        The unit is Pa.Default is fractured case (i.e., 0. Pa).
                    </Documentation>
                  """
    )
    def d01SetRockCohesion(self: Self, value: float) -> None:
        """Set rock cohesion.

        Args:
            value (float): rock cohesion (Pa)
        """
        self.m_rockCohesion = value
        self.Modified()

    def getRockCohesion(self: Self) -> float:
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
    @smdomain.xml(
        """
                    <Documentation>
                        Reference friction angle to compute critical pore pressure.
                        The unit is °. Default is 10°.
                    </Documentation>
                  """
    )
    def d02SetFrictionAngle(self: Self, value: float) -> None:
        """Set frition angle.

        Args:
            value (float): friction angle (°)
        """
        self.m_frictionAngle = value * np.pi / 180.0
        self.Modified()

    def getFrictionAngle(self: Self) -> float:
        """Get friction angle in radian.

        Returns:
            float: friction angle.
        """
        return self.m_frictionAngle

    @smproperty.xml(
        """
        <PropertyGroup
            label="Surface parameters / Advanced volume parameters">
            <Property name="RockCohesion"/>
            <Property name="FrictionAngle"/>
        </PropertyGroup>
        """
    )
    def d09GroupAdvancedOutputParameters(self: Self) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.intvector(
        name="AdvancedOutputsUse",
        label="Compute advanced geomechanical volume outputs",
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml(
        """
                    <BooleanDomain name="AdvancedOutputsUse"/>
                    <Documentation>
                        Check to compute advanced geomechanical outputs including
                        reservoir stress paths and fracture indexes.
                    </Documentation>
                  """
    )
    def e01SetAdvancedOutputs(self: Self, boolean: bool) -> None:
        """Set advanced output calculation option.

        Args:
            boolean (bool): if True advanced outputs are computed.
        """
        self.m_computeAdvancedOutputs = boolean
        self.Modified()

    def getComputeAdvancedOutputs(self: Self) -> float:
        """Access the advanced outputs option.

        Returns:
            float: self.m_computeAdvancedOutputs.
        """
        return self.m_computeAdvancedOutputs

    def FillInputPortInformation(self: Self, port: int, info: vtkInformation) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkMultiBlockDataSet")
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[vtkInformationVector],  # noqa: F841
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
        outInfo: vtkInformation = outInfoVec.GetInformationObject(0)  # noqa: F841
        return 1

    def RequestData(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[vtkInformationVector],
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
        try:
            input: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData(inInfoVec[0])
            self.m_volumeMesh = self.GetOutputData(outInfoVec, 0)
            self.m_surfaceMesh = self.GetOutputData(outInfoVec, 1)

            assert input is not None, "Input MultiBlockDataSet is null."
            assert self.m_volumeMesh is not None, "Output volume mesh is null."
            assert self.m_surfaceMesh is not None, "Output surface mesh is null."

            # 1. extract volume/surface
            self.doExtractAndMerge()
            # 2. compute Geomechanical outputs in volume mesh
            self.computeAdditionalOutputsVolume()
            # 3. compute geomechanical outputs on surface mesh
            self.computeSurfaceGeomecanics()

        except AssertionError as e:
            mess: str = "Geomechanics workflow failed due to:"
            self.m_logger.error(mess)
            self.m_logger.error(str(e))
            return 0
        except Exception as e:
            mess1: str = "Geomechanics workflow failed due to:"
            self.m_logger.critical(mess1)
            self.m_logger.critical(e, exc_info=True)
            return 0
        return 1

    def doExtractAndMerge(self: Self) -> bool:
        """Apply block extraction and merge filter.

        Args:
            input (vtkMultiBlockDataSet): input multi block

        Returns:
            bool: True if extraction and merge successfully eneded, False otherwise
        """
        filter: PVExtractMergeBlocksVolumeSurface = PVExtractMergeBlocksVolumeSurface()
        filter.SetInputConnection(self.GetInputConnection(0, 0))
        filter.SetLogger(self.m_logger)
        filter.Update()

        # recover output objects from PVExtractMergeBlocksVolumeSurface
        self.m_volumeMesh.ShallowCopy(filter.GetOutputDataObject(0))
        self.m_surfaceMesh.ShallowCopy(filter.GetOutputDataObject(1))
        self.m_volumeMesh.Modified()
        self.m_surfaceMesh.Modified()
        return True

    def computeAdditionalOutputsVolume(self: Self) -> bool:
        """Compute geomechanical outputs on the volume mesh.

        Returns:
            bool: True if calculation successfully eneded, False otherwise.
        """
        filter = PVGeomechanicsAnalysis()
        filter.SetInputDataObject(self.m_volumeMesh)
        filter.b01SetGrainBulkModulus(self.getGrainBulkModulus())
        filter.b02SetSpecificDensity(self.getSpecificDensity())
        filter.d01SetRockCohesion(self.getRockCohesion())
        filter.d02SetFrictionAngle(self.getFrictionAngle())
        filter.c01SetAdvancedOutputs(self.m_computeAdvancedOutputs)
        filter.SetLogger(self.m_logger)
        filter.Update()
        self.m_volumeMesh.ShallowCopy(filter.GetOutputDataObject(0))
        self.m_volumeMesh.Modified()
        return True

    def computeSurfaceGeomecanics(self: Self) -> bool:
        """Compute surface geomechanics new attributes.

        Returns:
            bool: True if calculation successfully eneded, False otherwise.
        """
        filter = PVSurfaceGeomechanics()
        filter.SetInputDataObject(self.m_surfaceMesh)
        filter.a01SetRockCohesion(self.getRockCohesion())
        filter.a02SetFrictionAngle(self.getFrictionAngle())
        filter.SetLogger(self.m_logger)
        filter.Update()
        self.m_surfaceMesh.ShallowCopy(filter.GetOutputDataObject(0))
        self.m_surfaceMesh.Modified()
        return True
