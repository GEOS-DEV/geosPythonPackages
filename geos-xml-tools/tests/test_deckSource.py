# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

from pathlib import Path

from geos.xml_tools.viewer.filters.geosDeckReader import GeosDeckReader

# Dir containing the files
FIXTURE_DIR = Path( __file__ ).parent.resolve() / "files"


# @pytest.mark.datafiles(FIXTURE_DIR / "singlePhaseFlow")
def test_DeckReader() -> None:
    """Test the DeckReader."""
    datafile = Path( "singlePhaseFlow/FieldCaseTutorial3_smoke.xml" )
    path = str( FIXTURE_DIR / datafile )
    reader = GeosDeckReader()
    reader.SetFileName( path )
    reader.SetAttributeName( "attribute" )
    reader.Update()
    assert ( reader.GetOutputDataObject( 0 ).GetClassName() == "vtkPartitionedDataSetCollection" )
    assert reader.GetOutputDataObject( 0 ).GetNumberOfPartitionedDataSets() == 5
