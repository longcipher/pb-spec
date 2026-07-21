"""Plan validation logic for design.md and tasks.md."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from pb_spec.exceptions import FileReadError
from pb_spec.validation.io import read_file_content
from pb_spec.validation.parser import (
    ALLOWED_TASK_STATUSES,
    TASK_CHECKBOX_RE,
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

_DESIGN_REQUIRED_SECTIONS: list[str] = []
_DESIGN_OPTIONAL_SECTIONS: list[str] = []
_TASK_REQUIRED_FIELDS: list[str] = []
_BUILD_BLOCKED_REQUIRED_FIELDS: frozenset[str] = frozenset()
_DCR_REQUIRED_FIELDS: frozenset[str] = frozenset()


def _load_config(config_path: Path | None = None) -> None:
    """Load contract configuration from TOML file into module globals."""
    global _DESIGN_REQUIRED_SECTIONS, _DESIGN_OPTIONAL_SECTIONS
    global _TASK_REQUIRED_FIELDS
    global _BUILD_BLOCKED_REQUIRED_FIELDS, _DCR_REQUIRED_FIELDS

    path = config_path or _DEFAULT_CONTRACT_CONFIG_PATH
    with path.open("rb") as f:
        config = tomllib.load(f)

    _DESIGN_REQUIRED_SECTIONS = list(config["design"]["required_sections"])
    _DESIGN_OPTIONAL_SECTIONS = list(config["design"]["optional_sections"])
    _TASK_REQUIRED_FIELDS = list(config["tasks"]["required_fields"])
    _BUILD_BLOCKED_REQUIRED_FIELDS = frozenset(config["build_blocked"]["required_fields"])
    _DCR_REQUIRED_FIELDS = frozenset(config["dcr"]["required_fields"])


# Eager load at import time; module path is static.
_load_config()


def load_contract_config(config_path: Path | None = None) -> None:
    """Reload contract configuration (used by CLI --config override)."""
    _load_config(config_path)


def validate_design_structure(spec_dir: Path) -> ValidationResult:
    """Validate design.md contains all required sections."""
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

    for sec in _DESIGN_REQUIRED_SECTIONS:
        if sec not in headings:
            errors.append(
                ValidationError(
                    message=f"design.md is missing required section: '{sec}'",
                    file_path="design.md",
                    field_name=sec,
                )
            )

    if not errors:
        warnings.append("design.md structural checks passed.")

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


def validate_features_directory(spec_dir: Path) -> ValidationResult:
    """Validate features directory contains at least one .feature file."""
    errors: list[ValidationError] = []
    warnings: list[str] = []
    features_dir = spec_dir / "features"
    has_features = features_dir.exists() and list(features_dir.glob("*.feature"))

    if not has_features:
        errors.append(
            ValidationError(
                message="No .feature files found in features/. Specs require at least one Scenario.",
                file_path=str(features_dir),
                severity=ErrorSeverity.HIGH,
            )
        )
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

    tasks_result = validate_tasks_structure(spec_dir)
    errors.extend(tasks_result.errors)
    warnings.extend(tasks_result.warnings)

    features_result = validate_features_directory(spec_dir)
    errors.extend(features_result.errors)
    warnings.extend(features_result.warnings)

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
