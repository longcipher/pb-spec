"""Validate command for pb-spec with --plan, --build, and --task modes."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from pb_spec.exceptions import SpecNotFoundError
from pb_spec.output import Colors, print_error, print_info, print_success, print_warning
from pb_spec.validation.build import validate_build, validate_task
from pb_spec.validation.plan import validate_plan
from pb_spec.validation.result import ErrorSeverity, ValidationError, ValidationResult
from pb_spec.validation.rumdl import FormatResult, run_rumdl_format


def get_latest_spec_dir(specs_dir: Path | None = None) -> Path:
    """Get the latest feature spec directory from specs/."""
    if specs_dir is None:
        specs_dir = Path("specs")

    if not specs_dir.exists() or not specs_dir.is_dir():
        raise SpecNotFoundError("Directory 'specs/' not found. Run /pb-plan first.")

    spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
    if not spec_dirs:
        raise SpecNotFoundError("No feature specs found in 'specs/'.")

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")

    def sort_key(d: Path) -> tuple[int, str]:
        if date_pattern.match(d.name):
            return (1, d.name)  # date-prefixed dirs sort by name
        return (0, d.name)  # non-date dirs sort after

    return sorted(spec_dirs, key=sort_key)[-1]


def _report_validation_result(result: ValidationResult, label: str) -> None:
    """Print validation errors and warnings with colored output."""
    print_info(f"Running {label} Validation")
    for error in result.errors:
        _print_validation_error(error)
    for warning in result.warnings:
        if "structural checks passed" in warning or "properly marked as DONE" in warning:
            print_success(warning)
        else:
            print_warning(warning)


def _print_validation_error(error: ValidationError) -> None:
    """Print a single validation error with severity prefix."""
    severity_prefix = {
        ErrorSeverity.CRITICAL: "[CRITICAL]",
        ErrorSeverity.HIGH: "[HIGH]",
        ErrorSeverity.MEDIUM: "[MEDIUM]",
        ErrorSeverity.LOW: "[LOW]",
    }
    prefix = severity_prefix.get(error.severity, "")
    location = ""
    if error.file_path:
        location = f" ({error.file_path}"
        if error.line_number:
            location += f":{error.line_number}"
        if error.field_name:
            location += f" field '{error.field_name}'"
        location += ")"
    print_error(f"{prefix} {error.message}{location}")


def _report_format_result(result: FormatResult) -> None:
    """Print rumdl format results."""
    if not result.messages:
        return
    for msg in result.messages:
        if "timed out" in msg or "failed" in msg or "not found" in msg:
            print_warning(msg)
        else:
            print_success(msg)


def _report_scan_result(result: ValidationResult) -> bool:
    """Print scan issues grouped by type. Returns True if clean."""
    if result.is_valid:
        print_success("Codebase scan passed - no issues found.")
        return True

    passed = True
    severity_counts: dict[ErrorSeverity, int] = {}
    for error in result.errors:
        severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1

    for severity, count in sorted(severity_counts.items(), key=lambda x: x[0].value):
        print_error(f"Found {count} {severity.value} issue(s):")
        severity_errors = [e for e in result.errors if e.severity == severity]
        for error in severity_errors[:10]:
            location = ""
            if error.file_path:
                location = f" ({error.file_path}"
                if error.line_number:
                    location += f":{error.line_number}"
                location += ")"
            print_info(f"  {error.message}{location}")
        if len(severity_errors) > 10:
            print_info(f"  ... and {len(severity_errors) - 10} more")
        passed = False
    return passed


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
def validate_cmd(mode: str | None, specs_dir: Path | None) -> None:
    """Validate pb-spec workflow artifacts at different stages.

    Use --plan after /pb-plan to check spec structure.
    Use --build after /pb-build to verify task completion.
    Use --task for subagent self-check before signaling READY_FOR_EVAL.
    """
    if mode is None:
        click.echo("Error: Must specify one of --plan, --build, or --task")
        click.echo("Run 'pb-spec validate --help' for usage information.")
        sys.exit(1)

    all_passed = True

    if mode in ("plan", "build"):
        try:
            latest_spec = get_latest_spec_dir(specs_dir)
        except SpecNotFoundError as e:
            print_error(str(e))
            sys.exit(1)

        if mode == "plan":
            format_result = run_rumdl_format(latest_spec)
            _report_format_result(format_result)
            result: ValidationResult = validate_plan(latest_spec)
            _report_validation_result(result, "Post-Plan")
            all_passed = result.is_valid

        if mode == "build":
            result = validate_build(latest_spec)
            _report_validation_result(result, "Post-Build")
            all_passed = result.is_valid

    if mode == "task":
        result = validate_task()
        all_passed = _report_scan_result(result)

    if not all_passed:
        click.echo(
            f"\n{Colors.RED}❌ Validation Failed. Please fix the above issues.{Colors.RESET}"
        )
        sys.exit(1)
    else:
        click.echo(f"\n{Colors.GREEN}🎉 All validations passed successfully!{Colors.RESET}")
        sys.exit(0)
