import asyncio
import logging
from asyncio.streams import _DEFAULT_LIMIT
from typing import Union

from pydantic import BaseModel, Schema, validator

from os_aio_pod.utils import model_from_string


class Server(object):

    def __init__(self, context, config):
        self.context = context
        self.config = config

    async def on_signal(self, sig):
        pass

    async def on_connect(self, reader, writer):
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
    protocol: model_from_string(asyncio.Protocol) = None
    backlog: int = 100
    limit: int = _DEFAULT_LIMIT
    server: model_from_string(Server) = Schema(Server, validate_always=True)

    class Config:
        allow_extra = True


class TCPServerAdapter(object):

    def __init__(self, context):
        self.context = context
        self.server = None

    async def add_stop_signal_handler(self, callback):
        for sig in ('SIGINT', 'SIGTERM'):
            await self.context.add_signal_handler(sig, callback)

    async def remove_stop_signal_handler(self, callback):
        for sig in ('SIGINT', 'SIGTERM'):
            await self.context.remove_signal_handler(sig, callback)

    async def __call__(self, **kwargs):
        logger = logging.getLogger(self.__class__.__name__)
        config = Config(**kwargs)
        loop = self.context.loop

        tcp_server = config.server(self.context, config)

        factory = None
        if config.protocol is None:
            factory = asyncio.start_server(
                tcp_server.on_connect,
                config.host,
                config.port,
                backlog=config.backlog,
                limit=config.limit,
                loop=loop
            )
        else:
            config.protocol.server = tcp_server
            factory = loop.create_server(
                config.protocol,
                config.host,
                config.port,
                backlog=config.backlog,
            )

        self.server = tcp_server
        logger.debug(f'Starting tcp server on {config.host}:{config.port}')

        on_setup_task = asyncio.ensure_future(tcp_server.on_setup(), loop=loop)
        on_start_task = asyncio.ensure_future(tcp_server.on_start(), loop=loop)

        cancelled = False

        async def cancel(**kwargs):
            for sig in kwargs['keys']:
                await tcp_server.on_signal(sig)

            for task in (on_setup_task, on_start_task):
                if not task.done():
                    task.cancel()
            cancelled = True

        await self.add_stop_signal_handler(cancel)

        try:
            await on_setup_task
            server = await factory
            await on_start_task
        except asyncio.CancelledError as e:
            if cancelled:
                await self.remove_stop_signal_handler(cancel)
                logger.warn(f'Cancelled {e}')
                return
            else:
                raise e

        await self.remove_stop_signal_handler(cancel)

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

        await self.add_stop_signal_handler(on_signal)

        await stop_event.wait()
        await tcp_server.on_cleanup()

        await self.remove_stop_signal_handler(on_signal)
        logger.debug(f'TCP server stopped')
