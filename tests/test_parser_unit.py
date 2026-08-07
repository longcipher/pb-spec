"""Unit tests for parser edge cases and contract-block parsing."""

from __future__ import annotations

from pb_spec.validation.parser import (
    _is_continuation_line,
    parse_contract_blocks,
    parse_contract_sections,
    parse_task_blocks,
    task_display_name,
    validate_contract_blocks,
)


class TestIsContinuationLine:
    """Tests for the continuation-line predicate."""

    def test_blank_line_is_not_continuation(self) -> None:
        """Blank lines are not continuations."""
        assert _is_continuation_line("") is False
        assert _is_continuation_line("   ") is False

    def test_checkbox_is_not_continuation(self) -> None:
        """Checkbox lines are never treated as continuations."""
        assert _is_continuation_line("- [ ] Step 1") is False

    def test_known_field_is_not_continuation(self) -> None:
        """Field declarations are not continuations."""
        assert _is_continuation_line("Status: 🔴 TODO") is False

    def test_plain_line_is_continuation(self) -> None:
        """A plain indented line continues the current field."""
        assert _is_continuation_line("  some extra detail") is True


class TestParseTaskBlocks:
    """Tests for task-block extraction edge cases."""

    def test_parses_level_two_and_three_headings(self) -> None:
        """Both '## Task' and '### Task' headings are parsed."""
        content = (
            "## Task 1.1: Level two\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1\n\n"
            "### Task 1.2: Level three\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1\n"
        )
        blocks = parse_task_blocks(content)
        assert [b.id for b in blocks] == ["1.1", "1.2"]

    def test_unknown_field_is_ignored(self) -> None:
        """Unknown 'Key: value' lines neither start a field nor extend one."""
        content = (
            "### Task 1.1: T\nContext: start\nOther: detail line\nStatus: 🔴 TODO\n- [ ] Step 1\n"
        )
        blocks = parse_task_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].fields["Context:"] == "start"
        assert "Other:" not in blocks[0].fields

    def test_known_field_with_empty_value(self) -> None:
        """A known field with an empty value parses to an empty string."""
        content = "### Task 1.1: T\nContext: \nStatus: 🔴 TODO\n- [ ] Step 1\n"
        blocks = parse_task_blocks(content)
        assert blocks[0].fields["Context:"] == ""

    def test_continuation_lines_join_with_newline(self) -> None:
        """Multi-line field values are newline-joined keeping indentation."""
        content = (
            "### Task 1.1: T\n"
            "Context: first line\n"
            "  second line\n"
            "  third line\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1\n"
        )
        blocks = parse_task_blocks(content)
        assert blocks[0].fields["Context:"] == "first line\n  second line\n  third line"

    def test_content_before_first_task_ignored(self) -> None:
        """Prose before the first task heading is ignored."""
        content = (
            "# Tasks\n\n"
            "Some intro text without fields.\n\n"
            "### Task 1.1: T\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1\n"
        )
        blocks = parse_task_blocks(content)
        assert [b.id for b in blocks] == ["1.1"]

    def test_task_without_checkbox_still_parsed(self) -> None:
        """A task with no checkbox parses (validation rejects it later)."""
        content = "### Task 1.1: T\nStatus: 🟢 DONE\njust some text\n"
        blocks = parse_task_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].name == "T"

    def test_multiple_tasks_isolate_fields(self) -> None:
        """Fields do not leak between adjacent tasks."""
        content = (
            "### Task 1.1: A\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1\n\n"
            "### Task 1.2: B\n"
            "Status: 🟢 DONE\n"
            "- [x] Step 1\n"
        )
        blocks = parse_task_blocks(content)
        assert blocks[0].fields["Status:"] == "🔴 TODO"
        assert blocks[1].fields["Status:"] == "🟢 DONE"


class TestTaskDisplayName:
    """Tests for the diagnostic display name."""

    def test_with_name(self) -> None:
        """Named tasks show 'id: name'."""
        block = parse_task_blocks("### Task 2.1: Login\nStatus: 🔴 TODO\n- [ ] x\n")[0]
        assert task_display_name(block) == "2.1: Login"

    def test_without_name(self) -> None:
        """Unnamed tasks fall back to the id."""
        block = parse_task_blocks("### Task 2.2:\nStatus: 🔴 TODO\n- [ ] x\n")[0]
        assert task_display_name(block) == "2.2"


class TestParseContractSections:
    """Tests for DCR / build-blocked section parsing."""

    def test_parses_multiple_sections(self) -> None:
        """Reason / Requested Change / Impact are extracted."""
        body = "Reason: unclear\nRequested Change: add schema\nImpact: blocks task 1.1\n"
        sections = parse_contract_sections(body)
        assert sections["Reason"] == "unclear"
        assert sections["Requested Change"] == "add schema"
        assert sections["Impact"] == "blocks task 1.1"

    def test_multiline_sections_join(self) -> None:
        """Indented continuation lines join the current section."""
        body = "Reason: first\n  second line\nImpact: x\n"
        sections = parse_contract_sections(body)
        assert sections["Reason"] == "first\nsecond line"

    def test_unknown_lines_before_first_section_ignored(self) -> None:
        """Prose before any known section is dropped."""
        body = "Just prose\nReason: real reason\n"
        sections = parse_contract_sections(body)
        assert sections == {"Reason": "real reason"}

    def test_empty_section_value(self) -> None:
        """A section header with no value yields an empty entry."""
        sections = parse_contract_sections("Reason:\nImpact: x\n")
        assert sections["Reason"] == ""


class TestParseContractBlocks:
    """Tests for contract block extraction."""

    def test_single_block(self) -> None:
        """A single DCR packet is parsed with its sections."""
        content = (
            "### Task 1.1: T\n"
            "Status: 🔄 DCR\n"
            "- [ ] Step 1\n\n"
            "🔄 Design Change Request — Task 1.1: T\n"
            "Reason: ambiguous\n"
            "Impact: blocked\n"
        )
        blocks = parse_contract_blocks(content)
        assert len(blocks) == 1
        assert blocks[0].kind == "🔄 Design Change Request"
        assert blocks[0].task_id == "1.1"
        assert blocks[0].sections["Reason"] == "ambiguous"

    def test_multiple_blocks_boundaries(self) -> None:
        """Adjacent packets do not bleed into each other."""
        content = (
            "🛑 Build Blocked — Task 1.1: A\n"
            "Reason: r1\n"
            "Impact: i1\n\n"
            "🛑 Build Blocked — Task 1.2: B\n"
            "Reason: r2\n"
            "Impact: i2\n"
        )
        blocks = parse_contract_blocks(content)
        assert len(blocks) == 2
        assert blocks[0].sections["Reason"] == "r1"
        assert blocks[1].sections["Reason"] == "r2"

    def test_block_stops_before_next_task(self) -> None:
        """A packet body is truncated at the next task heading."""
        content = (
            "🛑 Build Blocked — Task 1.1: A\n"
            "Reason: r1\n"
            "Impact: i1\n\n"
            "### Task 2.1: Next\n"
            "Status: 🔴 TODO\n"
            "- [ ] Step 1\n"
        )
        blocks = parse_contract_blocks(content)
        assert len(blocks) == 1
        assert "Task 2.1" not in blocks[0].sections["Impact"]


class TestValidateContractBlocks:
    """Tests for contract-block validation."""

    def test_complete_block_no_errors(self) -> None:
        """A complete packet validates clean."""
        content = "🛑 Build Blocked — Task 1.1: A\nReason: r\nRequested Change: c\nImpact: i\n"
        assert validate_contract_blocks(content) == []

    def test_missing_section_reports_message(self) -> None:
        """Missing sections produce a precise error."""
        content = "🛑 Build Blocked — Task 1.1: A\nReason: r\nImpact: i\n"
        errors = validate_contract_blocks(content)
        assert len(errors) == 1
        assert "Incomplete 🛑 Build Blocked packet for Task 1.1" in errors[0]
        assert "Requested Change" in errors[0]
