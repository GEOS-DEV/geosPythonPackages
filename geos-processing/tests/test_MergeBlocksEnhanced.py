# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from geos.processing.generic_processing_tools.MergeBlockEnhanced import MergeBlockEnhanced
from unittest import TestCase
from geos.utils.Errors import VTKError
import vtk
from packaging.version import Version


def test_MergeBlocksEnhancedFilter( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test MergeBlockEnhanced vtk filter."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "geosOutput2Ranks" )
    mergeBlockEnhancedFilter: MergeBlockEnhanced = MergeBlockEnhanced( multiBlockDataset )
    mergeBlockEnhancedFilter.applyFilter()


class RaiseMergeBlocksEnhanced( TestCase ):
    """Test failure on empty multiBlockDataSet."""

    def test_TypeError( self ) -> None:
        """Test raise of TypeError."""
        multiBlockDataset = vtkMultiBlockDataSet()  # should fail on empty data
        mergeBlockEnhancedFilter: MergeBlockEnhanced = MergeBlockEnhanced( multiBlockDataset )
        if Version( vtk.__version__ ) < Version( "9.5" ):
            self.assertRaises( VTKError, mergeBlockEnhancedFilter.applyFilter() )
