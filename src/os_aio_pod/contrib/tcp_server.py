import asyncio
import logging
from multiprocessing import Process
from socket import SO_REUSEADDR, SOL_SOCKET, socket
from typing import Union

from pydantic import BaseModel, validator

from os_aio_pod.utils import model_from_string


class Server(object):

    def __init__(self, context, config):
        self.context = context
        self.config = config

    async def on_signal(self, sig):
        pass

    async def on_setup(self):
        pass

    async def on_start(self):
        pass

    async def on_stop(self):
        pass

    async def on_cleanup(self):
        pass


class Config(BaseModel):

    host: str = '127.0.0.1'
    port: int = 9399
    protocol: model_from_string(asyncio.Protocol)
    backlog: int = 100
    server: model_from_string(Server) = Server

    class Config:
        allow_extra = True


class TCPServerAdapter(object):

    def __init__(self, context):
        self.context = context

    async def __call__(self, **kwargs):
        logger = logging.getLogger(self.__class__.__name__)
        config = Config(**kwargs)
        loop = self.context.loop

        tcp_server = config.server(self.context, config)
        config.protocol.server = tcp_server

        factory = loop.create_server(
            config.protocol,
            config.host,
            config.port,
            backlog=config.backlog,
        )

        logger.debug(f'Starting tcp server on {config.host}:{config.port}')

        await tcp_server.on_setup()
        server = await factory
        await tcp_server.on_start()

        stop_event = asyncio.Event(loop=loop)
        stoping_lock = asyncio.Lock(loop=loop)

        async def on_signal(**kwargs):
            for sig in kwargs['keys']:
                await tcp_server.on_signal(sig)

            await stoping_lock.acquire()
            if not stop_event.is_set():
                await tcp_server.on_stop()
                server.close()
                await server.wait_closed()
                stop_event.set()
            stoping_lock.release()

        for sig in ('SIGINT', 'SIGTERM'):
            await self.context.add_signal_handler(sig, on_signal)

        await stop_event.wait()
        await tcp_server.on_cleanup()
        logger.debug(f'TCP server stopped')
