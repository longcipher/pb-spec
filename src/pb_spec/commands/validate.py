"""Validate command for pb-spec CLI."""

from __future__ import annotations

from pathlib import Path

import click

from pb_spec.validation.runner import run_feedback_validation, run_spec_validation


@click.command("validate")
@click.argument(
    "target",
    metavar="TARGET",
    type=click.Path(path_type=Path, file_okay=True, dir_okay=True),
)
def validate_cmd(target: Path) -> None:
    """Validate a generated spec directory or feedback packet markdown file."""
    if target.is_dir():
        result = run_spec_validation(target)
    elif target.is_file():
        result = run_feedback_validation(target)
    else:
        raise click.ClickException(f"Validation target does not exist: {target}")

    if not result.is_valid():
        error_lines = "\n".join(f"- {error}" for error in result.to_error_strings())
        raise click.ClickException(f"Validation failed:\n{error_lines}")

    click.echo(f"Validation passed for {target}")
