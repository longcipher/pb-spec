"""Version command for pb-spec CLI."""

import click

from pb_spec.versioning import get_version


@click.command("version")
def version_cmd():
    """Show version information."""
    click.echo(f"pb-spec {get_version()}")
