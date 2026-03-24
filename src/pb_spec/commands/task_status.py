"""Task status management and synchronization for pb-spec workflow."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import click

from pb_spec.validation.tasks import parse_task_blocks

TASK_HEADING_RE: Final[re.Pattern[str]] = re.compile(r"^### (Task \d+\.\d+):\s+(.+?)\s*$")
STATUS_RE: Final[re.Pattern[str]] = re.compile(r"^- \*\*Status:\*\*\s*(.+?)\s*$")
CHECKBOX_RE: Final[re.Pattern[str]] = re.compile(r"^- \[([ xX])\] (.+)$")


@dataclass(slots=True)
class TaskStatus:
    """Represents the current status of a task."""

    task_id: str
    name: str
    status: str
    total_steps: int
    completed_steps: int
    is_complete: bool


def scan_task_statuses(spec_dir: Path) -> list[TaskStatus]:
    """Scan all tasks in a spec directory and return their statuses."""
    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        raise click.ClickException(f"Tasks file not found: {tasks_file}")

    task_blocks = parse_task_blocks(tasks_file)
    statuses: list[TaskStatus] = []

    for block in task_blocks:
        status = block.fields.get("Status", "🔴 TODO")
        total_steps = len(block.checkbox_lines)
        completed_steps = sum(
            1
            for line in block.checkbox_lines
            if line.startswith("- [x]") or line.startswith("- [X]")
        )
        is_complete = status == "🟢 DONE" and completed_steps == total_steps and total_steps > 0

        statuses.append(
            TaskStatus(
                task_id=block.task_id,
                name=block.name,
                status=status,
                total_steps=total_steps,
                completed_steps=completed_steps,
                is_complete=is_complete,
            )
        )

    return statuses


def fix_task_status(spec_dir: Path, task_id: str, *, dry_run: bool = False) -> dict[str, str]:
    """Fix task status based on checkbox completion.

    Returns dict with 'action' and 'details' describing what was done.
    """
    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        raise click.ClickException(f"Tasks file not found: {tasks_file}")

    content = tasks_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Find the task block
    in_task = False
    task_start = -1
    task_end = -1
    current_task_id = None

    for i, line in enumerate(lines):
        match = TASK_HEADING_RE.match(line)
        if match:
            if in_task and current_task_id == task_id:
                task_end = i
                break
            current_task_id = match.group(1)
            in_task = current_task_id == task_id
            if in_task:
                task_start = i
        elif in_task and TASK_HEADING_RE.match(line):
            task_end = i
            break

    if task_start == -1:
        raise click.ClickException(f"Task {task_id} not found in {tasks_file}")

    if task_end == -1:
        task_end = len(lines)

    # Analyze task block
    task_lines = lines[task_start:task_end]
    status_line_idx = None
    status_value = None
    total_steps = 0
    completed_steps = 0

    for i, line in enumerate(task_lines):
        status_match = STATUS_RE.match(line)
        if status_match:
            status_line_idx = i
            status_value = status_match.group(1).strip()

        checkbox_match = CHECKBOX_RE.match(line)
        if checkbox_match and "**Step" in line:
            total_steps += 1
            if checkbox_match.group(1).lower() == "x":
                completed_steps += 1

    # Determine correct status
    all_steps_complete = completed_steps == total_steps and total_steps > 0
    correct_status = "🟢 DONE" if all_steps_complete else "🟡 IN PROGRESS"

    # Check if status needs fixing
    needs_fix = status_value != correct_status

    if not needs_fix:
        return {
            "action": "no_change",
            "details": f"Task {task_id} status is already correct: {status_value}",
        }

    if dry_run:
        return {
            "action": "would_fix",
            "details": f"Task {task_id}: {status_value} -> {correct_status} ({completed_steps}/{total_steps} steps complete)",
        }

    # Apply fix
    if status_line_idx is not None:
        old_line = task_lines[status_line_idx]
        new_line = re.sub(
            r"^- \*\*Status:\*\*\s*.+$",
            f"- **Status:** {correct_status}",
            old_line,
        )
        lines[task_start + status_line_idx] = new_line
        tasks_file.write_text("\n".join(lines), encoding="utf-8")
        return {
            "action": "fixed",
            "details": f"Task {task_id}: {status_value} -> {correct_status} ({completed_steps}/{total_steps} steps complete)",
        }

    return {
        "action": "error",
        "details": f"Could not find Status field in Task {task_id}",
    }


def sync_all_tasks(spec_dir: Path, *, dry_run: bool = False) -> list[dict[str, str]]:
    """Sync all task statuses based on checkbox completion."""
    tasks_file = spec_dir / "tasks.md"
    if not tasks_file.exists():
        raise click.ClickException(f"Tasks file not found: {tasks_file}")

    task_blocks = parse_task_blocks(tasks_file)
    results: list[dict[str, str]] = []

    for block in task_blocks:
        result = fix_task_status(spec_dir, block.task_id, dry_run=dry_run)
        results.append(result)

    return results
