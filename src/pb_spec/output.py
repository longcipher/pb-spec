"""Terminal output helpers for pb-spec."""

from __future__ import annotations

import click


def print_success(msg: str) -> None:
    """Print a success message."""
    click.echo(click.style(f"✅ {msg}", fg="green"))


def print_error(msg: str) -> None:
    """Print an error message."""
    click.echo(click.style(f"❌ {msg}", fg="red"))


def print_warning(msg: str) -> None:
    """Print a warning message."""
    click.echo(click.style(f"⚠️  {msg}", fg="yellow"))


def print_info(msg: str) -> None:
    """Print an info message."""
    click.echo(click.style(f"ℹ️  {msg}", fg="blue"))
