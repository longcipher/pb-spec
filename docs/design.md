# Design Document: pb-spec (Plan-Build Spec)

| Metadata | Details |
| :--- | :--- |
| **Author** | pb-spec maintainers |
| **Status** | Synced with implementation |
| **Last Updated** | 2026-02-19 |

## 1. Executive Summary

`pb-spec` is a Python CLI that installs a consistent spec-driven workflow into multiple AI coding tools. It standardizes an end-to-end loop:

1. `/pb-init` builds project context (`AGENTS.md`)
2. `/pb-plan` generates `design.md` + `tasks.md`
3. `/pb-refine` iterates plans based on feedback or DCR
4. `/pb-build` executes tasks through TDD subagent orchestration

The tool is intentionally lightweight: platform-specific behavior is isolated in adapters, while skill/prompt source-of-truth stays in repository templates.

## 2. Goals and Scope

### 2.1 Goals

1. Provide one `init` command to install the same workflow across tools.
2. Keep prompts/skills deterministic and versioned in git.
3. Preserve idempotent installation behavior (`--force` only when needed).
4. Keep platform adapters minimal and composable.

### 2.2 Non-goals

1. Running model APIs directly.
2. Managing remote project state.
3. Replacing tool-native orchestration/runtime.

## 3. Current Architecture

```text
pb-spec/
├── src/pb_spec/
│   ├── cli.py
│   ├── commands/
│   │   ├── init.py
│   │   ├── update.py
│   │   └── version.py
│   ├── platforms/
│   │   ├── base.py
│   │   ├── claude.py
│   │   ├── copilot.py
│   │   ├── opencode.py
│   │   ├── gemini.py
│   │   └── codex.py
│   └── templates/
│       ├── skills/
│       │   ├── pb-init/
│       │   ├── pb-plan/
│       │   ├── pb-refine/
│       │   └── pb-build/
│       └── prompts/
│           ├── pb-init.prompt.md
│           ├── pb-plan.prompt.md
│           ├── pb-refine.prompt.md
│           └── pb-build.prompt.md
├── tests/
└── README.md
```

## 4. Platform Matrix

| Platform | Installed Path | Render Format | Reference Files |
| :--- | :--- | :--- | :--- |
| Claude Code | `.claude/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown skill | Yes (`references/`) |
| VS Code Copilot | `.github/prompts/pb-<name>.prompt.md` | Markdown prompt | No |
| OpenCode | `.opencode/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown skill | Yes (`references/`) |
| Gemini CLI | `.gemini/commands/pb-<name>.toml` | TOML command (`description`, `prompt`) | No |
| Codex | `.codex/prompts/pb-<name>.md` | YAML frontmatter + Markdown prompt | No |

Notes:

- Skills (`pb-init`, `pb-plan`, `pb-refine`, `pb-build`) are common semantic units.
- Prompt-oriented platforms consume templates from `templates/prompts`.
- Skill-oriented platforms consume templates from `templates/skills` and optional `references/`.

## 5. Installation Flow (`pb-spec init`)

1. Parse `--ai` target (`claude|copilot|opencode|gemini|codex|all`).
2. Resolve to concrete platform list.
3. For each skill name:
   - compute target path
   - skip if exists and `--force` not set
   - load template and platform-render content
   - write content with UTF-8 encoding
   - install references when platform supports references

Behavior guarantees:

- Idempotent by default.
- Explicit overwrite only with `--force`.
- Printed install paths are relative to cwd.

## 6. Prompt/Skill Design Pattern

### 6.1 pb-init

Audits the repository and produces a **minimal** `AGENTS.md` containing only information that agents cannot discover from the codebase itself. Applies a strict three-part filter: each entry must be (1) not inferrable from code, (2) operationally decisive, and (3) not guessable from industry conventions. The ideal AGENTS.md is empty — every entry represents a codebase smell that should eventually be fixed at the root cause. Re-runs audit existing entries and flag any that are now discoverable.

### 6.2 pb-plan

Creates `specs/<YYYY-MM-DD-NN-feature>/design.md` and `tasks.md` in one shot. It emphasizes live codebase analysis and verification-first planning.

### 6.3 pb-refine

Applies incremental changes to existing spec docs without full regeneration. It logs revisions and cascades design updates into tasks.

### 6.4 pb-build

Implements tasks sequentially with strict TDD and context hygiene. Failure recovery uses task-local rollback semantics to avoid destructive workspace-wide resets.

## 7. Reliability and Safety Rules

1. No blind edits in generated workflows.
2. Mandatory red-green-refactor sequence for implementation tasks.
3. Minimal context handoff between subagents.
4. File-scoped rollback guidance for failed task attempts.
5. Per-task verification criteria and explicit completion status tracking in `tasks.md`.

## 8. Testing and Verification

Current automated coverage validates:

1. CLI command shape and behavior (`init`, `version`, `update`).
2. Platform path/render behavior across all supported platforms.
3. End-to-end structure generation for `--ai all`.
4. Template loading and safety regressions (e.g., malformed wrappers, destructive command checks).

Primary verification commands:

```bash
uv run pytest -q
uv run ruff check .
```

## 9. Known Constraints and Follow-ups

1. Platform-specific runtime semantics can evolve; adapter paths/formats should be periodically re-validated against official tool docs.
2. Prompt/skill content parity is maintained by template discipline, not code generation.
3. Additional platforms should be added only through new adapter classes and test expansion, not conditional sprawl in shared install logic.
