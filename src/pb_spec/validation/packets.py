"""Validation helpers for markdown-carried build-block and DCR packets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

PLACEHOLDER_RE = re.compile(r"^(?:TBD|\[To be written\]|\[[^\]]+\])$", re.IGNORECASE)
BUILD_BLOCKED_HEADER_RE = re.compile(r"^🛑 Build Blocked — (Task \d+\.\d+: .+?)\s*$")
DCR_HEADER_RE = re.compile(r"^🔄 Design Change Request — (Task \d+\.\d+: .+?)\s*$")
QUOTED_TEXT_RE = re.compile(r'("[^"\n]{3,}"|\'[^\'\n]{3,}\'|`[^`\n]{3,}`)')
GHERKIN_STEP_RE = re.compile(r"^(?:Given|When|Then|And|But)\b")
TASK_REFERENCE_RE = re.compile(r"\bTask \d+\.\d+\b")

BUILD_BLOCKED_SECTIONS = (
    "Reason",
    "Loop Type",
    "Scenario Coverage",
    "What We Tried",
    "Failure Evidence",
    "Failing Step",
    "Suggested Design Change",
    "Impact",
    "Next Action",
)
DCR_SECTIONS = (
    "Scenario Coverage",
    "Problem",
    "What We Tried",
    "Failure Evidence",
    "Failing Step",
    "Suggested Change",
    "Impact",
)
_SECTION_NAME_ITEMS: list[str] = [*BUILD_BLOCKED_SECTIONS, *DCR_SECTIONS]
SECTION_NAMES: tuple[str, ...] = tuple(
    cast(str, section_name)
    for section_name in sorted(set(_SECTION_NAME_ITEMS), key=len, reverse=True)
)


@dataclass(slots=True)
class FeedbackPacket:
    kind: str
    task_label: str
    body_lines: list[str]


def validate_feedback_file(feedback_file: Path) -> list[str]:
    """Validate markdown-carried build-block or DCR packets in a feedback file."""
    packets = parse_feedback_packets(feedback_file)
    errors: list[str] = []

    for packet in packets:
        sections = _parse_packet_sections(packet.body_lines)
        required_sections = (
            BUILD_BLOCKED_SECTIONS if packet.kind == "🛑 Build Blocked" else DCR_SECTIONS
        )
        missing_sections: list[str] = []

        for section_name in required_sections:
            if section_name not in sections:
                missing_sections.append(section_name)
                continue

            is_placeholder = _is_placeholder_content(sections[section_name])
            if is_placeholder:
                errors.append(
                    f"Required packet section is empty or placeholder in {packet.kind}: {section_name}"
                )

            if (
                section_name == "Scenario Coverage"
                and not is_placeholder
                and not _has_concrete_packet_scenario_coverage(sections[section_name])
            ):
                errors.append(
                    f"Scenario Coverage must reference a .feature file and scenario name in {packet.kind}"
                )

            if (
                section_name == "Failure Evidence"
                and not is_placeholder
                and not _has_concrete_failure_evidence(sections[section_name])
            ):
                errors.append(
                    f"Failure Evidence must include concrete command output or quoted error text in {packet.kind}"
                )

            if (
                section_name == "Failing Step"
                and not is_placeholder
                and not _is_valid_failing_step(sections[section_name])
            ):
                errors.append(f"Failing Step must be a Gherkin step or N/A in {packet.kind}")

            if (
                packet.kind == "🛑 Build Blocked"
                and section_name == "Next Action"
                and not is_placeholder
                and not _has_concrete_build_blocked_next_action(sections[section_name])
            ):
                errors.append(
                    "Next Action must include concrete /pb-refine and /pb-build follow-up commands in 🛑 Build Blocked"
                )

            if (
                packet.kind == "🛑 Build Blocked"
                and section_name == "Suggested Design Change"
                and not is_placeholder
                and not _references_build_blocked_change_artifacts(sections[section_name])
            ):
                errors.append(
                    "Suggested Design Change must reference design.md or tasks.md in 🛑 Build Blocked"
                )

            if (
                packet.kind == "🔄 Design Change Request"
                and section_name == "Suggested Change"
                and not is_placeholder
                and not _references_dcr_change_artifacts(sections[section_name])
            ):
                errors.append(
                    "Suggested Change must reference design.md in 🔄 Design Change Request"
                )

            if (
                section_name == "Impact"
                and not is_placeholder
                and not _has_concrete_impact(sections[section_name])
            ):
                errors.append(
                    f"Impact must reference affected tasks or explicitly say no other tasks are affected in {packet.kind}"
                )

        if missing_sections:
            errors.append(
                f"Incomplete {packet.kind} packet. Missing required section(s): "
                + ", ".join(missing_sections)
            )

    return errors


def parse_feedback_packets(feedback_file: Path) -> list[FeedbackPacket]:
    """Parse build-block and DCR packets from a markdown feedback file."""
    lines = feedback_file.read_text(encoding="utf-8").splitlines()
    packets: list[FeedbackPacket] = []
    current_kind: str | None = None
    current_task_label: str | None = None
    current_body: list[str] = []

    for line in lines:
        header_match = BUILD_BLOCKED_HEADER_RE.match(line)
        if header_match:
            if current_kind is not None and current_task_label is not None:
                packets.append(FeedbackPacket(current_kind, current_task_label, current_body))
            current_kind = "🛑 Build Blocked"
            current_task_label = header_match.group(1)
            current_body = []
            continue

        header_match = DCR_HEADER_RE.match(line)
        if header_match:
            if current_kind is not None and current_task_label is not None:
                packets.append(FeedbackPacket(current_kind, current_task_label, current_body))
            current_kind = "🔄 Design Change Request"
            current_task_label = header_match.group(1)
            current_body = []
            continue

        if current_kind is not None:
            current_body.append(line)

    if current_kind is not None and current_task_label is not None:
        packets.append(FeedbackPacket(current_kind, current_task_label, current_body))

    return packets


def _parse_packet_sections(lines: list[str]) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_section: str | None = None
    current_content: list[str] = []

    for line in lines:
        section_name = _match_section_name(line)
        if section_name is not None:
            if current_section is not None:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = section_name
            current_content = [line[len(section_name) + 1 :].strip()]
            continue

        if current_section is not None:
            current_content.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _match_section_name(line: str) -> str | None:
    for section_name in SECTION_NAMES:
        if line.startswith(f"{section_name}:"):
            return section_name
    return None


def _is_placeholder_content(content: str) -> bool:
    stripped_content = content.strip()
    if not stripped_content:
        return True
    return bool(PLACEHOLDER_RE.fullmatch(stripped_content))


def _has_concrete_failure_evidence(content: str) -> bool:
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "->" in line:
            return True
        if QUOTED_TEXT_RE.search(line):
            return True
    return False


def _is_valid_failing_step(content: str) -> bool:
    stripped_content = content.strip()
    if stripped_content == "N/A":
        return True
    return bool(GHERKIN_STEP_RE.match(stripped_content))


def _has_concrete_build_blocked_next_action(content: str) -> bool:
    normalized_content = content.strip()
    return "/pb-refine" in normalized_content and "/pb-build" in normalized_content


def _references_build_blocked_change_artifacts(content: str) -> bool:
    normalized_content = content.strip()
    return "design.md" in normalized_content or "tasks.md" in normalized_content


def _references_dcr_change_artifacts(content: str) -> bool:
    normalized_content = content.strip()
    return "design.md" in normalized_content


def _has_concrete_impact(content: str) -> bool:
    normalized_content = content.strip()
    if TASK_REFERENCE_RE.search(normalized_content):
        return True

    lowered_content = normalized_content.lower()
    return "no other tasks are affected" in lowered_content


def _has_concrete_packet_scenario_coverage(content: str) -> bool:
    normalized_content = content.strip()
    feature_index = normalized_content.find(".feature")
    if feature_index == -1:
        return False

    trailing_content = normalized_content[feature_index + len(".feature") :].strip()
    trailing_content = trailing_content.lstrip(" :+-|>")
    return bool(trailing_content)
