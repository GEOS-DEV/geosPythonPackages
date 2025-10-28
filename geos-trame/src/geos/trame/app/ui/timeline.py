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
        self.state.tasks = self.tree.timeline()

        with self:
            with vuetify.VContainer( "Events chart" ):
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