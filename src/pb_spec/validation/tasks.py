"""Task-block parsing and validation for pb-spec workflow specs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pb_spec.validation.patterns import (
    CHECKBOX_LABEL_RE,
    CHECKBOX_RE,
    FIELD_RE,
    QUOTE_FIELD_RE,
    TASK_HEADING_RE,
)
from pb_spec.validation.types import ValidationResult

MINIMUM_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "Context",
    "Verification",
    "Status",
    "Loop Type",
    "Requirement Coverage",
    "Scenario Coverage",
    "Behavioral Contract",
    "Simplification Focus",
)
REQUIRED_CHECKBOX_FIELDS: Final[tuple[str, ...]] = (
    "BDD Verification",
    "Advanced Test Verification",
    "Runtime Verification",
)
FIELDS_REQUIRING_NA_REASON: Final[frozenset[str]] = frozenset(
    {
        "Requirement Coverage",
        "Scenario Coverage",
        "BDD Verification",
        "Advanced Test Verification",
        "Runtime Verification",
    }
)
ALLOWED_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "TODO",
        "🔴 TODO",
        "🟡 IN PROGRESS",
        "🟢 DONE",
        "⏭️ SKIPPED",
        "🔄 DCR",
        "⛔ OBSOLETE",
    }
)
ALLOWED_LOOP_TYPES: Final[frozenset[str]] = frozenset({"BDD+TDD", "TDD-only"})


@dataclass(slots=True, frozen=True)
class TaskBlock:
    """Parsed task block with structured data."""

    task_id: str
    name: str
    body_lines: list[str]
    fields: dict[str, str]
    checkbox_lines: list[str]
    evidence_checkbox_lines: list[str]
    checkbox_fields: dict[str, str]


def parse_task_blocks(tasks_file: Path) -> list[TaskBlock]:
    """Parse `### Task X.Y:` blocks from a tasks.md file."""
    content = tasks_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    task_blocks: list[TaskBlock] = []
    current_task_id: str | None = None
    current_name: str | None = None
    current_body: list[str] = []

    for line in lines:
        match = TASK_HEADING_RE.match(line)
        if match:
            if current_task_id is not None and current_name is not None:
                task_blocks.append(_build_task_block(current_task_id, current_name, current_body))
            current_task_id = match.group(1)
            current_name = match.group(2)
            current_body = []
            continue

        if current_task_id is not None:
            current_body.append(line)

    if current_task_id is not None and current_name is not None:
        task_blocks.append(_build_task_block(current_task_id, current_name, current_body))

    return task_blocks


def validate_task_file(
    tasks_file: Path,
    *,
    scenario_inventory: dict[str, Path] | None = None,
    known_requirement_ids: set[str] | None = None,
) -> list[str]:
    """Validate the minimum required task fields for each parsed task block.

    Returns list of error strings for backward compatibility.
    """
    result = validate_task_file_structured(
        tasks_file,
        scenario_inventory=scenario_inventory,
        known_requirement_ids=known_requirement_ids,
    )
    # Return only error messages without file path prefix for backward compatibility
    return [error.message for error in result.errors]


def validate_task_file_structured(
    tasks_file: Path,
    *,
    scenario_inventory: dict[str, Path] | None = None,
    known_requirement_ids: set[str] | None = None,
) -> ValidationResult:
    """Validate the minimum required task fields for each parsed task block.

    Returns structured ValidationResult with errors and warnings.
    """
    result = ValidationResult()
    task_blocks = parse_task_blocks(tasks_file)
    if not task_blocks:
        result.add_error(
            "No valid Task X.Y blocks found in tasks.md",
            file=str(tasks_file),
        )
        return result

    seen_task_ids: set[str] = set()

    for task_block in task_blocks:
        if task_block.task_id in seen_task_ids:
            result.add_error(
                f"Duplicate task ID in tasks.md: {task_block.task_id}",
                file=str(tasks_file),
            )
        else:
            seen_task_ids.add(task_block.task_id)

        for field_name in MINIMUM_REQUIRED_FIELDS:
            if field_name not in task_block.fields:
                result.add_error(
                    f"Missing required task field in {task_block.task_id}: {field_name}",
                    file=str(tasks_file),
                )

        if not task_block.checkbox_lines:
            result.add_error(
                f"Missing required task field in {task_block.task_id}: Step checkboxes",
                file=str(tasks_file),
            )

        status = task_block.fields.get("Status")
        if status is not None and status not in ALLOWED_STATUSES:
            result.add_error(
                f"Invalid task status in {task_block.task_id}: {status}",
                file=str(tasks_file),
            )

        loop_type = task_block.fields.get("Loop Type")
        if loop_type is not None and loop_type not in ALLOWED_LOOP_TYPES:
            result.add_error(
                f"Invalid loop type in {task_block.task_id}: {loop_type}",
                file=str(tasks_file),
            )

        for field_name in REQUIRED_CHECKBOX_FIELDS:
            if field_name not in task_block.checkbox_fields:
                result.add_error(
                    f"Missing required task field in {task_block.task_id}: {field_name}",
                    file=str(tasks_file),
                )

        for field_name in FIELDS_REQUIRING_NA_REASON:
            value = task_block.fields.get(field_name)
            if value is None:
                value = task_block.checkbox_fields.get(field_name)
            if value is not None and _is_bare_not_applicable_value(value):
                result.add_error(
                    f"N/A value must include a reason in {task_block.task_id}: {field_name}",
                    file=str(tasks_file),
                )

        if status == "🟢 DONE":
            incomplete_verification = []
            for field_name in REQUIRED_CHECKBOX_FIELDS:
                field_value = task_block.checkbox_fields.get(field_name)
                if field_value is None:
                    incomplete_verification.append(field_name)
                elif _is_not_applicable_value(field_value):
                    continue
            for line in task_block.evidence_checkbox_lines:
                label_match = CHECKBOX_LABEL_RE.match(line)
                if label_match:
                    normalized = _normalize_checkbox_field_name(label_match.group(1))
                    if normalized in REQUIRED_CHECKBOX_FIELDS and line.startswith("- [ ]"):
                        incomplete_verification.append(normalized)
            if incomplete_verification:
                result.add_error(
                    f"Task marked DONE still has incomplete verification evidence in "
                    f"{task_block.task_id}: {', '.join(sorted(set(incomplete_verification)))}",
                    file=str(tasks_file),
                )

        advanced_test_verification = task_block.checkbox_fields.get("Advanced Test Verification")
        if (
            advanced_test_verification is not None
            and not _is_not_applicable_value(advanced_test_verification)
            and "Advanced Test Coverage" not in task_block.fields
        ):
            result.add_error(
                f"Advanced Test Coverage is required when Advanced Test Verification is concrete in {task_block.task_id}",
                file=str(tasks_file),
            )

        scenario_coverage = task_block.fields.get("Scenario Coverage")
        if loop_type == "BDD+TDD" and scenario_coverage is not None:
            if _is_not_applicable_value(scenario_coverage):
                result.add_error(
                    "Scenario Coverage must name a concrete scenario for "
                    f"{task_block.task_id} when Loop Type is BDD+TDD",
                    file=str(tasks_file),
                )
            elif scenario_inventory is not None:
                scenario_names = _extract_scenario_names(scenario_coverage)
                for scenario_name in scenario_names:
                    if scenario_name not in scenario_inventory:
                        result.add_error(
                            f"Scenario reference not found for {task_block.task_id}: {scenario_name}",
                            file=str(tasks_file),
                        )

        requirement_coverage = task_block.fields.get("Requirement Coverage")
        if requirement_coverage is not None and not _is_not_applicable_value(requirement_coverage):
            requirement_ids = _extract_requirement_ids(requirement_coverage)
            if not requirement_ids:
                result.add_error(
                    f"Requirement Coverage must list concrete requirement IDs in {task_block.task_id}",
                    file=str(tasks_file),
                )
            elif known_requirement_ids is not None:
                for requirement_id in sorted(requirement_ids):
                    if requirement_id not in known_requirement_ids:
                        result.add_error(
                            f"Unknown requirement reference in {task_block.task_id}: {requirement_id}",
                            file=str(tasks_file),
                        )

    return result


def find_referenced_scenarios(task_blocks: list[TaskBlock]) -> set[str]:
    """Return the set of scenario names referenced by task blocks."""
    referenced: set[str] = set()
    for block in task_blocks:
        coverage = block.fields.get("Scenario Coverage")
        if coverage is not None and not _is_not_applicable_value(coverage):
            referenced.update(_extract_scenario_names(coverage))
    return referenced


def find_referenced_requirements(task_blocks: list[TaskBlock]) -> set[str]:
    """Return the set of requirement IDs referenced by task blocks."""
    referenced: set[str] = set()
    for block in task_blocks:
        coverage = block.fields.get("Requirement Coverage")
        if coverage is not None and not _is_not_applicable_value(coverage):
            referenced.update(_extract_requirement_ids(coverage))
    return referenced


def find_orphan_scenarios(
    scenario_inventory: dict[str, Path],
    task_blocks: list[TaskBlock],
) -> list[str]:
    """Return scenario names present in .feature files but not referenced by any task."""
    referenced = find_referenced_scenarios(task_blocks)
    return sorted(name for name in scenario_inventory if name not in referenced)


def _build_task_block(task_id: str, name: str, body_lines: list[str]) -> TaskBlock:
    fields: dict[str, str] = {}
    checkbox_lines: list[str] = []
    evidence_checkbox_lines: list[str] = []
    checkbox_fields: dict[str, str] = {}

    for line in body_lines:
        quote_field_match = QUOTE_FIELD_RE.match(line)
        if quote_field_match:
            fields[quote_field_match.group(1)] = _strip_backticks(quote_field_match.group(2))
            continue

        field_match = FIELD_RE.match(line)
        if field_match:
            fields[field_match.group(1)] = _strip_backticks(field_match.group(2))
            continue

        if CHECKBOX_RE.match(line):
            evidence_checkbox_lines.append(line)
            checkbox_label_match = CHECKBOX_LABEL_RE.match(line)
            if checkbox_label_match:
                checkbox_fields[_normalize_checkbox_field_name(checkbox_label_match.group(1))] = (
                    _strip_backticks(checkbox_label_match.group(2))
                )
            if line.startswith("- [ ] **Step") or line.startswith("- [x] **Step"):
                checkbox_lines.append(line)

    return TaskBlock(
        task_id=task_id,
        name=name,
        body_lines=body_lines,
        fields=fields,
        checkbox_lines=checkbox_lines,
        evidence_checkbox_lines=evidence_checkbox_lines,
        checkbox_fields=checkbox_fields,
    )


def _is_not_applicable_value(value: str) -> bool:
    normalized_value = value.strip()
    return normalized_value == "N/A" or normalized_value.startswith("N/A ")


def _is_bare_not_applicable_value(value: str) -> bool:
    return value.strip() == "N/A"


def _extract_scenario_names(coverage: str) -> list[str]:
    """Extract all scenario names from a coverage value.

    Handles formats:
    - 'Scenario Name'
    - 'feature_file.feature / Scenario Name'
    - 'feature_file.feature / all scenarios' (returns empty list)
    - '`feature / s1`, `feature / s2`' (multiple backtick-wrapped refs)
    - 'feature1 / s1, feature2 / s2' (comma-separated refs)
    """
    # Handle backtick-wrapped comma-separated format
    if "`, `" in coverage:
        parts = coverage.split("`, `")
        names = []
        for part in parts:
            name = _parse_single_scenario_ref(part.strip("`").strip())
            if name is not None:
                names.append(name)
        return names

    # Handle plain comma-separated format (without backticks)
    if ", " in coverage and " / " in coverage:
        parts = coverage.split(", ")
        names = []
        for part in parts:
            name = _parse_single_scenario_ref(part.strip())
            if name is not None:
                names.append(name)
        return names

    # Single scenario reference
    name = _parse_single_scenario_ref(coverage)
    return [name] if name is not None else []


def _extract_requirement_ids(coverage: str) -> set[str]:
    return set(re.findall(r"\b[A-Z]+[A-Z0-9_-]*\d+\b", coverage))


def _parse_single_scenario_ref(value: str) -> str | None:
    """Parse a single 'feature / scenario' or plain scenario reference."""
    stripped = value.strip().strip("`")
    if " / " in stripped:
        _feature, scenario = stripped.split(" / ", 1)
        scenario = scenario.strip()
        if scenario.lower() == "all scenarios":
            return None
        return scenario
    return stripped if stripped else None


def _strip_backticks(value: str) -> str:
    """Strip surrounding single backticks from a field value."""
    stripped = value.strip()
    if len(stripped) >= 2 and stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1]
    return stripped


def _normalize_checkbox_field_name(name: str) -> str:
    normalized_name = name.strip()
    if normalized_name.startswith("Runtime Verification"):
        return "Runtime Verification"
    return normalized_name
