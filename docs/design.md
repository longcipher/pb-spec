# Design Document: pb-spec (Plan-Build Spec)

| Metadata | Details |
| :--- | :--- |
| **Author** | pb-spec maintainers |
| **Status** | Synced with implementation |
| **Last Updated** | 2026-03-09 |

## 1. Executive Summary

`pb-spec` is a Python CLI that installs a consistent spec-driven workflow into multiple AI coding tools. It standardizes an end-to-end loop:

1. `/pb-init` builds project context (`AGENTS.md`)
2. `/pb-plan` generates `design.md` + `tasks.md` + `features/*.feature`
3. `/pb-refine` iterates plans based on feedback or DCR, including Gherkin scenario updates
4. `/pb-build` executes tasks through a BDD outer loop and a TDD inner loop

The tool is intentionally lightweight: platform-specific behavior is isolated in adapters, while skill/prompt source-of-truth stays in repository templates. The strengthened workflow contract still uses the same commands and the same markdown artifacts. No separate validator command or alternate schema language was added.

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
4. Introducing a new workflow command or side-channel validator for spec contracts.
5. Replacing markdown workflow artifacts with YAML or JSON schemas.

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

Audits the repository and updates a **managed snapshot block** inside `AGENTS.md`. The generated block captures current project context, key file locations, active specs, and an `Architecture Decision Snapshot` that later agents inherit. Re-runs replace only the managed block and preserve all user-authored content outside it.

### 6.2 pb-plan

Creates `specs/<YYYY-MM-DD-NN-feature>/design.md`, `tasks.md`, and `features/*.feature` in one shot. It emphasizes live codebase analysis, Gherkin-first behavior modeling, verification-first planning, template-identity cleanup for scaffolded repos, and risk-based advanced test planning.

Those markdown artifacts are the workflow's contract carrier. The strengthened contract keeps the current format, but requires explicit design sections, task fields, scenario coverage, verification fields, and state markers so downstream stages do not need to reconstruct missing structure from prose.

### 6.3 pb-refine

Applies incremental changes to existing spec docs without full regeneration. It logs revisions and cascades `.feature`, design, and task updates together.

`pb-refine` now validates the existing `🛑 Build Blocked` and `🔄 Design Change Request` markdown packets before editing spec artifacts. Required sections such as failure evidence, impact, and suggested change must be present; the refiner does not guess missing packet details.

### 6.4 pb-build

Implements tasks sequentially with strict context hygiene and an outside-in double loop. The BDD outer loop proves the scenario fails first and then passes, while the TDD inner loop drives the underlying implementation. Failure recovery uses task-local rollback semantics to avoid destructive workspace-wide resets.

Before task execution begins, `pb-build` performs a mandatory Phase 0 validation gate over the existing markdown contract: required design sections, required `Task X.Y` fields, and at least one feature scenario. If any contract item is missing, the workflow stops before spawning implementation work. During execution, the builder still uses explicit task status transitions. The current static validator is narrower: it enforces allowed status values and blocks `DONE` tasks that still leave required verification evidence unchecked, rather than reconstructing prior state history from a single markdown snapshot.

## 7. Reliability and Safety Rules

1. No blind edits in generated workflows.
2. Mandatory BDD outer loop for `BDD+TDD` tasks and red-green-refactor inner loop for implementation work.
3. Minimal context handoff between subagents.
4. File-scoped rollback guidance for failed task attempts.
5. Per-task verification criteria, scenario coverage mapping, and explicit completion status tracking in `tasks.md`.
6. Managed `AGENTS.md` snapshot updates instead of whole-file rewrites.
7. Mandatory markdown contract validation before build execution.
8. Required packet validation for blocked-build and DCR refine handoffs.

## 8. Testing and Verification

Current automated coverage validates:

1. CLI command shape and behavior (`init`, `version`, `update`).
2. Platform path/render behavior across all supported platforms.
3. End-to-end structure generation for `--ai all`.
4. Template loading and safety regressions (e.g., malformed wrappers, destructive command checks).
5. Prompt/skill parity checks for workflow-critical instructions and architecture constraints.

Primary verification commands:

```bash
uv run pytest -q
uv run ruff check .
uv run behave features/workflow_type_contracts.feature
just lint
just test
just bdd
just test-all
```

## 9. Known Constraints and Follow-ups

1. Platform-specific runtime semantics can evolve; adapter paths/formats should be periodically re-validated against official tool docs.
2. Prompt/skill content parity is maintained by template discipline, and parity is guarded by regression tests for workflow-critical instructions.
3. Additional platforms should be added only through new adapter classes and test expansion, not conditional sprawl in shared install logic.
