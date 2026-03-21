"""Structured validation types for pb-spec workflow specs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ErrorLevel(Enum):
    """Validation error severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(slots=True, frozen=True)
class ValidationError:
    """A single validation error with context."""

    level: ErrorLevel
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None

    def __str__(self) -> str:
        """Format error as a human-readable string."""
        parts: list[str] = [f"[{self.level.value.upper()}]"]
        if self.file:
            parts.append(f"{self.file}")
            if self.line is not None:
                parts.append(f":{self.line}")
                if self.column is not None:
                    parts.append(f":{self.column}")
            parts.append(":")
        parts.append(self.message)
        return " ".join(parts)


@dataclass(slots=True)
class ValidationResult:
    """Collection of validation errors and warnings."""

    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(
        self,
        message: str,
        *,
        file: str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Add an error-level validation issue."""
        self.errors.append(
            ValidationError(
                level=ErrorLevel.ERROR,
                message=message,
                file=file,
                line=line,
                column=column,
            )
        )

    def add_warning(
        self,
        message: str,
        *,
        file: str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Add a warning-level validation issue."""
        self.warnings.append(
            ValidationError(
                level=ErrorLevel.WARNING,
                message=message,
                file=file,
                line=line,
                column=column,
            )
        )

    def add_info(
        self,
        message: str,
        *,
        file: str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Add an info-level validation issue."""
        self.warnings.append(
            ValidationError(
                level=ErrorLevel.INFO,
                message=message,
                file=file,
                line=line,
                column=column,
            )
        )

    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def get_all_issues(self) -> list[ValidationError]:
        """Get all issues sorted by severity (errors first)."""
        return self.errors + self.warnings

    def to_error_strings(self) -> list[str]:
        """Convert all errors to string list for backward compatibility."""
        return [str(e) for e in self.errors]

    def to_all_strings(self) -> list[str]:
        """Convert all issues to string list."""
        return [str(e) for e in self.get_all_issues()]

    def merge(self, other: ValidationResult) -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def summary(self) -> str:
        """Get a summary of validation results."""
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        if not parts:
            return "Validation passed"
        return f"Validation failed: {', '.join(parts)}"


@dataclass(slots=True, frozen=True)
class TaskField:
    """A parsed task field with metadata."""

    name: str
    value: str
    is_required: bool = True
    allows_na: bool = False
    na_requires_reason: bool = True


@dataclass(slots=True, frozen=True)
class TaskBlock:
    """Parsed task block with structured data."""

    task_id: str
    name: str
    fields: dict[str, str]
    checkbox_fields: dict[str, str]
    step_checkboxes: list[str]
    verification_checkboxes: list[str]

    def get_field(self, name: str) -> str | None:
        """Get a field value by name."""
        return self.fields.get(name)

    def get_checkbox_field(self, name: str) -> str | None:
        """Get a checkbox field value by name."""
        return self.checkbox_fields.get(name)

    def is_done(self) -> bool:
        """Check if task is marked as done."""
        status = self.get_field("Status")
        return status in ("🟢 DONE", "DONE")


@dataclass(slots=True, frozen=True)
class DesignSection:
    """A parsed design document section."""

    name: str
    content: str
    level: int
    line_number: int

    def is_empty_or_placeholder(self) -> bool:
        """Check if section content is empty or placeholder."""
        import re

        stripped = self.content.strip()
        if not stripped:
            return True
        placeholder_re = re.compile(r"^(?:TBD|\[To be written\]|\[[^\]]+\])$", re.IGNORECASE)
        return bool(placeholder_re.fullmatch(stripped))


@dataclass(slots=True, frozen=True)
class FeatureScenario:
    """A parsed Gherkin scenario."""

    name: str
    feature_file: Path
    line_number: int
    is_outline: bool = False

    def __str__(self) -> str:
        """Format scenario reference."""
        return f"{self.feature_file.name} / {self.name}"
