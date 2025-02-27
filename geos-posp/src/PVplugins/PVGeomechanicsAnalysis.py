# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
from typing import Union

import numpy as np
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
    smdomain,
    smhint,
    smproperty,
    smproxy,
)
from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkPointSet, vtkUnstructuredGrid

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.dirname(dir_path)
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

from geos_posp.utils.Logger import Logger, getLogger
from geos_posp.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_DEG,
    DEFAULT_GRAIN_BULK_MODULUS,
    DEFAULT_ROCK_COHESION,
    WATER_DENSITY,
)

__doc__ = """
PVGeomechanicsAnalysis is a Paraview plugin that allows to compute
additional geomechanical attributes from the input mesh.

Input and output types are vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVGeomechanicsAnalysis.
* Select any pipeline child of the first ouput from PVExtractMergeBlocksVolume* filter.
* Search and Apply PVGeomechanicsAnalysis Filter.

"""


@smproxy.filter(name="PVGeomechanicsAnalysis", label="Geos Geomechanics Analysis")
@smhint.xml("""<ShowInMenu category="3- Geos Geomechanics"/>""")
@smproperty.input(name="Input", port_index=0)
@smdomain.datatype(
    dataTypes=["vtkUnstructuredGrid", "vtkPointSet"], composite_data_supported=True
)
class PVGeomechanicsAnalysis(VTKPythonAlgorithmBase):
    def __init__(self: Self) -> None:
        """Paraview plugin to compute additional geomechanical outputs.

        Input is either a vtkUnstructuredGrid or vtkPointSet with Geos
        geomechanical properties.
        """
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkPointSet")

        # outputs and additional parameters
        self.m_computeAdvancedOutputs: bool = False
        self.m_grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.m_specificDensity: float = WATER_DENSITY
        self.m_rockCohesion: float = DEFAULT_ROCK_COHESION
        self.m_frictionAngle: float = DEFAULT_FRICTION_ANGLE_DEG

        # set m_logger
        self.m_logger: Logger = getLogger("Geomechanics Analysis Filter")

    def SetLogger(self: Self, logger: Logger) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

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

    @smproperty.intvector(
        name="AdvancedOutputsUse",
        label="Compute advanced geomechanical outputs",
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
    def c01SetAdvancedOutputs(self: Self, boolean: bool) -> None:
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

    @smproperty.xml(
        """
                    <PropertyGroup
                        label="Advanced output parameters">
                        panel_visibility="default">
                        <Property name="AdvancedOutputsUse"/>
                    </PropertyGroup>"""
    )
    def c09GroupAdvancedOutputsUse(self: Self) -> None:
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
                        The unit is °. Default is no friction case (i.e., 0.°).
                    </Documentation>
                  """
    )
    def d02SetFrictionAngle(self: Self, value: float) -> None:
        """Set frition angle.

        Args:
            value (float): friction angle (°)
        """
        self.m_frictionAngle = value
        self.Modified()

    def getFrictionAngle(self: Self) -> float:
        """Get friction angle in radian.

        Returns:
            float: friction angle.
        """
        return self.m_frictionAngle * np.pi / 180.0

    @smproperty.xml(
        """
                    <PropertyGroup
                        panel_visibility="advanced">
                        <Property name="RockCohesion"/>
                        <Property name="FrictionAngle"/>
                        <Hints>
                            <PropertyWidgetDecorator type="GenericDecorator"
                            mode="visibility"
                            property="AdvancedOutputsUse"
                            value="1" />
                        </Hints>
                    </PropertyGroup>
                    """
    )
    def d09GroupAdvancedOutputParameters(self: Self) -> None:
        """Organize groups."""
        self.Modified()

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
        outInfo = outInfoVec.GetInformationObject(0)  # noqa: F841
        return 1

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[vtkInformationVector],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData(inInfoVec, 0, 0)
        outData = self.GetOutputData(outInfoVec, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfoVec, outInfoVec)  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
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
            self.m_logger.info(f"Apply filter {__name__}")
            from filters.GeomechanicsCalculator import GeomechanicsCalculator

            inData = self.GetInputData(inInfoVec, 0, 0)
            assert inData is not None

            input: Union[vtkPointSet, vtkUnstructuredGrid]
            output: Union[vtkPointSet, vtkUnstructuredGrid]
            if inData.IsA("vtkUnstructuredGrid"):
                input = vtkUnstructuredGrid.GetData(inInfoVec[0])
                output = vtkUnstructuredGrid.GetData(outInfoVec)
            elif inData.IsA("vtkPointSet"):
                input = vtkPointSet.GetData(inInfoVec[0])
                output = vtkPointSet.GetData(outInfoVec)
            else:
                raise TypeError("Error type")

            assert input is not None, "Input object is null"
            assert output is not None, "Output object is null"

            # create new properties
            geomechanicsCalculatorFilter: GeomechanicsCalculator = (
                GeomechanicsCalculator()
            )
            geomechanicsCalculatorFilter.SetLogger(self.m_logger)
            geomechanicsCalculatorFilter.SetInputDataObject(input)
            if self.m_computeAdvancedOutputs:
                geomechanicsCalculatorFilter.computeAdvancedOutputsOn()
            else:
                geomechanicsCalculatorFilter.computeAdvancedOutputsOff()
            geomechanicsCalculatorFilter.SetGrainBulkModulus(self.getGrainBulkModulus())
            geomechanicsCalculatorFilter.SetSpecificDensity(self.getSpecificDensity())
            geomechanicsCalculatorFilter.SetRockCohesion(self.getRockCohesion())
            geomechanicsCalculatorFilter.SetFrictionAngle(self.getFrictionAngle())
            geomechanicsCalculatorFilter.Update()
            output.ShallowCopy(geomechanicsCalculatorFilter.GetOutputDataObject(0))
            output.Modified()

        except AssertionError as e:
            self.m_logger.error(f"{__name__} filter execution failed due to:")
            self.m_logger.error(e)
        except Exception as e:
            self.m_logger.critical(f"{__name__} filter execution failed due to:")
            self.m_logger.critical(e, exc_info=True)
        return 1
