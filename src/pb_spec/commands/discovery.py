"""Spec directory discovery for pb-spec."""

from __future__ import annotations

import re
from pathlib import Path

from pb_spec.exceptions import SpecNotFoundError


def get_latest_spec_dir(specs_dir: Path | None = None) -> Path:
    """Get the latest feature spec directory from specs/."""
    if specs_dir is None:
        specs_dir = Path("specs")

    if not specs_dir.exists() or not specs_dir.is_dir():
        raise SpecNotFoundError("Directory 'specs/' not found. Run /pb-plan first.")

    spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
    if not spec_dirs:
        raise SpecNotFoundError("No feature specs found in 'specs/'.")

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")

    def sort_key(d: Path) -> tuple[int, str]:
        if date_pattern.match(d.name):
            return (1, d.name)
        return (0, d.name)

    return sorted(spec_dirs, key=sort_key)[-1]
