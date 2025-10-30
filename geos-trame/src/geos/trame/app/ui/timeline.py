# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any
from datetime import datetime, timedelta
from pandas import Timestamp
import pytz
import logging

# from trame.widgets import gantt
from geos.trame.app.gantt_chart.widgets.gantt_chart import Gantt
from trame.widgets import vuetify3 as vuetify
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
        self.state.sdate = None #Timestamp(self.tree.world_origin_time)
        self.state.change("sdate")(self._updated_sdate)
        self.state.tasks = self.tree.timeline()

        with self:
            with vuetify.VContainer( "Events chart" ):
                vuetify.VDateInput(
                    label="Select starting simulation date",
                    prepend_icon="",
                    prepend_inner_icon="$calendar",
                    # placeholder="09/18/2024",
                    v_model=("sdate",),
                )
                vuetify.VDivider()
                Gantt(
                        tasks=("tasks",),
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

    def _updated_sdate(self, sdate: str, **_: Any) -> None:
        #sdate seems to be a panda Timestamp
        if sdate is None:
            return

        logger.info(f"new origin of time {sdate.to_datetime()}")
        # return
        former_origin_time: str = min(self.state.tasks, key=lambda d: datetime.strptime(d.get("start"),date_fmt)).get("start")
        time_delta : timedelta =  sdate.to_datetime() - pytz.utc.localize(datetime.strptime(former_origin_time,date_fmt)) 
        self.state.tasks = list(map(lambda d: {**d, "start":(datetime.strptime(d["start"],date_fmt) + time_delta ).strftime(date_fmt), 
                                               "end" : (datetime.strptime(d["end"],date_fmt) + time_delta ).strftime(date_fmt) }, 
                                               self.state.tasks))
        return