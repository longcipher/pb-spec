"""Structured validation result types for pb-spec."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ValidationMode(Enum):
    """Validation execution mode."""

    PLAN = "plan"
    BUILD = "build"
    TASK = "task"


class ErrorSeverity(Enum):
    """Severity levels for validation errors."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ValidationError:
    """A single structured validation error.

    Attributes:
        severity: Error severity level for prioritization.
        message: Human-readable error description.
        file_path: Optional source file path where the error was found.
        line_number: Optional line number in the source file.
        field_name: Optional field name within the parsed structure.
    """

    severity: ErrorSeverity
    message: str
    file_path: str | None = None
    line_number: int | None = None
    field_name: str | None = None


def make_validation_error(
    message: str,
    file_path: str | None = None,
    line_number: int | None = None,
    field_name: str | None = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
) -> ValidationError:
    """Create a ValidationError with consistent defaults."""
    return ValidationError(
        severity=severity,
        message=message,
        file_path=file_path,
        line_number=line_number,
        field_name=field_name,
    )


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Used by validate_plan, validate_build, and validate_task to collect
    errors and warnings during spec validation.
    """

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def errors_by_severity(self, severity: ErrorSeverity) -> list[ValidationError]:
        """Return errors filtered by severity level."""
        return [e for e in self.errors if e.severity == severity]

    def has_critical(self) -> bool:
        """Return True if any CRITICAL errors exist."""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)
