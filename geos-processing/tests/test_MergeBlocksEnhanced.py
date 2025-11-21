# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from geos.processing.generic_processing_tools.MergeBlockEnhanced import MergeBlockEnhanced


def test_MergeBlocksEnhancedFilter( dataSetTest: vtkMultiBlockDataSet, ) -> None:
    """Test MergeBlockEnhanced vtk filter."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )
    mergeBlockEnhancedFilter: MergeBlockEnhanced = MergeBlockEnhanced( multiBlockDataset )
    assert mergeBlockEnhancedFilter.applyFilter()

    failedMergeBlockEnhancedFilter: MergeBlockEnhanced = MergeBlockEnhanced( vtkMultiBlockDataSet() )
    assert not failedMergeBlockEnhancedFilter.applyFilter()
