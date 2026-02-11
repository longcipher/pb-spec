"""Version command for pb-spec CLI."""

import importlib.metadata

import click


@click.command("version")
def version_cmd():
    """Show version information."""
    ver = importlib.metadata.version("pb-spec")
    click.echo(f"pb-spec {ver}")
