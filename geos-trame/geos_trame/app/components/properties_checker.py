# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from typing import Any

from trame_client.widgets.core import AbstractElement
from trame_simput import get_simput_manager

from geos_trame.app.data_types.field_status import FieldStatus
from geos_trame.app.deck.tree import DeckTree
from geos_trame.app.ui.viewer.regionViewer import RegionViewer
from geos_trame.app.utils.geos_utils import group_name_ref_array_to_list

# Doc reference: https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/CompleteXMLSchema.html
attributes_to_check = [ ( "region_attribute", str ), ( "fields_to_import", list ), ( "surfacicFieldsToImport", list ) ]


class PropertiesChecker( AbstractElement ):
    """Validity checker of properties within a deck tree."""

    def __init__( self, tree: DeckTree, region_viewer: RegionViewer, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__( "div", **kwargs )

        self.tree = tree
        self.region_viewer = region_viewer
        self.simput_manager = get_simput_manager( id=self.state.sm_id )

    def check_fields( self ) -> None:
        """Check all the fields in the deck_tree.

        Get the names of all the cell data arrays from the input of the region viewer, then check that
        all the attributes in `attributes_to_check` have a value corresponding to one of the array names.
        """
        cellData = self.region_viewer.input.GetCellData()
        arrayNames = [ cellData.GetArrayName( i ) for i in range( cellData.GetNumberOfArrays() ) ]
        for field in self.state.deck_tree:
            self.check_field( field, arrayNames )
        self.state.dirty( "deck_tree" )
        self.state.flush()

    def check_field( self, field: dict, array_names: list[ str ] ) -> None:
        """Check that all the attributes in `attributes_to_check` have a value corresponding to one of the array names.

        Set the `valid` property to the result of this check, and if necessary, indicate which properties are invalid.
        """
        field[ "valid" ] = FieldStatus.VALID.value
        field[ "invalid_properties" ] = []

        proxy = self.simput_manager.proxymanager.get( field[ "id" ] )
        if proxy is not None:
            for attr, expected_type in attributes_to_check:
                if attr in proxy.definition:
                    if ( expected_type is str and proxy[ attr ]  # value is not empty (valid)
                         and proxy[ attr ] not in array_names  # value is not in the expected names
                        ):
                        field[ "invalid_properties" ].append( attr )
                    elif expected_type is list:
                        arrays: list[ str ] | None = group_name_ref_array_to_list( proxy[ attr ] )
                        if arrays is None:
                            field[ "invalid_properties" ].append( attr )
                            continue
                        for array_name in arrays:
                            if array_name not in array_names:
                                field[ "invalid_properties" ].append( attr )
                                break

        if len( field[ "invalid_properties" ] ) != 0:
            field[ "valid" ] = FieldStatus.INVALID.value
        else:
            field.pop( "invalid_properties", None )

        if field[ "children" ] is not None:
            # Parents are only valid if all children are valid
            field[ "invalid_children" ] = []
            for child in field[ "children" ]:
                self.check_field( child, array_names )
                if child[ "valid" ] == FieldStatus.INVALID.value:
                    field[ "valid" ] = FieldStatus.INVALID.value
                    field[ "invalid_children" ].append( child[ "title" ] )
            if len( field[ "invalid_children" ] ) == 0:
                field.pop( "invalid_children", None )
