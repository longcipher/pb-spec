"""Version command for pb-spec CLI."""

from __future__ import annotations

import click

from pb_spec.versioning import get_version


@click.command("version")
def version_cmd():
    """Show version information."""
    click.echo(f"pb-spec {get_version()}")
