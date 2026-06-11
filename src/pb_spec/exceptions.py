"""Exception hierarchy for pb-spec."""

from __future__ import annotations


class ValidationError(Exception):
    """Base exception for all validation errors."""


class SpecNotFoundError(ValidationError):
    """Raised when spec directory is not found."""


class FileReadError(ValidationError):
    """Raised when spec files cannot be read."""


class ContractViolationError(ValidationError):
    """Raised when markdown contract is violated."""


class ConfigError(ValidationError):
    """Raised when configuration parsing fails."""
