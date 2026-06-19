"""Build validation logic for task completion and code quality."""

from __future__ import annotations

import logging
from pathlib import Path

from pb_spec.exceptions import FileReadError
from pb_spec.git_utils import get_git_modified_files
from pb_spec.validation.io import read_file_content
from pb_spec.validation.parser import (
    TASK_CHECKBOX_RE,
    UNCHECKED_TASK_CHECKBOX_RE,
    TaskBlock,
    parse_task_blocks,
    task_display_name,
)
from pb_spec.validation.result import (
    ErrorSeverity,
    ValidationError,
    ValidationResult,
)
from pb_spec.validation.scanner import CodeScanner, IssueType, ScanResult

logger = logging.getLogger(__name__)


def _scan_result_to_errors(scan_result: ScanResult) -> list[ValidationError]:
    """Convert ScanResult issues to structured ValidationErrors."""
    severity_map = {
        IssueType.SKIPPED_TEST: ErrorSeverity.HIGH,
        IssueType.NOT_IMPLEMENTED: ErrorSeverity.HIGH,
        IssueType.TODO: ErrorSeverity.LOW,
        IssueType.DEBUG_ARTIFACT: ErrorSeverity.MEDIUM,
    }
    return [
        ValidationError(
            message=issue.message,
            file_path=issue.file_path,
            line_number=issue.line_number,
            severity=severity_map.get(issue.issue_type, ErrorSeverity.MEDIUM),
        )
        for issue in scan_result.issues
    ]


def _validate_task_completion(task_blocks: list[TaskBlock], content: str) -> list[ValidationError]:
    """Validate that all tasks are marked DONE with complete steps."""
    errors: list[ValidationError] = []

    for task_block in task_blocks:
        display_name = task_display_name(task_block)

        status_field = task_block.fields.get("Status:", "")
        match status_field:
            case s if "🟢 DONE" in s:
                pass  # continue to checkbox check below
            case s if "⏭️ SKIPPED" in s:
                continue  # warned by caller, skip checkbox check
            case s if "⛔ OBSOLETE" in s:
                continue  # ignored in strict completion check
            case s if "🔄 DCR" in s:
                errors.append(
                    ValidationError(
                        message=f"Task Blocked by DCR: {display_name}. Needs design refinement.",
                        file_path="tasks.md",
                        field_name="Status:",
                        severity=ErrorSeverity.HIGH,
                    )
                )
                continue
            case s if "🔴 TODO" in s or "🟡 IN PROGRESS" in s or s.strip() == "TODO":
                errors.append(
                    ValidationError(
                        message=f"Task Unfinished: {display_name} is not marked as DONE.",
                        file_path="tasks.md",
                        field_name="Status:",
                        severity=ErrorSeverity.HIGH,
                    )
                )
                continue
            case _:
                errors.append(
                    ValidationError(
                        message=f"Task Invalid Status: {display_name}. Missing 🟢 DONE.",
                        file_path="tasks.md",
                        field_name="Status:",
                    )
                )
                continue

        unchecked = UNCHECKED_TASK_CHECKBOX_RE.findall(task_block.content)
        if unchecked:
            errors.append(
                ValidationError(
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
                ValidationError(
                    message=(
                        f"Task '{display_name}' is marked DONE but contains no step checkboxes. "
                        "Contract requires at least one step."
                    ),
                    file_path="tasks.md",
                )
            )

    return errors


def _validate_task_completion_warnings(task_blocks: list[TaskBlock]) -> list[str]:
    """Collect warnings for non-DONE tasks (SKIPPED, OBSOLETE)."""
    return [
        f"Task Skipped: {task_display_name(tb)}. (Ignored in strict completion check)"
        for tb in task_blocks
        if "⏭️ SKIPPED" in tb.fields.get("Status:", "")
    ]


def _run_codebase_scan(git_only: bool = False, root_dir: Path | str = ".") -> ScanResult:
    """Scan codebase for code quality issues."""
    target_files: set[Path] | None = None
    if git_only:
        target_files = get_git_modified_files(root_dir)
    scanner = CodeScanner(root_dir=root_dir, target_files=target_files)
    return scanner.scan()


def _validate_codebase_scan(root_dir: Path | str = ".") -> list[ValidationError]:
    """Run codebase scan and return errors."""
    scan_result = _run_codebase_scan(git_only=False, root_dir=root_dir)
    if not scan_result.has_issues:
        return []

    errors = [
        ValidationError(
            message="Codebase scan failed - found issues that need to be addressed.",
            severity=ErrorSeverity.HIGH,
        ),
    ]
    errors.extend(_scan_result_to_errors(scan_result))
    return errors


def _validate_feature_scenarios(spec_dir: Path) -> list[ValidationError]:
    """Validate that .feature files contain at least one Scenario."""
    errors: list[ValidationError] = []
    features_dir = spec_dir / "features"
    if not features_dir.exists():
        return errors

    for feature_file in features_dir.glob("*.feature"):
        try:
            content = read_file_content(feature_file)
        except FileReadError as e:
            logger.warning("Cannot read %s: %s", feature_file, e)
            continue
        if "Scenario" not in content:
            errors.append(
                ValidationError(
                    message=f"{feature_file.name} contains no Scenario definition",
                    file_path=str(feature_file),
                    severity=ErrorSeverity.HIGH,
                )
            )

    return errors


def validate_build(spec_dir: Path) -> ValidationResult:
    """Validate pb-build task completion (Orchestrator level).

    Returns a ValidationResult; callers are responsible for presenting results.
    """
    errors: list[ValidationError] = []
    warnings: list[str] = []

    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        return ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
                    message="Missing required file: tasks.md",
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
                ValidationError(
                    message=str(e),
                    file_path=str(tasks_file),
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    task_blocks = parse_task_blocks(content)
    warnings.extend(_validate_task_completion_warnings(task_blocks))
    errors.extend(_validate_task_completion(task_blocks, content))

    # Determine project root: spec_dir is typically specs/xxx, so root is two levels up
    project_root = spec_dir.parent.parent if spec_dir.parent.name == "specs" else spec_dir.parent
    errors.extend(_validate_codebase_scan(root_dir=project_root))

    errors.extend(_validate_feature_scenarios(spec_dir))

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_task(root_dir: Path | str = ".") -> ValidationResult:
    """Subagent self-check before signaling READY_FOR_EVAL.

    Returns a pure ValidationResult without side effects.
    """
    scan_result = _run_codebase_scan(git_only=True, root_dir=root_dir)
    if not scan_result.has_issues:
        return ValidationResult(is_valid=True)

    return ValidationResult(
        is_valid=False,
        errors=_scan_result_to_errors(scan_result),
    )
