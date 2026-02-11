"""Init command — install pb skill files into the current project."""

from pathlib import Path

import click

from pb.platforms import get_platform, resolve_targets


@click.command("init")
@click.option(
    "--ai",
    type=click.Choice(["claude", "copilot", "opencode", "all"]),
    required=True,
    help="Target AI platform(s) to install skills for.",
)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing files")
def init_cmd(ai: str, force: bool) -> None:
    """Install pb skill files into the current project."""
    cwd = Path.cwd()
    targets = resolve_targets(ai)

    for target_name in targets:
        platform = get_platform(target_name)
        click.echo(f"Installing for {platform.name}...")
        installed = platform.install(cwd, force=force)
        for path in installed:
            click.echo(f"  + {path}")

    click.echo("pb skills installed successfully!")
