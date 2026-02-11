"""Template loading system using importlib.resources."""

import importlib.resources


def load_template(skill_name: str, filename: str) -> str:
    """Load a template file from the skills directory.

    Args:
        skill_name: e.g. "pb-init", "pb-plan", "pb-build"
        filename: e.g. "SKILL.md"
    Returns:
        File content as string
    """
    ref = importlib.resources.files("pb.templates") / "skills" / skill_name / filename
    return ref.read_text(encoding="utf-8")


def load_skill_content(skill_name: str) -> str:
    """Load the main SKILL.md content for a skill."""
    return load_template(skill_name, "SKILL.md")


def load_references(skill_name: str) -> dict[str, str]:
    """Load all reference files for a skill.

    Returns:
        Dict mapping filename to content. Empty dict if no references/ directory.
    """
    refs_dir = importlib.resources.files("pb.templates") / "skills" / skill_name / "references"
    result = {}
    try:
        for item in refs_dir.iterdir():
            if item.is_file():
                result[item.name] = item.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError, NotADirectoryError):
        pass
    return result


def load_prompt(skill_name: str) -> str:
    """Load a Copilot prompt template.

    Args:
        skill_name: e.g. "pb-init", "pb-plan", "pb-build"
    Returns:
        Prompt file content as string
    """
    ref = importlib.resources.files("pb.templates") / "prompts" / f"{skill_name}.prompt.md"
    return ref.read_text(encoding="utf-8")
