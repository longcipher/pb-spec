"""Unit tests for shared configuration."""

from __future__ import annotations

import pytest

from pb_spec.config import _int_env


class TestIntEnv:
    """Tests for the _int_env helper."""

    def test_returns_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unset variable returns the default."""
        monkeypatch.delenv("PB_SPEC_TEST_UNSET", raising=False)
        assert _int_env("PB_SPEC_TEST_UNSET", 42) == 42

    def test_parses_valid_int(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A valid integer string is parsed."""
        monkeypatch.setenv("PB_SPEC_TEST_INT", "7")
        assert _int_env("PB_SPEC_TEST_INT", 42) == 7

    def test_invalid_value_returns_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A non-integer value logs a warning and returns the default."""
        monkeypatch.setenv("PB_SPEC_TEST_BAD", "not-a-number")
        assert _int_env("PB_SPEC_TEST_BAD", 42) == 42

    def test_warning_logs_original_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The warning carries the name, raw value, and default."""
        logged: list[tuple[object, ...]] = []
        monkeypatch.setenv("PB_SPEC_TEST_RAW", "zzz")
        monkeypatch.setattr(
            "pb_spec.config.logger.warning",
            lambda *args: logged.append(args),
        )
        _int_env("PB_SPEC_TEST_RAW", 7)
        assert logged
        assert logged[0][0] == "Invalid value for %s=%r, using default %d"
        assert logged[0][1] == "PB_SPEC_TEST_RAW"
        assert logged[0][2] == "zzz"
        assert logged[0][3] == 7
