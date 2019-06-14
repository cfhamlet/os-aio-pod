import click

from os_aio_pod.utils import walk_modules

from . import __version__


class CommandFinder(click.MultiCommand):
    def list_commands(self, ctx):
        ctx.ensure_object(dict)
        return list(self.__find_commnds(**ctx.obj).keys())

    def get_command(self, ctx, name):
        ctx.ensure_object(dict)
        commands = self.__find_commnds(**ctx.obj)
        return commands.get(name, None)

    def __find_commnds(self, **kwargs):
        command_packages = kwargs.get("command_packages", [])
        commands = {}
        for command_package in command_packages:
            for cmd_module in walk_modules(command_package, skip_fail=False):
                if hasattr(cmd_module, "cli") and isinstance(
                    cmd_module.cli, click.Command
                ):
                    commands[cmd_module.__name__.split(".")[-1]] = cmd_module.cli

        return commands


def execute(**kwargs):
    @click.command(cls=CommandFinder, context_settings=dict(obj=kwargs))
    @click.version_option(version=__version__)
    @click.pass_context
    def cli(ctx):
        """Command line tool for os-aio-pod."""

    cli()
