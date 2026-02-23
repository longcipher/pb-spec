"""OpenCode platform adapter."""

import os
from pathlib import Path

from pb_spec.platforms.base import SKILL_METADATA, Platform


class OpenCodePlatform(Platform):
    """OpenCode — skills as .opencode/skills/<name>/SKILL.md."""

    name = "opencode"

    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        if global_install:
            config_home = Path(
                os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            ).expanduser()
            return config_home / "opencode" / "skills" / skill_name / "SKILL.md"
        return cwd / ".opencode" / "skills" / skill_name / "SKILL.md"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        description = SKILL_METADATA.get(skill_name, "").replace('"', '\\"')
        frontmatter = f'---\nname: {skill_name}\ndescription: "{description}"\n---\n\n'
        return frontmatter + template_content
