# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from geos.mesh.processing.MergeBlockEnhanced import MergeBlockEnhanced
from unittest import TestCase
from geos.utils.Errors import VTKError


def test_MergeBlocksEnhancedFilter( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test MergeBlockEnhanced vtk filter."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )
    filter: MergeBlockEnhanced = MergeBlockEnhanced( multiBlockDataset )
    filter.applyFilter()


class RaiseMergeBlocksEnhanced( TestCase ):
    """Test failure on empty multiBlockDataSet."""

    def test_TypeError( self ) -> None:
        multiBlockDataset = vtkMultiBlockDataSet()
        filter: MergeBlockEnhanced = MergeBlockEnhanced( multiBlockDataset )
        self.assertRaises( VTKError, filter.applyFilter )
