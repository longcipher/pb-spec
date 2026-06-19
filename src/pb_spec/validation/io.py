"""File I/O utilities for validation module."""

from __future__ import annotations

from pathlib import Path

from pb_spec.exceptions import FileReadError


def read_file_content(file_path: Path) -> str:
    """Read file content with error handling.

    Raises:
        FileReadError: If the file cannot be read.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise FileReadError(f"Cannot read file {file_path}: {e}") from e
