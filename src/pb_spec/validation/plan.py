"""Plan validation logic for design.md and tasks.md."""

from __future__ import annotations

from pathlib import Path

from pb_spec.exceptions import FileReadError
from pb_spec.validation.parser import (
    ALLOWED_LOOP_TYPES,
    ALLOWED_TASK_STATUSES,
    NA_REASON_FIELDS,
    TASK_CHECKBOX_RE,
    MarkdownParser,
    is_bare_na,
    task_display_name,
    validate_contract_blocks,
)
from pb_spec.validation.result import ErrorSeverity, ValidationError, ValidationResult


def read_file_content(file_path: Path) -> str:
    """Safely read file content with error handling."""
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise FileReadError(f"Cannot read file {file_path}: {e}") from e


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


def validate_required_files_exist(spec_dir: Path) -> ValidationResult:
    """Check that required files exist."""
    errors: list[ValidationError] = []
    design_file = spec_dir / "design.md"
    tasks_file = spec_dir / "tasks.md"

    for f in [design_file, tasks_file]:
        if not f.exists():
            errors.append(
                _make_validation_error(
                    message=f"Missing required file: {f.name}",
                    file_path=str(f),
                    severity=ErrorSeverity.CRITICAL,
                )
            )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def detect_design_mode(content: str) -> tuple[bool, list[str]]:
    """Detect design.md mode and return required sections."""
    is_full_mode = "Executive Summary" in content or "Requirements & Goals" in content

    if is_full_mode:
        required_sections = [
            "Executive Summary",
            "Requirements & Goals",
            "Architecture Overview",
            "Detailed Design",
            "Verification & Testing Strategy",
            "Implementation Plan",
        ]
    else:
        required_sections = [
            "Summary",
            "Approach",
            "Architecture Decisions",
            "BDD/TDD Strategy",
            "Code Simplification Constraints",
            "BDD Scenario Inventory",
            "Existing Components to Reuse",
            "Verification",
        ]

    return is_full_mode, required_sections


def validate_design_structure(spec_dir: Path) -> ValidationResult:
    """Validate design.md required sections."""
    errors: list[ValidationError] = []
    warnings: list[str] = []
    design_file = spec_dir / "design.md"
    if not design_file.exists():
        return ValidationResult(
            is_valid=False,
            errors=[
                _make_validation_error(
                    message="design.md file does not exist",
                    file_path="design.md",
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    try:
        content = read_file_content(design_file)
    except FileReadError as e:
        return ValidationResult(
            is_valid=False,
            errors=[
                _make_validation_error(
                    message=str(e),
                    file_path="design.md",
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    is_full_mode, required_sections = detect_design_mode(content)

    for sec in required_sections:
        if sec not in content:
            errors.append(
                _make_validation_error(
                    message=f"design.md is missing required section: '{sec}'",
                    file_path="design.md",
                    field_name=sec,
                )
            )

    if not errors:
        mode_name = "full" if is_full_mode else "lightweight"
        warnings.append(f"design.md ({mode_name} mode) structural checks passed.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_tasks_structure(spec_dir: Path) -> ValidationResult:
    """Validate tasks.md structure and required fields."""
    errors: list[ValidationError] = []
    warnings: list[str] = []
    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        return ValidationResult(
            is_valid=False,
            errors=[
                _make_validation_error(
                    message="tasks.md file does not exist",
                    file_path="tasks.md",
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
                    file_path="tasks.md",
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    parser = MarkdownParser()
    task_blocks = parser.parse_task_blocks(content)

    if not task_blocks:
        return ValidationResult(
            is_valid=False,
            errors=[
                _make_validation_error(
                    message=(
                        "tasks.md does not contain any valid '## Task X.Y:' "
                        "or '### Task X.Y:' definitions."
                    ),
                    file_path="tasks.md",
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    contract_errors = validate_contract_blocks(content)
    for msg in contract_errors:
        errors.append(
            _make_validation_error(
                message=msg,
                file_path="tasks.md",
            )
        )

    required_task_fields = [
        "Context:",
        "Verification:",
        "Scenario Coverage:",
        "Loop Type:",
        "Behavioral Contract:",
        "Simplification Focus:",
        "Status:",
        "BDD Verification:",
        "Advanced Test Verification:",
        "Runtime Verification:",
    ]

    seen_task_ids: set[str] = set()

    for task_block in task_blocks:
        display_name = task_display_name(task_block)

        if task_block.id in seen_task_ids:
            errors.append(
                _make_validation_error(
                    message=f"Duplicate task ID found in tasks.md: Task {task_block.id}",
                    file_path="tasks.md",
                    severity=ErrorSeverity.HIGH,
                )
            )
        seen_task_ids.add(task_block.id)

        for required_field in required_task_fields:
            if required_field not in task_block.fields:
                errors.append(
                    _make_validation_error(
                        message=f"Task '{display_name}' is missing required field: '{required_field}'",
                        file_path="tasks.md",
                        field_name=required_field,
                    )
                )
            elif not task_block.fields[required_field].strip():
                errors.append(
                    _make_validation_error(
                        message=f"Task '{display_name}' has empty required field: '{required_field}'",
                        file_path="tasks.md",
                        field_name=required_field,
                    )
                )
            elif required_field in NA_REASON_FIELDS and is_bare_na(
                task_block.fields[required_field]
            ):
                errors.append(
                    _make_validation_error(
                        message=(
                            f"Task '{display_name}' field '{required_field}' "
                            "must be N/A with a brief reason."
                        ),
                        file_path="tasks.md",
                        field_name=required_field,
                    )
                )

        loop_type = task_block.fields.get("Loop Type:", "").strip()
        if loop_type and loop_type not in ALLOWED_LOOP_TYPES:
            errors.append(
                _make_validation_error(
                    message=(
                        f"Task '{display_name}' has invalid Loop Type: '{loop_type}'. "
                        f"Allowed values: {', '.join(sorted(ALLOWED_LOOP_TYPES))}"
                    ),
                    file_path="tasks.md",
                    field_name="Loop Type:",
                )
            )

        status = task_block.fields.get("Status:", "").strip()
        if status and status not in ALLOWED_TASK_STATUSES:
            errors.append(
                _make_validation_error(
                    message=(
                        f"Task '{display_name}' has invalid Status: '{status}'. "
                        "Use one of the contract task state markers."
                    ),
                    file_path="tasks.md",
                    field_name="Status:",
                )
            )

        if not TASK_CHECKBOX_RE.search(task_block.content):
            errors.append(
                _make_validation_error(
                    message=(
                        f"Task '{display_name}' contains no step checkboxes. "
                        "Contract requires at least one checkbox step."
                    ),
                    file_path="tasks.md",
                )
            )

    if not errors:
        warnings.append("tasks.md structural checks passed.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_features_directory(spec_dir: Path) -> ValidationResult:
    """Validate features directory has feature files."""
    warnings: list[str] = []
    features_dir = spec_dir / "features"
    has_features = features_dir.exists() and list(features_dir.glob("*.feature"))

    if not has_features:
        warnings.append("No .feature files found. (OK if this is a TDD-only lightweight spec)")
    else:
        warnings.append("Found Gherkin .feature files.")

    return ValidationResult(is_valid=True, warnings=warnings)


def combine_validation_results(*results: ValidationResult) -> ValidationResult:
    """Combine multiple ValidationResult objects."""
    combined_errors: list[ValidationError] = []
    combined_warnings: list[str] = []
    is_valid = True

    for result in results:
        combined_errors.extend(result.errors)
        combined_warnings.extend(result.warnings)
        is_valid &= result.is_valid

    return ValidationResult(is_valid=is_valid, errors=combined_errors, warnings=combined_warnings)


def validate_plan(spec_dir: Path) -> ValidationResult:
    """Validate pb-plan generated documents.

    Returns a pure ValidationResult without side effects.
    Callers are responsible for presenting the results.
    """
    results = [
        validate_required_files_exist(spec_dir),
        validate_design_structure(spec_dir),
        validate_tasks_structure(spec_dir),
        validate_features_directory(spec_dir),
    ]

    return combine_validation_results(*results)
