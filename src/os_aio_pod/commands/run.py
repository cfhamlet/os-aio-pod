import click


@click.command()
@click.option('--debug', is_flag=True,  help='Enable debug mode.')
@click.option('-c', '--config-file',
              default='config.py', show_default=True,
              type=click.File(mode='r'), help='Config file.')
@click.pass_context
def cli(ctx, **kwargs):
    '''Run server.'''

    ctx.ensure_object(dict)

    kwargs = dict([(k, v) for k, v in kwargs.items() if v])
    print(kwargs)
