from enum import Enum, auto, unique

from trame_client.widgets.html import H3, Div
from trame_server import Server
from trame_vuetify.widgets.vuetify3 import VCard


@unique
class SimulationStatus( Enum ):
    SCHEDULED = auto()
    RUNNING = auto()
    COMPLETING = auto()
    COPY_BACK = auto()
    DONE = auto()
    NOT_RUN = auto()
    UNKNOWN = auto()


class SimulationStatusView:
    """
    Simple component containing simulation status in a VCard with some coloring depending on the status.
    """

    def __init__( self, server: Server ):

        def state_name( state_str ):
            return f"{type(self).__name__}_{state_str}_{id(self)}"

        self._text_state = state_name( "text" )
        self._date_state = state_name( "date" )
        self._time_state = state_name( "time" )
        self._color_state = state_name( "color" )
        self._state = server.state

        for s in [ self._text_state, self._date_state, self._time_state, self._color_state ]:
            self._state.client_only( s )

        with VCard(
                classes="p-8",
                style=( f"`border: 4px solid ${{{self._color_state}}}; width: 300px; margin:auto; padding: 4px;`", ),
        ) as self.ui:
            H3( f"{{{{{self._text_state}}}}}", style="text-align:center;" )
            Div( f"{{{{{self._date_state}}}}} {{{{{self._time_state}}}}}", style="text-align:center;" )

        self.set_status( SimulationStatus.NOT_RUN )
        self.set_time_stamp( "" )

    def set_status( self, status: SimulationStatus ):
        self._state[ self._text_state ] = status.name
        self._state[ self._color_state ] = self.status_color( status )
        self._state.flush()

    def set_time_stamp( self, time_stamp: str ):
        date, time = self.split_time_stamp( time_stamp )
        self._state[ self._time_state ] = time
        self._state[ self._date_state ] = date
        self._state.flush()

    @staticmethod
    def split_time_stamp( time_stamp: str ) -> tuple[ str, str ]:
        default_time_stamp = "", ""
        if not time_stamp:
            return default_time_stamp

        time_stamp = time_stamp.split( "_" )
        if len( time_stamp ) < 2:
            return default_time_stamp

        return time_stamp[ 0 ].replace( "-", "/" ), time_stamp[ 1 ].split( "." )[ 0 ].replace( "-", ":" )

    @staticmethod
    def status_color( status: SimulationStatus ) -> str:
        return {
            SimulationStatus.DONE: "#4CAF50",
            SimulationStatus.RUNNING: "#3F51B5",
            SimulationStatus.SCHEDULED: "#FFC107",
            SimulationStatus.COMPLETING: "#C5E1A5",
            SimulationStatus.COPY_BACK: "#C5E1A5",
            SimulationStatus.UNKNOWN: "#E53935",
        }.get( status, "#607D8B" )
