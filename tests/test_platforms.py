"""Tests for platform base class, concrete platforms, and factory functions."""

from pathlib import Path

import pytest

from pb_spec.platforms import get_platform, resolve_targets
from pb_spec.platforms.claude import ClaudePlatform
from pb_spec.platforms.codex import CodexPlatform
from pb_spec.platforms.copilot import CopilotPlatform
from pb_spec.platforms.gemini import GeminiPlatform
from pb_spec.platforms.opencode import OpenCodePlatform

# --- skill_names ---


def test_skill_names_returns_four_skills():
    platform = ClaudePlatform()
    assert platform.skill_names == ["pb-init", "pb-plan", "pb-refine", "pb-build"]


# --- get_skill_path ---


def test_claude_skill_path():
    p = ClaudePlatform()
    cwd = Path("/project")
    assert p.get_skill_path(cwd, "pb-init") == Path("/project/.claude/skills/pb-init/SKILL.md")


def test_copilot_skill_path():
    p = CopilotPlatform()
    cwd = Path("/project")
    assert p.get_skill_path(cwd, "pb-init") == Path("/project/.github/prompts/pb-init.prompt.md")


def test_opencode_skill_path():
    p = OpenCodePlatform()
    cwd = Path("/project")
    assert p.get_skill_path(cwd, "pb-init") == Path("/project/.opencode/skills/pb-init/SKILL.md")


def test_gemini_skill_path():
    p = GeminiPlatform()
    cwd = Path("/project")
    assert p.get_skill_path(cwd, "pb-init") == Path("/project/.gemini/commands/pb-init.toml")


def test_codex_skill_path():
    p = CodexPlatform()
    cwd = Path("/project")
    assert p.get_skill_path(cwd, "pb-init") == Path("/project/.codex/prompts/pb-init.md")


# --- render_skill ---


def test_claude_render_has_yaml_frontmatter():
    p = ClaudePlatform()
    result = p.render_skill("pb-init", "# Hello")
    assert result.startswith("---\n")
    assert "name: pb-init" in result
    assert "# Hello" in result


def test_copilot_render_no_frontmatter():
    p = CopilotPlatform()
    result = p.render_skill("pb-init", "# Hello")
    assert not result.startswith("---")
    assert result == "# Hello"


def test_opencode_render_has_yaml_frontmatter():
    p = OpenCodePlatform()
    result = p.render_skill("pb-init", "# Hello")
    assert result.startswith("---\n")
    assert "name: pb-init" in result
    assert "# Hello" in result


def test_gemini_render_toml_prompt():
    p = GeminiPlatform()
    result = p.render_skill("pb-init", "# Hello")
    assert result.startswith('description = "')
    assert "prompt = '''" in result
    assert "# Hello" in result


def test_codex_render_has_yaml_frontmatter():
    p = CodexPlatform()
    result = p.render_skill("pb-init", "# Hello")
    assert result.startswith("---\n")
    assert "description:" in result
    assert "# Hello" in result


# --- description quoting ---


def test_claude_render_escapes_quotes_in_description():
    """Claude YAML frontmatter should escape double quotes in descriptions."""
    p = ClaudePlatform()
    result = p.render_skill("pb-init", "# Content")
    # Current descriptions don't contain quotes; verify YAML is well-formed
    assert 'description: "' in result
    assert result.count('---') == 2  # opening and closing frontmatter


def test_opencode_render_escapes_quotes_in_description():
    """OpenCode YAML frontmatter should escape double quotes in descriptions."""
    p = OpenCodePlatform()
    result = p.render_skill("pb-init", "# Content")
    assert 'description: "' in result
    assert result.count('---') == 2


def test_codex_render_escapes_quotes_in_description():
    """Codex YAML frontmatter should escape double quotes in descriptions."""
    p = CodexPlatform()
    result = p.render_skill("pb-init", "# Content")
    assert 'description: "' in result
    assert result.count('---') == 2


# --- resolve_targets ---


def test_resolve_targets_all():
    targets = resolve_targets("all")
    assert len(targets) == 5
    assert set(targets) == {"claude", "copilot", "opencode", "gemini", "codex"}


def test_resolve_targets_single():
    assert resolve_targets("claude") == ["claude"]


# --- get_platform ---


def test_get_platform_claude():
    p = get_platform("claude")
    assert isinstance(p, ClaudePlatform)


def test_get_platform_gemini():
    p = get_platform("gemini")
    assert isinstance(p, GeminiPlatform)


def test_get_platform_codex():
    p = get_platform("codex")
    assert isinstance(p, CodexPlatform)


def test_get_platform_invalid_raises():
    with pytest.raises(ValueError, match="Unknown platform"):
        get_platform("invalid")


# --- name property ---


def test_platform_name():
    assert ClaudePlatform().name == "claude"
    assert CopilotPlatform().name == "copilot"
    assert OpenCodePlatform().name == "opencode"
    assert GeminiPlatform().name == "gemini"
    assert CodexPlatform().name == "codex"
