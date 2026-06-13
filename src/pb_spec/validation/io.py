"""File I/O utilities for validation module."""

from __future__ import annotations

from pathlib import Path

from pb_spec.exceptions import FileReadError
from pb_spec.validation.result import (
    ErrorSeverity,
    ValidationResult,
    make_validation_error,
)


def read_file_content(file_path: Path) -> str:
    """Read file content with error handling.

    Raises:
        FileReadError: If the file cannot be read.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise FileReadError(f"Cannot read file {file_path}: {e}") from e


def read_spec_file(file_path: Path) -> tuple[str, None] | tuple[None, ValidationResult]:
    """Read a spec file, returning (content, None) on success or (None, error_result) on failure."""
    try:
        return read_file_content(file_path), None
    except FileReadError as e:
        return None, ValidationResult(
            is_valid=False,
            errors=[
                make_validation_error(
                    message=str(e),
                    file_path=str(file_path),
                    severity=ErrorSeverity.CRITICAL,
                )
            ],
        )
