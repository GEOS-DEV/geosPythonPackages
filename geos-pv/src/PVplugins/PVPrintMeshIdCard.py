# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy
)

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPointSet,
    vtkTable,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths
update_paths()

from geos.mesh.stats.ComputeMeshStats import ComputeMeshStats
from geos.mesh.model.MeshIdCard import MeshIdCard

__doc__ = """
Display mesh statistics.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVPrintMeshIdCard.
* Select the input mesh.
* Apply the filter.

"""

@smproxy.filter( name="PVPrintMeshIdCard", label="Print Mesh ID Card" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkPointSet"],
    composite_data_supported=True,
)
class PVPrintMeshIdCard(VTKPythonAlgorithmBase):
    def __init__(self:Self) ->None:
        """Merge collocated points."""
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkPointSet")

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
        inputMesh: vtkPointSet = self.GetInputData( inInfoVec, 0, 0 )
        output: vtkTable = self.GetOutputData( outInfoVec, 0 )
        assert inputMesh is not None, "Input server mesh is null."
        assert output is not None, "Output pipeline is null."

        output.ShallowCopy(inputMesh)
        filter: ComputeMeshStats = ComputeMeshStats()
        filter.SetInputDataObject(inputMesh)
        filter.Update()
        card: MeshIdCard = filter.GetMeshIdCard()
        print(card.print())
        return 1
