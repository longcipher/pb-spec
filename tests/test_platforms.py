"""Tests for platform base class, concrete platforms, and factory functions."""

from pathlib import Path

import pytest

from pb.platforms import get_platform, resolve_targets
from pb.platforms.base import Platform
from pb.platforms.claude import ClaudePlatform
from pb.platforms.copilot import CopilotPlatform
from pb.platforms.opencode import OpenCodePlatform


# --- skill_names ---


def test_skill_names_returns_three_skills():
    platform = ClaudePlatform()
    assert platform.skill_names == ["pb-init", "pb-plan", "pb-build"]


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


# --- resolve_targets ---


def test_resolve_targets_all():
    targets = resolve_targets("all")
    assert len(targets) == 3
    assert set(targets) == {"claude", "copilot", "opencode"}


def test_resolve_targets_single():
    assert resolve_targets("claude") == ["claude"]


# --- get_platform ---


def test_get_platform_claude():
    p = get_platform("claude")
    assert isinstance(p, ClaudePlatform)


def test_get_platform_invalid_raises():
    with pytest.raises(ValueError, match="Unknown platform"):
        get_platform("invalid")


# --- name property ---


def test_platform_name():
    assert ClaudePlatform().name == "claude"
    assert CopilotPlatform().name == "copilot"
    assert OpenCodePlatform().name == "opencode"
