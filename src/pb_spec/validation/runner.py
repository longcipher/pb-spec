"""Validation runner — orchestrates spec and feedback validation."""

from __future__ import annotations

from pathlib import Path

from pb_spec.validation.design import validate_design_file_structured
from pb_spec.validation.features import collect_feature_scenarios, find_feature_files
from pb_spec.validation.packets import parse_feedback_packets, validate_feedback_file
from pb_spec.validation.parsers import (
    extract_requirement_matrix_requirement_refs,
    extract_requirement_matrix_scenario_refs,
    extract_requirement_matrix_task_refs,
    is_not_applicable_matrix_value,
)
from pb_spec.validation.tasks import (
    find_orphan_scenarios,
    find_referenced_requirements,
    parse_task_blocks,
    validate_task_file_structured,
)
from pb_spec.validation.types import ValidationResult


def run_spec_validation(spec_dir: Path) -> ValidationResult:
    """Validate a generated pb-spec spec directory."""
    result = ValidationResult()

    design_file = spec_dir / "design.md"
    if not design_file.is_file():
        result.add_error(f"Missing required file: {design_file}")
        return result

    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.is_file():
        result.add_error(f"Missing required file: {tasks_file}")
        return result

    features_dir = spec_dir / "features"
    if not features_dir.is_dir():
        result.add_error(f"Missing required directory: {features_dir}")
        return result

    feature_files = find_feature_files(features_dir)
    if not feature_files:
        result.add_error(f"No .feature files found under {features_dir}")
        return result

    scenario_inventory = collect_feature_scenarios(features_dir)
    if not scenario_inventory:
        result.add_error(f"No Scenario entries found under {features_dir}")
        return result

    from pb_spec.validation.design import (
        _parse_design_sections,
        _parse_requirement_ids_from_table,
        _parse_requirement_matrix_rows,
    )

    # Read design file once and reuse parsed sections
    design_sections = _parse_design_sections(design_file)
    section_map = {name: content for name, content, _ in design_sections}

    # Use parsed sections for requirement extraction
    requirement_ids = _parse_requirement_ids_from_table(
        section_map.get("Source Requirement Ledger", "")
    )
    requirement_matrix_rows = _parse_requirement_matrix_rows(
        section_map.get("Requirements Coverage Matrix", "")
    )
    requirement_matrix = requirement_matrix_rows

    design_result = validate_design_file_structured(design_file)
    result.merge(design_result)

    task_result = validate_task_file_structured(
        tasks_file,
        scenario_inventory=scenario_inventory,
        known_requirement_ids=requirement_ids or None,
    )
    result.merge(task_result)

    task_blocks = parse_task_blocks(tasks_file)
    orphans = find_orphan_scenarios(scenario_inventory, task_blocks)
    for orphan in orphans:
        result.add_error(
            f"Orphan scenario not referenced by any task: {orphan}",
            file=str(spec_dir),
        )

    alignment_result = _validate_requirement_task_alignment(
        requirement_matrix=requirement_matrix,
        task_blocks=task_blocks,
        spec_dir=spec_dir,
    )
    result.merge(alignment_result)

    scenario_alignment_result = _validate_requirement_matrix_scenario_alignment(
        requirement_matrix=requirement_matrix,
        scenario_inventory=scenario_inventory,
        spec_dir=spec_dir,
    )
    result.merge(scenario_alignment_result)

    task_alignment_result = _validate_requirement_matrix_task_alignment(
        requirement_matrix=requirement_matrix,
        task_blocks=task_blocks,
        spec_dir=spec_dir,
    )
    result.merge(task_alignment_result)

    embedded_result = _validate_embedded_packets(design_file, tasks_file)
    result.merge(embedded_result)

    return result


def run_feedback_validation(feedback_file: Path) -> ValidationResult:
    """Validate a markdown feedback file carrying build-block or DCR packets."""
    result = ValidationResult()

    content = feedback_file.read_text(encoding="utf-8").strip()
    if not content:
        result.add_error(f"Feedback file is empty: {feedback_file}")
        return result

    packets = parse_feedback_packets(feedback_file)
    if not packets:
        result.add_error(
            f"No 🛑 Build Blocked or 🔄 Design Change Request packets found in {feedback_file}"
        )
        return result

    feedback_result = validate_feedback_file(feedback_file)
    result.merge(feedback_result)

    return result


def _validate_embedded_packets(*files: Path) -> ValidationResult:
    """Validate feedback packets embedded within spec artifact files."""
    result = ValidationResult()
    for file_path in files:
        if not file_path.is_file():
            continue
        packets = parse_feedback_packets(file_path)
        if not packets:
            continue
        feedback_result = validate_feedback_file(file_path)
        result.merge(feedback_result)
    return result


def _validate_requirement_task_alignment(
    *, requirement_matrix: dict, task_blocks: list, spec_dir: Path
) -> ValidationResult:
    """Ensure covered requirements in design.md map to at least one task."""
    result = ValidationResult()
    referenced_requirements = find_referenced_requirements(task_blocks)

    for requirement_id, row in requirement_matrix.items():
        status_rationale = row.status_rationale.strip().lower()
        if any(kw in status_rationale for kw in ("out of scope", "deferred", "non-goal")):
            continue
        if requirement_id not in referenced_requirements:
            result.add_error(
                "Requirement ID marked covered in Requirements Coverage Matrix but not "
                f"referenced by any task Requirement Coverage field: {requirement_id}",
                file=str(spec_dir),
            )

    return result


def _validate_requirement_matrix_scenario_alignment(
    *, requirement_matrix: dict, scenario_inventory: dict[str, Path], spec_dir: Path
) -> ValidationResult:
    """Ensure matrix scenario references point to real feature scenarios."""
    result = ValidationResult()

    for requirement_id, row in requirement_matrix.items():
        status_rationale = row.status_rationale.strip().lower()
        if any(kw in status_rationale for kw in ("out of scope", "deferred", "non-goal")):
            continue

        scenario_coverage = row.scenario_coverage
        for feature_name, scenario_name in extract_requirement_matrix_scenario_refs(
            scenario_coverage
        ):
            matched_feature = scenario_inventory.get(scenario_name)
            if matched_feature is None:
                result.add_error(
                    "Scenario reference not found in Requirements Coverage Matrix for "
                    f"{requirement_id}: {scenario_name}",
                    file=str(spec_dir),
                )
                continue
            if feature_name is not None and matched_feature.name != feature_name:
                result.add_error(
                    "Feature file reference does not match scenario location in Requirements Coverage Matrix "
                    f"for {requirement_id}: {feature_name} / {scenario_name}",
                    file=str(spec_dir),
                )

    return result


def _validate_requirement_matrix_task_alignment(
    *, requirement_matrix: dict, task_blocks: list, spec_dir: Path
) -> ValidationResult:
    """Ensure matrix task references point to real tasks covering the requirement."""
    result = ValidationResult()
    task_blocks_by_id = {task_block.task_id: task_block for task_block in task_blocks}

    for requirement_id, row in requirement_matrix.items():
        status_rationale = row.status_rationale.strip().lower()
        if any(kw in status_rationale for kw in ("out of scope", "deferred", "non-goal")):
            continue

        task_coverage = row.task_coverage
        task_refs = extract_requirement_matrix_task_refs(task_coverage)
        if not task_refs and not is_not_applicable_matrix_value(task_coverage):
            result.add_error(
                "Task Coverage must reference Task X.Y entries in Requirements Coverage Matrix for "
                f"{requirement_id}",
                file=str(spec_dir),
            )
            continue

        for task_id in task_refs:
            matched_task = task_blocks_by_id.get(task_id)
            if matched_task is None:
                result.add_error(
                    "Task reference not found in Requirements Coverage Matrix for "
                    f"{requirement_id}: {task_id}",
                    file=str(spec_dir),
                )
                continue

            referenced_requirements = extract_requirement_matrix_requirement_refs(
                matched_task.fields.get("Requirement Coverage", "")
            )
            if requirement_id not in referenced_requirements:
                result.add_error(
                    "Task reference does not cover requirement in Requirements Coverage Matrix for "
                    f"{requirement_id}: {task_id}",
                    file=str(spec_dir),
                )

    return result
