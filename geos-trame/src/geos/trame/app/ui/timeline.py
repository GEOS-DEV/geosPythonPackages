# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any
from datetime import datetime, timedelta

# from trame.widgets import gantt
from geos.trame.app.gantt_chart.widgets.gantt_chart import Gantt
from trame.widgets import vuetify3 as vuetify
from trame.widgets.html import Html
from trame_simput import get_simput_manager

from geos.trame.app.deck.tree import DeckTree

date_fmt = "%Y-%m-%d"
                
class TimelineEditor( vuetify.VCard ):

    def __init__( self, source: DeckTree, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__( **kwargs )

        self.tree = source
        self.simput_manager = get_simput_manager( id=self.state.sm_id )

        self.state.sdate = self.tree.world_origin_time
        self.state.change("sdate")(self._set_start_date)

        items = self.tree.timeline()

        fields = [ {
            "summary": {
                "label": "Summary",
                "component": "gantt-text",
                "width": 300,
                "placeholder": "Add a new task...",
            },
            "start_date": {
                "label": "",# "Start",
                "component": "gantt-date",
                "width": -1,
                "placeholder": "Start",
                "sort": "date",
            },
            "end_date": {
                "label": "",# "End",
                "component": "gantt-date",
                "width": -1,
                "placeholder": "End",
                "sort": "date",
            },
            "duration": {
                "label": "Days",
                "component": "gantt-number",
                "width": 150,
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
                v_model="sdate"
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
            tasks_ =  [{"id": "1", "name": " Analyse des besoins", "start": "2012-12-12", "end":"2012-12-31", "category":"Phase 1", "progress": "100", "color": "#C55C36"},
                       {"id": "2", "name": " Debut production", "start": "2012-12-12", "end":"2012-12-31", "category":"Phase 1", "progress": "100", "color": "#151A77"}]
            with vuetify.VContainer( "Events chart" ):
               Gantt(
                    tasks=("tasks", tasks_),
                    startDate="2012-11-01",
                    endDate="2013-01-12",
                    taskUpdated=(self._updated_tasks,"tasks")
                    )
                # 
                # Gantt(
                #     canEdit=False,
                #     dateLimit=40,
                #     startDate= self.state.sdate,
                #     endDate=(datetime.strptime( self.state.sdate,date_fmt) + timedelta(days=40)).strftime(date_fmt) if self.state.sdate else '2012-12-12',
                #     # title='Gantt-pre-test',
                #     fields=fields,
                #     update=( self.update_from_js, "items" ),
                #     items=( "items", items ),
                #     classes="fill_height",
                # )

    def _set_start_date(self, sdate : str | None, **_: Any) -> None:
        if sdate is None:
            self.state.sdate = self.tree.world_origin_time.strftime(date_fmt)
            return
        
        self.state.sdate = sdate
        print(f"new date :{self.state.sdate}")

    def update_from_js( self, *items: tuple ) -> None:
        """Update method called from javascript."""
        self.state.items = list( items )

    def _updated_tasks(self, *tasks: tuple) -> None:
        self.state.tasks_ = list( tasks )