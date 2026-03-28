"""Unit tests for the code scanner module."""

from __future__ import annotations

from pathlib import Path

from pb_spec.validation.scanner import (
    CodeScanner,
    IssueType,
    ScanIssue,
    ScanResult,
)


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_has_issues_empty(self) -> None:
        """Test has_issues returns False when no issues."""
        result = ScanResult()
        assert result.has_issues is False

    def test_has_issues_with_issues(self) -> None:
        """Test has_issues returns True when issues exist."""
        result = ScanResult(
            issues=[
                ScanIssue(
                    issue_type=IssueType.TODO,
                    file_path="test.py",
                    line_number=1,
                    line_content="TODO: fix me",
                    message="TODO found",
                )
            ]
        )
        assert result.has_issues is True

    def test_issues_by_type(self) -> None:
        """Test filtering issues by type."""
        result = ScanResult(
            issues=[
                ScanIssue(
                    issue_type=IssueType.TODO,
                    file_path="test.py",
                    line_number=1,
                    line_content="TODO: fix",
                    message="TODO found",
                ),
                ScanIssue(
                    issue_type=IssueType.SKIPPED_TEST,
                    file_path="test.py",
                    line_number=5,
                    line_content="@pytest.mark.skip",
                    message="Skipped test",
                ),
                ScanIssue(
                    issue_type=IssueType.TODO,
                    file_path="other.py",
                    line_number=10,
                    line_content="FIXME: broken",
                    message="FIXME found",
                ),
            ]
        )
        todos = result.issues_by_type(IssueType.TODO)
        assert len(todos) == 2
        assert all(i.issue_type == IssueType.TODO for i in todos)

        skipped = result.issues_by_type(IssueType.SKIPPED_TEST)
        assert len(skipped) == 1


class TestCodeScanner:
    """Tests for CodeScanner class."""

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """Test scanning an empty directory."""
        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()
        assert result.has_issues is False

    def test_scan_detects_todo(self, tmp_path: Path) -> None:
        """Test detection of TODO comments."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    TODO: implement this\n    pass\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        todos = result.issues_by_type(IssueType.TODO)
        assert len(todos) == 1
        assert "TODO: implement this" in todos[0].line_content

    def test_scan_detects_fixme(self, tmp_path: Path) -> None:
        """Test detection of FIXME comments."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# FIXME: this is broken\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        todos = result.issues_by_type(IssueType.TODO)
        assert len(todos) == 1

    def test_scan_detects_not_implemented_error(self, tmp_path: Path) -> None:
        """Test detection of NotImplementedError."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    raise NotImplementedError\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        issues = result.issues_by_type(IssueType.NOT_IMPLEMENTED)
        assert len(issues) == 1

    def test_scan_detects_pytest_skip(self, tmp_path: Path) -> None:
        """Test detection of pytest.mark.skip."""
        test_file = tmp_path / "test.py"
        test_file.write_text("@pytest.mark.skip\ndef test_foo():\n    pass\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        skipped = result.issues_by_type(IssueType.SKIPPED_TEST)
        assert len(skipped) == 1

    def test_scan_detects_console_log(self, tmp_path: Path) -> None:
        """Test detection of console.log in JavaScript."""
        test_file = tmp_path / "test.js"
        test_file.write_text("function foo() {\n  console.log('debug');\n}\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        debug = result.issues_by_type(IssueType.DEBUG_ARTIFACT)
        assert len(debug) == 1

    def test_scan_detects_pdb_set_trace(self, tmp_path: Path) -> None:
        """Test detection of pdb.set_trace()."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import pdb\npdb.set_trace()\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        debug = result.issues_by_type(IssueType.DEBUG_ARTIFACT)
        assert len(debug) >= 1

    def test_scan_detects_breakpoint(self, tmp_path: Path) -> None:
        """Test detection of breakpoint()."""
        test_file = tmp_path / "test.py"
        test_file.write_text("breakpoint()\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        debug = result.issues_by_type(IssueType.DEBUG_ARTIFACT)
        assert len(debug) == 1

    def test_scan_detects_rust_ignore(self, tmp_path: Path) -> None:
        """Test detection of Rust #[ignore] attribute."""
        test_file = tmp_path / "test.rs"
        test_file.write_text("#[ignore]\nfn test_foo() {\n    // ...\n}\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        skipped = result.issues_by_type(IssueType.SKIPPED_TEST)
        assert len(skipped) == 1

    def test_scan_detects_go_skip(self, tmp_path: Path) -> None:
        """Test detection of Go t.Skip()."""
        test_file = tmp_path / "test.go"
        test_file.write_text("func TestFoo(t *testing.T) {\n    t.Skip()\n}\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        skipped = result.issues_by_type(IssueType.SKIPPED_TEST)
        assert len(skipped) == 1

    def test_scan_excludes_venv(self, tmp_path: Path) -> None:
        """Test that .venv directory is excluded."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        test_file = venv_dir / "test.py"
        test_file.write_text("TODO: this should not be found\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is False

    def test_scan_excludes_node_modules(self, tmp_path: Path) -> None:
        """Test that node_modules directory is excluded."""
        node_dir = tmp_path / "node_modules"
        node_dir.mkdir()
        test_file = node_dir / "test.js"
        test_file.write_text("console.log('should not be found')\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is False

    def test_scan_excludes_specs_directory(self, tmp_path: Path) -> None:
        """Test that specs/ directory is excluded."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        test_file = specs_dir / "test.py"
        test_file.write_text("TODO: should not be found\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is False

    def test_scan_excludes_scanner_py(self, tmp_path: Path) -> None:
        """Test that scanner.py is excluded (prevents self-detection)."""
        test_file = tmp_path / "scanner.py"
        test_file.write_text("TODO: this is a pattern definition\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is False

    def test_scan_excludes_validate_py(self, tmp_path: Path) -> None:
        """Test that validate.py is excluded (prevents self-detection)."""
        test_file = tmp_path / "validate.py"
        test_file.write_text("@pytest.mark.skip\ndef test(): pass\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is False

    def test_scan_multiple_issues_same_line(self, tmp_path: Path) -> None:
        """Test that multiple issues on same line are all reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text("TODO: fix this; raise NotImplementedError\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        # Both TODO and NotImplementedError (raised) should be reported
        assert len(result.issues) == 2
        issue_types = {i.issue_type for i in result.issues}
        assert IssueType.TODO in issue_types
        assert IssueType.NOT_IMPLEMENTED in issue_types

    def test_scan_typescript_skip(self, tmp_path: Path) -> None:
        """Test detection of TypeScript test.skip()."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("test.skip('skipped test', () => {\n  // ...\n});\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        skipped = result.issues_by_type(IssueType.SKIPPED_TEST)
        assert len(skipped) == 1

    def test_scan_javascript_xit(self, tmp_path: Path) -> None:
        """Test detection of JavaScript xit()."""
        test_file = tmp_path / "test.js"
        test_file.write_text("xit('skipped test', function() {\n  // ...\n});\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        skipped = result.issues_by_type(IssueType.SKIPPED_TEST)
        assert len(skipped) == 1

    def test_scan_with_check_options(self, tmp_path: Path) -> None:
        """Test scanner with selective checking enabled."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "TODO: fix\nraise NotImplementedError\nconsole.log('debug')\n@pytest.mark.skip\n"
        )

        # Only check for TODOs
        scanner = CodeScanner(
            root_dir=tmp_path,
            check_skipped_tests=False,
            check_not_implemented=False,
            check_todos=True,
            check_debug_artifacts=False,
        )
        result = scanner.scan()

        assert result.has_issues is True
        assert len(result.issues_by_type(IssueType.TODO)) == 1
        assert len(result.issues_by_type(IssueType.NOT_IMPLEMENTED)) == 0
        assert len(result.issues_by_type(IssueType.DEBUG_ARTIFACT)) == 0
        assert len(result.issues_by_type(IssueType.SKIPPED_TEST)) == 0

    def test_scan_line_numbers_correct(self, tmp_path: Path) -> None:
        """Test that line numbers are correctly reported."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# line 1\n# line 2\nTODO: on line 3\n# line 4\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        assert result.issues[0].line_number == 3

    def test_scan_nested_directories(self, tmp_path: Path) -> None:
        """Test scanning nested directory structures."""
        nested_dir = tmp_path / "src" / "nested"
        nested_dir.mkdir(parents=True)
        test_file = nested_dir / "test.py"
        test_file.write_text("TODO: in nested dir\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is True
        assert "nested" in result.issues[0].file_path

    def test_scan_binary_extension_ignored(self, tmp_path: Path) -> None:
        """Test that non-code files are ignored."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("TODO: in text file\n")

        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()

        assert result.has_issues is False

    def test_scan_unreadable_file_handled(self, tmp_path: Path) -> None:
        """Test that files with encoding issues are handled gracefully."""
        test_file = tmp_path / "test.py"
        # Write binary data that's not valid UTF-8
        test_file.write_bytes(b"\xff\xfe TODO: binary\n")

        scanner = CodeScanner(root_dir=tmp_path)
        # Should not raise an exception
        result = scanner.scan()
        assert result.has_issues is False
