# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any
from datetime import datetime, timedelta

from trame.widgets import gantt
from trame.widgets import vuetify3 as vuetify
from trame_simput import get_simput_manager

from geos.trame.app.deck.tree import DeckTree


date_fmt = "%Y-%m-%d"
                
class TimelineEditor( vuetify.VCard ):

    def __init__( self, source: DeckTree, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__( **kwargs )

        self.tree = source
        self.simput_manager = get_simput_manager( id=self.state.sm_id )
        self.state.change("set_start_date")(self._set_start_date)

        items = self.tree.timeline()

        fields = [ {
            "summary": {
                "label": "Summary",
                "component": "gantt-text",
                "width": 300,
                "placeholder": "Add a new task...",
            },
            "start_date": {
                "label": "Start",
                "component": "gantt-date",
                "width": 175,
                "placeholder": "Start",
                "sort": "date",
            },
            "end_date": {
                "label": "End",
                "component": "gantt-date",
                "width": 0,
                "placeholder": "End",
                "sort": "date",
            },
            "duration": {
                "label": "Days",
                "component": "gantt-number",
                "width": 50,
                "placeholder": "0",
            },
        } ]

        with self:
            vuetify.VCardTitle( "Events View" )
            vuetify.VDateInput(
                label="Select starting simulation date",
                prepend_icon="",
                prepend_inner_icon="$calendar",
                # placeholder="09/18/2024",
                v_model="start_date",
            )
            vuetify.VDivider()
            # with (
            #         vuetify.VContainer( "Events timeline" ),
            #         vuetify.VTimeline(
            #             direction="horizontal",
            #             truncate_line="both",
            #             align="center",
            #             side="end",
            #         ),
            #         vuetify.VTimelineItem( v_for=( f"item in {items}", ), key="i", value="item", size="small" ),
            # ):
            #     vuetify.VAlert( "{{ item.summary }}" )
            #     vuetify.Template( "{{ item.start_date }}", raw_attrs=[ "v-slot:opposite" ] )

            with vuetify.VContainer( "Events chart" ):
                gantt.Gantt(
                    canEdit=True,
                    dateLimit=40,
                    startDate= self.state.start_date if self.state.start_date else self.tree.world_origin_time,
                    endDate=(datetime.strptime( self.state.start_date if self.state.start_date else self.tree.world_origin_time,date_fmt) + timedelta(days=40)).strftime(date_fmt),
                    # title='Gantt-pre-test',
                    fields=fields,
                    update=( self.update_from_js, "items" ),
                    items=( "items", items ),
                    classes="fill_height",
                )

    def _set_start_date(self, start_date : str | None, **_: Any) -> None:
        if start_date is None:
            start_date = self.tree.world_origin_time.strftime(date_fmt)
            return
        
        self.state.start_date = start_date

    def update_from_js( self, *items: tuple ) -> None:
        """Update method called from javascript."""
        self.state.items = list( items )
