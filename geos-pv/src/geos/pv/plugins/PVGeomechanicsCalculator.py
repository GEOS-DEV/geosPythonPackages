# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Union
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkPointSet, vtkUnstructuredGrid

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_GRAIN_BULK_MODULUS,
    DEFAULT_ROCK_COHESION,
    WATER_DENSITY,
)
from geos.mesh.processing.GeomechanicsCalculator import GeomechanicsCalculator

__doc__ = """
PVGeomechanicsCalculator is a paraview plugin that allows to compute additional
Geomechanical properties from existing ones.

The basic geomechanics outputs are:
    - Elastic modulus (young modulus and poisson ratio or bulk modulus and shear modulus)
    - Biot coefficient
    - Compressibility, oedometric compressibility and real compressibility coefficient
    - Specific gravity
    - Real effective stress ratio
    - Total initial stress, total current stress and total stress ratio
    - Lithostatic stress (physic to update)
    - Elastic stain
    - Reservoir stress path and reservoir stress path in oedometric condition

The advanced geomechanics outputs are:
    - fracture index and threshold
    - Critical pore pressure and pressure index

PVGeomechanicsCalculator paraview plugin input mesh is either vtkPointSet or vtkUnstructuredGrid
and returned mesh is of same type as input.

.. Note::
    To deals with Geos output, you may first process it with PVExtractMergeBlocksVolume

To use it:

* Load the module in Paraview: Tools > Manage Plugins... > Load new > PVGeomechanicsCalculator
* Select the mesh you want to compute geomechanics output on
* Search Filters > 3- Geos Geomechanics > Geos Geomechanics Calculator
* Set physical constants and computeAdvancedOutput if needed
* Apply

"""


@smproxy.filter( name="PVGeomechanicsCalculator", label="Geos Geomechanics Calculator" )
@smhint.xml( """<ShowInMenu category="3- Geos Geomechanics"/>""" )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkUnstructuredGrid", "vtkPointSet" ], composite_data_supported=True )
class PVGeomechanicsCalculator( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to compute additional geomechanical outputs.

        Input is either a vtkUnstructuredGrid or vtkPointSet with Geos
        geomechanical properties.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkPointSet" )

        self.computeAdvancedOutputs: bool = False

        # Defaults physical constants
        ## Basic outputs
        self.grainBulkModulus: float = DEFAULT_GRAIN_BULK_MODULUS
        self.specificDensity: float = WATER_DENSITY
        ## Advanced outputs
        self.rockCohesion: float = DEFAULT_ROCK_COHESION
        self.frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

    @smproperty.doublevector(
        name="GrainBulkModulus",
        label="Grain bulk modulus (Pa)",
        default_values=DEFAULT_GRAIN_BULK_MODULUS,
        panel_visibility="default",
    )
    @smdomain.xml( """
                    <Documentation>
                        Reference grain bulk modulus to compute Biot coefficient.
                        The unit is Pa. Default is Quartz bulk modulus (i.e., 38GPa).
                    </Documentation>
                  """ )
    def setGrainBulkModulus( self: Self, grainBulkModulus: float ) -> None:
        """Set grain bulk modulus.

        Args:
            grainBulkModulus (float): Grain bulk modulus (Pa).
        """
        self.grainBulkModulus = grainBulkModulus
        self.Modified()

    @smproperty.doublevector(
        name="SpecificDensity",
        label="Specific Density (kg/m3)",
        default_values=WATER_DENSITY,
        panel_visibility="default",
    )
    @smdomain.xml( """
                    <Documentation>
                        Reference density to compute specific gravity.
                        The unit is kg/m3. Default is fresh water density (i.e., 1000 kg/m3).
                    </Documentation>
                  """ )
    def setSpecificDensity( self: Self, specificDensity: float ) -> None:
        """Set specific density.

        Args:
            specificDensity (float): Reference specific density (kg/m3).
        """
        self.specificDensity = specificDensity
        self.Modified()

    @smproperty.xml( """
                <PropertyGroup label="Basic output parameters">
                    <Property name="GrainBulkModulus"/>
                    <Property name="SpecificDensity"/>
                </PropertyGroup>
                """ )
    def groupBasicOutputParameters( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.intvector(
        name="ComputeAdvancedOutputs",
        label="Compute advanced geomechanical outputs",
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <BooleanDomain name="ComputeAdvancedOutputs"/>
        <Documentation>
            Check to compute advanced geomechanical outputs including
            reservoir stress paths and fracture indexes.
        </Documentation>
    """ )
    def setComputeAdvancedOutputs( self: Self, computeAdvancedOutputs: bool ) -> None:
        """Set advanced output calculation option.

        Args:
            computeAdvancedOutputs (bool): True to compute advanced geomechanical parameters, False otherwise.
        """
        self.computeAdvancedOutputs = computeAdvancedOutputs
        self.Modified()

    @smproperty.doublevector(
        name="RockCohesion",
        label="Rock Cohesion (Pa)",
        default_values=DEFAULT_ROCK_COHESION,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            Reference rock cohesion to compute critical pore pressure.
            The unit is Pa.Default is fractured case (i.e., 0. Pa).
        </Documentation>
    """ )
    def setRockCohesion( self: Self, rockCohesion: float ) -> None:
        """Set rock cohesion.

        Args:
            rockCohesion (float): Rock cohesion (Pa).
        """
        self.rockCohesion = rockCohesion
        self.Modified()

    @smproperty.doublevector(
        name="FrictionAngle",
        label="Friction Angle (rad)",
        default_values=DEFAULT_FRICTION_ANGLE_RAD,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            Reference friction angle to compute critical pore pressure.
            The unit is rad. Default is 10.0 / 180.0 * np.pi rad.
        </Documentation>
    """ )
    def setFrictionAngle( self: Self, frictionAngle: float ) -> None:
        """Set friction angle.

        Args:
            frictionAngle (float): Friction angle (rad).
        """
        self.frictionAngle = frictionAngle
        self.Modified()

    @smproperty.xml( """
        <PropertyGroup label="Advanced output parameters" panel_visibility="advanced">
            <Property name="RockCohesion"/>
            <Property name="FrictionAngle"/>
            <Hints>
                <PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility"
                    property="ComputeAdvancedOutputs"
                    value="1" />
            </Hints>
        </PropertyGroup>
    """ )
    def groupAdvancedOutputParameters( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inputMesh: Union[ vtkPointSet, vtkUnstructuredGrid ] = self.GetInputData( inInfoVec, 0, 0 )
        outputMesh: Union[ vtkPointSet, vtkUnstructuredGrid ] = self.GetOutputData( outInfoVec, 0 )
        assert inputMesh is not None, "Input server mesh is null."
        assert outputMesh is not None, "Output pipeline is null."

        filter: GeomechanicsCalculator = GeomechanicsCalculator( inputMesh, self.computeAdvancedOutputs, True )

        if not filter.logger.hasHandlers():
            filter.setLoggerHandler( VTKHandler() )

        filter.setGrainBulkModulus( self.grainBulkModulus )
        filter.setSpecificDensity( self.specificDensity )
        filter.setRockCohesion( self.rockCohesion )
        filter.setFrictionAngle( self.frictionAngle )

        if filter.applyFilter():
            outputMesh.ShallowCopy( filter.getOutput() )
            outputMesh.Modified()

        return 1
