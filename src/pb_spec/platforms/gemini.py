"""Google Gemini CLI platform adapter."""

from __future__ import annotations

from pathlib import Path

from pb_spec.platforms.base import SKILL_METADATA, Platform


class GeminiPlatform(Platform):
    """Gemini CLI — skills as .gemini/skills/<name>/SKILL.md."""

    name = "gemini"

    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        if global_install:
            return Path.home() / ".gemini" / "skills" / skill_name / "SKILL.md"
        return cwd / ".gemini" / "skills" / skill_name / "SKILL.md"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        description = SKILL_METADATA.get(skill_name, "").replace('"', '\\"')
        frontmatter = f'---\nname: {skill_name}\ndescription: "{description}"\n---\n\n'
        return frontmatter + template_content
