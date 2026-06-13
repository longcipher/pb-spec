"""Build validation logic for task completion and code quality."""

from __future__ import annotations

import logging
from pathlib import Path

from pb_spec.exceptions import FileReadError
from pb_spec.git_utils import get_git_modified_files
from pb_spec.validation.io import read_file_content, read_spec_file
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
    ValidationMode,
    ValidationResult,
    make_validation_error,
)
from pb_spec.validation.scanner import CodeScanner, IssueType, ScanResult

logger = logging.getLogger(__name__)


def validate_feature_scenarios(spec_dir: Path) -> list[ValidationError]:
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
                make_validation_error(
                    message=f"{feature_file.name} contains no Scenario definition",
                    file_path=str(feature_file),
                    severity=ErrorSeverity.HIGH,
                )
            )

    return errors


def run_codebase_scan(mode: ValidationMode, root_dir: Path | str = ".") -> ScanResult:
    """Scan codebase for code quality issues.

    Args:
        mode: ValidationMode.TASK for subagent self-check (scoped to git-modified
            files), ValidationMode.BUILD for full scan.
        root_dir: Root directory to scan. Defaults to current working directory.

    Returns:
        Pure ScanResult without side effects. Callers are responsible
        for presenting the results.
    """
    target_files: set[Path] | None = None
    if mode == ValidationMode.TASK:
        target_files = get_git_modified_files(root_dir)

    scanner = CodeScanner(
        root_dir=root_dir,
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
            make_validation_error(
                message=issue.message,
                file_path=issue.file_path,
                line_number=issue.line_number,
                severity=severity_map.get(issue.issue_type, ErrorSeverity.MEDIUM),
            )
        )
    return errors


def _validate_task_completion(task_blocks: list[TaskBlock], content: str) -> list[ValidationError]:
    """Validate that all tasks are marked DONE with complete steps.

    Args:
        task_blocks: Pre-parsed task blocks from parse_task_blocks().
        content: Original markdown content for checkbox regex matching.
    """
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
                    make_validation_error(
                        message=f"Task Blocked by DCR: {display_name}. Needs design refinement.",
                        file_path="tasks.md",
                        field_name="Status:",
                        severity=ErrorSeverity.HIGH,
                    )
                )
                continue
            case s if "🔴 TODO" in s or "🟡 IN PROGRESS" in s or s.strip() == "TODO":
                errors.append(
                    make_validation_error(
                        message=f"Task Unfinished: {display_name} is not marked as DONE.",
                        file_path="tasks.md",
                        field_name="Status:",
                        severity=ErrorSeverity.HIGH,
                    )
                )
                continue
            case _:
                errors.append(
                    make_validation_error(
                        message=f"Task Invalid Status: {display_name}. Missing 🟢 DONE.",
                        file_path="tasks.md",
                        field_name="Status:",
                    )
                )
                continue

        unchecked = UNCHECKED_TASK_CHECKBOX_RE.findall(task_block.content)
        if unchecked:
            errors.append(
                make_validation_error(
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
                make_validation_error(
                    message=(
                        f"Task '{display_name}' is marked DONE but contains no step checkboxes. "
                        "Contract requires at least one step."
                    ),
                    file_path="tasks.md",
                )
            )

    return errors


def _validate_task_completion_warnings(task_blocks: list[TaskBlock]) -> list[str]:
    """Collect warnings for non-DONE tasks (SKIPPED, OBSOLETE).

    Args:
        task_blocks: Pre-parsed task blocks from parse_task_blocks().
    """
    warnings: list[str] = []

    for task_block in task_blocks:
        display_name = task_display_name(task_block)
        status_field = task_block.fields.get("Status:", "")
        if "⏭️ SKIPPED" in status_field:
            warnings.append(f"Task Skipped: {display_name}. (Ignored in strict completion check)")

    return warnings


def _validate_codebase_scan(root_dir: Path | str = ".") -> list[ValidationError]:
    """Run codebase scan and return errors."""
    scan_result = run_codebase_scan(mode=ValidationMode.BUILD, root_dir=root_dir)
    if not scan_result.has_issues:
        return []

    errors = [
        make_validation_error(
            message="Codebase scan failed - found issues that need to be addressed.",
            severity=ErrorSeverity.HIGH,
        ),
    ]
    errors.extend(_scan_result_to_errors(scan_result))
    return errors


def validate_build(spec_dir: Path) -> ValidationResult:
    """Validate pb-build task completion (Orchestrator level).

    Performs read-only operations (file reads, git status, codebase scan).
    Returns a ValidationResult; callers are responsible for presenting results.
    """
    errors: list[ValidationError] = []
    warnings: list[str] = []

    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        return ValidationResult(
            is_valid=False,
            errors=[
                make_validation_error(
                    message="Missing required file: tasks.md",
                    file_path=str(tasks_file),
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    content, error_result = read_spec_file(tasks_file)
    if error_result is not None:
        return error_result
    if content is None:
        return ValidationResult(
            is_valid=False,
            errors=[
                make_validation_error(
                    message=f"Failed to read {tasks_file}",
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

    errors.extend(validate_feature_scenarios(spec_dir))

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_task(root_dir: Path | str = ".") -> ValidationResult:
    """Subagent self-check before signaling READY_FOR_EVAL.

    Args:
        root_dir: Root directory to scan. Defaults to current working directory.

    Returns:
        A pure ValidationResult without side effects.
        Callers are responsible for presenting the results.
    """
    scan_result = run_codebase_scan(mode=ValidationMode.TASK, root_dir=root_dir)
    if not scan_result.has_issues:
        return ValidationResult(is_valid=True)

    return ValidationResult(
        is_valid=False,
        errors=_scan_result_to_errors(scan_result),
    )
