"""Exception hierarchy for pb-spec."""

from __future__ import annotations


class PbSpecError(Exception):
    """Base exception for all pb-spec errors."""


class SpecNotFoundError(PbSpecError):
    """Raised when spec directory is not found."""


class FileReadError(PbSpecError):
    """Raised when spec files cannot be read."""


class ConfigError(PbSpecError):
    """Raised when configuration parsing fails."""
