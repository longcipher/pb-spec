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


def is_rumdl_available() -> bool:
    """Check if rumdl is available and working."""
    try:
        timeouts = get_timeout_config()
        subprocess.run(
            ["rumdl", "--version"], capture_output=True, check=True, timeout=timeouts["rumdl_check"]
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def run_rumdl_format(spec_dir: Path) -> FormatResult:
    """Format markdown files using rumdl.

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
        )

    messages: list[str] = []
    formatted_count = 0

    for md_file in md_files:
        try:
            timeouts = get_timeout_config()
            subprocess.run(
                ["rumdl", "fmt", str(md_file)],
                capture_output=True,
                text=True,
                timeout=timeouts["rumdl_format"],
                check=True,
            )
            messages.append(f"Formatted: {md_file.name}")
            formatted_count += 1
        except subprocess.TimeoutExpired:
            messages.append(f"rumdl timed out on {md_file.name}")
        except subprocess.CalledProcessError as e:
            messages.append(f"rumdl failed on {md_file.name}: {e.stderr.strip()}")
        except OSError as e:
            messages.append(f"Unexpected error formatting {md_file.name}: {e}")

    return FormatResult(success=True, messages=messages, formatted_count=formatted_count)
