"""Unit tests for file I/O utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from pb_spec.exceptions import FileReadError
from pb_spec.validation.io import read_file_content


class TestReadFileContent:
    """Tests for read_file_content."""

    def test_reads_utf8_file(self, tmp_path: Path) -> None:
        """A readable UTF-8 file returns its content."""
        target = tmp_path / "notes.md"
        target.write_text("# hello\n", encoding="utf-8")
        assert read_file_content(target) == "# hello\n"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """A missing file raises FileReadError."""
        with pytest.raises(FileReadError):
            read_file_content(tmp_path / "nope.md")

    def test_unreadable_content_raises(self, tmp_path: Path) -> None:
        """Non-UTF-8 content raises FileReadError."""
        target = tmp_path / "binary.md"
        target.write_bytes(b"\xff\xfe\x00\x01")
        with pytest.raises(FileReadError):
            read_file_content(target)
