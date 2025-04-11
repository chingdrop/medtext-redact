import click

from vega_tools.commands import main


@click.group()
def cli():
    pass


cli.add_command(main)

if __name__ == '__main__':
    cli()
