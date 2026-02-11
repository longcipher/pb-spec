"""Tests for pb-spec CLI entry point and basic commands."""

import tomllib
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pb_spec.cli import main

runner = CliRunner()


def get_project_version() -> str:
    """Read version from pyproject.toml."""
    root_dir = Path(__file__).parents[1]
    with open(root_dir / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def test_help_contains_subcommands():
    """pb-spec --help should list init, version, and update subcommands."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "version" in result.output
    assert "update" in result.output


def test_version_shows_version_number():
    """pb-spec version should print the version number."""
    expected_version = get_project_version()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert expected_version in result.output


def test_version_option():
    """pb-spec --version should print the version number."""
    expected_version = get_project_version()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert expected_version in result.output


def test_update_calls_uv():
    """pb-spec update should call uv tool upgrade pb-spec."""
    with patch("pb_spec.commands.update.subprocess.run") as mock_run:
        result = runner.invoke(main, ["update"])
        assert result.exit_code == 0
        mock_run.assert_called_once_with(["uv", "tool", "upgrade", "pb-spec"], check=True)
