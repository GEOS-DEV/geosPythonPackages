# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smhint, smproperty, smproxy,
)

from vtkmodules.vtkCommonDataModel import (
    vtkPointSet,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths
update_paths()

from geos.mesh.processing.MergeColocatedPoints import MergeColocatedPoints
from geos.pv.utils.AbstractPVPluginVtkWrapper import AbstractPVPluginVtkWrapper

__doc__ = """
Merge collocated points of input mesh.

Output mesh is of same type as input mesh. If input mesh is a composite mesh, the plugin merge points of each part independently.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVMergeColocatedPoints.
* Select the input mesh.
* Apply the filter.

"""

@smproxy.filter( name="PVMergeColocatedPoints", label="Merge Colocated Points" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkPointSet"],
    composite_data_supported=True,
)
class PVMergeColocatedPoints(AbstractPVPluginVtkWrapper):
    def __init__(self:Self) ->None:
        """Merge collocated points."""
        super().__init__()

    def applyVtkFlilter(
        self: Self,
        input: vtkPointSet,
    ) -> vtkPointSet:
        """Apply vtk filter.

        Args:
            input (vtkPointSet): input mesh

        Returns:
            vtkPointSet: output mesh
        """
        filter :MergeColocatedPoints = MergeColocatedPoints()
        filter.SetInputDataObject(input)
        filter.Update()
        return filter.GetOutputDataObject( 0 )
