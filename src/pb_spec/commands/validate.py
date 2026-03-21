"""Validate command for pb-spec CLI."""

import re
from pathlib import Path

import click

from pb_spec.validation import (
    ValidationResult,
    collect_feature_scenarios,
    find_feature_files,
    find_orphan_scenarios,
    find_referenced_requirements,
    parse_feedback_packets,
    parse_requirements_coverage_matrix,
    parse_source_requirement_ids,
    parse_task_blocks,
    validate_design_file_structured,
    validate_feedback_file,
    validate_task_file_structured,
)


@click.command("validate")
@click.argument(
    "target",
    metavar="TARGET",
    type=click.Path(path_type=Path, file_okay=True, dir_okay=True),
)
def validate_cmd(target: Path) -> None:
    """Validate a generated spec directory or feedback packet markdown file."""
    if target.is_dir():
        _validate_spec_dir(target)
        click.echo(f"Validation passed for {target}")
        return

    if target.is_file():
        _validate_feedback_target(target)
        click.echo(f"Validation passed for {target}")
        return

    raise click.ClickException(f"Validation target does not exist: {target}")


def _validate_spec_dir(spec_dir: Path) -> None:
    """Validate a generated pb-spec spec directory."""

    design_file = spec_dir / "design.md"
    if not design_file.is_file():
        raise click.ClickException(f"Missing required file: {design_file}")

    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.is_file():
        raise click.ClickException(f"Missing required file: {tasks_file}")

    features_dir = spec_dir / "features"
    if not features_dir.is_dir():
        raise click.ClickException(f"Missing required directory: {features_dir}")

    feature_files = find_feature_files(features_dir)
    if not feature_files:
        raise click.ClickException(f"No .feature files found under {features_dir}")

    scenario_inventory = collect_feature_scenarios(features_dir)
    if not scenario_inventory:
        raise click.ClickException(f"No Scenario entries found under {features_dir}")

    requirement_ids = parse_source_requirement_ids(design_file)
    requirement_matrix = parse_requirements_coverage_matrix(design_file)

    # Use structured validation
    result = ValidationResult()

    # Validate design file
    design_result = validate_design_file_structured(design_file)
    result.merge(design_result)

    # Validate task file
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

    # Validate requirement task alignment
    alignment_result = _validate_requirement_task_alignment_structured(
        requirement_matrix=requirement_matrix,
        task_blocks=task_blocks,
        spec_dir=spec_dir,
    )
    result.merge(alignment_result)

    # Validate requirement matrix scenario alignment
    scenario_alignment_result = _validate_requirement_matrix_scenario_alignment_structured(
        requirement_matrix=requirement_matrix,
        scenario_inventory=scenario_inventory,
        spec_dir=spec_dir,
    )
    result.merge(scenario_alignment_result)

    # Validate requirement matrix task alignment
    task_alignment_result = _validate_requirement_matrix_task_alignment_structured(
        requirement_matrix=requirement_matrix,
        task_blocks=task_blocks,
        spec_dir=spec_dir,
    )
    result.merge(task_alignment_result)

    # Validate embedded packets
    embedded_result = _validate_embedded_packets_structured(design_file, tasks_file)
    result.merge(embedded_result)

    if not result.is_valid():
        error_lines = "\n".join(f"- {error}" for error in result.to_error_strings())
        raise click.ClickException(f"Validation failed:\n{error_lines}")


def _validate_feedback_target(feedback_file: Path) -> None:
    """Validate a markdown feedback file carrying build-block or DCR packets."""
    content = feedback_file.read_text(encoding="utf-8").strip()
    if not content:
        raise click.ClickException(f"Feedback file is empty: {feedback_file}")

    packets = parse_feedback_packets(feedback_file)
    if not packets:
        raise click.ClickException(
            f"No 🛑 Build Blocked or 🔄 Design Change Request packets found in {feedback_file}"
        )

    errors = validate_feedback_file(feedback_file)
    if errors:
        error_lines = "\n".join(f"- {error}" for error in errors)
        raise click.ClickException(f"Validation failed:\n{error_lines}")


def _validate_embedded_packets(*files: Path) -> list[str]:
    """Validate feedback packets embedded within spec artifact files."""
    result = _validate_embedded_packets_structured(*files)
    return result.to_error_strings()


def _validate_embedded_packets_structured(*files: Path) -> ValidationResult:
    """Validate feedback packets embedded within spec artifact files."""
    result = ValidationResult()
    for file_path in files:
        if not file_path.is_file():
            continue
        packets = parse_feedback_packets(file_path)
        if not packets:
            continue
        errors = validate_feedback_file(file_path)
        for error in errors:
            result.add_error(error, file=str(file_path))
    return result


def _validate_requirement_task_alignment(
    *, requirement_matrix: dict, task_blocks: list
) -> list[str]:
    """Ensure covered requirements in design.md map to at least one task."""
    result = _validate_requirement_task_alignment_structured(
        requirement_matrix=requirement_matrix,
        task_blocks=task_blocks,
        spec_dir=Path("."),
    )
    return result.to_error_strings()


def _validate_requirement_task_alignment_structured(
    *, requirement_matrix: dict, task_blocks: list, spec_dir: Path
) -> ValidationResult:
    """Ensure covered requirements in design.md map to at least one task."""
    result = ValidationResult()
    referenced_requirements = find_referenced_requirements(task_blocks)

    for requirement_id, row in requirement_matrix.items():
        status_rationale = getattr(row, "status_rationale", "").strip().lower()
        if any(keyword in status_rationale for keyword in ("out of scope", "deferred", "non-goal")):
            continue
        if requirement_id not in referenced_requirements:
            result.add_error(
                "Requirement ID marked covered in Requirements Coverage Matrix but not "
                f"referenced by any task Requirement Coverage field: {requirement_id}",
                file=str(spec_dir),
            )

    return result


def _validate_requirement_matrix_scenario_alignment(
    *,
    requirement_matrix: dict,
    scenario_inventory: dict[str, Path],
) -> list[str]:
    """Ensure matrix scenario references point to real feature scenarios."""
    result = _validate_requirement_matrix_scenario_alignment_structured(
        requirement_matrix=requirement_matrix,
        scenario_inventory=scenario_inventory,
        spec_dir=Path("."),
    )
    return result.to_error_strings()


def _validate_requirement_matrix_scenario_alignment_structured(
    *,
    requirement_matrix: dict,
    scenario_inventory: dict[str, Path],
    spec_dir: Path,
) -> ValidationResult:
    """Ensure matrix scenario references point to real feature scenarios."""
    result = ValidationResult()

    for requirement_id, row in requirement_matrix.items():
        status_rationale = getattr(row, "status_rationale", "").strip().lower()
        if any(keyword in status_rationale for keyword in ("out of scope", "deferred", "non-goal")):
            continue

        scenario_coverage = getattr(row, "scenario_coverage", "")
        for feature_name, scenario_name in _extract_requirement_matrix_scenario_refs(
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
    *,
    requirement_matrix: dict,
    task_blocks: list,
) -> list[str]:
    """Ensure matrix task references point to real tasks covering the requirement."""
    result = _validate_requirement_matrix_task_alignment_structured(
        requirement_matrix=requirement_matrix,
        task_blocks=task_blocks,
        spec_dir=Path("."),
    )
    return result.to_error_strings()


def _validate_requirement_matrix_task_alignment_structured(
    *,
    requirement_matrix: dict,
    task_blocks: list,
    spec_dir: Path,
) -> ValidationResult:
    """Ensure matrix task references point to real tasks covering the requirement."""
    result = ValidationResult()
    task_blocks_by_id = {task_block.task_id: task_block for task_block in task_blocks}

    for requirement_id, row in requirement_matrix.items():
        status_rationale = getattr(row, "status_rationale", "").strip().lower()
        if any(keyword in status_rationale for keyword in ("out of scope", "deferred", "non-goal")):
            continue

        task_coverage = getattr(row, "task_coverage", "")
        task_refs = _extract_requirement_matrix_task_refs(task_coverage)
        if not task_refs and not _is_not_applicable_requirement_matrix_value(task_coverage):
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

            referenced_requirements = _extract_requirement_matrix_requirement_refs(
                matched_task.fields.get("Requirement Coverage", "")
            )
            if requirement_id not in referenced_requirements:
                result.add_error(
                    "Task reference does not cover requirement in Requirements Coverage Matrix for "
                    f"{requirement_id}: {task_id}",
                    file=str(spec_dir),
                )

    return result


def _extract_requirement_matrix_scenario_refs(coverage: str) -> list[tuple[str | None, str]]:
    normalized_coverage = coverage.strip().strip("`")
    if (
        not normalized_coverage
        or normalized_coverage == "N/A"
        or normalized_coverage.startswith("N/A ")
    ):
        return []

    if "`, `" in normalized_coverage:
        refs = []
        for part in normalized_coverage.split("`, `"):
            parsed = _parse_requirement_matrix_scenario_ref(part.strip().strip("`"))
            if parsed is not None:
                refs.append(parsed)
        return refs

    parsed = _parse_requirement_matrix_scenario_ref(normalized_coverage.strip("`"))
    return [parsed] if parsed is not None else []


def _extract_requirement_matrix_task_refs(coverage: str) -> list[str]:
    normalized_coverage = coverage.strip().strip("`")
    if _is_not_applicable_requirement_matrix_value(normalized_coverage):
        return []
    return re.findall(r"Task \d+\.\d+", normalized_coverage)


def _extract_requirement_matrix_requirement_refs(coverage: str) -> set[str]:
    normalized_coverage = coverage.strip().strip("`")
    if _is_not_applicable_requirement_matrix_value(normalized_coverage):
        return set()
    return set(re.findall(r"\b[A-Z]+[A-Z0-9_-]*\d+\b", normalized_coverage))


def _is_not_applicable_requirement_matrix_value(value: str) -> bool:
    normalized = value.strip().strip("`")
    return not normalized or normalized == "N/A" or normalized.startswith("N/A ")


def _parse_requirement_matrix_scenario_ref(value: str) -> tuple[str | None, str] | None:
    normalized = value.strip()
    if not normalized:
        return None

    if " / " in normalized:
        feature_name, scenario_name = normalized.split(" / ", 1)
        scenario_name = scenario_name.strip()
        if scenario_name.lower() == "all scenarios":
            return None
        return feature_name.strip(), scenario_name

    scenario_name = re.sub(r"^[^A-Za-z0-9_\-]*", "", normalized).strip()
    return (None, scenario_name) if scenario_name else None
