"""Google Gemini CLI platform adapter."""

from __future__ import annotations

import json
from pathlib import Path

from pb_spec.platforms.base import SKILL_METADATA, PromptOnlyPlatform


class GeminiPlatform(PromptOnlyPlatform):
    """Gemini CLI — custom commands in .gemini/commands/<name>.toml."""

    name = "gemini"

    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        if global_install:
            return Path.home() / ".gemini" / "commands" / f"{skill_name}.toml"
        return cwd / ".gemini" / "commands" / f"{skill_name}.toml"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        description = SKILL_METADATA.get(skill_name, "")
        desc_value = json.dumps(description, ensure_ascii=False)
        escaped = template_content.rstrip().replace("\\", "\\\\").replace('"', '\\"')
        prompt_value = '"""\n' + escaped + '\n"""'
        return f"description = {desc_value}\nprompt = {prompt_value}\n"
