import asyncio
import os
from asyncio import CancelledError, ensure_future
from io import TextIOWrapper
from pathlib import Path
from typing import Callable, Optional, Union

from trame_server.utils import asynchronous


class AsyncPeriodicRunner:
    """
    While started, runs given callback at given period.
    """

    def __init__(self, callback: Callable, period_ms=100):
        self.last_m_time = None
        self.callback = callback
        self.period_ms = period_ms
        self.task = None
        self.start()

    def __del__(self):
        self.stop()

    def set_period_ms(self, period_ms):
        self.period_ms = period_ms

    def start(self):
        self.stop()
        self.task = asynchronous.create_task(self._runner())

    def stop(self):
        if not self.task:
            return

        ensure_future(self._wait_for_cancel())

    async def _wait_for_cancel(self):
        """
        Cancel and await cancel error for the task.
        If cancel is done outside async, it may raise warnings as cancelled exception may be triggered outside async
        loop.
        """
        if not self.task or self.task.done() or self.task.cancelled():
            self.task = None
            return

        try:
            self.task.cancel()
            await self.task
        except CancelledError:
            self.task = None

    async def _runner(self):
        while True:
            self.callback()
            await asyncio.sleep(self.period_ms / 1000.0)


class AsyncFileWatcher(AsyncPeriodicRunner):
    def __init__(self, path_to_watch: Path, on_modified_callback: Callable, check_time_out_ms=100):
        super().__init__(self._check_modified, check_time_out_ms)
        self.path_to_watch = Path(path_to_watch)
        self.last_m_time = None
        self.on_modified_callback = on_modified_callback

    def get_m_time(self):
        if not self.path_to_watch.exists():
            return None
        return os.stat(self.path_to_watch).st_mtime

    def _check_modified(self):
        if self.get_m_time() != self.last_m_time:
            self.last_m_time = self.get_m_time()
            self.on_modified_callback()


class AsyncSubprocess:
    def __init__(
        self,
        args,
        timeout: Union[float, None] = None,
    ) -> None:
        self.args = args
        self.timeout = timeout
        self._writer: Optional[TextIOWrapper] = None

        self.stdout: Optional[bytes] = None
        self.stderr: Optional[bytes] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.exception: Optional[RuntimeError] = None

    async def run(self) -> None:
        cmd = " ".join(map(str, self.args))
        self.process = await self._init_subprocess(cmd)

        try:
            self.stdout, self.stderr = await asyncio.wait_for(self.process.communicate(), timeout=self.timeout)
        except asyncio.exceptions.TimeoutError:
            self.process.kill()
            self.stdout, self.stderr = await self.process.communicate()
            self.exception = RuntimeError("Process timed out")
        finally:
            if self.process.returncode != 0:
                self.exception = RuntimeError(f"Process exited with code {self.process.returncode}")

    async def _init_subprocess(self, cmd: str) -> asyncio.subprocess.Process:
        return await asyncio.create_subprocess_shell(
            cmd=cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
