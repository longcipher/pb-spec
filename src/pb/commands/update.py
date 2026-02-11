"""Update command for pb CLI."""

import subprocess

import click


@click.command("update")
def update_cmd():
    """Update pb to the latest version."""
    try:
        subprocess.run(["uv", "tool", "upgrade", "pb"], check=True)
        click.echo("pb updated successfully.")
    except FileNotFoundError:
        click.echo("Error: uv is not installed. Install it first: https://docs.astral.sh/uv/", err=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: update failed with exit code {e.returncode}", err=True)
