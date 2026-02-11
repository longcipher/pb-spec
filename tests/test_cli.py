"""Tests for pb-spec CLI entry point and basic commands."""

from unittest.mock import patch

from click.testing import CliRunner

from pb_spec.cli import main

runner = CliRunner()


def test_help_contains_subcommands():
    """pb-spec --help should list init, version, and update subcommands."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "version" in result.output
    assert "update" in result.output


def test_version_shows_version_number():
    """pb-spec version should print the version number."""
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_version_option():
    """pb-spec --version should print the version number."""
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_update_calls_uv():
    """pb-spec update should call uv tool upgrade pb-spec."""
    with patch("pb_spec.commands.update.subprocess.run") as mock_run:
        result = runner.invoke(main, ["update"])
        assert result.exit_code == 0
        mock_run.assert_called_once_with(["uv", "tool", "upgrade", "pb-spec"], check=True)
