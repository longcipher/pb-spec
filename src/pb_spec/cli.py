"""CLI entry point for pb-spec."""

from pathlib import Path

import click

from pb_spec import __version__
from pb_spec.commands.init import init_cmd
from pb_spec.commands.task_status import (
    scan_task_statuses,
    sync_all_tasks,
)
from pb_spec.commands.update import update_cmd
from pb_spec.commands.validate import validate_cmd
from pb_spec.commands.version import version_cmd
from pb_spec.spec_resolver import SpecResolutionError, resolve_spec_dir


def _resolve_spec_dir(feature_or_path: str) -> Path:
    """Resolve spec directory with CLI-friendly error handling."""
    try:
        resolved = resolve_spec_dir(feature_or_path)
        # Warn about multiple matches
        specs_dir = Path("specs")
        if specs_dir.exists():
            matching_dirs = sorted(
                [
                    d
                    for d in specs_dir.iterdir()
                    if d.is_dir() and d.name.endswith(f"-{feature_or_path}")
                ],
                reverse=True,
            )
            if len(matching_dirs) > 1:
                click.echo(
                    f"Multiple matches found, using most recent: {matching_dirs[0].name}",
                    err=True,
                )
        return resolved
    except SpecResolutionError as exc:
        raise click.ClickException(str(exc)) from exc


@click.group()
@click.version_option(version=__version__, prog_name="pb-spec")
def main():
    """pb-spec (Plan-Build Spec) - A CLI tool for managing AI coding assistant skills."""


main.add_command(init_cmd, "init")
main.add_command(validate_cmd, "validate")
main.add_command(version_cmd, "version")
main.add_command(update_cmd, "update")


@main.command("status")
@click.argument("feature_or_path")
def task_status(feature_or_path: str) -> None:
    """Show task status for a spec directory.

    Supports full path (specs/...) or feature name (e.g., workflow-type-contracts).
    """
    spec_dir = _resolve_spec_dir(feature_or_path)
    statuses = scan_task_statuses(spec_dir)

    click.echo(f"\n📊 Task Status: {spec_dir}\n")

    for ts in statuses:
        status_icon = "✅" if ts.is_complete else "🔄" if ts.status == "🟡 IN PROGRESS" else "⏳"
        click.echo(f"  {status_icon} {ts.task_id}: {ts.name}")
        click.echo(f"     Status: {ts.status}")
        click.echo(f"     Progress: {ts.completed_steps}/{ts.total_steps} steps")
        click.echo()


@main.command("sync")
@click.argument("feature_or_path")
@click.option("--dry-run", is_flag=True, help="Show what would be changed without making changes.")
def task_sync(feature_or_path: str, dry_run: bool) -> None:
    """Sync task statuses based on checkbox completion.

    Supports full path (specs/...) or feature name (e.g., workflow-type-contracts).
    """
    spec_dir = _resolve_spec_dir(feature_or_path)
    results = sync_all_tasks(spec_dir, dry_run=dry_run)

    if dry_run:
        click.echo("\n🔍 Dry Run - Changes that would be made:\n")
    else:
        click.echo("\n✅ Task Status Sync Results:\n")

    for result in results:
        action = result["action"]
        details = result["details"]

        if action == "fixed":
            click.echo(f"  🔧 {details}")
        elif action == "would_fix":
            click.echo(f"  📝 {details}")
        elif action == "no_change":
            click.echo(f"  ✓ {details}")
        else:
            click.echo(f"  ⚠️  {details}")

    click.echo()
