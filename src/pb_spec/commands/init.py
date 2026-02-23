"""Init command — install pb-spec skill files into the current project."""

from pathlib import Path

import click

from pb_spec.platforms import get_platform, resolve_targets


@click.command("init")
@click.option(
    "--ai",
    type=click.Choice(["claude", "copilot", "opencode", "gemini", "codex", "all"]),
    required=True,
    help="Target AI platform(s) to install skills for.",
)
@click.option(
    "-g",
    "--global",
    "global_install",
    is_flag=True,
    default=False,
    help="Install into each AI tool's home config directory.",
)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing files")
def init_cmd(ai: str, global_install: bool, force: bool) -> None:
    """Install pb-spec skill files into the current project."""
    cwd = Path.cwd()
    targets = resolve_targets(ai)

    for target_name in targets:
        platform = get_platform(target_name)
        click.echo(f"Installing for {platform.name}...")
        installed = platform.install(cwd, force=force, global_install=global_install)
        for path in installed:
            click.echo(f"  + {path}")

    click.echo("pb-spec skills installed successfully!")
