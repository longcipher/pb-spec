"""Version command for pb CLI."""

import importlib.metadata

import click


@click.command("version")
def version_cmd():
    """Show version information."""
    ver = importlib.metadata.version("pb")
    click.echo(f"pb {ver}")
