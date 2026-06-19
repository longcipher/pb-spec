"""Terminal output formatting for validation results."""

from __future__ import annotations

from pb_spec.output import print_error, print_info, print_success, print_warning
from pb_spec.validation.result import ErrorSeverity, ValidationError, ValidationResult
from pb_spec.validation.rumdl import FormatResult

_SEVERITY_PREFIX: dict[ErrorSeverity, str] = {
    ErrorSeverity.CRITICAL: "[CRITICAL]",
    ErrorSeverity.HIGH: "[HIGH]",
    ErrorSeverity.MEDIUM: "[MEDIUM]",
    ErrorSeverity.LOW: "[LOW]",
}


def _format_location(error: ValidationError) -> str:
    if not error.file_path:
        return ""
    parts = [error.file_path]
    if error.line_number:
        parts.append(str(error.line_number))
    if error.field_name:
        parts.append(f"field '{error.field_name}'")
    return f" ({':'.join(parts[:2])}{' ' + ' '.join(parts[2:]) if len(parts) > 2 else ''})"


def report_validation_result(result: ValidationResult, label: str) -> None:
    """Print validation errors and warnings with colored output."""
    print_info(f"Running {label} Validation")
    for error in result.errors:
        print_validation_error(error)
    for warning in result.warnings:
        print_warning(warning)


def print_validation_error(error: ValidationError) -> None:
    """Print a single validation error with severity prefix."""
    prefix = _SEVERITY_PREFIX.get(error.severity, "")
    print_error(f"{prefix} {error.message}{_format_location(error)}")


def report_format_result(result: FormatResult) -> None:
    """Print rumdl format results."""
    if not result.messages:
        return
    for msg in result.messages:
        if result.success:
            print_success(msg)
        else:
            print_warning(msg)


def report_scan_result(result: ValidationResult) -> bool:
    """Print scan issues grouped by type and return whether the scan is clean.

    Side effect: prints formatted output to stdout.
    Returns True if no issues found, False otherwise.
    """
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
            print_info(f"  {error.message}{_format_location(error)}")
        if len(severity_errors) > 10:
            print_info(f"  ... and {len(severity_errors) - 10} more")
        passed = False
    return passed
