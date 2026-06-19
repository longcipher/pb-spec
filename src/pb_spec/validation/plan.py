"""Plan validation logic for design.md and tasks.md."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from pb_spec.exceptions import FileReadError
from pb_spec.validation.io import read_file_content
from pb_spec.validation.parser import (
    ALLOWED_LOOP_TYPES,
    ALLOWED_TASK_STATUSES,
    TASK_CHECKBOX_RE,
    is_bare_na,
    parse_task_blocks,
    task_display_name,
    validate_contract_blocks,
)
from pb_spec.validation.result import (
    ErrorSeverity,
    ValidationError,
    ValidationResult,
)

_DEFAULT_CONTRACT_CONFIG_PATH = Path(__file__).parent / "contract_sections.toml"

_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def _load_config(config_path: Path | None = None) -> None:
    """Load contract configuration from TOML file into module globals."""
    global _FULL_MODE_REQUIRED, _LIGHTWEIGHT_MODE_REQUIRED
    global _TASK_REQUIRED_FIELDS, _NA_REASON_FIELDS

    path = config_path or _DEFAULT_CONTRACT_CONFIG_PATH
    with path.open("rb") as f:
        config = tomllib.load(f)

    _FULL_MODE_REQUIRED = list(config["full_mode"]["required_sections"])
    _LIGHTWEIGHT_MODE_REQUIRED = list(config["lightweight_mode"]["required_sections"])
    _TASK_REQUIRED_FIELDS = list(config["tasks"]["required_fields"])
    _NA_REASON_FIELDS = frozenset(config["tasks"]["na_reason_fields"])


# ponytail: eager load at import time; module path is static
_FULL_MODE_REQUIRED: list[str] = []
_LIGHTWEIGHT_MODE_REQUIRED: list[str] = []
_TASK_REQUIRED_FIELDS: list[str] = []
_NA_REASON_FIELDS: frozenset[str] = frozenset()
_load_config()


def load_contract_config(config_path: Path | None = None) -> None:
    """Reload contract configuration (used by CLI --config override)."""
    _load_config(config_path)


def validate_design_structure(spec_dir: Path) -> ValidationResult:
    """Validate design.md required sections."""
    errors: list[ValidationError] = []
    warnings: list[str] = []
    design_file = spec_dir / "design.md"
    if not design_file.exists():
        return ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
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
                ValidationError(
                    message=str(e),
                    file_path="design.md",
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    headings = {m.group(1).strip() for m in _HEADING_RE.finditer(content)}
    is_full_mode = "Executive Summary" in headings or "Requirements & Goals" in headings
    required_sections = list(_FULL_MODE_REQUIRED if is_full_mode else _LIGHTWEIGHT_MODE_REQUIRED)

    for sec in required_sections:
        if sec not in headings:
            errors.append(
                ValidationError(
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
                ValidationError(
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
                ValidationError(
                    message=str(e),
                    file_path="tasks.md",
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    task_blocks = parse_task_blocks(content)

    if not task_blocks:
        return ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
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
        errors.append(ValidationError(message=msg, file_path="tasks.md"))

    seen_task_ids: set[str] = set()

    for task_block in task_blocks:
        display_name = task_display_name(task_block)

        if task_block.id in seen_task_ids:
            errors.append(
                ValidationError(
                    message=f"Duplicate task ID found in tasks.md: Task {task_block.id}",
                    file_path="tasks.md",
                    severity=ErrorSeverity.HIGH,
                )
            )
        seen_task_ids.add(task_block.id)

        for required_field in _TASK_REQUIRED_FIELDS:
            if required_field not in task_block.fields:
                errors.append(
                    ValidationError(
                        message=f"Task '{display_name}' is missing required field: '{required_field}'",
                        file_path="tasks.md",
                        field_name=required_field,
                    )
                )
            elif not task_block.fields[required_field].strip():
                errors.append(
                    ValidationError(
                        message=f"Task '{display_name}' has empty required field: '{required_field}'",
                        file_path="tasks.md",
                        field_name=required_field,
                    )
                )
            elif required_field in _NA_REASON_FIELDS and is_bare_na(
                task_block.fields[required_field]
            ):
                errors.append(
                    ValidationError(
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
                ValidationError(
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
                ValidationError(
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
                ValidationError(
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


def validate_features_directory(spec_dir: Path, *, is_full_mode: bool = False) -> ValidationResult:
    """Validate features directory has feature files."""
    errors: list[ValidationError] = []
    warnings: list[str] = []
    features_dir = spec_dir / "features"
    has_features = features_dir.exists() and list(features_dir.glob("*.feature"))

    if not has_features:
        if is_full_mode:
            errors.append(
                ValidationError(
                    message="No .feature files found in features/. Full-mode specs require at least one Scenario.",
                    file_path=str(features_dir),
                    severity=ErrorSeverity.HIGH,
                )
            )
        else:
            warnings.append("No .feature files found. (OK if this is a TDD-only lightweight spec)")
    else:
        warnings.append("Found Gherkin .feature files.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_plan(spec_dir: Path) -> ValidationResult:
    """Validate pb-plan generated documents.

    Returns a ValidationResult; callers are responsible for presenting results.
    """
    errors: list[ValidationError] = []
    warnings: list[str] = []

    # Check required files exist
    for f in [spec_dir / "design.md", spec_dir / "tasks.md"]:
        if not f.exists():
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(
                        message=f"Missing required file: {f.name}",
                        file_path=str(f),
                        severity=ErrorSeverity.CRITICAL,
                    )
                ],
            )

    design_result = validate_design_structure(spec_dir)
    errors.extend(design_result.errors)
    warnings.extend(design_result.warnings)
    is_full_mode = bool(design_result.warnings and "full mode" in design_result.warnings[0])

    tasks_result = validate_tasks_structure(spec_dir)
    errors.extend(tasks_result.errors)
    warnings.extend(tasks_result.warnings)

    features_result = validate_features_directory(spec_dir, is_full_mode=is_full_mode)
    errors.extend(features_result.errors)
    warnings.extend(features_result.warnings)

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
