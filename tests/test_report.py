"""Unit tests for validation-result terminal reporting."""

from __future__ import annotations

import pytest

from pb_spec.commands.report import (
    _format_location,
    print_validation_error,
    report_format_result,
    report_scan_result,
    report_validation_result,
)
from pb_spec.validation.result import ErrorSeverity, ValidationError, ValidationResult
from pb_spec.validation.rumdl import FormatResult


@pytest.fixture
def echo_lines(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture everything routed to click.echo (style reduced to identity)."""
    out: list[str] = []
    monkeypatch.setattr("pb_spec.output.click.style", lambda msg, **kw: msg)
    monkeypatch.setattr(
        "pb_spec.output.click.echo",
        lambda msg, **kw: out.append(msg),
    )
    return out


def _err(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    file_path: str | None = None,
    line_number: int | None = None,
    field_name: str | None = None,
) -> ValidationError:
    """Build a ValidationError quickly."""
    return ValidationError(
        message=message,
        severity=severity,
        file_path=file_path,
        line_number=line_number,
        field_name=field_name,
    )


class TestFormatLocation:
    """Tests for the location formatter."""

    def test_empty_when_no_file(self) -> None:
        """No file path yields an empty string."""
        assert _format_location(_err("x")) == ""

    def test_file_only(self) -> None:
        """A bare file path yields just the path."""
        assert _format_location(_err("x", file_path="design.md")) == " (design.md)"

    def test_file_and_line(self) -> None:
        """File and line join with a colon."""
        assert _format_location(_err("x", file_path="design.md", line_number=3)) == " (design.md:3)"

    def test_file_line_field(self) -> None:
        """All three parts are rendered."""
        loc = _format_location(
            _err("x", file_path="design.md", line_number=3, field_name="Summary")
        )
        assert loc == " (design.md:3 field 'Summary')"

    def test_file_and_field_without_line(self) -> None:
        """Field without line number still renders (colon-joined)."""
        loc = _format_location(_err("x", file_path="design.md", field_name="Summary"))
        assert loc == " (design.md:field 'Summary')"


class TestPrintValidationError:
    """Tests for single-error printing."""

    @pytest.mark.parametrize(
        ("severity", "prefix"),
        [
            (ErrorSeverity.CRITICAL, "[CRITICAL]"),
            (ErrorSeverity.HIGH, "[HIGH]"),
            (ErrorSeverity.MEDIUM, "[MEDIUM]"),
            (ErrorSeverity.LOW, "[LOW]"),
        ],
    )
    def test_severity_prefix(
        self, echo_lines: list[str], severity: ErrorSeverity, prefix: str
    ) -> None:
        """Each severity maps to its bracket prefix."""
        print_validation_error(_err("msg", severity))
        assert echo_lines
        assert prefix in echo_lines[0]
        assert "msg" in echo_lines[0]

    def test_unknown_severity_has_no_prefix(self, echo_lines: list[str]) -> None:
        """An unrecognized severity value renders without a prefix."""
        from typing import cast

        error = ValidationError(
            message="plain",
            severity=cast(ErrorSeverity, "weird"),
        )
        print_validation_error(error)
        assert echo_lines
        # prefix is empty, so the message is "❌  plain" (double space after marker)
        assert echo_lines[0] == "❌  plain"
        assert "[MEDIUM]" not in echo_lines[0]

    def test_location_appended(self, echo_lines: list[str]) -> None:
        """The formatted location is appended to the message."""
        error = _err("bad", ErrorSeverity.HIGH, file_path="tasks.md", line_number=5)
        print_validation_error(error)
        assert "tasks.md:5" in echo_lines[0]


class TestReportValidationResult:
    """Tests for the batch reporter."""

    def test_prints_header_and_issues(self, echo_lines: list[str]) -> None:
        """Header, errors, and warnings are all printed."""
        result = ValidationResult(
            is_valid=False,
            errors=[_err("err1", ErrorSeverity.HIGH)],
            warnings=["warn1"],
        )
        report_validation_result(result, "Post-Plan")
        assert any("Post-Plan" in line for line in echo_lines)
        assert any("err1" in line for line in echo_lines)
        assert any("warn1" in line for line in echo_lines)

    def test_empty_result_prints_header_only(self, echo_lines: list[str]) -> None:
        """A clean result prints only the header."""
        report_validation_result(ValidationResult(is_valid=True), "Post-Build")
        assert any("Post-Build" in line for line in echo_lines)
        assert len(echo_lines) == 1


class TestReportFormatResult:
    """Tests for rumdl format reporting."""

    def test_no_messages_prints_nothing(self, echo_lines: list[str]) -> None:
        """An empty FormatResult produces no output."""
        report_format_result(FormatResult(success=True))
        assert echo_lines == []

    def test_success_messages_use_success_style(self, echo_lines: list[str]) -> None:
        """Successful messages print with the success marker."""
        report_format_result(FormatResult(success=True, messages=["Formatted 3 file(s)"]))
        assert any("✅" in line for line in echo_lines)
        assert any("Formatted 3 file(s)" in line for line in echo_lines)

    def test_failure_messages_use_warning_style(self, echo_lines: list[str]) -> None:
        """Failed messages print with the warning marker."""
        report_format_result(FormatResult(success=False, messages=["rumdl failed"]))
        assert any("⚠️" in line for line in echo_lines)
        assert any("rumdl failed" in line for line in echo_lines)


class TestReportScanResult:
    """Tests for the code-scan reporter."""

    def test_clean_result_returns_true(self, echo_lines: list[str]) -> None:
        """A valid result prints success and returns True."""
        result = ValidationResult(is_valid=True)
        assert report_scan_result(result) is True
        assert any(
            line.startswith("✅ ") and line[2:] == "Codebase scan passed - no issues found."
            for line in echo_lines
        )

    def test_invalid_without_errors_returns_true(self, echo_lines: list[str]) -> None:
        """An is_valid=False result with no errors still reports clean."""
        assert report_scan_result(ValidationResult(is_valid=False)) is True

    def test_errors_grouped_by_severity(self, echo_lines: list[str]) -> None:
        """Errors are grouped and counted by severity in ascending order."""
        result = ValidationResult(
            is_valid=False,
            errors=[
                _err("low issue", ErrorSeverity.LOW),
                _err("high issue", ErrorSeverity.HIGH),
                _err("high issue 2", ErrorSeverity.HIGH),
            ],
        )
        assert report_scan_result(result) is False
        joined = "\n".join(echo_lines)
        assert "Found 2 high issue(s)" in joined
        assert "Found 1 low issue(s)" in joined
        assert "low issue" in joined
        assert "high issue" in joined

    def test_more_than_ten_errors_truncated(self, echo_lines: list[str]) -> None:
        """More than 10 errors of one severity are truncated with a note."""
        errors = [_err(f"e{i}", ErrorSeverity.HIGH) for i in range(12)]
        result = ValidationResult(is_valid=False, errors=errors)
        assert report_scan_result(result) is False
        joined = "\n".join(echo_lines)
        assert "... and 2 more" in joined
        assert "e10" not in joined

    def test_exactly_ten_errors_not_truncated(self, echo_lines: list[str]) -> None:
        """Exactly 10 errors of one severity are all shown."""
        errors = [_err(f"e{i}", ErrorSeverity.MEDIUM) for i in range(10)]
        result = ValidationResult(is_valid=False, errors=errors)
        assert report_scan_result(result) is False
        joined = "\n".join(echo_lines)
        assert "and 0 more" not in joined
        assert "e9" in joined

    def test_eleven_errors_truncated(self, echo_lines: list[str]) -> None:
        """11 errors of one severity are truncated with a one-more note."""
        errors = [_err(f"e{i}", ErrorSeverity.LOW) for i in range(11)]
        result = ValidationResult(is_valid=False, errors=errors)
        assert report_scan_result(result) is False
        joined = "\n".join(echo_lines)
        assert "... and 1 more" in joined
