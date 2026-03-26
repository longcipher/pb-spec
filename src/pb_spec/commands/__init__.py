"""CLI commands for pb-spec."""

from __future__ import annotations

__all__ = [
    "init_cmd",
    "task_status",
    "task_sync",
    "update_cmd",
    "validate_cmd",
    "version_cmd",
]

from pb_spec.commands.init import init_cmd
from pb_spec.commands.task_status import scan_task_statuses, sync_all_tasks
from pb_spec.commands.update import update_cmd
from pb_spec.commands.validate import validate_cmd
from pb_spec.commands.version import version_cmd

# Aliases for CLI registration
task_status = scan_task_statuses
task_sync = sync_all_tasks
