import asyncio
import logging
import socket
import warnings
from collections.abc import Iterable
from typing import Any, Awaitable, Callable, List, Optional, Type, Union, cast

from pydantic import BaseModel

from os_aio_pod.bean import BeanContext
from os_aio_pod.utils import module_from_string, pydantic_dict

try:
    from aiohttp import web
    from aiohttp.abc import AbstractAccessLogger
    from aiohttp.log import access_logger
    from aiohttp.web_app import Application
    from aiohttp.web_log import AccessLogger
    from aiohttp.web_runner import AppRunner, SockSite, TCPSite, UnixSite
except:
    warnings.warn("Should install aiohttp first!")
    raise

try:
    from ssl import SSLContext
except ImportError:  # pragma: no cover
    SSLContext = Any  # type: ignore


class Config(BaseModel):
    app: module_from_string(web.Application, instance=True)

    class Config:
        extra = "allow"


async def run_app(
    context: BeanContext,
    app: Union[Application, Awaitable[Application]],
    *,
    host: Optional[str] = None,
    port: Optional[int] = None,
    path: Optional[str] = None,
    sock: Optional[socket.socket] = None,
    shutdown_timeout: float = 60.0,
    ssl_context: Optional[SSLContext] = None,
    print: Callable[..., None] = print,
    backlog: int = 128,
    access_log_class: Type[AbstractAccessLogger] = AccessLogger,
    access_log_format: str = AccessLogger.LOG_FORMAT,
    access_log: Optional[logging.Logger] = access_logger,
    handle_signals: bool = True,
    reuse_address: Optional[bool] = None,
    reuse_port: Optional[bool] = None
) -> None:

    loop = context.loop
    stop_event = asyncio.Event(loop=loop)

    def stop(**kwargs):
        stop_event.set()

    for sig in ("SIGINT", "SIGTERM"):
        await context.add_signal_handler(sig, stop)
    # A internal functio to actually do all dirty job for application running
    if asyncio.iscoroutine(app):
        app = await app  # type: ignore

    app = cast(Application, app)

    runner = AppRunner(
        app,
        handle_signals=handle_signals,
        access_log_class=access_log_class,
        access_log_format=access_log_format,
        access_log=access_log,
    )

    await runner.setup()

    sites = []  # type: List[BaseSite]

    try:
        if host is not None:
            if isinstance(host, (str, bytes, bytearray, memoryview)):
                sites.append(
                    TCPSite(
                        runner,
                        host,
                        port,
                        shutdown_timeout=shutdown_timeout,
                        ssl_context=ssl_context,
                        backlog=backlog,
                        reuse_address=reuse_address,
                        reuse_port=reuse_port,
                    )
                )
            else:
                for h in host:
                    sites.append(
                        TCPSite(
                            runner,
                            h,
                            port,
                            shutdown_timeout=shutdown_timeout,
                            ssl_context=ssl_context,
                            backlog=backlog,
                            reuse_address=reuse_address,
                            reuse_port=reuse_port,
                        )
                    )
        elif path is None and sock is None or port is not None:
            sites.append(
                TCPSite(
                    runner,
                    port=port,
                    shutdown_timeout=shutdown_timeout,
                    ssl_context=ssl_context,
                    backlog=backlog,
                    reuse_address=reuse_address,
                    reuse_port=reuse_port,
                )
            )

        if path is not None:
            if isinstance(path, (str, bytes, bytearray, memoryview)):
                sites.append(
                    UnixSite(
                        runner,
                        path,
                        shutdown_timeout=shutdown_timeout,
                        ssl_context=ssl_context,
                        backlog=backlog,
                    )
                )
            else:
                for p in path:
                    sites.append(
                        UnixSite(
                            runner,
                            p,
                            shutdown_timeout=shutdown_timeout,
                            ssl_context=ssl_context,
                            backlog=backlog,
                        )
                    )

        if sock is not None:
            if not isinstance(sock, Iterable):
                sites.append(
                    SockSite(
                        runner,
                        sock,
                        shutdown_timeout=shutdown_timeout,
                        ssl_context=ssl_context,
                        backlog=backlog,
                    )
                )
            else:
                for s in sock:
                    sites.append(
                        SockSite(
                            runner,
                            s,
                            shutdown_timeout=shutdown_timeout,
                            ssl_context=ssl_context,
                            backlog=backlog,
                        )
                    )
        for site in sites:
            await site.start()

        app.aio_pod_context = context

        if print:  # pragma: no branch
            names = sorted(str(s.name) for s in runner.sites)
            print("======== Running on {} ========\n".format(", ".join(names)))
        await stop_event.wait()
    finally:
        await runner.cleanup()


class WebAdapter(object):
    def __init__(self, context):
        self.context = context

    async def __call__(self, **kwargs):
        for c in (
            "access_log_class",
            "access_log_format",
            "ssl_context",
            "print",
            "handle_signals",
            "sock",
        ):
            kwargs.pop(c, None)
        config = Config(**kwargs)

        loop = self.context.loop
        access_log = access_logger
        if loop.get_debug() and access_log and access_log.name == "aiohttp.access":
            if access_log.level == logging.NOTSET:
                access_log.setLevel(logging.DEBUG)
            if not access_log.hasHandlers():
                access_log.addHandler(logging.StreamHandler())

        await run_app(
            self.context,
            config.app,
            access_log=access_log,
            handle_signals=False,
            **pydantic_dict(config, exclude={"app"})
        )
