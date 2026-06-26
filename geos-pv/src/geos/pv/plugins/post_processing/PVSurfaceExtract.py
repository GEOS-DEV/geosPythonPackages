# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging
from pathlib import Path

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.utils.Errors import VTKError
from geos.pv.utils.details import ( SISOFilter, FilterCategory )

from vtkmodules.vtkCommonDataModel import vtkDataSet #vtkMultiBlockDataSet
from geos.processing.generic_processing_tools.SurfaceExtract import ExtractCellsNearSurface
from geos.utils.Logger import isHandlerInLogger

__doc__ = f"""
Clip the input mesh to the main frame applying the correct LandmarkTransform

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/generic_processing/PVClipToMainFrame
* Select the mesh to process
* Select the filter: Filters > { FilterCategory.GENERIC_PROCESSING.value } >  Extract nearest cells layer to a surface
* Apply
"""

HANDLER: logging.Handler = VTKHandler()
loggerTitle: str = "PVSurfaceExtract"

@SISOFilter( category=FilterCategory.GENERIC_PROCESSING,
             decoratedLabel="Extract nearest cells layer to a surface",
             decoratedType=[ "vtkDataSet" ] )
class PVSurfaceExtract( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        """Init motherclass, filter and logger."""
        self._realFilter = ExtractCellsNearSurface( speHandler=True )

        if not isHandlerInLogger( HANDLER, self._realFilter.logger ):
            self._realFilter.SetLoggerHandler( HANDLER )

    def ApplyFilter( self, inputMesh: vtkDataSet, outputMesh: vtkDataSet ) -> None:
        """Is applying surface extract filter.

        Args:
            inputMesh : A mesh to transform.
            outputMesh : A mesh transformed.
        """
        try:
            self._realFilter.applyFilter( inputMesh, outputMesh )
        except VTKError as e:
            logger = logging.getLogger( loggerTitle )
            logger.error( f"VTKError: { e }" )