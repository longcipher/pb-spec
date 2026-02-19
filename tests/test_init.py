"""Tests for `pb-spec init` command — skill installation across platforms."""

import pytest
from click.testing import CliRunner

from pb_spec.cli import main


@pytest.fixture()
def runner():
    return CliRunner()


# --- pb init --ai claude ---


def test_init_claude(tmp_path, monkeypatch, runner):
    """pb-spec init --ai claude creates SKILL.md files + references for all skills."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "claude"])

    assert result.exit_code == 0, result.output

    # Main skill files
    assert (tmp_path / ".claude" / "skills" / "pb-init" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "pb-plan" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "pb-refine" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "pb-build" / "SKILL.md").exists()

    # Reference files for pb-plan
    assert (
        tmp_path / ".claude" / "skills" / "pb-plan" / "references" / "design_template.md"
    ).exists()
    assert (
        tmp_path / ".claude" / "skills" / "pb-plan" / "references" / "tasks_template.md"
    ).exists()

    # Reference files for pb-build
    assert (
        tmp_path / ".claude" / "skills" / "pb-build" / "references" / "implementer_prompt.md"
    ).exists()


# --- pb init --ai copilot ---


def test_init_copilot(tmp_path, monkeypatch, runner):
    """pb-spec init --ai copilot creates .prompt.md files (no references)."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "copilot"])

    assert result.exit_code == 0, result.output

    assert (tmp_path / ".github" / "prompts" / "pb-init.prompt.md").exists()
    assert (tmp_path / ".github" / "prompts" / "pb-plan.prompt.md").exists()
    assert (tmp_path / ".github" / "prompts" / "pb-refine.prompt.md").exists()
    assert (tmp_path / ".github" / "prompts" / "pb-build.prompt.md").exists()


# --- pb init --ai opencode ---


def test_init_opencode(tmp_path, monkeypatch, runner):
    """pb-spec init --ai opencode creates .opencode/skills/ structure with references."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "opencode"])

    assert result.exit_code == 0, result.output

    assert (tmp_path / ".opencode" / "skills" / "pb-init" / "SKILL.md").exists()
    assert (tmp_path / ".opencode" / "skills" / "pb-plan" / "SKILL.md").exists()
    assert (tmp_path / ".opencode" / "skills" / "pb-refine" / "SKILL.md").exists()
    assert (tmp_path / ".opencode" / "skills" / "pb-build" / "SKILL.md").exists()

    # Reference files for pb-plan
    assert (
        tmp_path / ".opencode" / "skills" / "pb-plan" / "references" / "design_template.md"
    ).exists()
    assert (
        tmp_path / ".opencode" / "skills" / "pb-plan" / "references" / "tasks_template.md"
    ).exists()

    # Reference files for pb-build
    assert (
        tmp_path / ".opencode" / "skills" / "pb-build" / "references" / "implementer_prompt.md"
    ).exists()


# --- pb init --ai gemini ---


def test_init_gemini(tmp_path, monkeypatch, runner):
    """pb-spec init --ai gemini creates .gemini command TOML files."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "gemini"])

    assert result.exit_code == 0, result.output

    assert (tmp_path / ".gemini" / "commands" / "pb-init.toml").exists()
    assert (tmp_path / ".gemini" / "commands" / "pb-plan.toml").exists()
    assert (tmp_path / ".gemini" / "commands" / "pb-refine.toml").exists()
    assert (tmp_path / ".gemini" / "commands" / "pb-build.toml").exists()


# --- pb init --ai codex ---


def test_init_codex(tmp_path, monkeypatch, runner):
    """pb-spec init --ai codex creates .codex prompt markdown files."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "codex"])

    assert result.exit_code == 0, result.output

    assert (tmp_path / ".codex" / "prompts" / "pb-init.md").exists()
    assert (tmp_path / ".codex" / "prompts" / "pb-plan.md").exists()
    assert (tmp_path / ".codex" / "prompts" / "pb-refine.md").exists()
    assert (tmp_path / ".codex" / "prompts" / "pb-build.md").exists()


# --- pb init --ai all ---


def test_init_all(tmp_path, monkeypatch, runner):
    """pb-spec init --ai all generates files for all supported platforms."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "all"])

    assert result.exit_code == 0, result.output

    # Claude
    assert (tmp_path / ".claude" / "skills" / "pb-init" / "SKILL.md").exists()
    # Copilot
    assert (tmp_path / ".github" / "prompts" / "pb-init.prompt.md").exists()
    # OpenCode
    assert (tmp_path / ".opencode" / "skills" / "pb-init" / "SKILL.md").exists()
    # Gemini
    assert (tmp_path / ".gemini" / "commands" / "pb-init.toml").exists()
    # Codex
    assert (tmp_path / ".codex" / "prompts" / "pb-init.md").exists()


# --- --force overwrites ---


def test_init_force_overwrites(tmp_path, monkeypatch, runner):
    """With --force, existing file is overwritten."""
    monkeypatch.chdir(tmp_path)

    # Pre-create a file with dummy content
    target = tmp_path / ".claude" / "skills" / "pb-init" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("OLD CONTENT")

    result = runner.invoke(main, ["init", "--ai", "claude", "--force"])
    assert result.exit_code == 0, result.output

    # File should be overwritten with real content
    content = target.read_text()
    assert content != "OLD CONTENT"
    assert len(content) > 20  # has real content


# --- skips existing without --force ---


def test_init_skips_existing(tmp_path, monkeypatch, runner):
    """Without --force, existing file is skipped."""
    monkeypatch.chdir(tmp_path)

    target = tmp_path / ".claude" / "skills" / "pb-init" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("OLD CONTENT")

    result = runner.invoke(main, ["init", "--ai", "claude"])
    assert result.exit_code == 0, result.output
    assert "Skipping" in result.output

    # File content should not change
    assert target.read_text() == "OLD CONTENT"


# --- content checks ---


def test_init_claude_has_frontmatter(tmp_path, monkeypatch, runner):
    """Claude SKILL.md files start with YAML frontmatter (---)."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "claude"])

    content = (tmp_path / ".claude" / "skills" / "pb-init" / "SKILL.md").read_text()
    assert content.startswith("---")


def test_init_copilot_no_frontmatter(tmp_path, monkeypatch, runner):
    """Copilot .prompt.md files do NOT start with YAML frontmatter."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "copilot"])

    content = (tmp_path / ".github" / "prompts" / "pb-init.prompt.md").read_text()
    assert not content.startswith("---")


def test_init_gemini_toml_shape(tmp_path, monkeypatch, runner):
    """Gemini command files should be TOML with description and prompt fields."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "gemini"])

    content = (tmp_path / ".gemini" / "commands" / "pb-init.toml").read_text()
    assert content.startswith('description = "')
    assert "\nprompt = '''\n" in content


def test_init_codex_has_frontmatter(tmp_path, monkeypatch, runner):
    """Codex prompt files should start with YAML frontmatter."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "codex"])

    content = (tmp_path / ".codex" / "prompts" / "pb-init.md").read_text()
    assert content.startswith("---")
