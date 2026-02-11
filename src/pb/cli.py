"""CLI entry point for pb."""

import click

from pb.commands.init import init_cmd
from pb.commands.update import update_cmd
from pb.commands.version import version_cmd


@click.group()
@click.version_option(package_name="pb")
def main():
    """pb (Plan-Build) - A CLI tool for managing AI coding assistant skills."""


main.add_command(init_cmd, "init")
main.add_command(version_cmd, "version")
main.add_command(update_cmd, "update")
