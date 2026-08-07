"""Verify command: strict TDD suite then the incremental mutation gate."""

from __future__ import annotations

import subprocess

import click

from pb_spec.commands.mutate import build_mutate_command, mutation_script_path
from pb_spec.commands.test import build_pytest_command
from pb_spec.output import print_error, print_info, print_success, print_warning


@click.command("verify")
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
@click.option(
    "--coverage/--no-coverage",
    "coverage",
    default=True,
    help="Run tests with coverage (default: on).",
)
@click.pass_context
def verify_cmd(
    ctx: click.Context,
    against: str | None,
    threshold: int | None,
    coverage: bool,
) -> None:
    """One-command gate: TDD tests (with coverage) + incremental mutation check."""
    print_info("Step 1/2: Running strict TDD test suite")
    test_rc = subprocess.call(build_pytest_command(parallel=True, coverage=coverage))
    if test_rc != 0:
        print_error(f"TDD test suite failed (exit {test_rc}). Fix tests before mutating.")
        ctx.exit(test_rc)

    print_info("Step 2/2: Running incremental mutation gate")
    script = mutation_script_path()
    if script is None:
        print_error(
            "scripts/run-mutation-diff.sh not found. Clone the pb-spec repo or install the script."
        )
        ctx.exit(1)

    mut_rc = subprocess.call(build_mutate_command(script, against, threshold))
    if mut_rc == 2:
        print_warning("No changed files to mutate — nothing to verify.")
        print_success("Verify passed: TDD suite green.")
        ctx.exit(0)
    if mut_rc == 0:
        print_success("Verify passed: TDD suite green + all changed-code mutants killed.")
    else:
        print_error(
            f"Verify failed (exit {mut_rc}). "
            "Surviving mutants detected — strengthen TDD assertions."
        )
    ctx.exit(mut_rc)
