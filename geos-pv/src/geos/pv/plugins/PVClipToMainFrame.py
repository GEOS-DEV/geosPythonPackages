# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet, )

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.pv.utils.details import ( SISOFilter, FilterCategory )
from geos.processing.generic_processing_tools.ClipToMainFrame import ClipToMainFrame, loggerTitle, getLogger
from geos.utils.Logger import Logger, addPluginLogSupport

__doc__ = """
Clip the input mesh to the main frame applying the correct LandmarkTransform

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVClipToMainFrame.
* Apply.

"""


@SISOFilter( category=FilterCategory.GEOS_UTILS,
             decoratedLabel="Clip to the main frame",
             decoratedType=[ "vtkMultiBlockDataSet", "vtkDataSet" ] )
@addPluginLogSupport( loggerTitles=[ loggerTitle ] )
class PVClipToMainFrame( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        """Init motherclass, filter and logger."""
        self._realFilter = ClipToMainFrame()
        self.logger: Logger = getLogger( loggerTitle )

    def ApplyFilter( self, inputMesh: vtkMultiBlockDataSet, outputMesh: vtkMultiBlockDataSet ) -> None:
        """Is applying CreateConstantAttributePerRegion filter.

        Args:
            inputMesh : A mesh to transform.
            outputMesh : A mesh transformed.
        """
        # struct
        self.logger.info( f"Applying plugin {self.logger.name}." )

        self._realFilter.SetInputData( inputMesh )
        self._realFilter.ComputeTransform()
        self._realFilter.Update()
        outputMesh.ShallowCopy( self._realFilter.GetOutputDataObject( 0 ) )

        return
