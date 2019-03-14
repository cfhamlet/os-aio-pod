import asyncio
import os

import click

from os_aio_pod.initializers import (InitBeans, InitDebug, InitLog, InitLoop,
                                     InitSignal)
from os_aio_pod.pod import create
from os_aio_pod.prototype import LogLevel, LoopType, PodConfig
from os_aio_pod.utils import load_module_from_pyfile

DEFAULT_CONFIG = PodConfig()


@click.command()
@click.option(
    '--debug', is_flag=True,
    help='Enable debug mode.'
)
@click.option(
    '-c', '--config-file',
    type=click.File(mode='r'),
    help='Config file.'
)
@click.option(
    '-l', '--log-level',
    default=DEFAULT_CONFIG.LOG_LEVEL.name, show_default=True,
    type=click.Choice([l.name for l in LogLevel]),
    help='Log level.'
)
@click.option(
    '--loop-type',
    default=DEFAULT_CONFIG.LOOP_TYPE.name, show_default=True,
    type=click.Choice([l.name for l in LoopType]),
    help='Loop type.'
)
@click.option(
    '--stop-wait-time',
    default=DEFAULT_CONFIG.STOP_WAIT_TIME, show_default=True,
    type=click.INT,
    help='Stop wait time.'
)
@click.pass_context
def cli(ctx, **kwargs):
    '''Run server.'''

    ctx.ensure_object(dict)

    kwargs = dict([(k, v) for k, v in kwargs.items() if v])
    config = DEFAULT_CONFIG
    if 'config_file' in kwargs:
        cfile = kwargs.pop('config_file')
        m = load_module_from_pyfile(os.path.abspath(cfile.name))
        config = PodConfig.parse_obj(dict(
            [(i, getattr(m, i)) for i in dir(m)
             if not i.startswith('_') and i.isupper()]))

    config = PodConfig(
        **config.copy(update=dict([(i.upper(), kwargs[i]) for i in kwargs])).dict())

    pod = create(config, *[c() for c in [
        InitLoop,
        InitLog,
        InitBeans,
        InitDebug,
        InitSignal,
    ]]
    )

    loop = pod.loop
    try:
        loop.run_until_complete(pod.run())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
