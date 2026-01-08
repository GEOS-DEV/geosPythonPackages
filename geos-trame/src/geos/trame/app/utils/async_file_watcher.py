# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc

import asyncio
from asyncio import CancelledError, ensure_future
from typing import Callable

from trame_server.utils import asynchronous


class AsyncPeriodicRunner:
    """While started, runs given callback at given period."""

    def __init__( self, callback: Callable, period_ms: int = 100 ) -> None:
        """Init the async watcher object."""
        self.last_m_time = None
        self.callback = callback
        self.period_ms = period_ms
        self.task = None
        self.start()

    def __del__( self ) -> None:
        """Clean up async watch on destruction."""
        self.stop()

    def set_period_ms( self, period_ms: int ) -> None:
        """Set the async watch period.

        :params:period_ms period in ms
        """
        self.period_ms = period_ms

    def start( self ) -> None:
        """Stop existing async watch and start a new stream."""
        self.stop()
        self.task = asynchronous.create_task( self._runner() )

    def stop( self ) -> None:
        """Stop the async watch."""
        if not self.task:
            return

        ensure_future( self._wait_for_cancel() )  # type:ignore[unreachable]

    async def _wait_for_cancel( self ) -> None:
        """Cancel and await cancel error for the task.

        If cancel is done outside async, it may raise warnings as cancelled exception may be triggered outside async
        loop.
        """
        if not self.task or self.task.done() or self.task.cancelled():  # type:ignore[unreachable]
            self.task = None
            return

        try:  # type:ignore[unreachable]
            self.task.cancel()
            await self.task
        except CancelledError:
            self.task = None

    async def _runner( self ) -> None:
        while True:
            self.callback()
            await asyncio.sleep( self.period_ms / 1000.0 )
