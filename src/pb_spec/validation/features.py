"""Feature-file scenario inventory for pb-spec workflow specs."""

from __future__ import annotations

import re
from pathlib import Path

SCENARIO_RE = re.compile(r"^\s*Scenario(?:\s+Outline|\s+Template)?:\s+(.+?)\s*$")


def collect_feature_scenarios(features_dir: Path) -> dict[str, Path]:
    """Collect scenario names from `.feature` files under a features directory.

    Recursively scans subdirectories and supports Scenario, Scenario Outline,
    and Scenario Template variants.
    """
    scenario_inventory: dict[str, Path] = {}

    for feature_file in sorted(features_dir.rglob("*.feature")):
        for line in feature_file.read_text(encoding="utf-8").splitlines():
            match = SCENARIO_RE.match(line)
            if match:
                scenario_inventory[match.group(1)] = feature_file

    return scenario_inventory


def find_feature_files(features_dir: Path) -> list[Path]:
    """Return the `.feature` files present under a features directory (recursive)."""
    return sorted(features_dir.rglob("*.feature"))
