"""Unit tests for spec directory discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from pb_spec.commands.discovery import get_latest_spec_dir
from pb_spec.exceptions import SpecNotFoundError


class TestGetLatestSpecDir:
    """Tests for latest-spec-dir resolution."""

    def test_defaults_to_specs_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """With no argument the cwd specs/ directory is used."""
        (tmp_path / "specs" / "2026-03-01-a").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        assert get_latest_spec_dir().name == "2026-03-01-a"

    def test_path_that_is_a_file_raises(self, tmp_path: Path) -> None:
        """A file passed as specs_dir is not a directory and raises."""
        target = tmp_path / "not-a-dir"
        target.write_text("x\n")
        with pytest.raises(SpecNotFoundError) as exc_info:
            get_latest_spec_dir(target)
        assert str(exc_info.value) == "Directory 'specs/' not found. Run /pb-plan first."

    def test_missing_specs_dir_message(self, tmp_path: Path) -> None:
        """A missing specs directory raises the precise message."""
        with pytest.raises(SpecNotFoundError) as exc_info:
            get_latest_spec_dir(tmp_path / "specs")
        assert str(exc_info.value) == "Directory 'specs/' not found. Run /pb-plan first."

    def test_empty_specs_dir_message(self, tmp_path: Path) -> None:
        """An empty specs directory raises the precise message."""
        specs = tmp_path / "specs"
        specs.mkdir()
        with pytest.raises(SpecNotFoundError) as exc_info:
            get_latest_spec_dir(specs)
        assert str(exc_info.value) == "No feature specs found in 'specs/'."

    def test_date_dirs_win_over_plain_dirs(self, tmp_path: Path) -> None:
        """Dated spec dirs sort before plain-named dirs."""
        (tmp_path / "2026-03-01-dated").mkdir()
        (tmp_path / "zzz-plain").mkdir()
        latest = get_latest_spec_dir(tmp_path)
        assert latest.name == "2026-03-01-dated"

    def test_latest_date_wins(self, tmp_path: Path) -> None:
        """The newest dated directory is selected."""
        (tmp_path / "2026-03-01-old").mkdir()
        (tmp_path / "2026-03-28-new").mkdir()
        assert get_latest_spec_dir(tmp_path).name == "2026-03-28-new"

    def test_plain_dirs_sorted_last(self, tmp_path: Path) -> None:
        """Among plain dirs, the lexicographically last wins."""
        (tmp_path / "alpha").mkdir()
        (tmp_path / "beta").mkdir()
        assert get_latest_spec_dir(tmp_path).name == "beta"
