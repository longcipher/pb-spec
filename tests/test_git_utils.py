"""Unit tests for git interaction utilities."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from pb_spec.git_utils import get_git_modified_files


def _fake_run(stdout: str = "") -> SimpleNamespace:
    """A minimal subprocess.CompletedProcess stand-in."""
    return SimpleNamespace(stdout=stdout, stderr="")


class TestSubprocessInvocation:
    """Tests that git is invoked with the exact contract."""

    def test_invocation_arguments(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The git command, flags, and run kwargs match the contract."""
        captured: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.git_utils.subprocess.run",
            lambda *a, **kw: captured.update(cmd=a[0], **kw) or _fake_run(""),
        )
        get_git_modified_files()
        assert captured["cmd"] == [
            "git",
            "-c",
            "core.quotePath=false",
            "status",
            "--porcelain",
            "-uall",
        ]
        assert captured["capture_output"] is True
        assert captured["text"] is True
        assert captured["encoding"] == "utf-8"
        assert captured["timeout"] == 60
        assert captured["cwd"] == Path(".").resolve()


class TestGetGitModifiedFiles:
    """Tests for the porcelain parser."""

    def test_empty_stdout_returns_empty_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No output yields an empty set."""
        monkeypatch.setattr(
            "pb_spec.git_utils.subprocess.run",
            lambda *a, **kw: _fake_run(""),
        )
        assert get_git_modified_files() == set()

    def test_parses_modified_and_untracked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Modified and untracked lines resolve to absolute paths."""
        stdout = " M src/a.py\n?? src/new.py\n"
        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", lambda *a, **kw: _fake_run(stdout))
        files = get_git_modified_files()
        root = Path(".").resolve()
        assert files == {root / "src" / "a.py", root / "src" / "new.py"}

    def test_short_lines_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Malformed short lines are skipped."""
        stdout = "M\n??\n M src/a.py\n"
        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", lambda *a, **kw: _fake_run(stdout))
        files = get_git_modified_files()
        assert files == {Path(".").resolve() / "src" / "a.py"}

    def test_rename_lines_take_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Renamed files resolve to the new path."""
        stdout = "R  src/old.py -> src/new.py\n"
        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", lambda *a, **kw: _fake_run(stdout))
        files = get_git_modified_files()
        root = Path(".").resolve()
        assert files == {root / "src" / "new.py"}

    def test_quoted_paths_are_unquoted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Quoted porcelain paths lose their quotes."""
        stdout = '?? "src/weird name.py"\n'
        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", lambda *a, **kw: _fake_run(stdout))
        files = get_git_modified_files()
        root = Path(".").resolve()
        assert files == {root / "src" / "weird name.py"}

    def test_four_char_line_is_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A porcelain line of exactly 4 characters is still parsed."""
        stdout = " M a\n"  # len(" M a") == 4
        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", lambda *a, **kw: _fake_run(stdout))
        files = get_git_modified_files()
        assert files == {Path(".").resolve() / "a"}

    def test_rename_split_takes_first_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A chain of renames resolves to the first arrow target."""
        stdout = "R  src/a.py -> src/b.py -> src/c.py\n"
        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", lambda *a, **kw: _fake_run(stdout))
        files = get_git_modified_files()
        root = Path(".").resolve()
        assert files == {root / "src" / "b.py -> src/c.py"}

    def test_quote_start_only_kept(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A path with only a leading quote keeps it (both-ends rule)."""
        stdout = '?? "abc.py\n'
        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", lambda *a, **kw: _fake_run(stdout))
        files = get_git_modified_files()
        root = Path(".").resolve()
        assert files == {root / '"abc.py'}

    def test_timeout_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A timeout is swallowed and yields an empty set."""
        warned: list[tuple[object, ...]] = []
        monkeypatch.setattr("pb_spec.git_utils.logger.warning", lambda *a: warned.append(a))

        def raise_timeout(*a: object, **kw: object) -> None:
            raise subprocess.TimeoutExpired("git", 60)

        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", raise_timeout)
        assert get_git_modified_files() == set()
        assert warned
        assert warned[0][0] == "git status timed out in %s"
        assert warned[0][1] == Path(".").resolve()

    def test_called_process_error_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A CalledProcessError is swallowed and yields an empty set."""
        debugs: list[tuple[object, ...]] = []
        monkeypatch.setattr("pb_spec.git_utils.logger.debug", lambda *a: debugs.append(a))

        def raise_cpe(*a: object, **kw: object) -> None:
            raise subprocess.CalledProcessError(128, ["git"], stderr="boom")

        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", raise_cpe)
        assert get_git_modified_files() == set()
        assert debugs
        assert debugs[0][0] == "git status failed: %s"
        assert debugs[0][1] == "boom"

    def test_missing_git_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing git binary yields an empty set."""
        debugs: list[tuple[object, ...]] = []
        monkeypatch.setattr("pb_spec.git_utils.logger.debug", lambda *a: debugs.append(a))

        def raise_missing(*a: object, **kw: object) -> None:
            raise FileNotFoundError("git")

        monkeypatch.setattr("pb_spec.git_utils.subprocess.run", raise_missing)
        assert get_git_modified_files() == set()
        assert debugs == [("git not found, returning empty set",)]

    def test_real_git_repo_end_to_end(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A real git repo surfaces modified files, including the spec dir."""
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        tracked = tmp_path / "src" / "tracked.py"
        tracked.parent.mkdir()
        tracked.write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "--no-gpg-sign", "-qm", "init"], cwd=tmp_path, check=True)

        tracked.write_text("x = 2\n")  # modified
        (tmp_path / "src" / "untracked.py").write_text("y = 1\n")  # untracked

        files = get_git_modified_files(tmp_path)
        assert tmp_path.resolve() / "src" / "tracked.py" in files
        assert tmp_path.resolve() / "src" / "untracked.py" in files
