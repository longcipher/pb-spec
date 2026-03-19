"""Validate command for pb-spec CLI."""

from pathlib import Path

import click

from pb_spec.validation import (
    collect_feature_scenarios,
    find_feature_files,
    find_orphan_scenarios,
    parse_feedback_packets,
    parse_task_blocks,
    validate_design_file,
    validate_feedback_file,
    validate_task_file,
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

    errors = validate_design_file(design_file)
    errors.extend(validate_task_file(tasks_file, scenario_inventory=scenario_inventory))

    task_blocks = parse_task_blocks(tasks_file)
    orphans = find_orphan_scenarios(scenario_inventory, task_blocks)
    for orphan in orphans:
        errors.append(f"Orphan scenario not referenced by any task: {orphan}")

    errors.extend(_validate_embedded_packets(design_file, tasks_file))

    if errors:
        error_lines = "\n".join(f"- {error}" for error in errors)
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
    errors: list[str] = []
    for file_path in files:
        if not file_path.is_file():
            continue
        packets = parse_feedback_packets(file_path)
        if not packets:
            continue
        errors.extend(validate_feedback_file(file_path))
    return errors
