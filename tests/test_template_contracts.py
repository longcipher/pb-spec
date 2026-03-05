"""Contract tests for markdown templates and rendered frontmatter."""

import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from pb_spec.cli import main

SKILL_NAMES = ("pb-init", "pb-plan", "pb-refine", "pb-build")
TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "src" / "pb_spec" / "templates"
FENCE_RE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$")
BARE_ANGLE_PLACEHOLDER_RE = re.compile(r'^\s*<[^!/?][^>="\'`]*>\s*$')


def _template_markdown_files() -> list[Path]:
    return sorted(TEMPLATES_ROOT.rglob("*.md"))


def _collect_fence_issues(content: str) -> list[str]:
    issues: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    open_line = 0

    for line_no, line in enumerate(content.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if not match:
            continue

        fence = match.group(1)
        trailing = match.group(2)
        char = fence[0]
        length = len(fence)

        if not in_fence:
            in_fence = True
            fence_char = char
            fence_len = length
            open_line = line_no
            continue

        if char == fence_char and length >= fence_len:
            # CommonMark closing fences only allow optional spaces after the fence.
            if trailing.strip():
                issues.append(f"line {line_no}: closing fence has trailing text: {line.strip()}")
                continue
            in_fence = False
            fence_char = ""
            fence_len = 0
            open_line = 0

    if in_fence:
        issues.append(f"unclosed fence opened at line {open_line}")

    return issues


def _collect_bare_angle_placeholders_outside_fences(content: str) -> list[tuple[int, str]]:
    placeholders: list[tuple[int, str]] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line_no, line in enumerate(content.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if match:
            fence = match.group(1)
            trailing = match.group(2)
            char = fence[0]
            length = len(fence)
            if not in_fence:
                in_fence = True
                fence_char = char
                fence_len = length
                continue
            if char == fence_char and length >= fence_len and not trailing.strip():
                in_fence = False
                fence_char = ""
                fence_len = 0
                continue

        if in_fence:
            continue

        stripped = line.strip()
        if BARE_ANGLE_PLACEHOLDER_RE.match(stripped):
            placeholders.append((line_no, stripped))

    return placeholders


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    lines = content.splitlines()
    assert lines and lines[0] == "---", "frontmatter must start with ---"

    frontmatter: list[str] = []
    closing_index = -1
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
        frontmatter.append(lines[index])

    assert closing_index != -1, "frontmatter closing marker --- is missing"

    parsed: dict[str, str] = {}
    for line in frontmatter:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        parsed[key.strip()] = value.strip().strip('"').strip("'")

    body = "\n".join(lines[closing_index + 1 :]).strip()
    return parsed, body


def test_templates_have_balanced_markdown_fences():
    failures: list[str] = []
    for path in _template_markdown_files():
        issues = _collect_fence_issues(path.read_text(encoding="utf-8"))
        if issues:
            rel = path.relative_to(TEMPLATES_ROOT.parents[2])
            failures.extend(f"{rel}: {issue}" for issue in issues)

    assert not failures, "\n".join(failures)


def test_templates_do_not_use_bare_angle_placeholders_outside_code_fences():
    failures: list[str] = []
    for path in _template_markdown_files():
        placeholders = _collect_bare_angle_placeholders_outside_fences(
            path.read_text(encoding="utf-8")
        )
        if placeholders:
            rel = path.relative_to(TEMPLATES_ROOT.parents[2])
            for line_no, placeholder in placeholders:
                failures.append(f"{rel}:{line_no}: bare placeholder {placeholder}")

    assert not failures, "\n".join(failures)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_claude_rendered_skills_frontmatter_contract(tmp_path, monkeypatch, runner):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "claude"])
    assert result.exit_code == 0, result.output

    for skill in SKILL_NAMES:
        content = (tmp_path / ".claude" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        frontmatter, body = _parse_frontmatter(content)
        assert frontmatter.get("name") == skill
        assert frontmatter.get("description"), f"missing description for {skill}"
        assert body, f"empty body for {skill}"


def test_opencode_rendered_skills_frontmatter_contract(tmp_path, monkeypatch, runner):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "opencode"])
    assert result.exit_code == 0, result.output

    for skill in SKILL_NAMES:
        content = (tmp_path / ".opencode" / "skills" / skill / "SKILL.md").read_text(
            encoding="utf-8"
        )
        frontmatter, body = _parse_frontmatter(content)
        assert frontmatter.get("name") == skill
        assert frontmatter.get("description"), f"missing description for {skill}"
        assert body, f"empty body for {skill}"


def test_codex_rendered_prompts_frontmatter_contract(tmp_path, monkeypatch, runner):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init", "--ai", "codex"])
    assert result.exit_code == 0, result.output

    for skill in SKILL_NAMES:
        content = (tmp_path / ".codex" / "prompts" / f"{skill}.md").read_text(encoding="utf-8")
        frontmatter, body = _parse_frontmatter(content)
        assert frontmatter.get("description"), f"missing description for {skill}"
        assert body, f"empty body for {skill}"
