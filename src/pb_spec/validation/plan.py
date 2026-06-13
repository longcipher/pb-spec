"""Plan validation logic for design.md and tasks.md."""

from __future__ import annotations

import re
import threading
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
    make_validation_error,
)

_DEFAULT_CONTRACT_CONFIG_PATH = Path(__file__).parent / "contract_sections.toml"

_CONTRACT_CONFIG: dict = {}
_FULL_MODE_REQUIRED: list[str] = []
_LIGHTWEIGHT_MODE_REQUIRED: list[str] = []
_TASK_REQUIRED_FIELDS: list[str] = []
_NA_REASON_FIELDS: frozenset[str] = frozenset()
_config_loaded = False
_config_lock = threading.Lock()


def _load_contract_config(config_path: Path | None = None) -> None:
    """Load contract configuration from TOML file.

    When config_path is None, loads from the default bundled config.
    Projects may override by placing a contract_sections.toml in their spec directory.
    Thread-safe with double-checked locking.
    """
    global _CONTRACT_CONFIG, _FULL_MODE_REQUIRED, _LIGHTWEIGHT_MODE_REQUIRED
    global _TASK_REQUIRED_FIELDS, _NA_REASON_FIELDS, _config_loaded

    with _config_lock:
        path = config_path or _DEFAULT_CONTRACT_CONFIG_PATH
        with path.open("rb") as f:
            _CONTRACT_CONFIG = tomllib.load(f)

        _FULL_MODE_REQUIRED = list(_CONTRACT_CONFIG["full_mode"]["required_sections"])
        _LIGHTWEIGHT_MODE_REQUIRED = list(
            _CONTRACT_CONFIG["lightweight_mode"]["required_sections"]
        )
        _TASK_REQUIRED_FIELDS = list(_CONTRACT_CONFIG["tasks"]["required_fields"])
        _NA_REASON_FIELDS = frozenset(_CONTRACT_CONFIG["tasks"]["na_reason_fields"])
        _config_loaded = True


def _ensure_contract_config() -> None:
    """Ensure contract configuration is loaded (lazy initialization)."""
    if not _config_loaded:
        _load_contract_config()


def validate_required_files_exist(spec_dir: Path) -> ValidationResult:
    """Check that required files exist."""
    errors: list[ValidationError] = []
    design_file = spec_dir / "design.md"
    tasks_file = spec_dir / "tasks.md"

    for f in [design_file, tasks_file]:
        if not f.exists():
            errors.append(
                make_validation_error(
                    message=f"Missing required file: {f.name}",
                    file_path=str(f),
                    severity=ErrorSeverity.CRITICAL,
                )
            )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def detect_design_mode(content: str) -> tuple[bool, list[str]]:
    """Detect design.md mode and return required sections.

    Uses heading-level matching (## Executive Summary) to avoid false positives
    from the same words appearing in prose.
    Required sections are loaded from contract_sections.toml (single source of truth).
    """
    _ensure_contract_config()
    headings = {m.group(1).strip() for m in _HEADING_RE.finditer(content)}
    is_full_mode = "Executive Summary" in headings or "Requirements & Goals" in headings

    if is_full_mode:
        required_sections = list(_FULL_MODE_REQUIRED)
    else:
        required_sections = list(_LIGHTWEIGHT_MODE_REQUIRED)

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
                make_validation_error(
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
                make_validation_error(
                    message=str(e),
                    file_path="design.md",
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )

    is_full_mode, required_sections = detect_design_mode(content)

    headings = {m.group(1).strip() for m in _HEADING_RE.finditer(content)}
    for sec in required_sections:
        if sec not in headings:
            errors.append(
                make_validation_error(
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
    _ensure_contract_config()
    errors: list[ValidationError] = []
    warnings: list[str] = []
    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        return ValidationResult(
            is_valid=False,
            errors=[
                make_validation_error(
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
                make_validation_error(
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
                make_validation_error(
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
            make_validation_error(
                message=msg,
                file_path="tasks.md",
            )
        )

    required_task_fields = list(_TASK_REQUIRED_FIELDS)

    seen_task_ids: set[str] = set()

    for task_block in task_blocks:
        display_name = task_display_name(task_block)

        if task_block.id in seen_task_ids:
            errors.append(
                make_validation_error(
                    message=f"Duplicate task ID found in tasks.md: Task {task_block.id}",
                    file_path="tasks.md",
                    severity=ErrorSeverity.HIGH,
                )
            )
        seen_task_ids.add(task_block.id)

        for required_field in required_task_fields:
            if required_field not in task_block.fields:
                errors.append(
                    make_validation_error(
                        message=f"Task '{display_name}' is missing required field: '{required_field}'",
                        file_path="tasks.md",
                        field_name=required_field,
                    )
                )
            elif not task_block.fields[required_field].strip():
                errors.append(
                    make_validation_error(
                        message=f"Task '{display_name}' has empty required field: '{required_field}'",
                        file_path="tasks.md",
                        field_name=required_field,
                    )
                )
            elif required_field in _NA_REASON_FIELDS and is_bare_na(
                task_block.fields[required_field]
            ):
                errors.append(
                    make_validation_error(
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
                make_validation_error(
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
                make_validation_error(
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
                make_validation_error(
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
    """Validate features directory has feature files.

    For full-mode specs, missing features/ is an error (contract §8.1).
    For lightweight specs, it's only a warning.
    """
    errors: list[ValidationError] = []
    warnings: list[str] = []
    features_dir = spec_dir / "features"
    has_features = features_dir.exists() and list(features_dir.glob("*.feature"))

    if not has_features:
        if is_full_mode:
            errors.append(
                make_validation_error(
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

    Returns a ValidationResult; callers are responsible for presenting results.
    Short-circuits when required files are missing to avoid redundant checks.
    """
    file_check = validate_required_files_exist(spec_dir)
    if not file_check.is_valid:
        return file_check

    design_result = validate_design_structure(spec_dir)
    is_full_mode = bool(design_result.warnings and "full mode" in design_result.warnings[0])

    return combine_validation_results(
        design_result,
        validate_tasks_structure(spec_dir),
        validate_features_directory(spec_dir, is_full_mode=is_full_mode),
    )
