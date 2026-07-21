"""Markdown parser for extracting task blocks and contract blocks from tasks.md."""

from __future__ import annotations

import re
from dataclasses import dataclass

TASK_HEADING_RE = re.compile(r"^(#{2,3})\s+Task\s+(\d+\.\d+):\s*(.*)$", re.MULTILINE)
TASK_CHECKBOX_RE = re.compile(r"^[ \t]*- \[[ xX]\].*", re.MULTILINE)
UNCHECKED_TASK_CHECKBOX_RE = re.compile(r"^[ \t]*- \[ \].*", re.MULTILINE)
CONTRACT_BLOCK_HEADER_RE = re.compile(
    r"^(🛑 Build Blocked|🔄 Design Change Request)\s+—\s+Task\s+(\d+\.\d+):\s*(.*)$",
    re.MULTILINE,
)
FIELD_RE = re.compile(r"^\s*(\w+(?:\s+\w+)*):\s*(.*)")

ALLOWED_TASK_STATUSES = frozenset(
    {
        "🔴 TODO",
        "🟡 IN PROGRESS",
        "🟢 DONE",
        "⏭️ SKIPPED",
        "🔄 DCR",
        "⛔ OBSOLETE",
        "TODO",
    }
)
BUILD_BLOCKED_REQUIRED_SECTIONS = frozenset({"Reason", "Requested Change", "Impact"})
DCR_REQUIRED_SECTIONS = frozenset({"Reason", "Requested Change", "Impact"})
CONTRACT_SECTION_NAMES = BUILD_BLOCKED_REQUIRED_SECTIONS | DCR_REQUIRED_SECTIONS

_CONTRACT_REQUIRED_SECTIONS: dict[str, frozenset[str]] = {
    "🛑 Build Blocked": BUILD_BLOCKED_REQUIRED_SECTIONS,
    "🔄 Design Change Request": DCR_REQUIRED_SECTIONS,
}

KNOWN_TASK_FIELDS = frozenset(
    {
        "Context:",
        "Verification:",
        "Status:",
        "Scenario Coverage:",
    }
)


@dataclass(frozen=True)
class TaskBlock:
    """Represents a parsed task block from tasks.md."""

    id: str
    name: str
    content: str
    fields: dict[str, str]


@dataclass(frozen=True)
class ContractBlock:
    """Represents a markdown-carried workflow contract block."""

    kind: str
    task_id: str
    name: str
    sections: dict[str, str]


def _is_continuation_line(line: str) -> bool:
    """Check if a line is a continuation of a multi-line field value."""
    stripped = line.strip()
    if not stripped:
        return False
    if TASK_CHECKBOX_RE.match(line):
        return False
    return not FIELD_RE.match(line)


def parse_task_blocks(content: str) -> list[TaskBlock]:
    """Parse markdown content and extract task blocks."""
    lines = content.split("\n")
    task_blocks: list[TaskBlock] = []

    task_id = ""
    task_name = ""
    task_content_lines: list[str] = []
    task_fields: dict[str, str] = {}
    current_field = ""
    current_field_content: list[str] = []
    in_task = False

    def _flush_field() -> None:
        if in_task and current_field:
            task_fields[current_field] = "\n".join(current_field_content).strip()

    def _flush_task() -> None:
        if in_task:
            task_blocks.append(
                TaskBlock(
                    id=task_id,
                    name=task_name,
                    content="\n".join(task_content_lines),
                    fields=dict(task_fields),
                )
            )

    for line in lines:
        task_match = TASK_HEADING_RE.match(line)
        if task_match:
            _flush_field()
            _flush_task()

            _level, task_id, task_name_raw = task_match.groups()
            task_name = task_name_raw.strip()
            task_content_lines = [line]
            task_fields = {}
            current_field = ""
            current_field_content = []
            in_task = True
            continue

        if not in_task:
            continue

        task_content_lines.append(line)

        field_match = FIELD_RE.match(line)
        if field_match:
            candidate_name = field_match.group(1) + ":"
            if candidate_name in KNOWN_TASK_FIELDS:
                _flush_field()
                field_value = field_match.group(2).strip()
                current_field = candidate_name
                current_field_content = [field_value] if field_value else []
                task_fields[current_field] = field_value
            elif _is_continuation_line(line) and current_field:
                current_field_content.append(line)
                task_fields[current_field] = "\n".join(current_field_content).strip()
        elif _is_continuation_line(line) and current_field:
            current_field_content.append(line)
            task_fields[current_field] = "\n".join(current_field_content).strip()

    _flush_field()
    _flush_task()

    return task_blocks


def task_display_name(task_block: TaskBlock) -> str:
    """Return a stable task display name for diagnostics."""
    return f"{task_block.id}: {task_block.name}" if task_block.name else task_block.id


def parse_contract_sections(block_body: str) -> dict[str, str]:
    """Parse colon-delimited sections from a DCR or build-blocked body."""
    sections: dict[str, list[str]] = {}
    current_section = ""

    for raw_line in block_body.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        section_name, separator, value = line.partition(":")
        if separator and section_name in CONTRACT_SECTION_NAMES:
            current_section = section_name
            sections.setdefault(current_section, [])
            if value.strip():
                sections[current_section].append(value.strip())
            continue

        if current_section:
            sections[current_section].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def parse_contract_blocks(content: str) -> list[ContractBlock]:
    """Parse markdown-carried DCR and build-blocked packets from tasks.md."""
    matches = list(CONTRACT_BLOCK_HEADER_RE.finditer(content))
    blocks: list[ContractBlock] = []

    for index, match in enumerate(matches):
        kind, task_id, name = match.groups()
        end_candidates = [len(content)]

        if index + 1 < len(matches):
            end_candidates.append(matches[index + 1].start())

        next_task = TASK_HEADING_RE.search(content, match.end())
        if next_task:
            end_candidates.append(next_task.start())

        block_body = content[match.end() : min(end_candidates)]
        blocks.append(
            ContractBlock(
                kind=kind,
                task_id=task_id,
                name=name.strip(),
                sections=parse_contract_sections(block_body),
            )
        )

    return blocks


def validate_contract_blocks(content: str) -> list[str]:
    """Validate required sections for markdown workflow contract blocks.

    Both Build Blocked and DCR packets require the same three sections:
    Reason, Requested Change, Impact.
    """
    errors: list[str] = []

    for block in parse_contract_blocks(content):
        required = _CONTRACT_REQUIRED_SECTIONS.get(block.kind, DCR_REQUIRED_SECTIONS)
        missing_sections = [
            section for section in required if not block.sections.get(section, "").strip()
        ]
        if missing_sections:
            errors.append(
                f"Incomplete {block.kind} packet for Task {block.task_id}: "
                f"Missing required section(s): {', '.join(missing_sections)}"
            )

    return errors
