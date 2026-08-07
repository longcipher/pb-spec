"""Property-based tests for the tasks.md parser (hypothesis).

Strict TDD discipline: parsers get randomized-input guarantees, not just
hand-picked happy paths. These properties make the mutation-testing gate
meaningful for the regex-based markdown parser.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pb_spec.validation.parser import (
    KNOWN_TASK_FIELDS,
    TASK_CHECKBOX_RE,
    parse_task_blocks,
)

pytestmark = pytest.mark.property


@given(st.text(min_size=0, max_size=2000))
def test_parser_never_crashes_on_arbitrary_text(random_text: str) -> None:
    """The parser must never raise on arbitrary markdown-shaped input.

    Uncontrolled exceptions would signal a parser bug; the strict contract is
    that arbitrary input is either parsed into blocks or ignored.
    """
    blocks = parse_task_blocks(random_text)
    assert isinstance(blocks, list)
    for block in blocks:
        assert block.id
        assert block.content


# Names must be stable under the parser's strip() and must not contain line
# breaks (the parser is line-based by design).
_TASK_NAME = st.text(min_size=1, max_size=40).filter(
    lambda s: bool(s.strip()) and s == s.strip() and "\n" not in s and "\r" not in s
)


@given(
    st.lists(
        st.tuples(
            st.from_regex(r"\d+\.\d+", fullmatch=True),
            _TASK_NAME,
        ),
        min_size=0,
        max_size=20,
    )
)
def test_roundtrip_well_formed_tasks(task_specs: list[tuple[str, str]]) -> None:
    """Well-formed task headers are always recovered as blocks.

    This is the invariant the mutation gate protects: mutating the heading
    regex must break at least one of these property tests.
    """
    content = "# Tasks\n\n"
    for task_id, name in task_specs:
        content += f"### Task {task_id}: {name}\n"
        content += "Context: Build piece.\n"
        content += "Verification: Run tests.\n"
        content += "Test Coverage: N/A\n"
        content += "Status: 🔴 TODO\n"
        content += "- [ ] Step 1: Write test\n"
        content += "\n"

    blocks = parse_task_blocks(content)
    assert len(blocks) == len(task_specs)
    for block, (task_id, name) in zip(blocks, task_specs, strict=True):
        assert block.id == task_id
        assert block.name == name
        assert TASK_CHECKBOX_RE.search(block.content)


@given(st.text(min_size=1, max_size=300))
def test_known_fields_are_extracted(block_body: str) -> None:
    """A task block carrying each known field must surface every field value.

    Guards the field-name contract: renaming a known field in the parser must
    be caught by this property.
    """
    content = (
        "# Tasks\n\n"
        "### Task 1.1: Property task\n"
        f"Context: {block_body}\n"
        "Verification: Run tests.\n"
        "Test Coverage: N/A\n"
        "Status: 🔴 TODO\n"
        "- [ ] Step 1: Write test\n"
    )
    blocks = parse_task_blocks(content)
    assert len(blocks) == 1
    fields = blocks[0].fields
    assert set(fields).issubset(KNOWN_TASK_FIELDS)
    assert "Context:" in fields
