# pb-spec — Plan-Build Spec

[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/longcipher/pb-spec)
[![Context7](https://img.shields.io/badge/Website-context7.com-blue)](https://context7.com/longcipher/pb-spec)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pb-spec.svg)](https://pypi.org/project/pb-spec/)

![pb-spec](https://socialify.git.ci/longcipher/pb-spec/image?font=Source+Code+Pro&language=1&name=1&owner=1&pattern=Circuit+Board&theme=Auto)

pb-spec is a set of [Agent Skills Specification](https://agentskills.io) compliant AI Coding assistant workflow skill packages. It turns natural-language requirements into well-architected, strictly tested code via **strict TDD + selective, scope-bounded mutation testing**.

## Design Philosophy

Five skills, no ceremony. Modern models are strong: pb-spec adds the few things they still miss — a spec that stays the source of truth, a strict Red → Green → Refactor → Mutate loop, multi-layer test coverage, and goal-driven execution that doesn't stop until the objective is verifiably achieved.

| Principle | Description |
|---|---|
| **Spec Is Source of Truth** | `design.md` + `tasks.md` carry type contracts, invariants, and the test matrix. Builders don't improvise — ambiguity routes back via DCR. |
| **TDD-First** | No production code without a failing test first. |
| **Multi-Layer Testing** | Unit + property (hypothesis/proptest) + fuzz + integration + E2E — covering all business scenarios, all branches, boundary and exception paths. |
| **Selective Mutation-Gating** | Mutation testing only where subtle correctness risk lives (parsers, state machines, boundary math), only on changed files. Surviving mutants are test failures. |
| **Autonomy with an Escape Hatch** | Agents pick the best option themselves. They ask the user — and wait — only for genuinely incomparable, expensive-to-undo choices. |
| **Goal-Driven Mode** | `/pb-goal` locks one objective, persists state to disk, and keeps working until evidence proves completion. No token budget. |

## Installation

No manual file configuration needed. As long as your AI assistant supports the standard Agent Skills specification (Claude Code, Cursor, GitHub Copilot, OpenCode, etc.), you can install with one command.

Run in your project root:

```bash
# Install all pb-spec workflow skills at once
npx skills add longcipher/pb-spec

# Or install only the ones you need
npx skills add longcipher/pb-spec --skill pb-plan
npx skills add longcipher/pb-spec --skill pb-build
npx skills add longcipher/pb-spec --skill pb-refine
npx skills add longcipher/pb-spec --skill pb-improve
npx skills add longcipher/pb-spec --skill pb-goal
```

*(After installation, skills will be placed in `.agents/skills/` or the compatible local directory for your environment, and automatically indexed by your AI.)*

## Skills Overview

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-plan` | `/pb-plan <requirement>` | `specs/<spec-dir>/design.md` + `tasks.md` | Design + multi-layer test matrix + DAG task breakdown |
| `pb-build` | `/pb-build <feature>` | Code + tests | Strict TDD loop; selective, scope-bounded mutation testing; DCR escalation |
| `pb-refine` | `/pb-refine <feature>` | Revised spec files | Apply feedback or Design Change Requests to an existing spec |
| `pb-improve` | `/pb-improve` | `specs/<spec>/` + `specs/context.md` | Codebase audit → prioritized findings → pb-plan-compatible specs |
| `pb-goal` | `/pb-goal <objective>` | `.pb-goal.md` + shipped work | Goal-driven mode: persist state, keep working, evidence-driven completion |

## Workflow

```text
/pb-plan → [/pb-refine] → /pb-build
           ↘
           /pb-improve → specs/ → /pb-build
           ↘
           /pb-goal <objective>   # free-form, runs to completion
```

### 1. `/pb-plan <requirement>` — Design & Task Planning

Produces a complete feature spec:

```text
specs/<YYYY-MM-DD-NO-feature-name>/
├── design.md    # 5 required sections
└── tasks.md     # 4-field task blocks with DAG metadata
```

Key capabilities:

- **Type-First**: `design.md` carries a `TDD & Mutation Testing Strategy` section with type contracts, invariants, boundary conditions, and the test matrix.
- **Multi-layer test matrix**: unit + property (hypothesis) + fuzz + integration + E2E tests covering all scenarios, branches, and boundary/exception paths.
- **Selective mutation strategy**: the spec declares which files/functions get mutated (core logic only), the score target (default ≥ 85%), and the tool. Infra/trivial code is mutation-exempt.
- **4-field task schema**: `Context:`, `Verification:`, `Status:`, `Test Coverage:` with `TaskID`/`DependsOn` DAG metadata.
- **Decision protocol**: picks the best option and records it as an assumption; asks the user — and waits — only when options are genuinely incomparable and the choice is expensive to undo.

### 2. `/pb-refine <feature-name>` — Design Iteration (Optional)

Reads user feedback or Design Change Requests and updates `design.md` and `tasks.md` with precise, incremental edits. Maintains a revision history, resets invalidated tasks, and never silently modifies completed work. Validates `🛑 Build Blocked` and `🔄 Design Change Request` packets (3 fields each: `Reason`, `Requested Change`, `Impact`).

### 3. `/pb-build <feature-name>` — Strict TDD Execution

Executes tasks in dependency order (independent tasks may fan out to parallel subagents; same-file tasks never share a wave):

```text
Red (failing test) → Green (minimum code) → Refactor → Mutate (only core logic, only changed files)
Task failure: retry → root-cause analysis → Build Blocked packet → /pb-refine
```

Key principles: evidence before claims (fresh command output, pasted, exit code checked), no mutation runs for infra/trivial/UI code, surviving mutants on changed code are test failures, DCR instead of silent design changes.

### 4. `/pb-improve` — Codebase Audit & Plan Generation

Audits any codebase and writes pb-plan-compatible specs for other agents to execute. Never modifies source code — only produces specs under `specs/`.

```text
/pb-improve                        full audit → prioritized findings → specs
/pb-improve quick                  cheap pass: hotspots, top findings only
/pb-improve deep                   exhaustive: whole repo
/pb-improve security               focused audit (also: perf, tests, ...)
/pb-improve branch                 audit only what the current branch changes
/pb-improve next                   feature suggestions — where to take the project
/pb-improve plan <description>     skip the audit, spec one thing
/pb-improve review-spec <feature>  critique and tighten an existing spec
```

### 5. `/pb-goal <objective>` — Goal-Driven Mode

For large objectives meant to run to completion without hand-holding (inspired by [goal mode](https://github.com/prevalentWare/opencode-goal-plugin)):

- **One explicit goal** with acceptance criteria, persisted to `.pb-goal.md` so state survives compaction and session resume.
- **Keeps working**: at the end of every turn it continues the next unblocked step instead of asking "shall I continue?". No token/time budget.
- **Evidence-driven completion**: `COMPLETE` only when every criterion has fresh verifiable evidence (command output, passing tests, real artifacts). Criteria are never silently weakened.
- **Stops only on real blockers**: a genuinely ambiguous criterion with no best interpretation, a missing external dependency, or a user interrupt. Everything else is work to push through — on no progress, change the approach, don't repeat it.

## Strict TDD + Mutation Testing

The core loop replaces behavior-driven layers with a single, strict, typed pipeline:

```text
specs/design.md (Type Contracts + Test Matrix) → tasks.md → /pb-build (RED → GREEN → REFACTOR → MUTATE)
```

**Multi-layer testing** — all business scenarios, all branches, boundary and exception paths, via unit tests, property tests (hypothesis/proptest), fuzz tests for untrusted input, integration tests for cross-module behavior, and E2E tests for user-visible flows.

**Mutation testing is selective and scope-bounded** — it is very slow:

- Run it only for core logic with subtle correctness risk (parsers, state machines, crypto/boundary math, concurrency), or when the spec marks it required.
- Mutate only files changed by the current task — `pb-spec mutate --against <base>` or the diff-based script. Never whole-repo runs.
- Skip it for infra, config, docs, trivial accessors, and UI code.
- Surviving mutants on changed code = test failure: strengthen assertions until killed, or record a justified exemption.

```bash
# The whole gate in one command
pb-spec verify

# Or individually
pb-spec test           # pytest, parallel (-n auto), optional --coverage
pb-spec mutate         # incremental mutation on git-changed files only
```

### CLI Commands

| Command | Purpose |
|---|---|
| `pb-spec validate --plan/--build/--task` | Validate workflow artifacts and code quality |
| `pb-spec test` | Run the strict TDD suite (pytest-xdist parallel; `--coverage` for the coverage gate) |
| `pb-spec mutate` | Run incremental mutation testing on changed files (mutmut / cargo-mutants / stryker) |
| `pb-spec verify` | One-command gate: tests + coverage + mutation kill-rate check |

### 4-Field Task Schema

```markdown
### Task 2.1: "Successful login" — User authenticates

- **TaskID:** `T1` - **DependsOn:** `None` - **Complexity:** `High`
- **Context:** Implement JWT auth guard for login endpoint. Key files: src/auth/jwt.ts, src/routes/login.ts.
- **Verification:** `pytest tests/auth/test_jwt.py -q` exits 0; `pb-spec mutate --against HEAD` score ≥ 85%.
- **Status:** 🔴 TODO
- **Test Coverage:** tests/auth/test_jwt.py::test_valid_token, tests/auth/test_jwt.py::test_expired_token
```

| Field | Required | Description |
|---|---|---|
| `Context:` | Yes | Why this task exists, what to do, key files, dependencies |
| `Verification:` | Yes | Exact command(s) + expected output proving task is done |
| `Status:` | Yes | 🔴 TODO / 🟡 IN_PROGRESS / 🟢 DONE / 🔄 DCR / ⛔ OBSOLETE |
| `Test Coverage:` | Yes | pytest test paths proving the task, or `N/A` for infrastructure-only tasks |

### Build Blocked / DCR Packets

Both `🛑 Build Blocked` and `🔄 Design Change Request` packets carry 3 fields: `Reason` (one sentence), `Requested Change` (one paragraph), `Impact` (affected task IDs).

## Skill Evaluation (skill-up)

Every skill ships integration/E2E evals for [skill-up](https://github.com/alibaba/skill-up) — declarative cases run against a real agent engine in a fixture workspace, graded by `expect` gating, `script` judges (workspace assertions) and `agent_judge` (semantic rubrics).

```text
skills/<skill>/
├── SKILL.md
└── evals/
    ├── eval.yaml            # opencode engine
    ├── eval-cmd.yaml        # cross-engine variant (Command Code via custom local transport)
    ├── cases/*.yaml         # one file per case (happy path + decision-protocol cases)
    └── fixtures/            # repo fixtures + judge scripts
```

```bash
just skill-eval-validate                 # validate all eval configs
just skill-eval pb-plan                  # run one skill's evals (reports in skills/<skill>-workspace/)
skill-up run skills/pb-plan/evals/eval-cmd.yaml   # cross-engine comparison with `cmd`
```

Case highlights: `pb-plan` verifies both sides of the decision protocol (clear requirement → autonomous spec; genuinely incomparable → ask / flag a load-bearing assumption), `pb-build` runs a full TDD E2E in a fixture repo, `pb-improve` asserts strict read-only behavior, and `pb-goal` covers evidence-driven completion plus honest `BLOCKED` reporting.

## Verification

```bash
just format && just lint && just type-check && just verify
```

## Supported AI Tools

Compatible with any tool supporting the `agentskills.io` specification: Cursor, Claude Code, GitHub Copilot / GitHub Spark, OpenCode, Gemini CLI, Codex.

## License

[Apache-2.0](LICENSE)
