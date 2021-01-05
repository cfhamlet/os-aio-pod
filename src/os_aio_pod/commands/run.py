import sys

import click

from os_aio_pod.config import LogLevel, LoopType, PodConfig
from os_aio_pod.initializers import InitBeans, InitDebug, InitLog, InitLoop, InitSignal
from os_aio_pod.pod import create
from os_aio_pod.utils import (
    load_core_config_from_pyfile,
    parse_beans_arguments,
    pydantic_dict,
    update_from_bean_config_file,
)

DEFAULT_CONFIG = PodConfig()


def run(config):
    pod = create(
        config, *[c() for c in [InitLoop, InitLog, InitBeans, InitDebug, InitSignal]]
    )

    loop = pod.loop
    try:
        loop.run_until_complete(pod.run())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


@click.command()
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.option("-c", "--config-file", type=click.File(mode="r"), help="Config file.")
@click.option(
    "-l",
    "--log-level",
    show_default=True,
    type=click.Choice([l.name for l in LogLevel]),
    help=f"Log level.  [default: {DEFAULT_CONFIG.LOG_LEVEL.name}]",
)
@click.option(
    "--loop-type",
    show_default=True,
    type=click.Choice([l.name for l in LoopType]),
    help=f"Loop type.  [default: {DEFAULT_CONFIG.LOOP_TYPE.name}]",
)
@click.option(
    "--stop-wait-time",
    default=DEFAULT_CONFIG.STOP_WAIT_TIME,
    show_default=True,
    type=click.INT,
    help=f"Stop wait time.",
)
@click.argument("BEANS", nargs=-1)
@click.pass_context
def cli(ctx, **kwargs):
    """Run pod."""

    ctx.ensure_object(dict)

    config = DEFAULT_CONFIG.copy()
    if "config_file" in kwargs and kwargs["config_file"]:
        cfile = kwargs.pop("config_file")
        config = load_core_config_from_pyfile(PodConfig, cfile.name)

    if not kwargs["debug"]:
        kwargs.pop("debug")

    config.BEANS.extend(parse_beans_arguments(kwargs.pop("beans")))

    config = PodConfig(
        **pydantic_dict(
            config.copy(
                update=dict(
                    [(k.upper(), v) for k, v in kwargs.items() if v is not None]
                )
            )
        )
    )
    config = update_from_bean_config_file(config)

    if config.DEBUG:
        config = config.copy(update={"LOG_LEVEL": LogLevel.debug})
        try:
            import inspect

            print("PodConfig:", file=sys.stderr)
            print(
                config.json(
                    encoder=lambda v: str(v) if inspect.isclass(v) else v, indent=4
                ),
                file=sys.stderr,
            )
        except Exception as e:
            import warnings

            warnings.warn(f"Can not print config debug info, {e}")
    run(config)
