"""rumdl markdown formatting integration for pb-spec."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pb_spec.config import get_timeout_config


@dataclass(frozen=True)
class FormatResult:
    """Result of a rumdl formatting operation."""

    success: bool
    messages: list[str] = field(default_factory=list)
    formatted_count: int = 0
    has_warnings: bool = False


def is_rumdl_available() -> bool:
    """Check if rumdl is available and working."""
    try:
        timeouts = get_timeout_config()
        subprocess.run(
            ["rumdl", "--version"], capture_output=True, check=True, timeout=timeouts.rumdl_check
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


MAX_RUMDL_TIMEOUT = 120


def run_rumdl_format(spec_dir: Path) -> FormatResult:
    """Format markdown files using rumdl.

    Passes all files in a single rumdl invocation for efficiency.
    Returns a pure FormatResult without side effects.
    Callers are responsible for presenting the results.
    """
    md_files = list(spec_dir.rglob("*.md"))
    if not md_files:
        return FormatResult(success=True)

    if not is_rumdl_available():
        return FormatResult(
            success=True,
            messages=[
                "Command 'rumdl' not found — skipping markdown auto-format. "
                "Install it with: cargo install rumdl  (or: pip install rumdl) "
                "to enable automatic markdown formatting."
            ],
            has_warnings=True,
        )

    try:
        timeouts = get_timeout_config()
        file_args = [str(f) for f in md_files]
        subprocess.run(
            ["rumdl", "fmt", *file_args],
            capture_output=True,
            text=True,
            timeout=min(timeouts.rumdl_format * len(md_files), MAX_RUMDL_TIMEOUT),
            check=True,
        )
        return FormatResult(
            success=True,
            messages=[f"Formatted {len(md_files)} file(s)"],
            formatted_count=len(md_files),
        )
    except subprocess.TimeoutExpired:
        return FormatResult(
            success=False,
            messages=[f"rumdl timed out formatting {len(md_files)} files"],
            has_warnings=True,
        )
    except subprocess.CalledProcessError as e:
        return FormatResult(
            success=False,
            messages=[f"rumdl failed: {e.stderr.strip()}"],
            has_warnings=True,
        )
    except OSError as e:
        return FormatResult(
            success=False,
            messages=[f"Unexpected error formatting files: {e}"],
            has_warnings=True,
        )
