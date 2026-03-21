"""Feature-file scenario inventory for pb-spec workflow specs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from pb_spec.validation.types import FeatureScenario

# Enhanced regex patterns for Gherkin parsing
SCENARIO_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(Scenario(?:\s+Outline|\s+Template)?)\s*:\s*(.+?)\s*$", re.IGNORECASE
)
COMMENT_RE: Final[re.Pattern[str]] = re.compile(r"^\s*#")
TAG_RE: Final[re.Pattern[str]] = re.compile(r"^\s*@")
EXAMPLES_RE: Final[re.Pattern[str]] = re.compile(r"^\s*Examples\s*:", re.IGNORECASE)


def collect_feature_scenarios(features_dir: Path) -> dict[str, Path]:
    """Collect scenario names from `.feature` files under a features directory.

    Recursively scans subdirectories and supports Scenario, Scenario Outline,
    and Scenario Template variants.

    Args:
        features_dir: Root directory containing .feature files.

    Returns:
        Dictionary mapping scenario names to their source file paths.
    """
    scenario_inventory: dict[str, Path] = {}

    for feature_file in sorted(features_dir.rglob("*.feature")):
        scenarios = parse_feature_file(feature_file)
        for scenario in scenarios:
            scenario_inventory[scenario.name] = scenario.feature_file

    return scenario_inventory


def parse_feature_file(feature_file: Path) -> list[FeatureScenario]:
    """Parse a single .feature file and extract all scenarios.

    Handles:
    - Regular Scenario
    - Scenario Outline / Scenario Template
    - Comments (lines starting with #)
    - Tags (lines starting with @)
    - Multi-line scenario names (continues until non-indented line)

    Args:
        feature_file: Path to the .feature file.

    Returns:
        List of FeatureScenario objects found in the file.
    """
    scenarios: list[FeatureScenario] = []
    content = feature_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    in_examples = False
    current_scenario: str | None = None
    current_line: int = 0
    current_is_outline: bool = False

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or COMMENT_RE.match(line):
            continue

        # Skip tags (they precede scenarios but don't affect parsing)
        if TAG_RE.match(line):
            continue

        # Detect Examples section (we skip scenario names in Examples)
        if EXAMPLES_RE.match(line):
            in_examples = True
            continue

        # Exit Examples section when we hit a non-table line
        if in_examples:
            if stripped.startswith("|") or not stripped:
                continue
            in_examples = False

        # Try to match a scenario
        scenario_match = SCENARIO_RE.match(line)
        if scenario_match:
            # Save previous scenario if exists
            if current_scenario is not None:
                scenarios.append(
                    FeatureScenario(
                        name=current_scenario,
                        feature_file=feature_file,
                        line_number=current_line,
                        is_outline=current_is_outline,
                    )
                )

            # Start new scenario
            scenario_type = scenario_match.group(1).strip().lower()
            current_scenario = scenario_match.group(2).strip()
            current_line = line_num
            current_is_outline = "outline" in scenario_type or "template" in scenario_type
            continue

        # Handle multi-line scenario names (indented continuation)
        if (
            current_scenario is not None
            and line.startswith("  ")
            and not stripped.startswith(("Given", "When", "Then", "And", "But", "|"))
        ):
            # This is a continuation of the scenario name
            current_scenario = f"{current_scenario} {stripped}"
            continue

    # Don't forget the last scenario
    if current_scenario is not None:
        scenarios.append(
            FeatureScenario(
                name=current_scenario,
                feature_file=feature_file,
                line_number=current_line,
                is_outline=current_is_outline,
            )
        )

    return scenarios


def find_feature_files(features_dir: Path) -> list[Path]:
    """Return the `.feature` files present under a features directory (recursive).

    Args:
        features_dir: Root directory to search.

    Returns:
        Sorted list of .feature file paths.
    """
    return sorted(features_dir.rglob("*.feature"))


def get_scenario_by_name(features_dir: Path, scenario_name: str) -> FeatureScenario | None:
    """Find a specific scenario by name across all feature files.

    Args:
        features_dir: Root directory containing .feature files.
        scenario_name: Name of the scenario to find.

    Returns:
        FeatureScenario if found, None otherwise.
    """
    for feature_file in sorted(features_dir.rglob("*.feature")):
        scenarios = parse_feature_file(feature_file)
        for scenario in scenarios:
            if scenario.name == scenario_name:
                return scenario
    return None
