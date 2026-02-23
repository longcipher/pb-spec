"""Google Gemini CLI platform adapter."""

import json
from pathlib import Path

from pb_spec.platforms.base import SKILL_METADATA, Platform


class GeminiPlatform(Platform):
    """Gemini CLI — custom commands in .gemini/commands/<name>.toml."""

    name = "gemini"

    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        if global_install:
            return Path.home() / ".gemini" / "commands" / f"{skill_name}.toml"
        return cwd / ".gemini" / "commands" / f"{skill_name}.toml"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        description = SKILL_METADATA.get(skill_name, "")
        desc_value = json.dumps(description, ensure_ascii=False)
        body = template_content.rstrip()
        if "'''" not in body:
            prompt_value = "'''\n" + body + "\n'''"
        else:
            escaped = body.replace("\\", "\\\\").replace('"', '\\"')
            prompt_value = '"""\n' + escaped + '\n"""'
        return f"description = {desc_value}\nprompt = {prompt_value}\n"

    def _load_and_render(self, skill_name: str) -> str:
        """Gemini commands use TOML prompt files."""
        from pb_spec.templates import load_prompt

        prompt = load_prompt(skill_name)
        return self.render_skill(skill_name, prompt)

    def _install_references(
        self, cwd: Path, skill_name: str, skill_target: Path, force: bool, installed: list[str]
    ) -> None:
        """Gemini command files are self-contained — no references."""
