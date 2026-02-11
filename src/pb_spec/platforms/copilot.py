"""GitHub Copilot platform adapter."""

from pathlib import Path
from typing import TYPE_CHECKING

from pb_spec.platforms.base import Platform

if TYPE_CHECKING:
    pass


class CopilotPlatform(Platform):
    """GitHub Copilot — skills as .github/prompts/<name>.prompt.md."""

    name = "copilot"

    def get_skill_path(self, cwd: Path, skill_name: str) -> Path:
        return cwd / ".github" / "prompts" / f"{skill_name}.prompt.md"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        return template_content

    def _load_and_render(self, skill_name: str) -> str:
        """Copilot uses prompt files, not SKILL.md."""
        from pb_spec.templates import load_prompt

        return load_prompt(skill_name)

    def _install_references(
        self, cwd: Path, skill_name: str, skill_target: Path, force: bool, installed: list[str]
    ) -> None:
        """Copilot prompt files are self-contained — no references."""
