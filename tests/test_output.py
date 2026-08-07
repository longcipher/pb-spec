"""Unit tests for terminal output helpers."""

from __future__ import annotations

import pytest

from pb_spec.output import print_error, print_info, print_success, print_warning


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture everything routed to click.echo."""
    out: list[str] = []
    monkeypatch.setattr(
        "pb_spec.output.click.echo",
        lambda msg, **kw: out.append(msg),
    )
    return out


class TestPrintSuccess:
    """Tests for print_success."""

    def test_prints_message(self, captured: list[str]) -> None:
        """The message is printed with the success marker."""
        print_success("done")
        assert captured
        assert "done" in captured[0]
        assert "✅" in captured[0]

    def test_green_style(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """print_success styles its message green."""
        style_kw: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.output.click.style",
            lambda msg, **kw: style_kw.update(kw) or msg,
        )
        print_success("ok")
        assert style_kw.get("fg") == "green"


class TestPrintError:
    """Tests for print_error."""

    def test_prints_message(self, captured: list[str]) -> None:
        """The message is printed with the error marker."""
        print_error("boom")
        assert captured
        assert "boom" in captured[0]
        assert "❌" in captured[0]

    def test_red_style(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """print_error styles its message red."""
        style_kw: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.output.click.style",
            lambda msg, **kw: style_kw.update(kw) or msg,
        )
        print_error("bad")
        assert style_kw.get("fg") == "red"


class TestPrintWarning:
    """Tests for print_warning."""

    def test_prints_message(self, captured: list[str]) -> None:
        """The message is printed with the warning marker."""
        print_warning("careful")
        assert captured
        assert "careful" in captured[0]
        assert "⚠️" in captured[0]

    def test_yellow_style(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """print_warning styles its message yellow."""
        style_kw: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.output.click.style",
            lambda msg, **kw: style_kw.update(kw) or msg,
        )
        print_warning("watch")
        assert style_kw.get("fg") == "yellow"


class TestPrintInfo:
    """Tests for print_info."""

    def test_prints_message(self, captured: list[str]) -> None:
        """The message is printed with the info marker."""
        print_info("running")
        assert captured
        assert "running" in captured[0]
        assert "ℹ️" in captured[0]

    def test_blue_style(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """print_info styles its message blue."""
        style_kw: dict[str, object] = {}
        monkeypatch.setattr(
            "pb_spec.output.click.style",
            lambda msg, **kw: style_kw.update(kw) or msg,
        )
        print_info("note")
        assert style_kw.get("fg") == "blue"
