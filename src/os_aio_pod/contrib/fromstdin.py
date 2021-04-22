import asyncio
import sys

from os_aio_pod.contrib.pcflow import Server as BaseServer


class Server(BaseServer):
    async def produce(self, **kwargs):
        while not self.stopping:
            try:
                yield await self.stdin.readuntil(b"\n")
            except asyncio.IncompleteReadError as e:
                break
            except Exception as e:
                self.logger.error(f"{e}")

    async def run(self, **kwargs):
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        self.stdin = reader
        self.stopping = False

        def _on_stop(**kwargs):
            self.stopping = True

        for signal in ("SIGTERM", "SIGINT"):
            await self.context.add_signal_handler(signal, _on_stop)
        return await super(Server, self).run(**kwargs)
