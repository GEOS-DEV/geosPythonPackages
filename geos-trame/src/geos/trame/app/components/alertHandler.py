# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
import asyncio

from trame.widgets import vuetify3


class AlertHandler( vuetify3.VContainer ):
    """Vuetify component used to display an alert status.

    This alert will be displayed in the bottom right corner of the screen.
    It will be displayed until closed by the user or after 10 seconds if it is a success or warning.
    """

    def __init__( self ) -> None:
        """Constructor."""
        super().__init__(
            fluid=True,
            classes="pa-0 ma-0",
        )

        self.__max_number_of_status = 5
        self.__lifetime_of_alert = 10.0
        self._status_id = 0

        self.state.alerts = []

        self.server.controller.on_add_error.add_task( self.add_error )
        self.server.controller.on_add_warning.add_task( self.add_warning )

        self.generate_alert_ui()

    def generate_alert_ui( self ) -> None:
        """Generate the alert UI.

        The alert will be displayed in the bottom right corner of the screen.

        Use an abritary z-index value to put the alert on top of the other components.
        """
        with (
                self,
                vuetify3.VCol( style="width: 40%; position: fixed; right: 50px; bottom: 50px; z-index: 100;", ),
        ):
            vuetify3.VAlert(
                style="max-height: 20vh; overflow-y: auto",
                classes="ma-2",
                v_for=( "(status, index) in alerts", ),
                key="status",
                type=( "status.type", "info" ),
                text=( "status.message", "" ),
                title=( "status.title", "" ),
                closable=True,
                click_close=( self.on_close, "[status.id]" ),
            )

    def add_alert( self, type: str, title: str, message: str ) -> None:
        """Add a status to the stack with a unique id.

        If there are more than 5 alerts displayed, remove the oldest.
        A warning will be automatically closed after 10 seconds.
        """
        self.state.alerts.append( {
            "id": self._status_id,
            "type": type,
            "title": title,
            "message": message,
        } )

        if len( self.state.alerts ) > self.__max_number_of_status:
            self.state.alerts.pop( 0 )

        alert_id = self._status_id
        self._status_id += 1
        self.state.dirty( "alerts" )
        self.state.flush()

        if type == "warning":
            asyncio.get_event_loop().call_later( self.__lifetime_of_alert, self.on_close, alert_id )

    async def add_warning( self, title: str, message: str ) -> None:
        """Add an alert of type 'warning'."""
        self.add_alert( "warning", title, message )

    async def add_error( self, title: str, message: str ) -> None:
        """Add an alert of type 'error'."""
        self.add_alert( "error", title, message )

    def on_close( self, alert_id: int ) -> None:
        """Remove in the state the alert associated to the given id."""
        self.state.alerts = list( filter( lambda i: i[ "id" ] != alert_id, self.state.alerts ) )
        self.state.flush()
