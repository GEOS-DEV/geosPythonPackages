# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner, Jacques Franc
from typing import Any
from datetime import datetime, timedelta
from pandas import Timestamp
import pytz
import logging
import dpath.util


# from trame.widgets import gantt
from geos.trame.app.gantt_chart.widgets.gantt_chart import Gantt
from trame.widgets import vuetify3 as vuetify
from trame_simput import get_simput_manager
from geos.trame.schema_generated.schema_mod import PeriodicEvent

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
        former_origin_time: datetime = datetime.strptime( min(self.state.tasks, key=lambda d: datetime.strptime(d.get("start"),date_fmt)).get("start"), date_fmt)
        for i,t in enumerate(self.state.tasks):
            event = {"begin_time": str(( datetime.strptime(t["start"],date_fmt) - former_origin_time).days) , #should be seconds / days for debug
                     "end_time": str(( datetime.strptime(t["end"],date_fmt) - former_origin_time ).days),
                     "name": t["name"]}
            
            self.tree.update(f'Problem/Events/0/PeriodicEvent/{i}','beginTime', event['begin_time'])
            self.tree.update(f'Problem/Events/0/PeriodicEvent/{i}','endTime', event['end_time'])
            self.tree.update(f'Problem/Events/0/PeriodicEvent/{i}','name', event['name'])

        return


    def _updated_sdate(self, sdate: str, **_: Any) -> None:
        #sdate seems to be a panda Timestamp
        if sdate is None:
            return

        former_origin_time: str = min(self.state.tasks, key=lambda d: datetime.strptime(d.get("start"),date_fmt)).get("start")
        time_delta : timedelta =  sdate.to_datetime() - pytz.utc.localize(datetime.strptime(former_origin_time,date_fmt)) 
        self.state.tasks = list(map(lambda d: {**d, "start":(datetime.strptime(d["start"],date_fmt) + time_delta ).strftime(date_fmt), 
                                               "end" : (datetime.strptime(d["end"],date_fmt) + time_delta ).strftime(date_fmt) }, 
                                               self.state.tasks))
        return