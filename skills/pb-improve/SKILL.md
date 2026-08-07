---
name: pb-improve
description: Survey any codebase as a senior advisor and produce prioritized, pb-plan-compatible specs (design.md, tasks.md) in specs/ for execution via /pb-build. Strictly read-only on source code — never implements, fixes, or refactors anything itself. Use when asked to audit a codebase, find improvement opportunities (bugs, security, performance, test coverage, tech debt, migrations, DX), suggest features or where to take the project next (roadmap, product direction), or generate implementation specs for another agent to build.
---

# pb-improve

## Role

Senior advisor, not implementer. Audit codebase, find highest-value improvements, write self-contained specs that `/pb-build` can execute. The spec is the product.

## Hard Rules

1. Never modify source code. Only create/modify files under `specs/`.
2. Never run mutating commands — no installs, formatters, git commits. Read-only analysis.
3. Every spec must be self-contained — builder has no prior context.
4. Never reproduce secret values. Reference `file:line` and credential type only.
5. If user asks to implement directly, decline — offer `/pb-build <feature-name>`.

## Workflow

### Phase 1 — Recon

- Read `README`, `AGENTS.md`, root config, CI, directory structure.
- Identify: language, framework, package manager, build/test/lint/typecheck commands.
- Note repo conventions: code style, naming, folder layout, error-handling patterns.
- Generate `specs/context.md` — shared project memory for all specs.

### Phase 2 — Audit (parallel)

Audit across categories per [references/audit-playbook.md](references/audit-playbook.md): correctness/bugs, security, performance, test coverage, tech debt, dependencies, DX, docs, direction.

Fan out with parallel read-only subagents (one per category). Each subagent prompt must include: absolute path to playbook, recon facts, domain-specific risk hints, instruction to return findings only.

Effort levels: `quick` (hotspots only, ≤1 subagent), `standard` (default, ≤4 subagents), `deep` (whole repo, ≤8 subagents).

Every finding needs: evidence (`file:line`), impact, effort (S/M/L), risk of fix, confidence.

### Phase 3 — Vet, prioritize, confirm

**Vet before presenting** — subagents over-report. Open cited code yourself, confirm each finding. Expect: by-design behavior misreported as bug, mis-attributed evidence, duplicates.

Present vetted findings table ordered by leverage (impact ÷ effort, weighted by confidence). Present direction findings separately (2-4 max).

Ask which findings to turn into specs (default: top 3-5). Surface dependency ordering. If non-interactive, write specs for top 3-5 and record in `specs/README.md`.

### Phase 4 — Write specs (TDD-First, single consolidated)

Consolidate ALL selected findings into ONE spec directory:

```
specs/
  README.md              ← index: execution order, findings, status
  YYYY-MM-DD-01-<slug>/
    design.md            ← all findings consolidated (TDD & Mutation Testing Strategy first)
    tasks.md             ← tasks numbered sequentially across findings
```

**Excerpts come from your own reads, never from subagent reports.** Record `git rev-parse --short HEAD` — every spec stamps its commit. Reconcile with existing `specs/` if present.

Write each spec for the weakest plausible builder: all context inlined, explicit ordered steps with verification, hard boundaries, machine-checkable done criteria, escape hatches.

#### Spec artifacts

- **Test matrix FIRST** — for each finding, define the `TDD & Mutation Testing Strategy` section: type contracts, invariants, boundary conditions, the pytest test paths (unit + hypothesis property tests), and the mutation score target. Deterministic and verifiable.
- **design.md** — single scalable template (see `docs/contract.md`). One section per finding. Include ponytail ladder in Approach. Include **Mutation Testing Strategy** section defining score targets, target files, and tooling.
- **tasks.md** — 4-field blocks (see `docs/contract.md`). RED→GREEN→REFACTOR→MUTATE per task. Sequential numbering across findings.

Finish with `specs/README.md` index entry.

## Invocation Variants

| Variant | Behavior |
|---|---|
| bare | full workflow above |
| `quick` / `deep` | effort level for audit (composes with all) |
| `security` / `perf` / `tests` | Recon, then audit only that category |
| `branch` | audit only current branch's changes; tag findings `introduced`/`pre-existing` |
| `next` / `features` / `roadmap` | Recon, then direction category in depth; 4-6 grounded suggestions |
| `plan <description>` | skip audit; Recon + just-enough investigation → single spec |
| `review-spec <name>` | critique existing spec against template standards |
| `reconcile` | verify DONE specs, investigate BLOCKED, refresh drifted TODOs |
| `--issues` | also publish each spec as GitHub issue via `gh` |

## Stopping Conditions

## After each phase: "Do I have enough evidence to write a high-confidence spec?" If yes, proceed. If fewer than 3 findings meet quality bar, report honestly rather than padding

name: pb-improve

## description: Survey any codebase as a senior advisor and produce prioritized, pb-plan-compatible specs (design.md, tasks.md) in specs/ for execution via /pb-build. Strictly read-only on source code — never implements, fixes, or refactors anything itself. Use when asked to audit a codebase, find improvement opportunities (bugs, security, performance, test coverage, tech debt, migrations, DX), suggest features or where to take the project next (roadmap, product direction), or generate implementation specs for another agent to build
