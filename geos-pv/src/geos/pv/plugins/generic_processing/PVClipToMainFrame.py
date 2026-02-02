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

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.pv.utils.details import ( SISOFilter, FilterCategory )
from geos.processing.generic_processing_tools.ClipToMainFrame import ClipToMainFrame
from geos.utils.Logger import isHandlerInLogger

__doc__ = f"""
Clip the input mesh to the main frame applying the correct LandmarkTransform

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/generic_processing/PVClipToMainFrame
* Select the mesh to process
* Select the filter: Filters > { FilterCategory.GENERIC_PROCESSING.value } > Clip to the main frame
* Apply

"""


@SISOFilter( category=FilterCategory.GENERIC_PROCESSING,
             decoratedLabel="Clip to the main frame",
             decoratedType=[ "vtkMultiBlockDataSet", "vtkDataSet" ] )
class PVClipToMainFrame( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        """Init motherclass, filter and logger."""
        self._realFilter = ClipToMainFrame( speHandler=True )
        self.handler: logging.Handler = VTKHandler()

        if not isHandlerInLogger( self.handler, self._realFilter.logger ):
            self._realFilter.SetLoggerHandler( self.handler )

    def ApplyFilter( self, inputMesh: vtkMultiBlockDataSet, outputMesh: vtkMultiBlockDataSet ) -> None:
        """Is applying CreateConstantAttributePerRegion filter.

        Args:
            inputMesh : A mesh to transform.
            outputMesh : A mesh transformed.
        """
        # struct
        self._realFilter.SetInputData( inputMesh )
        self._realFilter.ComputeTransform()
        self._realFilter.Update()
        outputMesh.ShallowCopy( self._realFilter.GetOutputDataObject( 0 ) )

        return
