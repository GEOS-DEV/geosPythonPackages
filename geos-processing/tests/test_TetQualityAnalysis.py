# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.processing.pre_processing.TetQualityAnalysis import TetQualityAnalysis


def test_TetQualityAnalysis( dataSetTest: vtkUnstructuredGrid ) -> None:
    """Test applying TetQualityAnalysis filter."""
    meshes: dict[ str, vtkUnstructuredGrid ] = {
        'mesh1': dataSetTest( "meshtet1" ),
        'mesh1b': dataSetTest( "meshtet1b" )
    }
    tetQualityFilter: TetQualityAnalysis = TetQualityAnalysis( meshes )

    tetQualityFilter.applyFilter()


def test_TetQualityAnalysisRaisePathError( dataSetTest: vtkUnstructuredGrid ) -> None:
    """Test applying TetQualityAnalysis filter."""
    meshes: dict[ str, vtkUnstructuredGrid ] = {
        'mesh1': dataSetTest( "meshtet1" ),
        'mesh1b': dataSetTest( "meshtet1b" )
    }
    tetQualityFilter: TetQualityAnalysis = TetQualityAnalysis( meshes )

    tetQualityFilter.setFilename( "/qliuf/moidh/meshComparison.png" )

    with pytest.raises( FileNotFoundError ):
        tetQualityFilter.applyFilter()