# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner, Jacques Franc
from typing import Any
from datetime import datetime, timedelta
import pytz
import logging

from geos.trame.app.gantt_chart.widgets.gantt_chart import Gantt
from trame.widgets import vuetify3 as vuetify
from trame_simput import get_simput_manager
from geos.trame.schema_generated.schema_mod import PeriodicEvent

from geos.trame.app.deck.tree import DeckTree

date_fmt = "%Y-%m-%d"
logger = logging.getLogger( "timeline" )
logger.setLevel( logging.ERROR )


class TimelineEditor( vuetify.VCard ):

    def __init__( self, source: DeckTree, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__( **kwargs )

        self.tree = source
        self.simput_manager = get_simput_manager( id=self.state.sm_id )
        self.state.sdate = None  #Timestamp(self.tree.world_origin_time)
        self.state.change( "sdate" )( self._updated_sdate )
        self.state.tasks = self.tree.timeline()
        self.state.regList = list( self.tree.registered_targets.keys() )

        with self:  #noqa
            with vuetify.VContainer( "Events chart" ):  #noqa
                vuetify.VDateInput(
                    label="Select starting simulation date",
                    prepend_icon="",
                    prepend_inner_icon="$calendar",
                    v_model=( "sdate", ),
                )
                vuetify.VDivider()
                Gantt(
                    tasks=( "tasks", ),
                    availableCategoriesList=( "regList", ),
                    taskUpdated=( self._updated_tasks, "$event" ),
                    classes="fill_height",
                )

            #use to refect change in simput to gantt
            # def _on_change( topic: str, ids: list | None = None ) -> None:
            #     if ids is not None and topic == "changed":
            #         print("blablabla")

            # self.simput_manager.proxymanager.on( _on_change )

    def _updated_tasks( self, *tasks: Any, **_: Any ) -> None:

        rm_list = ( { t_id
                      for t in self.state.tasks if ( t_id := t.get( "id" ) ) is not None } -
                    { t_id
                      for t in tasks if ( t_id := t.get( "id" ) ) is not None } )

        self.state.tasks = tasks
        former_origin_time: datetime = datetime.strptime(
            min( self.state.tasks, key=lambda d: datetime.strptime( d.get( "start" ), date_fmt ) ).get( "start" ),
            date_fmt )
        #update and erase
        for t in self.state.tasks:
            start_time = ( datetime.strptime( t[ "start" ], date_fmt ) - former_origin_time ).total_seconds()
            end_time = ( datetime.strptime( t[ "end" ], date_fmt ) - former_origin_time ).total_seconds()

            #negative events
            if ( start_time < 0 or end_time < 0 ):
                continue

            event = {
                "begin_time": f"{ start_time: .6e}",
                "end_time": f"{ end_time: .6e}",
                "name": t[ "name" ],
                "category": t[ "category" ]
            }

            #if added Event then
            if not self.tree._search( f'Problem/Events/0/PeriodicEvent/{t["id"]}' ):
                self.tree.input_file.pb_dict[ 'Problem' ][ 'Events' ][ 0 ][ 'PeriodicEvent' ].append(
                    self.tree.encode_data( PeriodicEvent( name="test" ) ) )
                proxy = self.simput_manager.proxymanager.create( proxy_type='PeriodicEvent',
                                                                 proxy_id=f'Problem/Events/0/PeriodicEvent/{t["id"]}',
                                                                 initial_values=self.tree.encode_data(
                                                                     PeriodicEvent( name="test" ) ) )
            else:
                proxy = self.simput_manager.proxymanager.get( f'Problem/Events/0/PeriodicEvent/{t["id"]}' )

            self.tree.update( f'Problem/Events/0/PeriodicEvent/{t["id"]}', 'beginTime', event[ 'begin_time' ] )
            proxy.set_property( "begin_time", event[ 'begin_time' ] )
            self.tree.update( f'Problem/Events/0/PeriodicEvent/{t["id"]}', 'endTime', event[ 'end_time' ] )
            proxy.set_property( "end_time", event[ 'end_time' ] )
            self.tree.update( f'Problem/Events/0/PeriodicEvent/{t["id"]}', 'name', event[ 'name' ] )
            proxy.set_property( "name", event[ 'name' ] )
            self.tree.update( f'Problem/Events/0/PeriodicEvent/{t["id"]}', 'target',
                              self.tree.registered_targets[ event[ 'category' ] ] )
            proxy.set_property( "target", event[ 'category' ] )

            if "freq" in t and t[ "freq" ] is not None:
                self.tree.update( f'Problem/Events/0/PeriodicEvent/{t["id"]}', 'timeFrequency',
                                  str( timedelta( days=int( t[ "freq" ] ) ).total_seconds() ) )
                proxy.set_property( "time_frequency", str( timedelta( days=int( t[ "freq" ] ) ).total_seconds() ) )
            
            proxy.commit()

        self.ctrl.simput_reload_data()

        #remove lost indexes
        for i in rm_list:
            self.tree.drop( f'Problem/Events/0/PeriodicEvent/{i}' )
            #drop proxies as well
            self.simput_manager.proxymanager.delete( proxy_id=f'Problem/Events/0/PeriodicEvent/{t["id"]}' )

        return

    @staticmethod
    def shift_str( dt_str: str, time_delta: timedelta ) -> str:
        """Helper function for shifting time."""
        return ( datetime.strptime( dt_str, date_fmt ) + time_delta ).strftime( date_fmt )

    def _updated_sdate( self, sdate: Any, **_: Any ) -> None:
        #sdate seems to some sort of panda Timestamp
        if sdate is not None:
            former_origin_time: str = min( self.state.tasks,
                                        key=lambda d: datetime.strptime( d.get( "start" ), date_fmt ) ).get( "start" )
            time_delta: timedelta = sdate.to_datetime() - pytz.utc.localize(
                datetime.strptime( former_origin_time, date_fmt ) )
            self.state.tasks = [ {
                **d, "start": TimelineEditor.shift_str( d[ "start" ], time_delta ),
                "end": TimelineEditor.shift_str( d[ "end" ], time_delta )
            } for d in self.state.tasks ]

        return
