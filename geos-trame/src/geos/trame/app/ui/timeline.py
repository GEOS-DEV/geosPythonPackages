# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any
from datetime import datetime, timedelta
import logging

# from trame.widgets import gantt
from geos.trame.app.gantt_chart.widgets.gantt_chart import Gantt
from trame.widgets import vuetify3 as vuetify
from trame.widgets.html import Html
from trame_simput import get_simput_manager

from geos.trame.app.deck.tree import DeckTree

date_fmt = "%Y-%m-%d"
logger = logging.getLogger("timeline")
logger.setLevel(logging.ERROR)         
class TimelineEditor( vuetify.VCard ):

    def __init__( self, source: DeckTree, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__( **kwargs )

        self.tree = source
        self.simput_manager = get_simput_manager( id=self.state.sm_id )

        self.state.tasks = []
        dtasks = [{"id": "1", "name": " Analyse des besoins", "start": "2012-12-12", "end":"2012-12-31", "category":"Phase 1", "progress": "100", "color": "#C55C36"},
                       {"id": "2", "name": " Debut production", "start": "2012-12-12", "end":"2012-12-31", "category":"Phase 2", "progress": "100", "color": "#151A77"}]
        # self.state.tasks = list( tasks )
        # self.state.change("tasks")(self._updated_tasks)
        # self.state.tasks = dtasks

        self.state.tasks = self.tree.timeline()

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
            # vuetify.VDateInput(
            #     label="Select starting simulation date",
            #     prepend_icon="",
            #     prepend_inner_icon="$calendar",
            #     # placeholder="09/18/2024",
            #     v_model="sdate"
            # )
            vuetify.VDivider()
            with vuetify.VContainer( "Events chart" ):
               Gantt(
                    tasks=("tasks",),
                    startDate="2012-11-01",
                    endDate="2013-01-12",
                    taskUpdated=(self._updated_tasks,"$event"),
                    classes="fill_height",
                    )
            with vuetify.VContainer("Debug"):
               vuetify.VAlert("{{tasks}}", vmodel=("tasks",))

    def _updated_tasks(self, *tasks: Any, **_: Any) -> None:
        if tasks is None:
            print('None values')
        logger.info(f"new tasks {tasks}")
        self.state.tasks = tasks