"""Mutate command: incremental mutation testing on changed files."""

from __future__ import annotations

import subprocess
from pathlib import Path

import click

from pb_spec.output import print_error, print_success, print_warning


def mutation_script_path() -> Path | None:
    """Locate scripts/run-mutation-diff.sh relative to cwd or the package root."""
    candidates = [
        Path("scripts") / "run-mutation-diff.sh",
        Path(__file__).resolve().parents[3] / "scripts" / "run-mutation-diff.sh",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def build_mutate_command(
    script: Path,
    against: str | None = None,
    threshold: int | None = None,
) -> list[str]:
    """Build the incremental mutation runner invocation."""
    cmd = ["bash", str(script)]
    if against:
        cmd += ["--against", against]
    if threshold is not None:
        cmd += ["--threshold", str(threshold)]
    return cmd


@click.command("mutate")
@click.option(
    "--against",
    default=None,
    help="Git ref to diff against (default: main/master/HEAD).",
)
@click.option(
    "--threshold",
    type=int,
    default=None,
    help="Minimum mutation score threshold (default: 85).",
)
@click.pass_context
def mutate_cmd(
    ctx: click.Context,
    against: str | None,
    threshold: int | None,
) -> None:
    """Run incremental mutation testing on changed files.

    Mutates only files changed since the base ref, keeping the AI loop fast.
    Surviving mutants mean the TDD test suite is not strict enough — strengthen
    assertions until every mutant on changed code is killed.
    """
    script = mutation_script_path()
    if script is None:
        print_error(
            "scripts/run-mutation-diff.sh not found. Clone the pb-spec repo or install the script."
        )
        ctx.exit(1)

    exit_code = subprocess.call(build_mutate_command(script, against, threshold))
    if exit_code == 2:
        print_warning("No changed files to mutate — nothing to verify.")
        ctx.exit(0)
    if exit_code == 0:
        print_success("Mutation gate passed: all changed-code mutants killed (score >= threshold).")
    else:
        print_error(
            f"Mutation gate failed (exit {exit_code}). "
            "Surviving mutants detected — strengthen TDD assertions."
        )
    ctx.exit(exit_code)
