# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase  # type: ignore[import-not-found]

from vtkmodules.vtkCommonDataModel import vtkPointSet

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.processing.generic_processing_tools.SplitMesh import ( SplitMesh, loggerTitle )
from geos.processing.pre_processing.CellTypeCounterEnhanced import loggerTitle as cloggerTitle
from geos.pv.utils.details import ( SISOFilter, FilterCategory )
from geos.utils.Logger import addPluginLogSupport

__doc__ = """
Split each cell of input mesh to smaller cells.

Output mesh is of same type as input mesh. If input mesh is a composite mesh, the plugin split cells of each part independently.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVSplitMesh.
* Select the input mesh.
* Apply the filter.

"""


@SISOFilter( category=FilterCategory.GEOS_UTILS, decoratedLabel="Split Mesh", decoratedType="vtkPointSet" )
@addPluginLogSupport( loggerTitles=[ loggerTitle, cloggerTitle ] )
class PVSplitMesh( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Split mesh cells."""
        pass

    def ApplyFilter( self: Self, inputMesh: vtkPointSet, outputMesh: vtkPointSet ) -> None:
        """Apply vtk filter.

        Args:
            inputMesh(vtkPointSet): Input mesh.
            outputMesh: Output mesh.
        """
        splitMeshFilter: SplitMesh = SplitMesh( inputMesh )
        if splitMeshFilter.applyFilter():
            outputMesh.ShallowCopy( splitMeshFilter.getOutput() )

        return
