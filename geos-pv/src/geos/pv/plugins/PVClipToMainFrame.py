# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet, )

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.pv.utils.details import ( SISOFilter, FilterCategory )
from geos.processing.generic_processing_tools.ClipToMainFrame import ClipToMainFrame

__doc__ = """
Clip the input mesh to the main frame applying the correct LandmarkTransform

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVClipToMainFrame.
* Apply.

"""


@SISOFilter( category=FilterCategory.GEOS_UTILS,
             decoratedLabel="Clip to the main frame",
             decoratedType=[ "vtkMultiBlockDataSet", "vtkDataSet" ] )
class PVClipToMainFrame( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        """Init motherclass, filter and logger."""
        self._realFilter = ClipToMainFrame( speHandler=True )
        if not self._realFilter.logger.hasHandlers():
            self._realFilter.SetLoggerHandler( VTKHandler() )

    def Filter( self, inputMesh: vtkMultiBlockDataSet, outputMesh: vtkMultiBlockDataSet ) -> None:
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
