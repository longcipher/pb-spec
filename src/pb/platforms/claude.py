"""Claude platform adapter."""

from pathlib import Path

from pb.platforms.base import SKILL_METADATA, Platform


class ClaudePlatform(Platform):
    """Claude Code — skills as .claude/skills/<name>/SKILL.md."""

    name = "claude"

    def get_skill_path(self, cwd: Path, skill_name: str) -> Path:
        return cwd / ".claude" / "skills" / skill_name / "SKILL.md"

    def render_skill(self, skill_name: str, template_content: str) -> str:
        description = SKILL_METADATA.get(skill_name, "")
        frontmatter = f'---\nname: {skill_name}\ndescription: "{description}"\n---\n\n'
        return frontmatter + template_content
