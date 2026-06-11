"""Markdown parser for extracting task blocks and contract blocks from tasks.md."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TASK_HEADING_RE = re.compile(r"^(#{2,3})\s+Task\s+(\d+\.\d+):\s*(.*)$", re.MULTILINE)
TASK_CHECKBOX_RE = re.compile(r"^[ \t]*- \[[ xX]\].*", re.MULTILINE)
UNCHECKED_TASK_CHECKBOX_RE = re.compile(r"^[ \t]*- \[ \].*", re.MULTILINE)
CONTRACT_BLOCK_HEADER_RE = re.compile(
    r"^(🛑 Build Blocked|🔄 Design Change Request)\s+—\s+Task\s+(\d+\.\d+):\s*(.*)$",
    re.MULTILINE,
)
FIELD_RE = re.compile(r"^\s*(\w+(?:\s+\w+)*):\s*(.*)")
_NA_TRAILING_RE = re.compile(r"\s*[-—:;,.()\[\]]+\s*$")

ALLOWED_LOOP_TYPES = frozenset({"BDD+TDD", "TDD-only"})
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
NA_REASON_FIELDS = frozenset(
    {
        "Scenario Coverage:",
        "BDD Verification:",
        "Advanced Test Verification:",
        "Runtime Verification:",
    }
)
BUILD_BLOCKED_REQUIRED_SECTIONS = (
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
DCR_REQUIRED_SECTIONS = (
    "Scenario Coverage",
    "Problem",
    "What We Tried",
    "Failure Evidence",
    "Failing Step",
    "Suggested Change",
    "Impact",
)
CONTRACT_SECTION_NAMES = frozenset(BUILD_BLOCKED_REQUIRED_SECTIONS + DCR_REQUIRED_SECTIONS)

_DEFAULT_KNOWN_TASK_FIELDS = frozenset(
    {
        "Context:",
        "Verification:",
        "Scenario Coverage:",
        "Loop Type:",
        "Behavioral Contract:",
        "Simplification Focus:",
        "Status:",
        "BDD Verification:",
        "Advanced Test Verification:",
        "Runtime Verification:",
        "Advanced Test Coverage:",
        "Priority:",
        "Scope:",
        "Requirement Coverage:",
    }
)

_KNOWN_TASK_FIELDS_FILE = Path(__file__).parent / "known_task_fields.txt"
_known_task_fields_cache: frozenset[str] | None = None


def _load_known_task_fields() -> frozenset[str]:
    """Load known task fields from file or return defaults.

    Supports external file at validation/known_task_fields.txt for easier
    maintenance without code changes.
    """
    global _known_task_fields_cache
    if _known_task_fields_cache is not None:
        return _known_task_fields_cache

    if _KNOWN_TASK_FIELDS_FILE.exists():
        fields: set[str] = set()
        for line in _KNOWN_TASK_FIELDS_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if not stripped.endswith(":"):
                    stripped += ":"
                fields.add(stripped)
        if fields:
            _known_task_fields_cache = frozenset(fields)
            return _known_task_fields_cache

    _known_task_fields_cache = _DEFAULT_KNOWN_TASK_FIELDS
    return _known_task_fields_cache


def _reset_known_task_fields_cache() -> None:
    """Reset the cached fields. For testing only."""
    global _known_task_fields_cache
    _known_task_fields_cache = None


KNOWN_TASK_FIELDS = _load_known_task_fields()


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


def required_sections_for_contract_block(kind: str) -> tuple[str, ...]:
    """Return required section names for a workflow contract block kind."""
    if kind == "🛑 Build Blocked":
        return BUILD_BLOCKED_REQUIRED_SECTIONS
    return DCR_REQUIRED_SECTIONS


def _is_continuation_line(line: str) -> bool:
    """Check if a line is a continuation of a multi-line field value."""
    stripped = line.strip()
    if not stripped:
        return False
    if TASK_CHECKBOX_RE.match(line):
        return False
    return not FIELD_RE.match(line)


def parse_task_blocks(content: str) -> list[TaskBlock]:
    """Parse markdown content and extract task blocks.

    Handles multi-line field values by continuing to accumulate content
    until the next known field, checkbox, or task heading is encountered.
    """
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
            if candidate_name in _load_known_task_fields():
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


def is_bare_na(value: str) -> bool:
    """Return True when a field says N/A without a meaningful reason."""
    stripped = value.strip()
    if not stripped.lower().startswith("n/a"):
        return False

    remainder = _NA_TRAILING_RE.sub("", stripped[3:])
    return not remainder.strip()


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
    """Validate required sections for markdown workflow contract blocks."""
    errors = []

    for block in parse_contract_blocks(content):
        missing_sections = [
            section
            for section in required_sections_for_contract_block(block.kind)
            if not block.sections.get(section, "").strip()
        ]
        if missing_sections:
            errors.append(
                f"Incomplete {block.kind} packet for Task {block.task_id}: "
                f"Missing required section(s): {', '.join(missing_sections)}"
            )

    return errors
