"""Design document validation for pb-spec workflow specs."""

from __future__ import annotations

import re
from pathlib import Path

HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
LEADING_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
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
    section_names = {name for name, _, _ in sections}
    required_sections = _select_required_sections(section_names, sections)

    errors: list[str] = []
    section_map = {name: content for name, content, _ in sections}
    for section_name in required_sections:
        if section_name not in section_map:
            errors.append(f"Missing required design section in design.md: {section_name}")
            continue

        if _is_placeholder_content(section_map[section_name]) and not _has_subsections(
            section_name, sections
        ):
            errors.append(
                f"Required design section is empty or placeholder in design.md: {section_name}"
            )

    for section_name in _select_conditional_required_sections(section_names, sections):
        if section_name in required_sections:
            continue
        if section_name not in section_map:
            errors.append(f"Missing required design section in design.md: {section_name}")
            continue

        if _is_placeholder_content(section_map[section_name]) and not _has_subsections(
            section_name, sections
        ):
            errors.append(
                f"Required design section is empty or placeholder in design.md: {section_name}"
            )

    return errors


def _parse_design_sections(design_file: Path) -> list[tuple[str, str, int]]:
    """Parse design.md sections, returning (name, content, heading_level) tuples."""
    lines = design_file.read_text(encoding="utf-8").splitlines()
    sections: list[tuple[str, str, int]] = []
    current_heading: str | None = None
    current_level: int = 0
    current_content: list[str] = []

    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            normalized_heading = _normalize_heading(heading_match.group(2))
            if current_heading is not None:
                sections.append(
                    (current_heading, "\n".join(current_content).strip(), current_level)
                )
            current_heading = normalized_heading
            current_level = level
            current_content = []
            continue

        if current_heading is not None:
            current_content.append(line)

    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_content).strip(), current_level))

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


def _select_required_sections(
    section_names: set[str], sections: list[tuple[str, str, int]] | None = None
) -> tuple[str, ...]:
    lightweight_names = section_names & LIGHTWEIGHT_ONLY_SECTIONS
    if lightweight_names and sections:
        for name, _, level in sections:
            if name in lightweight_names and level == 2:
                return LIGHTWEIGHT_MODE_REQUIRED_SECTIONS
    elif lightweight_names:
        return LIGHTWEIGHT_MODE_REQUIRED_SECTIONS
    return FULL_MODE_REQUIRED_SECTIONS


def _select_conditional_required_sections(
    section_names: set[str], sections: list[tuple[str, str, int]] | None = None
) -> tuple[str, ...]:
    conditional_sections: list[str] = []
    is_lightweight = False
    lightweight_names = section_names & LIGHTWEIGHT_ONLY_SECTIONS
    if lightweight_names and sections:
        for name, _, level in sections:
            if name in lightweight_names and level == 2:
                is_lightweight = True
                break
    elif lightweight_names:
        is_lightweight = True

    if "Existing Components to Reuse" not in section_names:
        conditional_sections.append("Existing Components to Reuse")

    if (
        is_lightweight
        and "BDD/TDD Strategy" in section_names
        and "BDD Scenario Inventory" not in section_names
    ):
        conditional_sections.append("BDD Scenario Inventory")

    return tuple(conditional_sections)


def _has_subsections(section_name: str, sections: list[tuple[str, str, int]]) -> bool:
    """Check whether a section has child subsections at a deeper heading level."""
    idx = None
    parent_level = 0
    for i, (name, _, level) in enumerate(sections):
        if name == section_name:
            idx = i
            parent_level = level
            break
    if idx is None:
        return False
    for _, _, level in sections[idx + 1 :]:
        if level > parent_level:
            return True
        break
    return False


def _is_placeholder_content(content: str) -> bool:
    stripped_content = content.strip()
    if not stripped_content:
        return True
    return bool(PLACEHOLDER_RE.fullmatch(stripped_content))
