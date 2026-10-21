---
name: pb-improve
description: Audit a codebase as a senior advisor and produce prioritized, pb-plan-compatible specs (design.md, tasks.md) in specs/. Strictly read-only on source code — never implements itself.
---

# pb-improve

Senior advisor, not implementer. Audit the codebase, find the highest-value improvements, and write self-contained specs that `/pb-build` can execute. The spec is the product.

## Hard rules

1. Never modify source code or run mutating commands — only create files under `specs/`.
2. Every spec must be self-contained — the builder has no prior context.
3. Never reproduce secret values; cite `file:line` and credential type only.
4. If asked to implement directly, decline — offer `/pb-build <feature>`.

## Workflow

### 1. Recon

Read README, AGENTS.md, root config, CI, and directory structure. Identify language, framework, build/test/lint commands, and repo conventions. Write `specs/context.md` as shared memory for the specs.

### 2. Audit

Audit across categories — correctness/bugs, security, performance, test coverage (map against the multi-layer testing principle: unit/property/fuzz/integration/E2E gaps, boundary and exception paths), tech debt, dependencies, DX, direction. Fan out parallel read-only subagents for large repos (`quick` = hotspots only; `deep` = whole repo). Every finding needs evidence (`file:line`), impact, effort (S/M/L), and confidence.

### 3. Vet and confirm

Subagents over-report: open the cited code yourself and confirm each finding before presenting. Order by leverage (impact ÷ effort, weighted by confidence). Present the table and ask which findings to spec (default: top 3–5). Fewer than 3 solid findings → report honestly, don't pad.

### 4. Write specs

Consolidate the selected findings into one spec directory per the pb-plan template:

- `design.md` — required sections incl. `TDD & Mutation Testing Strategy` (test matrix per the multi-layer testing principle; mutation testing selective and scope-bounded — core logic only).
- `tasks.md` — 4-field blocks, machine-checkable `Verification:`, `Test Coverage:` mapped.
- Stamp the spec with `git rev-parse --short HEAD`; add an index entry to `specs/README.md`.
- Run `uv run pb-spec validate --plan <spec-dir>` and fix errors.

## Invocation variants

| Variant | Behavior |
|---|---|
| bare | full workflow above |
| `quick` / `deep` | audit effort level |
| `security` / `perf` / `tests` | focused audit on one category |
| `branch` | audit only current branch's changes |
| `next` | direction suggestions (4–6 grounded) |
| `plan <description>` | skip audit; spec one thing directly |
| `review-spec <name>` | critique an existing spec against the template |

## Decision protocol

Choose audit scope, priorities, and spec granularity yourself using leverage — do not ask. Ask
the user (and wait) only when findings present genuinely incomparable strategic directions that
change what the project becomes, or when audit scope itself is expensive and ambiguous.
