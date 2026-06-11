"""Terminal output helpers for pb-spec."""

from __future__ import annotations

import os
import sys

import click


def _should_use_color() -> bool:
    """Check if colored output should be used.

    Respects NO_COLOR standard, FORCE_COLOR override, and terminal capability.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def _colorize(text: str, color: str) -> str:
    """Apply color if terminal supports it."""
    if _should_use_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_success(msg: str) -> None:
    """Print a success message."""
    click.echo(_colorize(f"✅ {msg}", Colors.GREEN))


def print_error(msg: str) -> None:
    """Print an error message."""
    click.echo(_colorize(f"❌ {msg}", Colors.RED))


def print_warning(msg: str) -> None:
    """Print a warning message."""
    click.echo(_colorize(f"⚠️  {msg}", Colors.YELLOW))


def print_info(msg: str) -> None:
    """Print an info message."""
    click.echo(_colorize(f"ℹ️  {msg}", Colors.BLUE))
