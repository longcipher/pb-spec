"""Shared parsing helpers for validation modules."""

from __future__ import annotations

import re


def extract_requirement_matrix_scenario_refs(coverage: str) -> list[tuple[str | None, str]]:
    """Extract scenario references from a Requirements Coverage Matrix cell."""
    normalized_coverage = coverage.strip().strip("`")
    if (
        not normalized_coverage
        or normalized_coverage == "N/A"
        or normalized_coverage.startswith("N/A ")
    ):
        return []

    if "`, `" in normalized_coverage:
        refs = []
        for part in normalized_coverage.split("`, `"):
            parsed = _parse_requirement_matrix_scenario_ref(part.strip().strip("`"))
            if parsed is not None:
                refs.append(parsed)
        return refs

    parsed = _parse_requirement_matrix_scenario_ref(normalized_coverage.strip("`"))
    return [parsed] if parsed is not None else []


def extract_requirement_matrix_task_refs(coverage: str) -> list[str]:
    """Extract Task X.Y references from a Requirements Coverage Matrix cell."""
    normalized_coverage = coverage.strip().strip("`")
    if _is_not_applicable_matrix_value(normalized_coverage):
        return []
    return re.findall(r"Task \d+\.\d+", normalized_coverage)


def extract_requirement_matrix_requirement_refs(coverage: str) -> set[str]:
    """Extract requirement ID references from a task's Requirement Coverage field."""
    normalized_coverage = coverage.strip().strip("`")
    if _is_not_applicable_matrix_value(normalized_coverage):
        return set()
    return set(re.findall(r"\b[A-Z]+[A-Z0-9_-]*\d+\b", normalized_coverage))


def is_not_applicable_matrix_value(value: str) -> bool:
    """Check if a matrix cell value is N/A."""
    return _is_not_applicable_matrix_value(value)


def _is_not_applicable_matrix_value(value: str) -> bool:
    normalized = value.strip().strip("`")
    return not normalized or normalized == "N/A" or normalized.startswith("N/A ")


def _parse_requirement_matrix_scenario_ref(value: str) -> tuple[str | None, str] | None:
    normalized = value.strip()
    if not normalized:
        return None

    if " / " in normalized:
        feature_name, scenario_name = normalized.split(" / ", 1)
        scenario_name = scenario_name.strip()
        if scenario_name.lower() == "all scenarios":
            return None
        return feature_name.strip(), scenario_name

    scenario_name = re.sub(r"^[^A-Za-z0-9_\-]*", "", normalized).strip()
    return (None, scenario_name) if scenario_name else None
