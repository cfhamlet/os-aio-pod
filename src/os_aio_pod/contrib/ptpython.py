import asyncio
import warnings

try:
    from ptpython.repl import embed
except:
    warnings.warn("Should install ptpython first!")
    raise

try:
    from prompt_toolkit import print_formatted_text
    from prompt_toolkit.contrib.telnet.server import TelnetServer
except Exception as e:
    warnings.warn(f"Import prompt_toolkit fail {e}")
    raise

from .simple import Server


class TelnetServerAdapter(Server):
    async def run(self, **kwargs):
        lcs = {"context": self.context}

        async def interact(connection=None):
            global_dict = {**globals(), "print": print_formatted_text}
            await embed(return_asyncio_coroutine=True, globals=global_dict, locals=lcs)

        port = kwargs.get("port", 23)
        host = kwargs.get("host", "127.0.0.1")
        telnet_server = TelnetServer(interact=interact, port=port, host=host)
        stop_event = asyncio.Event(loop=self.context.loop)

        async def stop(**kwargs):
            if not stop_event.is_set():
                try:
                    await telnet_server.stop()
                finally:
                    stop_event.set()

        for sig in ("SIGINT", "SIGTERM"):
            await self.context.add_signal_handler(sig, stop)

        telnet_server.start()

        await stop_event.wait()
