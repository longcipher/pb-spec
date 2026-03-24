"""OpenAI Codex platform adapter."""

import os
from pathlib import Path

from pb_spec.platforms.base import SKILL_METADATA, PromptOnlyPlatform


class CodexPlatform(PromptOnlyPlatform):
    """Codex — custom prompts in .codex/prompts/<name>.md."""

    name = "codex"

    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        if global_install:
            codex_home = Path(
                os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
            ).expanduser()
            return codex_home / "prompts" / f"{skill_name}.md"
        return cwd / ".codex" / "prompts" / f"{skill_name}.md"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        description = SKILL_METADATA.get(skill_name, "").replace('"', '\\"')
        frontmatter = f'---\ndescription: "{description}"\n---\n\n'
        return frontmatter + template_content
