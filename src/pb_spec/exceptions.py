"""Exception hierarchy for pb-spec."""

from __future__ import annotations


class SpecNotFoundError(Exception):
    """Raised when spec directory is not found."""


class FileReadError(Exception):
    """Raised when spec files cannot be read."""
