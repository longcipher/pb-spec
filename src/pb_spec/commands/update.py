"""Update command for pb-spec CLI."""

import subprocess

import click


@click.command("update")
def update_cmd():
    """Update pb-spec to the latest version."""
    try:
        subprocess.run(["uv", "tool", "upgrade", "pb-spec"], check=True)
        click.echo("pb-spec updated successfully.")
    except FileNotFoundError as exc:
        raise click.ClickException(
            "uv is not installed. Install it first: https://docs.astral.sh/uv/"
        ) from exc
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"update failed with exit code {e.returncode}") from e
