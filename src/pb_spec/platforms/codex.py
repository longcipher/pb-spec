"""OpenAI Codex platform adapter."""

import os
from pathlib import Path

from pb_spec.platforms.base import SKILL_METADATA, Platform


class CodexPlatform(Platform):
    """Codex — custom prompts in .codex/prompts/<name>.md."""

    name = "codex"

    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        if global_install:
            codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
            return codex_home / "prompts" / f"{skill_name}.md"
        return cwd / ".codex" / "prompts" / f"{skill_name}.md"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        description = SKILL_METADATA.get(skill_name, "").replace('"', '\\"')
        frontmatter = f'---\ndescription: "{description}"\n---\n\n'
        return frontmatter + template_content

    def _load_and_render(self, skill_name: str) -> str:
        """Codex uses prompt files, not SKILL.md."""
        from pb_spec.templates import load_prompt

        prompt = load_prompt(skill_name)
        return self.render_skill(skill_name, prompt)

    def _install_references(
        self, cwd: Path, skill_name: str, skill_target: Path, force: bool, installed: list[str]
    ) -> None:
        """Codex prompt files are self-contained — no references."""
