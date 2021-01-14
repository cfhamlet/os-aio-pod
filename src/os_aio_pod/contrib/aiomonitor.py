import asyncio
import warnings
from concurrent import futures

from pydantic import BaseModel, Schema

from os_aio_pod.utils import module_from_string

try:
    from aiomonitor import monitor
    from aiomonitor.monitor import Monitor, start_monitor
except:
    warnings.warn("Should install aiomonitor first!")
    raise


class Config(BaseModel):

    host: str = monitor.MONITOR_HOST
    port: int = monitor.MONITOR_PORT
    console_port: int = monitor.CONSOLE_PORT
    console_enabled: bool = True
    monitor: module_from_string(Monitor) = Schema(Monitor, validate_always=True)


class AioMonitorAdapter(object):
    def __init__(self, context):
        self.context = context

    async def __call__(self, **kwargs):
        cwargs = {}
        config = Config()
        for k in config.dict().keys():
            if k in kwargs:
                cwargs[k] = kwargs.pop(k)
        config = Config(**cwargs)
        loop = self.context.loop

        monitor = start_monitor(loop=loop, **config.dict(), locals=kwargs)

        stop_event = asyncio.Event(loop=loop)

        async def stop(**kwargs):
            if not stop_event.is_set() and not monitor.closed:
                try:
                    with futures.ThreadPoolExecutor() as pool:
                        await loop.run_in_executor(pool, monitor.close)
                finally:
                    stop_event.set()

        for sig in ("SIGINT", "SIGTERM"):
            await self.context.add_signal_handler(sig, stop)

        await stop_event.wait()
