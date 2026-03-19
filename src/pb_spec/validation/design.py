"""Design document validation for pb-spec workflow specs."""

from __future__ import annotations

import re
from pathlib import Path

HEADING_RE = re.compile(r"^#{2,6}\s+(.+?)\s*$")
LEADING_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.\s+")
PLACEHOLDER_RE = re.compile(r"^(?:TBD|\[To be written\]|\[[^\]]+\])$", re.IGNORECASE)

FULL_MODE_REQUIRED_SECTIONS = (
    "Executive Summary",
    "Requirements & Goals",
    "Architecture Overview",
    "Detailed Design",
    "Verification & Testing Strategy",
    "Implementation Plan",
)
LIGHTWEIGHT_MODE_REQUIRED_SECTIONS = (
    "Summary",
    "Approach",
    "Architecture Decisions",
    "BDD/TDD Strategy",
    "Code Simplification Constraints",
    "BDD Scenario Inventory",
    "Existing Components to Reuse",
    "Verification",
)


def validate_design_file(design_file: Path) -> list[str]:
    """Validate required design.md sections for full or lightweight mode."""
    sections = _parse_design_sections(design_file)
    section_names = {name for name, _ in sections}
    required_sections = _select_required_sections(section_names)

    errors: list[str] = []
    section_map = dict(sections)
    for section_name in required_sections:
        if section_name not in section_map:
            errors.append(f"Missing required design section in design.md: {section_name}")
            continue

        if _is_placeholder_content(section_map[section_name]):
            errors.append(
                f"Required design section is empty or placeholder in design.md: {section_name}"
            )

    for section_name in _select_conditional_required_sections(section_names):
        if section_name in required_sections:
            continue
        if section_name not in section_map:
            errors.append(f"Missing required design section in design.md: {section_name}")
            continue

        if _is_placeholder_content(section_map[section_name]):
            errors.append(
                f"Required design section is empty or placeholder in design.md: {section_name}"
            )

    return errors


def _parse_design_sections(design_file: Path) -> list[tuple[str, str]]:
    lines = design_file.read_text(encoding="utf-8").splitlines()
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_content: list[str] = []

    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match:
            normalized_heading = _normalize_heading(heading_match.group(1))
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_content).strip()))
            current_heading = normalized_heading
            current_content = []
            continue

        if current_heading is not None:
            current_content.append(line)

    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_content).strip()))

    return sections


def _normalize_heading(heading: str) -> str:
    normalized_heading = heading.strip()
    normalized_heading = LEADING_NUMBER_RE.sub("", normalized_heading)
    return normalized_heading


LIGHTWEIGHT_ONLY_SECTIONS = frozenset(
    {
        "Code Simplification Constraints",
    }
)


def _select_required_sections(section_names: set[str]) -> tuple[str, ...]:
    if section_names & LIGHTWEIGHT_ONLY_SECTIONS:
        return LIGHTWEIGHT_MODE_REQUIRED_SECTIONS
    return FULL_MODE_REQUIRED_SECTIONS


def _select_conditional_required_sections(section_names: set[str]) -> tuple[str, ...]:
    conditional_sections: list[str] = []
    is_lightweight = bool(section_names & LIGHTWEIGHT_ONLY_SECTIONS)

    if "Existing Components to Reuse" not in section_names:
        conditional_sections.append("Existing Components to Reuse")

    if (
        is_lightweight
        and "BDD/TDD Strategy" in section_names
        and "BDD Scenario Inventory" not in section_names
    ):
        conditional_sections.append("BDD Scenario Inventory")

    return tuple(conditional_sections)


def _is_placeholder_content(content: str) -> bool:
    stripped_content = content.strip()
    if not stripped_content:
        return True
    return bool(PLACEHOLDER_RE.fullmatch(stripped_content))
