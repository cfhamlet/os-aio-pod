import asyncio
import warnings

try:
    from aiomonitor.monitor import Monitor as BaseMonitor
    from aiomonitor.utils import close_server
except:
    warnings.warn("Should install aiomonitor first!")
    raise


class Monitor(BaseMonitor):
    async def close(self) -> None:
        if not self._closed:
            self._closing.set()
            self._ui_thread.join()
            if self._console_future is not None:
                server = self._console_future.result(timeout=15)
                await close_server(server)
            self._closed = True


class AioMonitorAdapter(object):
    def __init__(self, context):
        self.context = context

    async def __call__(self, **kwargs):
        monitor = Monitor(loop=self.context.loop, **kwargs)

        stop_event = asyncio.Event(loop=self.context.loop)

        async def stop(**kwargs):
            if not stop_event.is_set() and not monitor.closed:
                try:
                    await monitor.close()
                finally:
                    stop_event.set()

        for sig in ("SIGINT", "SIGTERM"):
            await self.context.add_signal_handler(sig, stop)

        monitor.start()
        await stop_event.wait()
