"""Task-block parsing and validation for pb-spec workflow specs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TASK_HEADING_RE = re.compile(r"^### (Task \d+\.\d+):\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^- \*\*(.+?):\*\*\s*(.+?)\s*$")
QUOTE_FIELD_RE = re.compile(r"^> \*\*(.+?):\*\*\s*(.+?)\s*$")
CHECKBOX_RE = re.compile(r"^- \[[ xX]\] ")
CHECKBOX_LABEL_RE = re.compile(r"^- \[[ xX]\] \*\*(.+?):\*\*\s*(.+?)\s*$")

MINIMUM_REQUIRED_FIELDS = (
    "Context",
    "Verification",
    "Status",
    "Loop Type",
    "Scenario Coverage",
    "Behavioral Contract",
    "Simplification Focus",
)
REQUIRED_CHECKBOX_FIELDS = (
    "BDD Verification",
    "Advanced Test Verification",
    "Runtime Verification",
)
FIELDS_REQUIRING_NA_REASON = {
    "Scenario Coverage",
    "BDD Verification",
    "Advanced Test Verification",
    "Runtime Verification",
}
ALLOWED_STATUSES = {
    "TODO",
    "🔴 TODO",
    "🟡 IN PROGRESS",
    "🟢 DONE",
    "⏭️ SKIPPED",
    "🔄 DCR",
    "⛔ OBSOLETE",
}
ALLOWED_LOOP_TYPES = {"BDD+TDD", "TDD-only"}


@dataclass(slots=True)
class TaskBlock:
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
) -> list[str]:
    """Validate the minimum required task fields for each parsed task block."""
    errors: list[str] = []
    task_blocks = parse_task_blocks(tasks_file)
    if not task_blocks:
        return ["No valid Task X.Y blocks found in tasks.md"]

    seen_task_ids: set[str] = set()

    for task_block in task_blocks:
        if task_block.task_id in seen_task_ids:
            errors.append(f"Duplicate task ID in tasks.md: {task_block.task_id}")
        else:
            seen_task_ids.add(task_block.task_id)

        for field_name in MINIMUM_REQUIRED_FIELDS:
            if field_name not in task_block.fields:
                errors.append(f"Missing required task field in {task_block.task_id}: {field_name}")

        if not task_block.checkbox_lines:
            errors.append(f"Missing required task field in {task_block.task_id}: Step checkboxes")

        status = task_block.fields.get("Status")
        if status is not None and status not in ALLOWED_STATUSES:
            errors.append(f"Invalid task status in {task_block.task_id}: {status}")

        loop_type = task_block.fields.get("Loop Type")
        if loop_type is not None and loop_type not in ALLOWED_LOOP_TYPES:
            errors.append(f"Invalid loop type in {task_block.task_id}: {loop_type}")

        for field_name in REQUIRED_CHECKBOX_FIELDS:
            if field_name not in task_block.checkbox_fields:
                errors.append(f"Missing required task field in {task_block.task_id}: {field_name}")

        for field_name in FIELDS_REQUIRING_NA_REASON:
            value = task_block.fields.get(field_name)
            if value is None:
                value = task_block.checkbox_fields.get(field_name)
            if value is not None and _is_bare_not_applicable_value(value):
                errors.append(
                    f"N/A value must include a reason in {task_block.task_id}: {field_name}"
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
                errors.append(
                    f"Task marked DONE still has incomplete verification evidence in "
                    f"{task_block.task_id}: {', '.join(sorted(set(incomplete_verification)))}"
                )

        advanced_test_verification = task_block.checkbox_fields.get("Advanced Test Verification")
        if (
            advanced_test_verification is not None
            and not _is_not_applicable_value(advanced_test_verification)
            and "Advanced Test Coverage" not in task_block.fields
        ):
            errors.append(
                f"Advanced Test Coverage is required when Advanced Test Verification is concrete in {task_block.task_id}"
            )

        scenario_coverage = task_block.fields.get("Scenario Coverage")
        if loop_type == "BDD+TDD" and scenario_coverage is not None:
            if _is_not_applicable_value(scenario_coverage):
                errors.append(
                    "Scenario Coverage must name a concrete scenario for "
                    f"{task_block.task_id} when Loop Type is BDD+TDD"
                )
            elif scenario_inventory is not None and scenario_coverage not in scenario_inventory:
                errors.append(
                    f"Scenario reference not found for {task_block.task_id}: {scenario_coverage}"
                )

    return errors


def find_referenced_scenarios(task_blocks: list[TaskBlock]) -> set[str]:
    """Return the set of scenario names referenced by task blocks."""
    referenced: set[str] = set()
    for block in task_blocks:
        coverage = block.fields.get("Scenario Coverage")
        if coverage is not None and not _is_not_applicable_value(coverage):
            referenced.add(coverage)
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
            fields[quote_field_match.group(1)] = quote_field_match.group(2)
            continue

        field_match = FIELD_RE.match(line)
        if field_match:
            fields[field_match.group(1)] = field_match.group(2)
            continue

        if CHECKBOX_RE.match(line):
            evidence_checkbox_lines.append(line)
            checkbox_label_match = CHECKBOX_LABEL_RE.match(line)
            if checkbox_label_match:
                checkbox_fields[_normalize_checkbox_field_name(checkbox_label_match.group(1))] = (
                    checkbox_label_match.group(2)
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


def _normalize_checkbox_field_name(name: str) -> str:
    normalized_name = name.strip()
    if normalized_name.startswith("Runtime Verification"):
        return "Runtime Verification"
    return normalized_name
