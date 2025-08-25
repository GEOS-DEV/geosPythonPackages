# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# Copyright (c) 2019-     INRIA project-team Makutu
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
from typing_extensions import Self
from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy
from paraview.detail.loghandler import VTKHandler
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.fault.DMZFinder import DMZFinder

__doc__ = """
PVDMZFinder is a Paraview plugin that finds Damage/Fractured Zone (DMZ) cells in mesh.

Input and output types are vtkUnstructuredGrid.

This filter results in a single output pipeline that contains the volume mesh with added DMZ array.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVDMZFinder.py
* Select the .vtu grid loaded in Paraview.
* Set the parameters (Fault ID, Region ID, DZ Length, etc.)
* Apply.

"""


@smproxy.filter( name="PVDMZFinder", label="Damage Zone Finder" )
@smhint.xml( '<ShowInMenu category="Geos Faults"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkUnstructuredGrid" ], composite_data_supported=True )
class PVDMZFinder( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Find Damage/Fractured Zone (DMZ) cells in mesh."""
        super().__init__( nInputPorts=1,
                          nOutputPorts=1,
                          inputType="vtkUnstructuredGrid",
                          outputType="vtkUnstructuredGrid" )

        self.region_array_name: str = "attribute"
        self.active_region_id: int = 0
        self.active_fault_id: int = 0
        self.output_array_name: str = "isDMZ"
        self.dmz_length: float = 100.0

    @smproperty.intvector( name="Fault ID", default_values=0, number_of_elements=1 )
    def SetActiveFaultID( self: Self, value: int ) -> None:
        """Set the active fault ID.

        Args:
            value (int): The fault ID to set.
        """
        if self.active_fault_id != value:
            self.active_fault_id = value
            self.Modified()

    @smproperty.intvector( name="Region ID", default_values=0, number_of_elements=1 )
    def SetActiveRegionID( self: Self, value: int ) -> None:
        """Set the active region ID.

        Args:
            value (int): The region ID to set.
        """
        if self.active_region_id != value:
            self.active_region_id = value
            self.Modified()

    @smproperty.doublevector( name="DZ Length", default_values=100.0, number_of_elements=1 )
    def SetDmzLength( self: Self, value: float ) -> None:
        """Set the DMZ length.

        Args:
            value (float): The DMZ length to set.
        """
        if self.dmz_length != value:
            self.dmz_length = value
            self.Modified()

    @smproperty.stringvector( name="Output Array Name", default_values="isDMZ", number_of_elements=1 )
    def SetOutputArrayName( self: Self, name: str ) -> None:
        """Set the output array name.

        Args:
            name (str): The output array name to set.
        """
        if self.output_array_name != name:
            self.output_array_name = name
            self.Modified()

    @smproperty.stringvector( name="Region Array Name", default_values="attribute", number_of_elements=1 )
    def SetRegionArrayName( self: Self, name: str ) -> None:
        """Set the region array name.

        Args:
            name (str): The region array name to set.
        """
        if self.region_array_name != name:
            self.region_array_name = name
            self.Modified()

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

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
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inputMesh: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outputMesh: vtkUnstructuredGrid = self.GetOutputData( outInfoVec, 0 )
        assert inputMesh is not None, "Input mesh is null."
        assert outputMesh is not None, "Output pipeline is null."

        outputMesh.ShallowCopy( inputMesh )

        filter: DMZFinder = DMZFinder(
            outputMesh,
            self.region_array_name,
            self.active_region_id,
            self.active_fault_id,
            self.output_array_name,
            self.dmz_length,
            True,
        )

        if not filter.logger.hasHandlers():
            filter.setLoggerHandler( VTKHandler() )

        filter.applyFilter()

        return 1
