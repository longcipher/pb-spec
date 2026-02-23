"""Platform abstract base class."""

from abc import ABC, abstractmethod
from pathlib import Path

# Skill metadata: name -> description
SKILL_METADATA: dict[str, str] = {
    "pb-init": (
        "Use when onboarding a repo or after major structural changes to regenerate AGENTS.md "
        "project context."
    ),
    "pb-plan": (
        "Use when converting a requirement into a design proposal and executable tasks before coding."
    ),
    "pb-refine": (
        "Use when feedback or a Design Change Request requires incremental updates to design.md "
        "and tasks.md."
    ),
    "pb-build": (
        "Use when tasks.md is ready and you need sequential TDD implementation with recovery loops."
    ),
}

DEFAULT_SKILL_NAMES = list(SKILL_METADATA.keys())


class Platform(ABC):
    """AI Platform Adapter Base Class."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def skill_names(self) -> list[str]:
        """Return list of skill names to install."""
        return DEFAULT_SKILL_NAMES

    @abstractmethod
    def get_skill_path(self, cwd: Path, skill_name: str, global_install: bool = False) -> Path:
        """Return path for skill file in target project."""
        ...

    @abstractmethod
    def render_skill(self, skill_name: str, template_content: str) -> str:
        """Render template content into platform-specific format."""
        ...

    def install(self, cwd: Path, force: bool = False, global_install: bool = False) -> list[str]:
        """Install all skills to target directory."""
        installed = []
        for skill_name in self.skill_names:
            target = self.get_skill_path(cwd, skill_name, global_install=global_install)
            if target.exists() and not force:
                print(f"  Skipping {target} (exists, use --force)")
                continue
            content = self._load_and_render(skill_name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            installed.append(self._format_output_path(target, cwd))

            # Install reference files alongside the main skill file
            self._install_references(cwd, skill_name, target, force, installed)
        return installed

    def _install_references(
        self,
        cwd: Path,
        skill_name: str,
        skill_target: Path,
        force: bool,
        installed: list[str],
    ) -> None:
        """Install reference files next to the skill file. Override to skip."""
        from pb_spec.templates import load_references

        refs = load_references(skill_name)
        if not refs:
            return
        refs_dir = skill_target.parent / "references"
        refs_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in refs.items():
            ref_target = refs_dir / filename
            if ref_target.exists() and not force:
                print(f"  Skipping {ref_target} (exists, use --force)")
                continue
            ref_target.write_text(content, encoding="utf-8")
            installed.append(self._format_output_path(ref_target, cwd))

    @staticmethod
    def _format_output_path(path: Path, cwd: Path) -> str:
        """Format path for CLI output across project/global installs."""
        try:
            return str(path.relative_to(cwd))
        except ValueError:
            home = Path.home()
            try:
                return f"~/{path.relative_to(home)}"
            except ValueError:
                return str(path)

    def _load_and_render(self, skill_name: str) -> str:
        """Load template and render for this platform."""
        from pb_spec.templates import load_skill_content

        template_content = load_skill_content(skill_name)
        return self.render_skill(skill_name, template_content)
