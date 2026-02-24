# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging
from pathlib import Path
from typing_extensions import Self

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonDataModel import vtkPointSet

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.processing.generic_processing_tools.SplitMesh import SplitMesh
from geos.utils.Logger import isHandlerInLogger
from geos.pv.utils.details import ( SISOFilter, FilterCategory )

__doc__ = f"""
Split each cell of input mesh to smaller cells.

Output mesh is of same type as input mesh. If input mesh is a composite mesh, the plugin split cells of each part independently.

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/generic_processing/PVSplitMesh
* Select the input mesh to process
* Select the filter: Filters > { FilterCategory.GENERIC_PROCESSING.value } > Split Mesh
* Apply

"""


@SISOFilter( category=FilterCategory.GENERIC_PROCESSING, decoratedLabel="Split Mesh", decoratedType="vtkPointSet" )
class PVSplitMesh( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Split mesh cells."""
        self.handler: logging.Handler = VTKHandler()

    def ApplyFilter( self: Self, inputMesh: vtkPointSet, outputMesh: vtkPointSet ) -> None:
        """Apply vtk filter.

        Args:
            inputMesh(vtkPointSet): Input mesh.
            outputMesh: Output mesh.
        """
        splitMeshFilter: SplitMesh = SplitMesh( inputMesh, True )
        if not isHandlerInLogger( self.handler, splitMeshFilter.logger ):
            splitMeshFilter.setLoggerHandler( self.handler )

        try:
            splitMeshFilter.applyFilter()
            outputMesh.ShallowCopy( splitMeshFilter.getOutput() )
        except ( TypeError, AttributeError ) as e:
            splitMeshFilter.logger.error( f"The filter {splitMeshFilter.logger.name } failed due to:\n{ e }" )
        except Exception as e:
            mess: str = f"The filter { splitMeshFilter.logger.name } failed due to:\n{ e }"
            splitMeshFilter.logger.critical( mess, exc_info=True )

        return
