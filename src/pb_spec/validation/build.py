"""Build validation logic for task completion and code quality."""

from __future__ import annotations

from pathlib import Path

from pb_spec.exceptions import FileReadError
from pb_spec.git_utils import get_git_modified_files
from pb_spec.validation.parser import (
    TASK_CHECKBOX_RE,
    UNCHECKED_TASK_CHECKBOX_RE,
    MarkdownParser,
    task_display_name,
)
from pb_spec.validation.plan import read_file_content
from pb_spec.validation.result import ErrorSeverity, ValidationError, ValidationResult
from pb_spec.validation.scanner import CodeScanner, IssueType, ScanResult


def _make_validation_error(
    message: str,
    file_path: str | None = None,
    line_number: int | None = None,
    field_name: str | None = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
) -> ValidationError:
    """Create a ValidationError with consistent defaults."""
    return ValidationError(
        severity=severity,
        message=message,
        file_path=file_path,
        line_number=line_number,
        field_name=field_name,
    )


def validate_feature_scenarios(spec_dir: Path) -> list[ValidationError]:
    """Validate that .feature files contain at least one Scenario."""
    errors: list[ValidationError] = []
    features_dir = spec_dir / "features"
    if not features_dir.exists():
        return errors

    for feature_file in features_dir.glob("*.feature"):
        try:
            content = read_file_content(feature_file)
        except FileReadError:
            continue
        if "Scenario" not in content:
            errors.append(
                _make_validation_error(
                    message=f"{feature_file.name} contains no Scenario definition",
                    file_path=str(feature_file),
                    severity=ErrorSeverity.HIGH,
                )
            )

    return errors


def run_codebase_scan(mode: str) -> ScanResult:
    """Scan codebase for code quality issues.

    Args:
        mode: "build" for full scan, "task" for subagent self-check.
            In task mode, scanning is scoped to git-modified files only
            to prevent subagents from chasing historical tech debt.

    Returns:
        Pure ScanResult without side effects. Callers are responsible
        for presenting the results.
    """
    target_files: set[Path] | None = None
    if mode == "task":
        target_files = get_git_modified_files()

    scanner = CodeScanner(
        root_dir=".",
        check_skipped_tests=True,
        check_not_implemented=True,
        check_todos=True,
        check_debug_artifacts=True,
        target_files=target_files,
    )

    return scanner.scan()


def _scan_result_to_errors(scan_result: ScanResult) -> list[ValidationError]:
    """Convert ScanResult issues to structured ValidationErrors."""
    errors: list[ValidationError] = []
    severity_map = {
        IssueType.SKIPPED_TEST: ErrorSeverity.HIGH,
        IssueType.NOT_IMPLEMENTED: ErrorSeverity.HIGH,
        IssueType.TODO: ErrorSeverity.LOW,
        IssueType.DEBUG_ARTIFACT: ErrorSeverity.MEDIUM,
    }
    for issue in scan_result.issues:
        errors.append(
            _make_validation_error(
                message=issue.message,
                file_path=issue.file_path,
                line_number=issue.line_number,
                severity=severity_map.get(issue.issue_type, ErrorSeverity.MEDIUM),
            )
        )
    return errors


def validate_build(spec_dir: Path) -> ValidationResult:
    """Validate pb-build task completion (Orchestrator level).

    Returns a pure ValidationResult without side effects.
    Callers are responsible for presenting the results.
    """
    errors: list[ValidationError] = []
    warnings: list[str] = []

    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        return ValidationResult(
            is_valid=False,
            errors=[
                _make_validation_error(
                    message=f"Missing {tasks_file.name}",
                    file_path=str(tasks_file),
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    try:
        content = read_file_content(tasks_file)
    except FileReadError as e:
        return ValidationResult(
            is_valid=False,
            errors=[
                _make_validation_error(
                    message=str(e),
                    file_path=str(tasks_file),
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    parser = MarkdownParser()
    task_blocks = parser.parse_task_blocks(content)

    for task_block in task_blocks:
        display_name = task_display_name(task_block)

        status_field = task_block.fields.get("Status:", "")
        if "🟢 DONE" not in status_field:
            if "⏭️ SKIPPED" in status_field:
                warnings.append(
                    f"Task Skipped: {display_name}. (Ignored in strict completion check)"
                )
            elif "⛔ OBSOLETE" in status_field:
                pass  # ignored in strict completion check
            elif "🔴 TODO" in status_field or "🟡 IN PROGRESS" in status_field:
                errors.append(
                    _make_validation_error(
                        message=f"Task Unfinished: {display_name} is not marked as DONE.",
                        file_path="tasks.md",
                        field_name="Status:",
                        severity=ErrorSeverity.HIGH,
                    )
                )
            elif "🔄 DCR" in status_field:
                errors.append(
                    _make_validation_error(
                        message=f"Task Blocked by DCR: {display_name}. Needs design refinement.",
                        file_path="tasks.md",
                        field_name="Status:",
                        severity=ErrorSeverity.HIGH,
                    )
                )
            else:
                errors.append(
                    _make_validation_error(
                        message=f"Task Invalid Status: {display_name}. Missing 🟢 DONE.",
                        file_path="tasks.md",
                        field_name="Status:",
                    )
                )
            continue

        unchecked = UNCHECKED_TASK_CHECKBOX_RE.findall(task_block.content)
        if unchecked:
            errors.append(
                _make_validation_error(
                    message=(
                        f"Task '{display_name}' is marked DONE but has incomplete steps:\n  "
                        + "\n  ".join(unchecked)
                    ),
                    file_path="tasks.md",
                )
            )

        all_checkboxes = TASK_CHECKBOX_RE.findall(task_block.content)
        if not all_checkboxes:
            errors.append(
                _make_validation_error(
                    message=(
                        f"Task '{display_name}' is marked DONE but contains no step checkboxes. "
                        "Contract requires at least one step."
                    ),
                    file_path="tasks.md",
                )
            )

    scan_result = run_codebase_scan(mode="build")
    if scan_result.has_issues:
        errors.extend(_scan_result_to_errors(scan_result))
        errors.insert(
            0,
            _make_validation_error(
                message="Codebase scan failed - found issues that need to be addressed.",
                severity=ErrorSeverity.HIGH,
            ),
        )

    feature_errors = validate_feature_scenarios(spec_dir)
    errors.extend(feature_errors)

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_task() -> ValidationResult:
    """Subagent self-check before signaling READY_FOR_EVAL.

    Returns a pure ValidationResult without side effects.
    Callers are responsible for presenting the results.
    """
    scan_result = run_codebase_scan(mode="task")
    if not scan_result.has_issues:
        return ValidationResult(is_valid=True)

    return ValidationResult(
        is_valid=False,
        errors=_scan_result_to_errors(scan_result),
    )
