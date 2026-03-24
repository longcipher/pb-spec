"""Design document validation for pb-spec workflow specs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pb_spec.validation.types import ValidationResult

HEADING_RE: Final[re.Pattern[str]] = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
LEADING_NUMBER_RE: Final[re.Pattern[str]] = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
PLACEHOLDER_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:TBD|\[To be written\]|\[[^\]]+\])$", re.IGNORECASE
)

FULL_MODE_REQUIRED_SECTIONS: Final[tuple[str, ...]] = (
    "Executive Summary",
    "Source Inputs & Normalization",
    "Requirements & Goals",
    "Requirements Coverage Matrix",
    "Architecture Overview",
    "Detailed Design",
    "Verification & Testing Strategy",
    "Implementation Plan",
)
LIGHTWEIGHT_MODE_REQUIRED_SECTIONS: Final[tuple[str, ...]] = (
    "Summary",
    "Approach",
    "Architecture Decisions",
    "BDD/TDD Strategy",
    "Code Simplification Constraints",
    "BDD Scenario Inventory",
    "Existing Components to Reuse",
    "Verification",
)


@dataclass(slots=True, frozen=True)
class RequirementCoverageRow:
    requirement_id: str
    covered_in_design: str
    scenario_coverage: str
    task_coverage: str
    status_rationale: str


def validate_design_file(design_file: Path) -> list[str]:
    """Validate required design.md sections for full or lightweight mode.

    Returns list of error strings for backward compatibility.
    """
    result = validate_design_file_structured(design_file)
    # Return only error messages without file path prefix for backward compatibility
    return [error.message for error in result.errors]


def validate_design_file_structured(design_file: Path) -> ValidationResult:
    """Validate required design.md sections for full or lightweight mode.

    Returns structured ValidationResult with errors and warnings.
    """
    result = ValidationResult()
    sections = _parse_design_sections(design_file)
    section_names = {name for name, _, _ in sections}
    required_sections = _select_required_sections(section_names, sections)

    section_map = {name: content for name, content, _ in sections}
    for section_name in required_sections:
        if section_name not in section_map:
            result.add_error(
                f"Missing required design section in design.md: {section_name}",
                file=str(design_file),
            )
            continue

        if _is_placeholder_content(section_map[section_name]) and not _has_subsections(
            section_name, sections
        ):
            result.add_error(
                f"Required design section is empty or placeholder in design.md: {section_name}",
                file=str(design_file),
            )

    for section_name in _select_conditional_required_sections(section_names, sections):
        if section_name in required_sections:
            continue
        if section_name not in section_map:
            result.add_error(
                f"Missing required design section in design.md: {section_name}",
                file=str(design_file),
            )
            continue

        if _is_placeholder_content(section_map[section_name]) and not _has_subsections(
            section_name, sections
        ):
            result.add_error(
                f"Required design section is empty or placeholder in design.md: {section_name}",
                file=str(design_file),
            )

    if _select_required_sections(section_names, sections) == FULL_MODE_REQUIRED_SECTIONS:
        traceability_result = _validate_requirement_traceability(section_map, design_file)
        result.merge(traceability_result)

    return result


def parse_source_requirement_ids(design_file: Path) -> set[str]:
    """Return requirement IDs listed in the source requirement ledger."""
    sections = _parse_design_sections(design_file)
    section_map = {name: content for name, content, _ in sections}
    return _parse_requirement_ids_from_table(section_map.get("Source Requirement Ledger", ""))


def parse_requirements_coverage_matrix(
    design_file: Path,
) -> dict[str, RequirementCoverageRow]:
    """Return requirement rows from the requirements coverage matrix."""
    sections = _parse_design_sections(design_file)
    section_map = {name: content for name, content, _ in sections}
    return _parse_requirement_matrix_rows(section_map.get("Requirements Coverage Matrix", ""))


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


def _validate_requirement_traceability(
    section_map: dict[str, str], design_file: Path
) -> ValidationResult:
    """Validate requirement traceability between ledger and matrix."""
    result = ValidationResult()
    ledger_section = section_map.get("Source Requirement Ledger", "")
    matrix_section = section_map.get("Requirements Coverage Matrix", "")

    ledger_ids = _parse_requirement_ids_from_table(ledger_section)
    matrix_rows = _parse_requirement_matrix_rows(matrix_section)
    matrix_ids = set(matrix_rows)

    if ledger_section and not ledger_ids:
        result.add_error(
            "No requirement IDs found in Source Requirement Ledger",
            file=str(design_file),
        )

    if matrix_section and not matrix_ids:
        result.add_error(
            "No requirement IDs found in Requirements Coverage Matrix",
            file=str(design_file),
        )

    for requirement_id in sorted(ledger_ids - matrix_ids):
        result.add_error(
            "Requirement ID listed in Source Requirement Ledger but missing from "
            f"Requirements Coverage Matrix: {requirement_id}",
            file=str(design_file),
        )

    for requirement_id in sorted(matrix_ids - ledger_ids):
        result.add_error(
            "Requirement ID listed in Requirements Coverage Matrix but missing from "
            f"Source Requirement Ledger: {requirement_id}",
            file=str(design_file),
        )

    return result


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


def _parse_requirement_ids_from_table(content: str) -> set[str]:
    requirement_ids: set[str] = set()
    for row in _parse_markdown_table(content):
        requirement_id = row.get("Requirement ID", "").strip().strip("`")
        if requirement_id:
            requirement_ids.add(requirement_id)
    return requirement_ids


def _parse_requirement_matrix_rows(content: str) -> dict[str, RequirementCoverageRow]:
    rows: dict[str, RequirementCoverageRow] = {}
    for row in _parse_markdown_table(content):
        requirement_id = row.get("Requirement ID", "").strip().strip("`")
        if not requirement_id:
            continue
        rows[requirement_id] = RequirementCoverageRow(
            requirement_id=requirement_id,
            covered_in_design=row.get("Covered In Design", "").strip(),
            scenario_coverage=row.get("Scenario Coverage", "").strip(),
            task_coverage=row.get("Task Coverage", "").strip(),
            status_rationale=row.get("Status / Rationale", "").strip(),
        )
    return rows


def _parse_markdown_table(content: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 2:
        return []

    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


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
