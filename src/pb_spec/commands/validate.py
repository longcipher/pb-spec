"""Validate command for pb-spec with --plan, --build, and --task modes."""

from __future__ import annotations

from pathlib import Path

import click

from pb_spec.commands.discovery import get_latest_spec_dir
from pb_spec.commands.report import (
    report_format_result,
    report_scan_result,
    report_validation_result,
)
from pb_spec.exceptions import SpecNotFoundError
from pb_spec.output import print_error, print_success
from pb_spec.validation.build import validate_build, validate_task
from pb_spec.validation.plan import load_contract_config, validate_plan
from pb_spec.validation.rumdl import run_rumdl_format


@click.command("validate")
@click.option(
    "--plan",
    "mode",
    flag_value="plan",
    help="Validate and format specs after /pb-plan.",
)
@click.option(
    "--build",
    "mode",
    flag_value="build",
    help="Validate strict completion after /pb-build.",
)
@click.option(
    "--task",
    "mode",
    flag_value="task",
    help="Subagent self-check before signaling READY_FOR_EVAL.",
)
@click.option(
    "--specs-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to specs directory (default: specs/).",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path, exists=True),
    default=None,
    help="Path to project-specific contract_sections.toml.",
)
@click.pass_context
def validate_cmd(
    ctx: click.Context,
    mode: str | None,
    specs_dir: Path | None,
    config_path: Path | None,
) -> None:
    """Validate pb-spec workflow artifacts at different stages.

    Use --plan after /pb-plan to check spec structure.
    Use --build after /pb-build to verify task completion.
    Use --task for subagent self-check before signaling READY_FOR_EVAL.
    Use --config to load project-specific validation rules.
    """
    if config_path is not None:
        load_contract_config(config_path)
    if mode is None:
        print_error("Must specify one of --plan, --build, or --task")
        click.echo("Run 'pb-spec validate --help' for usage information.")
        ctx.exit(1)

    all_passed = True

    if mode in ("plan", "build"):
        try:
            latest_spec = get_latest_spec_dir(specs_dir)
        except SpecNotFoundError as e:
            print_error(str(e))
            ctx.exit(1)

        if mode == "plan":
            format_result = run_rumdl_format(latest_spec)
            report_format_result(format_result)
            result = validate_plan(latest_spec)
            report_validation_result(result, "Post-Plan")
            all_passed = result.is_valid

        elif mode == "build":
            result = validate_build(latest_spec)
            report_validation_result(result, "Post-Build")
            all_passed = result.is_valid

    elif mode == "task":
        result = validate_task()
        all_passed = report_scan_result(result)

    if not all_passed:
        print_error("Validation Failed. Please fix the above issues.")
        ctx.exit(1)
    else:
        print_success("All validations passed successfully!")
        ctx.exit(0)
