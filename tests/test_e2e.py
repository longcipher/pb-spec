"""End-to-end tests for pb-spec init workflow."""

import pytest
from click.testing import CliRunner

from pb_spec.cli import main


@pytest.fixture()
def runner():
    return CliRunner()


def test_e2e_init_all_creates_complete_structure(tmp_path, monkeypatch, runner):
    """Verify pb-spec init --ai all creates all files for all supported platforms."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "all"])
    assert result.exit_code == 0, result.output

    # Claude files
    assert (tmp_path / ".claude" / "skills" / "pb-init" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "pb-plan" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "pb-refine" / "SKILL.md").exists()
    assert (
        tmp_path / ".claude" / "skills" / "pb-plan" / "references" / "design_template.md"
    ).exists()
    assert (
        tmp_path / ".claude" / "skills" / "pb-plan" / "references" / "tasks_template.md"
    ).exists()
    assert (tmp_path / ".claude" / "skills" / "pb-build" / "SKILL.md").exists()
    assert (
        tmp_path / ".claude" / "skills" / "pb-build" / "references" / "implementer_prompt.md"
    ).exists()

    # Copilot files
    assert (tmp_path / ".github" / "prompts" / "pb-init.prompt.md").exists()
    assert (tmp_path / ".github" / "prompts" / "pb-plan.prompt.md").exists()
    assert (tmp_path / ".github" / "prompts" / "pb-refine.prompt.md").exists()
    assert (tmp_path / ".github" / "prompts" / "pb-build.prompt.md").exists()

    # OpenCode files
    assert (tmp_path / ".opencode" / "skills" / "pb-init" / "SKILL.md").exists()
    assert (tmp_path / ".opencode" / "skills" / "pb-plan" / "SKILL.md").exists()
    assert (tmp_path / ".opencode" / "skills" / "pb-refine" / "SKILL.md").exists()
    assert (
        tmp_path / ".opencode" / "skills" / "pb-plan" / "references" / "design_template.md"
    ).exists()
    assert (
        tmp_path / ".opencode" / "skills" / "pb-plan" / "references" / "tasks_template.md"
    ).exists()
    assert (tmp_path / ".opencode" / "skills" / "pb-build" / "SKILL.md").exists()
    assert (
        tmp_path / ".opencode" / "skills" / "pb-build" / "references" / "implementer_prompt.md"
    ).exists()

    # Gemini files
    assert (tmp_path / ".gemini" / "commands" / "pb-init.toml").exists()
    assert (tmp_path / ".gemini" / "commands" / "pb-plan.toml").exists()
    assert (tmp_path / ".gemini" / "commands" / "pb-refine.toml").exists()
    assert (tmp_path / ".gemini" / "commands" / "pb-build.toml").exists()

    # Codex files
    assert (tmp_path / ".codex" / "prompts" / "pb-init.md").exists()
    assert (tmp_path / ".codex" / "prompts" / "pb-plan.md").exists()
    assert (tmp_path / ".codex" / "prompts" / "pb-refine.md").exists()
    assert (tmp_path / ".codex" / "prompts" / "pb-build.md").exists()


def test_e2e_claude_frontmatter(tmp_path, monkeypatch, runner):
    """Verify Claude SKILL.md files have YAML frontmatter."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "claude"])

    for skill in ["pb-init", "pb-plan", "pb-refine", "pb-build"]:
        content = (tmp_path / ".claude" / "skills" / skill / "SKILL.md").read_text()
        assert content.startswith("---\n"), f"Claude {skill} missing frontmatter"
        assert "name:" in content, f"Claude {skill} missing name: in frontmatter"
        assert "description:" in content, f"Claude {skill} missing description: in frontmatter"


def test_e2e_opencode_frontmatter(tmp_path, monkeypatch, runner):
    """Verify OpenCode SKILL.md files have YAML frontmatter."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "opencode"])

    for skill in ["pb-init", "pb-plan", "pb-refine", "pb-build"]:
        content = (tmp_path / ".opencode" / "skills" / skill / "SKILL.md").read_text()
        assert content.startswith("---\n"), f"OpenCode {skill} missing frontmatter"
        assert "name:" in content, f"OpenCode {skill} missing name: in frontmatter"
        assert "description:" in content, f"OpenCode {skill} missing description: in frontmatter"


def test_e2e_copilot_no_frontmatter(tmp_path, monkeypatch, runner):
    """Verify Copilot prompt files do NOT have YAML frontmatter."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "copilot"])

    for prompt in ["pb-init", "pb-plan", "pb-refine", "pb-build"]:
        content = (tmp_path / ".github" / "prompts" / f"{prompt}.prompt.md").read_text()
        assert not content.startswith("---"), f"Copilot {prompt} should not have frontmatter"


def test_e2e_gemini_toml_format(tmp_path, monkeypatch, runner):
    """Verify Gemini command files are TOML with description and prompt fields."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "gemini"])

    for command in ["pb-init", "pb-plan", "pb-refine", "pb-build"]:
        content = (tmp_path / ".gemini" / "commands" / f"{command}.toml").read_text()
        assert content.startswith('description = "'), f"Gemini {command} missing description field"
        assert "\nprompt = '''\n" in content, f"Gemini {command} missing prompt field"


def test_e2e_codex_frontmatter(tmp_path, monkeypatch, runner):
    """Verify Codex prompt files have YAML frontmatter."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "codex"])

    for prompt in ["pb-init", "pb-plan", "pb-refine", "pb-build"]:
        content = (tmp_path / ".codex" / "prompts" / f"{prompt}.md").read_text()
        assert content.startswith("---\n"), f"Codex {prompt} missing frontmatter"
        assert "description:" in content, f"Codex {prompt} missing description in frontmatter"


def test_e2e_references_exist(tmp_path, monkeypatch, runner):
    """Verify reference files exist and are non-empty for all skill-based platforms."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "all"])

    expected_refs = {
        ".claude/skills/pb-plan/references/design_template.md",
        ".claude/skills/pb-plan/references/tasks_template.md",
        ".claude/skills/pb-build/references/implementer_prompt.md",
        ".opencode/skills/pb-plan/references/design_template.md",
        ".opencode/skills/pb-plan/references/tasks_template.md",
        ".opencode/skills/pb-build/references/implementer_prompt.md",
    }
    for ref in expected_refs:
        ref_path = tmp_path / ref
        assert ref_path.exists(), f"Missing reference: {ref}"
        assert ref_path.stat().st_size > 0, f"Empty reference: {ref}"


def test_e2e_idempotent_rerun(tmp_path, monkeypatch, runner):
    """Verify running init twice without --force skips existing files."""
    monkeypatch.chdir(tmp_path)

    # First run
    result1 = runner.invoke(main, ["init", "--ai", "claude"])
    assert result1.exit_code == 0, result1.output

    # Second run without --force
    result2 = runner.invoke(main, ["init", "--ai", "claude"])
    assert result2.exit_code == 0, result2.output
    # Skipping messages go via print(); check combined output
    assert "Skipping" in result2.output or "skip" in result2.output.lower()


def test_e2e_force_rerun(tmp_path, monkeypatch, runner):
    """Verify --force overwrites existing files."""
    monkeypatch.chdir(tmp_path)

    # First run
    runner.invoke(main, ["init", "--ai", "claude"])

    # Modify a file
    skill_path = tmp_path / ".claude" / "skills" / "pb-init" / "SKILL.md"
    skill_path.write_text("modified content")

    # Rerun with --force
    result = runner.invoke(main, ["init", "--ai", "claude", "--force"])
    assert result.exit_code == 0, result.output

    # Verify file was overwritten (not "modified content")
    content = skill_path.read_text()
    assert content != "modified content"
    assert content.startswith("---\n")


def test_e2e_output_message(tmp_path, monkeypatch, runner):
    """Verify CLI output contains expected success message."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "all"])
    assert result.exit_code == 0
    assert "installed successfully" in result.output.lower()


def test_e2e_copilot_no_references_dir(tmp_path, monkeypatch, runner):
    """Verify Copilot platform does not create references directories."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "copilot"])

    # Copilot uses flat prompt files; no references/ subdirs should exist
    prompts_dir = tmp_path / ".github" / "prompts"
    assert prompts_dir.exists()
    for child in prompts_dir.iterdir():
        assert child.is_file(), f"Unexpected directory in Copilot prompts: {child}"


def test_e2e_gemini_and_codex_no_references_dir(tmp_path, monkeypatch, runner):
    """Verify Gemini/Codex platforms do not create references directories."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(main, ["init", "--ai", "all"])

    for directory in [
        tmp_path / ".gemini" / "commands",
        tmp_path / ".codex" / "prompts",
    ]:
        assert directory.exists()
        for child in directory.iterdir():
            assert child.is_file(), f"Unexpected directory in prompt folder: {child}"
