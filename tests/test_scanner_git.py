"""Unit tests for scanner internals: git-backed discovery and targeting."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from pb_spec.validation.scanner import CodeScanner, IssueType, ScanResult


def _fake_run(stdout: str = "") -> SimpleNamespace:
    """A minimal subprocess.CompletedProcess stand-in."""
    return SimpleNamespace(stdout=stdout, stderr="")


class TestGetGitFiles:
    """Tests for git-backed file discovery."""

    def test_git_ls_files_filtered(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Git output is filtered by extension and exclusion rules."""
        (tmp_path / "specs").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "keep.py").write_text("x = 1\n")
        (tmp_path / "skip.txt").write_text("x\n")
        stdout = "keep.py\nskip.txt\nspecs/design.md\n"
        monkeypatch.setattr(
            "pb_spec.validation.scanner.subprocess.run",
            lambda *a, **kw: _fake_run(stdout),
        )
        scanner = CodeScanner(root_dir=tmp_path)
        files = scanner._get_git_files()
        assert files is not None
        assert files == [tmp_path / "keep.py"]

    def test_git_invocation_contract(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The git ls-files invocation matches the contract."""
        captured: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.validation.scanner.subprocess.run",
            lambda *a, **kw: captured.update(cmd=a[0], **kw) or _fake_run(""),
        )
        scanner = CodeScanner(root_dir=tmp_path)
        scanner._get_git_files()
        assert captured["cmd"] == ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
        assert captured["capture_output"] is True
        assert captured["text"] is True
        assert captured["check"] is True
        assert captured["cwd"] == tmp_path
        assert captured["timeout"] == 60

    def test_git_error_returns_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A git failure falls back to None so os.walk is used."""

        def raise_error(*a: object, **kw: object) -> None:
            raise subprocess.CalledProcessError(128, ["git"])

        monkeypatch.setattr("pb_spec.validation.scanner.subprocess.run", raise_error)
        scanner = CodeScanner(root_dir=tmp_path)
        assert scanner._get_git_files() is None

    def test_missing_git_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing git binary also returns None."""

        def raise_missing(*a: object, **kw: object) -> None:
            raise FileNotFoundError("git")

        monkeypatch.setattr("pb_spec.validation.scanner.subprocess.run", raise_missing)
        scanner = CodeScanner(root_dir=tmp_path)
        assert scanner._get_git_files() is None

    def test_blank_lines_skipped(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Blank lines in git output are skipped."""
        (tmp_path / "a.py").write_text("x\n")
        stdout = "\n\na.py\n"
        monkeypatch.setattr(
            "pb_spec.validation.scanner.subprocess.run",
            lambda *a, **kw: _fake_run(stdout),
        )
        scanner = CodeScanner(root_dir=tmp_path)
        assert scanner._get_git_files() == [tmp_path / "a.py"]


class TestGetFilesToScan:
    """Tests for scan-target resolution."""

    def test_target_files_restrict_scan(self, tmp_path: Path) -> None:
        """Explicit target files limit scanning to those files."""
        keep = tmp_path / "keep.py"
        keep.write_text("TODO: x\n")
        (tmp_path / "other.py").write_text("TODO: y\n")
        scanner = CodeScanner(root_dir=tmp_path, target_files={keep})
        result = scanner.scan()
        assert len(result.issues) == 1
        assert result.issues[0].file_path == "keep.py"

    def test_git_files_override_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Git-discovered files take precedence over the os.walk fallback."""
        keep = tmp_path / "keep.py"
        keep.write_text("TODO: x\n")
        (tmp_path / "other.py").write_text("TODO: y\n")
        scanner = CodeScanner(root_dir=tmp_path)
        monkeypatch.setattr(scanner, "_get_git_files", lambda: [keep])
        result = scanner.scan()
        assert len(result.issues) == 1
        assert result.issues[0].file_path == "keep.py"

    def test_external_target_file_keeps_absolute_path(self, tmp_path: Path) -> None:
        """A target file outside the root keeps its absolute path."""
        outside_dir = tmp_path.parent / f"{tmp_path.name}-outside"
        outside_dir.mkdir(exist_ok=True)
        external = outside_dir / "external.py"
        external.write_text("TODO: outside\n")
        scanner = CodeScanner(root_dir=tmp_path, target_files={external})
        result = scanner.scan()
        assert len(result.issues) == 1
        assert result.issues[0].file_path == str(external)

    def test_target_files_filter_by_extension(self, tmp_path: Path) -> None:
        """Target files with non-scan extensions are dropped."""
        keep = tmp_path / "keep.py"
        keep.write_text("TODO: x\n")
        txt = tmp_path / "notes.txt"
        txt.write_text("TODO: y\n")
        scanner = CodeScanner(root_dir=tmp_path, target_files={keep, txt})
        result = scanner.scan()
        assert len(result.issues) == 1

    def test_missing_target_file_ignored(self, tmp_path: Path) -> None:
        """Non-existent target files are ignored."""
        keep = tmp_path / "keep.py"
        keep.write_text("TODO: x\n")
        ghost = tmp_path / "ghost.py"
        scanner = CodeScanner(root_dir=tmp_path, target_files={keep, ghost})
        result = scanner.scan()
        assert len(result.issues) == 1


class TestGetFilesFallback:
    """Tests for the os.walk fallback."""

    def test_excludes_hidden_dirs(self, tmp_path: Path) -> None:
        """Dot-directories are excluded during fallback traversal."""
        (tmp_path / "app.py").write_text("TODO: x\n")
        hidden = tmp_path / ".cache"
        hidden.mkdir()
        (hidden / "bad.py").write_text("TODO: y\n")
        scanner = CodeScanner(root_dir=tmp_path)
        result = scanner.scan()
        assert all("bad.py" not in i.file_path for i in result.issues)

    def test_custom_exclude_dirs(self, tmp_path: Path) -> None:
        """Custom exclude dirs are honored."""
        (tmp_path / "app.py").write_text("TODO: x\n")
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / "bad.py").write_text("TODO: y\n")
        scanner = CodeScanner(root_dir=tmp_path, exclude_dirs=frozenset({"vendor"}))
        result = scanner.scan()
        assert all("bad.py" not in i.file_path for i in result.issues)


class TestCheckLine:
    """Tests for single-line inspection."""

    def test_todo_case_insensitive(self) -> None:
        """'todo:' matches regardless of case."""
        scanner = CodeScanner(root_dir=".")
        result = ScanResult()
        scanner._check_line("a.py", 1, "todo: lowercase", result)
        assert len(result.issues) == 1
        assert result.issues[0].issue_type == IssueType.TODO

    def test_first_matching_pattern_wins(self) -> None:
        """Only the first matching pattern in a category reports."""
        scanner = CodeScanner(root_dir=".")
        result = ScanResult()
        scanner._check_line("a.py", 1, "pdb.set_trace()  # TODO: also", result)
        types = {i.issue_type for i in result.issues}
        assert IssueType.DEBUG_ARTIFACT in types
        assert IssueType.TODO in types

    def test_message_format(self) -> None:
        """Issue messages are title-cased with the line content."""
        scanner = CodeScanner(root_dir=".")
        result = ScanResult()
        scanner._check_line("a.py", 7, "  TODO: fix me", result)
        assert result.issues[0].message == "Todo found: TODO: fix me"
        assert result.issues[0].line_content == "TODO: fix me"
        assert result.issues[0].line_number == 7


class TestShouldScanFile:
    """Tests for the scan-exclusion predicate."""

    def test_specs_dir_excluded(self, tmp_path: Path) -> None:
        """Files under specs/ are excluded."""
        scanner = CodeScanner(root_dir=tmp_path)
        assert scanner._should_scan_file(tmp_path / "specs" / "design.md") is False

    def test_regular_file_included(self, tmp_path: Path) -> None:
        """A normal source file is scanned."""
        scanner = CodeScanner(root_dir=tmp_path)
        assert scanner._should_scan_file(tmp_path / "src" / "app.py") is True

    def test_validation_package_excluded(self, tmp_path: Path) -> None:
        """Files inside the validation package are excluded."""
        from pb_spec.validation.scanner import VALIDATION_PACKAGE_DIR

        scanner = CodeScanner(root_dir=VALIDATION_PACKAGE_DIR.parent.parent.parent)
        assert scanner._should_scan_file(VALIDATION_PACKAGE_DIR / "scanner.py") is False

    def test_default_root_dir_used(self) -> None:
        """The default root ('.') excludes the repo specs directory."""
        scanner = CodeScanner()
        assert scanner._should_scan_file(Path("specs") / "design.md") is False
