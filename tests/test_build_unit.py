"""Unit tests for build-validation internals (strong assertions)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pb_spec.validation.build import (
    _run_codebase_scan,
    _scan_result_to_errors,
    _validate_codebase_scan,
    _validate_task_completion,
    _validate_task_completion_warnings,
)
from pb_spec.validation.parser import parse_task_blocks
from pb_spec.validation.result import ErrorSeverity
from pb_spec.validation.scanner import IssueType, ScanIssue, ScanResult


def _blocks(tasks_md: str):
    """Parse task blocks from a tasks.md body."""
    return parse_task_blocks(tasks_md)


class TestScanResultToErrors:
    """Tests for converting ScanIssues into ValidationErrors."""

    def test_empty_scan_yields_no_errors(self) -> None:
        """No issues means no errors."""
        assert _scan_result_to_errors(ScanResult()) == []

    @pytest.mark.parametrize(
        ("issue_type", "expected_severity"),
        [
            (IssueType.SKIPPED_TEST, ErrorSeverity.HIGH),
            (IssueType.NOT_IMPLEMENTED, ErrorSeverity.HIGH),
            (IssueType.TODO, ErrorSeverity.LOW),
            (IssueType.DEBUG_ARTIFACT, ErrorSeverity.MEDIUM),
        ],
    )
    def test_severity_mapping(
        self, issue_type: IssueType, expected_severity: ErrorSeverity
    ) -> None:
        """Each issue type maps to its severity."""
        issue = ScanIssue(
            issue_type=issue_type,
            file_path="src/a.py",
            line_number=3,
            line_content="bad line",
            message="problem found",
        )
        errors = _scan_result_to_errors(ScanResult(issues=[issue]))
        assert len(errors) == 1
        error = errors[0]
        assert error.severity == expected_severity
        assert error.message == "problem found"
        assert error.file_path == "src/a.py"
        assert error.line_number == 3

    def test_all_issues_preserved(self) -> None:
        """Every issue is converted, keeping order."""
        issues = [
            ScanIssue(IssueType.TODO, "a.py", 1, "l", "m1"),
            ScanIssue(IssueType.TODO, "b.py", 2, "l", "m2"),
        ]
        errors = _scan_result_to_errors(ScanResult(issues=issues))
        assert [e.message for e in errors] == ["m1", "m2"]
        assert all(e.file_path in ("a.py", "b.py") for e in errors)

    def test_unknown_issue_type_falls_back_to_medium(self) -> None:
        """An unrecognized issue type maps to MEDIUM severity."""
        from typing import cast

        issue = ScanIssue(
            issue_type=cast(IssueType, "mystery"),
            file_path="a.py",
            line_number=1,
            line_content="x",
            message="m",
        )
        errors = _scan_result_to_errors(ScanResult(issues=[issue]))
        assert len(errors) == 1
        assert errors[0].severity == ErrorSeverity.MEDIUM


class TestRunCodebaseScan:
    """Tests for the scan runner."""

    def test_full_scan_without_git(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Full scan passes target_files=None to the scanner."""
        captured: dict[str, object] = {}

        class FakeScanner:
            def __init__(self, root_dir: object, target_files: object | None = None) -> None:
                captured["target_files"] = target_files
                captured["root_dir"] = root_dir

            def scan(self) -> ScanResult:
                return ScanResult()

        monkeypatch.setattr("pb_spec.validation.build.CodeScanner", FakeScanner)
        result = _run_codebase_scan(git_only=False)
        assert captured["target_files"] is None
        assert isinstance(result, ScanResult)

    def test_git_only_scan_uses_modified_files(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """git_only mode restricts the scan to modified files."""
        captured: dict[str, object] = {}
        fake_files = {Path("/tmp/x.py")}
        monkeypatch.setattr(
            "pb_spec.validation.build.get_git_modified_files",
            lambda _root=".": fake_files,
        )

        class FakeScanner:
            def __init__(self, root_dir: object, target_files: object | None = None) -> None:
                captured["target_files"] = target_files

            def scan(self) -> ScanResult:
                return ScanResult()

        monkeypatch.setattr("pb_spec.validation.build.CodeScanner", FakeScanner)
        _run_codebase_scan(git_only=True)
        assert captured["target_files"] == fake_files


class TestValidateCodebaseScan:
    """Tests for scan-based validation."""

    def test_clean_scan_returns_no_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A clean scan produces an empty error list."""
        monkeypatch.setattr(
            "pb_spec.validation.build._run_codebase_scan",
            lambda **kw: ScanResult(),
        )
        assert _validate_codebase_scan() == []

    def test_issues_append_header_and_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Issues produce a header error plus per-issue errors."""
        issue = ScanIssue(IssueType.TODO, "src/a.py", 1, "TODO: fix", "TODO found")
        monkeypatch.setattr(
            "pb_spec.validation.build._run_codebase_scan",
            lambda **kw: ScanResult(issues=[issue]),
        )
        errors = _validate_codebase_scan()
        assert len(errors) == 2
        assert errors[0].message == "Codebase scan failed - found issues that need to be addressed."
        assert errors[0].severity == ErrorSeverity.HIGH
        assert errors[1].message == "TODO found"


class TestValidateTaskCompletion:
    """Tests for per-task completion validation (strong assertions)."""

    def test_done_task_with_checked_steps_passes(self) -> None:
        """A DONE task with all steps checked produces no errors."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Done\n"
            "Status: 🟢 DONE\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [x] Step 1\n"
        )
        assert _validate_task_completion(blocks, "") == []

    def test_dcr_status_error_message(self) -> None:
        """A DCR task yields a precise blocked-by-DCR error."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Wait\n"
            "Status: 🔄 DCR\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [ ] Step 1\n"
        )
        errors = _validate_task_completion(blocks, "")
        assert len(errors) == 1
        assert errors[0].message == "Task Blocked by DCR: 1.1: Wait. Needs design refinement."
        assert errors[0].field_name == "Status:"
        assert errors[0].file_path == "tasks.md"
        assert errors[0].severity == ErrorSeverity.HIGH

    def test_missing_status_field_is_invalid(self) -> None:
        """A task with no Status field yields an Invalid Status error."""
        blocks = _blocks("# Tasks\n\n### Task 1.1: Bare\nContext: c.\n- [ ] Step 1\n")
        errors = _validate_task_completion(blocks, "")
        assert len(errors) == 1
        assert "Invalid Status" in errors[0].message
        assert errors[0].field_name == "Status:"

    def test_skipped_then_todo_both_checked(self) -> None:
        """A SKIPPED task must not short-circuit checks on later tasks."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Skip\n"
            "Status: ⏭️ SKIPPED\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [ ] Step 1\n\n"
            "### Task 1.2: Pending\n"
            "Status: 🔴 TODO\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [ ] Step 1\n"
        )
        errors = _validate_task_completion(blocks, "")
        assert len(errors) == 1
        assert "1.2: Pending" in errors[0].message

    @pytest.mark.parametrize(
        ("status", "fragment"),
        [
            ("🔴 TODO", "not marked as DONE"),
            ("🟡 IN PROGRESS", "not marked as DONE"),
            ("TODO", "not marked as DONE"),
            ("DONE", "Invalid Status"),
            ("🚀 STARTED", "Invalid Status"),
        ],
    )
    def test_unfinished_statuses(self, status: str, fragment: str) -> None:
        """Non-DONE statuses produce precise unfinished/invalid errors."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Busy\n"
            f"Status: {status}\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [ ] Step 1\n"
        )
        errors = _validate_task_completion(blocks, "")
        assert len(errors) == 1
        assert fragment in errors[0].message
        assert errors[0].field_name == "Status:"

    def test_skipped_task_skips_checkbox_check(self) -> None:
        """A SKIPPED task is ignored by completion validation."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Skip\n"
            "Status: ⏭️ SKIPPED\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [ ] Step 1\n"
        )
        assert _validate_task_completion(blocks, "") == []

    def test_obsolete_task_skips_checkbox_check(self) -> None:
        """An OBSOLETE task is ignored by completion validation."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Obsolete\n"
            "Status: ⛔ OBSOLETE\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [ ] Step 1\n"
        )
        assert _validate_task_completion(blocks, "") == []

    def test_done_with_unchecked_steps_error(self) -> None:
        """A DONE task with an unchecked step names the step."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Partial\n"
            "Status: 🟢 DONE\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [x] Step 1\n"
            "- [ ] Step 2\n"
        )
        errors = _validate_task_completion(blocks, "")
        assert len(errors) == 1
        assert "marked DONE but has incomplete steps" in errors[0].message
        assert "Step 2" in errors[0].message

    def test_done_without_any_checkbox_error(self) -> None:
        """A DONE task with no checkboxes at all is rejected."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Bare\n"
            "Status: 🟢 DONE\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- plain line\n"
        )
        errors = _validate_task_completion(blocks, "")
        assert len(errors) == 1
        assert "contains no step checkboxes" in errors[0].message


class TestValidateBuild:
    """Tests for the build-level validator."""

    def test_missing_tasks_file_critical(self, tmp_path: Path) -> None:
        """A missing tasks.md is a CRITICAL error with full details."""
        from pb_spec.validation.build import validate_build

        result = validate_build(tmp_path)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "Missing required file: tasks.md"
        assert result.errors[0].file_path == str(tmp_path / "tasks.md")
        assert result.errors[0].severity.value == "critical"

    def test_unreadable_tasks_file_critical(self, tmp_path: Path) -> None:
        """An unreadable tasks.md surfaces the read error."""
        from pb_spec.validation.build import validate_build

        (tmp_path / "tasks.md").write_bytes(b"\xff\xfe\x00")
        result = validate_build(tmp_path)
        assert result.is_valid is False
        assert result.errors[0].severity.value == "critical"
        assert result.errors[0].message


class TestValidateTaskCompletionWarnings:
    """Tests for the skipped-task warning collector."""

    def test_skipped_tasks_warn(self) -> None:
        """Skipped tasks produce warnings, not errors."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Skip\n"
            "Status: ⏭️ SKIPPED\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [ ] Step 1\n"
        )
        warnings = _validate_task_completion_warnings(blocks)
        assert len(warnings) == 1
        assert "Task Skipped: 1.1: Skip" in warnings[0]

    def test_done_tasks_do_not_warn(self) -> None:
        """DONE tasks produce no warnings."""
        blocks = _blocks(
            "# Tasks\n\n"
            "### Task 1.1: Done\n"
            "Status: 🟢 DONE\n"
            "Context: c.\n"
            "Verification: v.\n"
            "Test Coverage: t.\n"
            "- [x] Step 1\n"
        )
        assert _validate_task_completion_warnings(blocks) == []
