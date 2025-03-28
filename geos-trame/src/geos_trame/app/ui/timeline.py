# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from trame.widgets import code, gantt, html, simput
from trame.widgets import vuetify3 as vuetify
from trame_simput import get_simput_manager


class TimelineEditor(vuetify.VCard):
    def __init__(self, source=None, **kwargs):
        super().__init__(**kwargs)

        self.tree = source
        self.simput_manager = get_simput_manager(id=self.state.sm_id)

        items = self.tree.timeline()
        # print(items)

        # DRAFT
        # items = [
        #     {"id": 1,
        #     "summary": "outputInjectionPeriod",
        #     "start_date": "2024-11-02 00:00",
        #     "end_date": "2024-11-02 00:00",
        #     "duration": 23
        #     },
        #     {
        #     "id": 2,
        #     "summary": "This is a task with a longer description.",
        #     "start_date": "2024-11-03 00:00",
        #     "end_date": "2024-11-04 00:00",
        #     "duration": 1
        #     }
        # ]

        items_alt = [
            {
                "id": 3,
                "summary": "Lorem ipsum.",
                "start_date": "2024-11-07 00:00",
                "end_date": "2024-11-09 00:00",
                "duration": 2,
            }
        ]

        fields = [
            {
                "summary": {
                    "label": "Summary",
                    "component": "gantt-text",
                    "width": 300,
                    "placeholder": "Add a new task...",
                },
                "start_date": {
                    "label": "Start",
                    "component": "gantt-date",
                    "width": 75,
                    "placeholder": "Start",
                    "sort": "date",
                },
                "end_date": {
                    "label": "End",
                    "component": "gantt-date",
                    "width": 75,
                    "placeholder": "End",
                    "sort": "date",
                },
                "duration": {
                    "label": "Days",
                    "component": "gantt-number",
                    "width": 50,
                    "placeholder": "0",
                },
            }
        ]

        with self:
            # with vuetify.VRow(
            # rows=2,
            # style="width: 100%;",
            # dense=True
            # classes="fill-height"
            # ):
            vuetify.VCardTitle("Events View")
            vuetify.VDateInput(
                label="Select starting simulation date",
                prepend_icon="",
                prepend_inner_icon="$calendar",
                placeholder="09/18/2024",
            )
            vuetify.VDivider()
            with vuetify.VContainer("Events timeline"):
                with vuetify.VTimeline(
                    direction="horizontal",
                    truncate_line="both",
                    align="center",
                    side="end",
                ):  # , truncate_line="both", side="end", line_inset="12"):
                    with vuetify.VTimelineItem(
                        v_for=(f"item in {items}",), key="i", value="item", size="small"
                    ):
                        vuetify.VAlert("{{ item.summary }}")
                        vuetify.Template(
                            "{{ item.start_date }}", raw_attrs=["v-slot:opposite"]
                        )

            with vuetify.VContainer("Events chart"):
                gantt.Gantt(
                    canEdit=True,
                    dateLimit=30,
                    startDate="2024-11-01 00:00",
                    endDate="2024-12-01 00:00",
                    # title='Gantt-pre-test',
                    fields=fields,
                    update=(self.update_from_js, "items"),
                    items=("items", items),
                    classes="fill_height",
                )

    def update_from_js(self, *items):
        self.state.items = list(items)
