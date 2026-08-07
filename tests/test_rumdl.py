"""Unit tests for the rumdl markdown formatting integration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from pb_spec.validation.rumdl import (
    MAX_RUMDL_TIMEOUT,
    FormatResult,
    is_rumdl_available,
    run_rumdl_format,
)


def _fake_run(stdout: str = "", stderr: str = "") -> SimpleNamespace:
    """A minimal subprocess.CompletedProcess stand-in."""
    return SimpleNamespace(stdout=stdout, stderr=stderr)


class TestIsRumdlAvailable:
    """Tests for the availability probe."""

    def test_returns_true_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A successful version probe returns True."""
        monkeypatch.setattr("pb_spec.validation.rumdl.subprocess.run", lambda *a, **kw: _fake_run())
        assert is_rumdl_available() is True

    def test_version_probe_contract(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The version probe runs with the exact command and kwargs."""
        captured: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.validation.rumdl.subprocess.run",
            lambda *a, **kw: captured.update(cmd=a[0], **kw) or _fake_run(),
        )
        assert is_rumdl_available() is True
        assert captured["cmd"] == ["rumdl", "--version"]
        assert captured["capture_output"] is True
        assert captured["check"] is True
        assert captured["timeout"] == 10

    def test_false_when_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A FileNotFoundError returns False."""

        def raise_not_found(*a: object, **kw: object) -> None:
            raise FileNotFoundError("rumdl")

        monkeypatch.setattr("pb_spec.validation.rumdl.subprocess.run", raise_not_found)
        assert is_rumdl_available() is False

    def test_false_on_nonzero_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A CalledProcessError returns False."""

        def raise_cpe(*a: object, **kw: object) -> None:
            raise subprocess.CalledProcessError(1, ["rumdl"])

        monkeypatch.setattr("pb_spec.validation.rumdl.subprocess.run", raise_cpe)
        assert is_rumdl_available() is False

    def test_false_on_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A TimeoutExpired returns False."""

        def raise_timeout(*a: object, **kw: object) -> None:
            raise subprocess.TimeoutExpired("rumdl", 10)

        monkeypatch.setattr("pb_spec.validation.rumdl.subprocess.run", raise_timeout)
        assert is_rumdl_available() is False


class TestRunRumdlFormat:
    """Tests for the formatting entry point."""

    def test_no_markdown_files_returns_success(self, tmp_path: Path) -> None:
        """A spec dir without markdown files short-circuits to success."""
        result = run_rumdl_format(tmp_path)
        assert result.success is True
        assert result.formatted_count == 0
        assert result.has_warnings is False

    def test_skips_with_warning_when_unavailable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing rumdl produces a success-with-warning result."""
        (tmp_path / "design.md").write_text("# t\n")
        monkeypatch.setattr(
            "pb_spec.validation.rumdl.is_rumdl_available",
            lambda: False,
        )
        result = run_rumdl_format(tmp_path)
        assert result.success is True
        assert result.has_warnings is True
        assert result.messages == [
            "Command 'rumdl' not found — skipping markdown auto-format. "
            "Install it with: cargo install rumdl  (or: pip install rumdl) "
            "to enable automatic markdown formatting."
        ]

    def test_success_formats_all_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A successful format reports every markdown file."""
        (tmp_path / "a.md").write_text("a\n")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "b.md").write_text("b\n")
        calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        monkeypatch.setattr(
            "pb_spec.validation.rumdl.subprocess.run",
            lambda *a, **kw: calls.append((a, kw)) or _fake_run(),
        )
        monkeypatch.setattr("pb_spec.validation.rumdl.is_rumdl_available", lambda: True)
        result = run_rumdl_format(tmp_path)
        assert result.success is True
        assert result.formatted_count == 2
        assert result.messages == ["Formatted 2 file(s)"]
        cmd = calls[0][0][0]
        assert isinstance(cmd, list)
        assert cmd[0] == "rumdl"
        assert cmd[1] == "fmt"
        assert {str(f) for f in cmd[2:]} == {str(tmp_path / "a.md"), str(tmp_path / "sub" / "b.md")}
        assert calls[0][1]["capture_output"] is True
        assert calls[0][1]["text"] is True
        assert calls[0][1]["check"] is True
        assert calls[0][1]["timeout"] == 60

    def test_timeout_returns_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A timeout produces a failed result with a warning."""
        (tmp_path / "design.md").write_text("# t\n")

        def raise_timeout(*args: object, **kw: object) -> None:
            raise subprocess.TimeoutExpired("rumdl", 30)

        monkeypatch.setattr("pb_spec.validation.rumdl.subprocess.run", raise_timeout)
        monkeypatch.setattr("pb_spec.validation.rumdl.is_rumdl_available", lambda: True)
        result = run_rumdl_format(tmp_path)
        assert result.success is False
        assert result.has_warnings is True
        assert any("timed out" in m for m in result.messages)

    def test_called_process_error_returns_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A nonzero rumdl exit reports stderr."""
        (tmp_path / "design.md").write_text("# t\n")

        def raise_cpe(*args: object, **kw: object) -> None:
            raise subprocess.CalledProcessError(3, ["rumdl"], stderr="lint error\n")

        monkeypatch.setattr("pb_spec.validation.rumdl.subprocess.run", raise_cpe)
        monkeypatch.setattr("pb_spec.validation.rumdl.is_rumdl_available", lambda: True)
        result = run_rumdl_format(tmp_path)
        assert result.success is False
        assert any("lint error" in m for m in result.messages)

    def test_oserror_returns_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """An OSError produces a failure result."""
        (tmp_path / "design.md").write_text("# t\n")

        def raise_oserror(*args: object, **kw: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr("pb_spec.validation.rumdl.subprocess.run", raise_oserror)
        monkeypatch.setattr("pb_spec.validation.rumdl.is_rumdl_available", lambda: True)
        result = run_rumdl_format(tmp_path)
        assert result.success is False
        assert any("disk full" in m for m in result.messages)

    def test_timeout_capped_at_max(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The format timeout is capped by MAX_RUMDL_TIMEOUT."""
        for i in range(20):
            (tmp_path / f"f{i}.md").write_text("x\n")
        seen: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.validation.rumdl.subprocess.run",
            lambda *a, **kw: seen.update(kw) or _fake_run(),
        )
        monkeypatch.setattr("pb_spec.validation.rumdl.is_rumdl_available", lambda: True)
        run_rumdl_format(tmp_path)
        assert seen["timeout"] == MAX_RUMDL_TIMEOUT

    def test_single_file_timeout_is_scaled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A single file uses the per-file timeout (not the cap)."""
        (tmp_path / "a.md").write_text("a\n")
        seen: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.validation.rumdl.subprocess.run",
            lambda *a, **kw: seen.update(kw) or _fake_run(),
        )
        monkeypatch.setattr("pb_spec.validation.rumdl.is_rumdl_available", lambda: True)
        run_rumdl_format(tmp_path)
        assert seen["timeout"] == 30


class TestFormatResult:
    """Tests for the FormatResult dataclass."""

    def test_defaults(self) -> None:
        """The defaults are inert."""
        result = FormatResult(success=True)
        assert result.messages == []
        assert result.formatted_count == 0
        assert result.has_warnings is False
