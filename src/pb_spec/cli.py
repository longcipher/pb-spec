"""CLI entry point for pb-spec."""

import click

from pb_spec import __version__
from pb_spec.commands.init import init_cmd
from pb_spec.commands.update import update_cmd
from pb_spec.commands.version import version_cmd


@click.group()
@click.version_option(version=__version__, prog_name="pb-spec")
def main():
    """pb-spec (Plan-Build Spec) - A CLI tool for managing AI coding assistant skills."""


main.add_command(init_cmd, "init")
main.add_command(version_cmd, "version")
main.add_command(update_cmd, "update")
