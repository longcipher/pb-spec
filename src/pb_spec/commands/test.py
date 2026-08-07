"""Test command: fast, strict TDD test runner (pytest)."""

from __future__ import annotations

import subprocess
import sys

import click

from pb_spec.output import print_error, print_success


def build_pytest_command(
    parallel: bool = True,
    coverage: bool = False,
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build the pytest invocation.

    Returns a command list suitable for subprocess. Parallel execution uses
    pytest-xdist (``-n auto``); coverage uses pytest-cov with a term report and
    the configured ``fail_under`` gate.
    """
    cmd = [sys.executable, "-m", "pytest"]
    if parallel:
        cmd += ["-n", "auto"]
    if coverage:
        cmd += ["--cov=pb_spec", "--cov-report=term-missing"]
    cmd += list(extra_args)
    return cmd


def run_test_suite(
    parallel: bool = True,
    coverage: bool = False,
    extra_args: tuple[str, ...] = (),
) -> int:
    """Run the pytest suite and return its exit code."""
    return subprocess.call(
        build_pytest_command(parallel=parallel, coverage=coverage, extra_args=extra_args)
    )


@click.command("test", context_settings={"ignore_unknown_options": True})
@click.option(
    "--parallel/--serial",
    "parallel",
    default=True,
    help="Run tests in parallel with pytest-xdist (default: parallel).",
)
@click.option(
    "--coverage",
    is_flag=True,
    help="Report coverage with pytest-cov (fail_under=80).",
)
@click.argument("pytest_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def test_cmd(
    ctx: click.Context,
    parallel: bool,
    coverage: bool,
    pytest_args: tuple[str, ...],
) -> None:
    """Run the strict TDD test suite (pytest).

    Extra positional arguments are passed through to pytest unchanged, e.g.
    ``pb-spec test tests/test_parser.py -k boundary``.
    """
    exit_code = run_test_suite(parallel=parallel, coverage=coverage, extra_args=pytest_args)
    if exit_code == 0:
        print_success("TDD test suite passed.")
    else:
        print_error(f"TDD test suite failed (exit {exit_code}).")
    ctx.exit(exit_code)
