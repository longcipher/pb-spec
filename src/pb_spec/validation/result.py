"""Structured validation result types for pb-spec."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ErrorSeverity(Enum):
    """Severity levels for validation errors."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ValidationError:
    """A single structured validation error."""

    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    file_path: str | None = None
    line_number: int | None = None
    field_name: str | None = None


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
