---
name: pb-init
description: Audit the current project and generate or update AGENTS.md with architecture snapshot, project structure, and key files. Use when setting up a new project, onboarding to an existing repo, or refreshing project context for AI coding agents.
---

# pb-init

Audit the project and generate/update `AGENTS.md` at project root. No clarifying questions — run analysis and produce output directly.

## Workflow

### 1. Detect language, framework, build tool

Scan root for config files (`pyproject.toml`, `Cargo.toml`, `package.json`, `go.mod`, etc.). Infer framework from dependencies. Infer test command from config or conventions.

### 2. Generate directory tree

Preferred: `git ls-files --others --cached --exclude-standard | head -200`, summarize into tree.
Fallback: traverse with adaptive depth (3 default; auto-expand `src/`, `lib/`, `app/`, `packages/`, `cmd/`, `internal/`, `pkg/` to depth 6; stop >20 children).

Exclude: `.git/`, `node_modules/`, `__pycache__/`, `target/`, `.venv/`, `dist/`, `build/`, hidden dirs except `.github/`.

### 3. Identify key files

Entry point, config, test directory, CI, docs.

### 4. Capture architecture decisions

Search project for explicit architecture decisions grounded in evidence (from `AGENTS.md`, `README.md`, `docs/`, source modules). Record: established patterns, DI boundaries, error handling conventions, state/workflow modeling, external dependency access, known TODOs. If none detected, write `No explicit architecture decisions detected.`

### 5. Detect active specs

Check `specs/` directory. For each spec: count completed vs total task checkboxes in `tasks.md` → status. Read `design.md` metadata `Status` field. Report last modified date.

### 6. Write AGENTS.md (managed block)

Use marker-based managed block. Do NOT parse or rewrite user sections.

Markers:

- `<!-- BEGIN PB-INIT MANAGED BLOCK -->`
- `<!-- END PB-INIT MANAGED BLOCK -->`

Merge: if no `AGENTS.md` → create with managed block. If markers present → replace only the block. If markers absent → append at end. Never delete/reorder existing content outside the block.

Managed block contains: Project Overview, Project Structure, Key Files, Architecture Decision Snapshot, Active Specs.

## Constraints

- Read-only analysis. Do NOT modify source code, configs, or tests.
- Only write `AGENTS.md`.
- Non-destructive merge.
- No interactive questions. Single pass.

## Edge Cases

- No config files → Language/Framework/Build Tool = "Unknown". Still generate tree and key files.
- Multiple languages → primary first (by code volume), note others.
- Monorepo → list each workspace member.
- Empty project → minimal AGENTS.md with "Empty project — no source files detected".
- `specs/` absent → "No active specs found."
- Legacy `AGENTS.md` without markers → append managed block, preserve all existing text.

---

name: pb-init

## description: Audit the current project and generate or update AGENTS.md with architecture snapshot, project structure, and key files. Use when setting up a new project, onboarding to an existing repo, or refreshing project context for AI coding agents
