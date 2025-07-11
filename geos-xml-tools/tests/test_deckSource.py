# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

from pathlib import Path

from geos.xml_tools.vtk_builder import create_vtk_deck

# Dir containing the files
FIXTURE_DIR = Path( __file__ ).parent.resolve() / "files"


# @pytest.mark.datafiles(FIXTURE_DIR / "singlePhaseFlow")
def test_DeckReader() -> None:
    """Test the DeckReader."""
    datafile = Path( "singlePhaseFlow/FieldCaseTutorial3_smoke.xml" )
    path = str( FIXTURE_DIR / datafile )
    vtk_collection = create_vtk_deck( path, "attribute" )
    assert ( vtk_collection.GetClassName() == "vtkPartitionedDataSetCollection" )
    assert vtk_collection.GetNumberOfPartitionedDataSets() == 5
