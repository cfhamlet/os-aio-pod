import asyncio

import click

from os_aio_pod.initializers import (InitBeans, InitDebug, InitLog, InitLoop,
                                     InitSignal)
from os_aio_pod.pod import create


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug mode.')
@click.option('-c', '--config-file',
              default='config.py', show_default=True,
              type=click.File(mode='r'), help='Config file.')
@click.pass_context
def cli(ctx, **kwargs):
    '''Run server.'''

    ctx.ensure_object(dict)

    kwargs = dict([(k, v) for k, v in kwargs.items() if v])
    config = None

    pod = create(config,
                 *[c() for c in [InitLoop,
                                 InitLog,
                                 InitBeans,
                                 InitDebug,
                                 InitSignal]])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(pod.run())
