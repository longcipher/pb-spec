"""GitHub Copilot platform adapter."""

from pathlib import Path

from pb_spec.platforms.base import PromptOnlyPlatform


class CopilotPlatform(PromptOnlyPlatform):
    """GitHub Copilot — skills as .github/prompts/<name>.prompt.md."""

    name = "copilot"

    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        if global_install:
            return Path.home() / ".copilot" / "prompts" / f"{skill_name}.prompt.md"
        return cwd / ".github" / "prompts" / f"{skill_name}.prompt.md"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        return template_content
