"""Main CLI entry point for pb-spec."""

from __future__ import annotations

import click

from pb_spec import __version__
from pb_spec.commands.validate import validate_cmd


@click.group()
@click.version_option(version=__version__, prog_name="pb-spec")
def main() -> None:
    """Plan-Build Spec (pb-spec): A CLI tool for managing AI coding assistant skills."""


main.add_command(validate_cmd)


if __name__ == "__main__":
    main()
