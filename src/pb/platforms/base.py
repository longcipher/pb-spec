"""Platform abstract base class."""

from abc import ABC, abstractmethod
from pathlib import Path

# Skill metadata: name -> description
SKILL_METADATA: dict[str, str] = {
    "pb-init": "Project State Initialization",
    "pb-plan": "Design & Task Planning",
    "pb-build": "Subagent-Driven Implementation",
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
    def get_skill_path(self, cwd: Path, skill_name: str) -> Path:
        """Return path for skill file in target project."""
        ...

    @abstractmethod
    def render_skill(self, skill_name: str, template_content: str) -> str:
        """Render template content into platform-specific format."""
        ...

    def install(self, cwd: Path, force: bool = False) -> list[str]:
        """Install all skills to target directory."""
        installed = []
        for skill_name in self.skill_names:
            target = self.get_skill_path(cwd, skill_name)
            if target.exists() and not force:
                print(f"  Skipping {target} (exists, use --force)")
                continue
            content = self._load_and_render(skill_name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            installed.append(str(target.relative_to(cwd)))

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
        from pb.templates import load_references

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
            ref_target.write_text(content)
            installed.append(str(ref_target.relative_to(cwd)))

    def _load_and_render(self, skill_name: str) -> str:
        """Load template and render for this platform."""
        from pb.templates import load_skill_content
        template_content = load_skill_content(skill_name)
        return self.render_skill(skill_name, template_content)
