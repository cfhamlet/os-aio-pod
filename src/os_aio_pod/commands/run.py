import asyncio
import os

import click

from os_aio_pod.initializers import (InitBeans, InitDebug, InitLog, InitLoop,
                                     InitSignal)
from os_aio_pod.pod import create
from os_aio_pod.prototype import PodConfig
from os_aio_pod.utils import load_module_from_pyfile


DEFAULT_CONFIG = PodConfig()


def valid_log_level(ctx, param, value):
    try:
        return DEFAULT_CONFIG.valid_log_level(value)
    except ValueError as e:
        raise click.BadParameter(e)


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug mode.')
@click.option('-c', '--config-file',
              type=click.File(mode='r'), help='Config file.')
@click.option('-l', '--log-level', metavar='LOG_LEVEL',
              default=DEFAULT_CONFIG.LOG_LEVEL, show_default=True,
              callback=valid_log_level,
              help=f'Log level.'
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

    config = config.copy(update=dict([(i.upper(), kwargs[i]) for i in kwargs]))

    pod = create(config,
                 *[c() for c in [InitLoop,
                                 InitLog,
                                 InitBeans,
                                 InitDebug,
                                 InitSignal]])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(pod.run())
