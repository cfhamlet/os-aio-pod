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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server = None

    async def add_stop_signal_handler(self, callback):
        for sig in ('SIGINT', 'SIGTERM'):
            await self.context.add_signal_handler(sig, callback)

    async def remove_stop_signal_handler(self, callback):
        for sig in ('SIGINT', 'SIGTERM'):
            await self.context.remove_signal_handler(sig, callback)

    def create(self, config, loop):
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

        return tcp_server, factory

    async def wait(self, tcp_server, method, loop):
        task = asyncio.ensure_future(getattr(tcp_server, method)(), loop=loop)
        cancelled = []

        async def cancel(**kwargs):
            for sig in kwargs['keys']:
                try:
                    await tcp_server.on_signal(sig)
                except Exception as e:
                    self.logger.error(f'On signal error {e}')

            if not task.done():
                task.cancel()
            cancelled.append(1)

        await self.add_stop_signal_handler(cancel)
        try:
            await task
        except asyncio.CancelledError as e:
            if cancelled:
                self.logger.warn(f'Cancelled {e}')
                return False
            else:
                raise e
        finally:
            await self.remove_stop_signal_handler(cancel)

        return True

    async def __call__(self, **kwargs):
        config = Config(**kwargs)
        loop = self.context.loop

        tcp_server, factory = self.create(config, loop)
        self.server = tcp_server

        if not await self.wait(tcp_server, 'on_setup', loop):
            return

        self.logger.debug(
            f'Starting tcp server on {config.host}:{config.port}')

        server = await factory
        stop_event = asyncio.Event(loop=loop)
        stoping_lock = asyncio.Lock(loop=loop)

        async def on_signal(**kwargs):
            for sig in kwargs['keys']:
                try:
                    await tcp_server.on_signal(sig)
                except Exception as e:
                    self.logger.error(f'On signal error {e}')

            async with stoping_lock:
                if not stop_event.is_set():
                    try:
                        await tcp_server.on_stop()
                    except Exception as e:
                        self.logger.error(f'On stop error {e}')
                    server.close()
                    await server.wait_closed()
                    stop_event.set()

        await self.add_stop_signal_handler(on_signal)

        await tcp_server.on_start()
        await stop_event.wait()
        try:
            await tcp_server.on_cleanup()
        except Exception as e:
            self.logger.error(f'On cleanup error {e}')

        await self.remove_stop_signal_handler(on_signal)
        self.logger.debug(f'TCP server stopped')
