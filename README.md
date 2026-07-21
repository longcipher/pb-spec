# pb-spec — Plan-Build Spec

[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/longcipher/pb-spec)
[![Context7](https://img.shields.io/badge/Website-context7.com-blue)](https://context7.com/longcipher/pb-spec)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pb-spec.svg)](https://pypi.org/project/pb-spec/)

![pb-spec](https://socialify.git.ci/longcipher/pb-spec/image?font=Source+Code+Pro&language=1&name=1&owner=1&pattern=Circuit+Board&theme=Auto)

pb-spec is a set of [Agent Skills Specification](https://agentskills.io) compliant AI Coding assistant workflow skill packages. It provides a structured process — `plan` → `build` — that turns natural-language requirements into well-architected, BDD-driven, tested code.

## Design Philosophy

pb-spec implements the **Plan-Build pattern**: a Planner Agent generates design specs, and a Builder Agent executes code with verification. The core innovation is making `.feature` files the **absolute source of truth** — all design and tasks derive FROM scenarios, not the other way around.

### Core Principles

| Principle | Description |
|---|---|
| **BDD-First** | Feature scenarios are the source of truth. Design and tasks derive FROM scenarios. |
| **RFC 2119 Constraints** | Architectural constraints use MUST/SHOULD/MAY keywords — binding for the Builder. |
| **DAG Execution** | Tasks include DependsOn metadata for parallel execution of independent tasks. |
| **Adaptive Steering** | Tasks with Complexity=High route to reasoning models; Low to fast models. |
| **Escalation Protocol** | Repeated failures auto-escalate to stronger models for root-cause analysis. |
| **Generator/Evaluator Isolation** | Generator builds; Evaluator judges with fresh context — never inherits Generator state. |

## Installation

No manual file configuration needed. As long as your AI assistant supports the standard Agent Skills specification (Claude Code, Cursor, GitHub Copilot, OpenCode, etc.), you can install with one command.

Run in your project root:

```bash
# Install all pb-spec workflow skills at once
npx skills add longcipher/pb-spec

# Or install only the ones you need
npx skills add longcipher/pb-spec --skill pb-init
npx skills add longcipher/pb-spec --skill pb-plan
npx skills add longcipher/pb-spec --skill pb-build
npx skills add longcipher/pb-spec --skill pb-improve
```

*(After installation, skills will be placed in `.agents/skills/` or the compatible local directory for your environment, and automatically indexed by your AI.)*

## Quick Start

```text
/pb-init            → audit project, write AGENTS.md snapshot
/pb-plan "<req>"    → generate design.md, tasks.md, features/*.feature
/pb-build "<feat>"  → execute via Generator/Evaluator with BDD+TDD loops
/pb-refine "<feat>" → (optional) iterate specs on Build Blocked / DCR
/pb-improve         → audit codebase, generate prioritized specs
```

## Skills Overview

### Core SDD Workflow Skills

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-init` | `/pb-init` | `AGENTS.md` | Audit repo and update managed snapshot block |
| `pb-plan` | `/pb-plan <requirement>` | `specs/<spec>/design.md` + `tasks.md` + `features/*.feature` | Design + Gherkin scenarios + ordered task breakdown with RFC 2119 constraints and DAG metadata |
| `pb-build` | `/pb-build <feature>` | Code + tests | BDD+TDD via Generator/Evaluator with Escalation protocol and Wave-Based parallel execution (4 Invariants) |
| `pb-refine` | `/pb-refine <feature>` | Revised spec files | Apply feedback or Design Change Requests |
| `pb-improve` | `/pb-improve` | `specs/<spec>/` + `specs/context.md` | Codebase audit → prioritized findings → pb-plan-compatible specs |
| `pb-brainstorming` | Before creative work | Design exploration | Explores intent, requirements, and design before implementation |

### Review/Finalization Skills

| Skill | Trigger | Description |
|---|---|---|
| `pb-code-review` | Before merge | Two-axis review (Standards + Spec) + receiving decision tree |
| `pb-branch-finalization` | Work complete | Conflict resolution + integration options |

### Meta/Utility Skills

| Skill | Trigger | Description |
|---|---|---|
| `pb-systematic-debugging` | Any bug or failure | Find root cause before attempting fixes |
| `pb-prototype` | Design validation | Build throwaway prototypes (terminal or UI) for design questions |
| `pb-writing-skills` | Creating/editing skills | Skills are code, not prose — test them |
| `using-pb-spec` | Session start | Bootstrap: establishes skill invocation discipline |

## Workflow

```text
/pb-init → /pb-plan → [/pb-refine] → /pb-build
                    ↘
                    /pb-improve → specs/ → /pb-build
```

Supporting skills activate automatically during the workflow:

- `pb-brainstorming` — before `/pb-plan` when requirements are unclear
- `pb-code-review` — review cycles around `/pb-build` tasks
- `pb-branch-finalization` — finalization after `/pb-build`
- `pb-systematic-debugging` — when tasks fail repeatedly

### 1. `/pb-init` — AGENTS.md Snapshot & Safe Merge

Audits your project and writes a `pb-init` snapshot into `AGENTS.md` using managed markers:

- `<!-- BEGIN PB-INIT MANAGED BLOCK -->`
- `<!-- END PB-INIT MANAGED BLOCK -->`

Merge behavior is non-destructive: existing content outside the managed block is preserved verbatim. The snapshot includes an **Architecture Decision Snapshot** so later agents inherit repo-level conventions.

### 2. `/pb-plan <requirement>` — Design & Task Planning

Produces a complete feature spec:

```text
specs/<YYYY-MM-DD-NO-feature-name>/
├── design.md    # Scalable template: 5 required + 5 optional sections
├── tasks.md     # 4-field task blocks with DAG metadata
└── features/    # Gherkin acceptance artifacts (Source of Truth)
```

Key capabilities:

- **BDD-First**: Feature scenarios written FIRST; design and tasks derive FROM scenarios
- **Scalable design template**: 5 required sections (`Summary`, `Approach`, `Architecture Decisions`, `BDD/TDD Strategy`, `Verification`) + 5 optional sections (`Requirements & Goals`, `Architecture Overview`, `Data Models`, `Interface Contracts`, `Implementation Plan`)
- **RFC 2119 Constraints**: `§Architectural Constraints` section with MUST/SHOULD/MAY keywords — binding for Builder
- **4-field task schema**: `Context:`, `Verification:`, `Status:`, `Scenario Coverage:`
- **DAG-Enabled Tasks**: `TaskID`, `DependsOn`, `Complexity` metadata
- **Behavior Traceability Matrix**: Every design component maps to a Feature scenario (no scenario = remove from design)

### 3. `/pb-refine <feature-name>` — Design Iteration (Optional)

Reads user feedback or Design Change Requests and updates `design.md` and `tasks.md`. Maintains a revision history and cascades changes without overwriting completed work.

Validates `🛑 Build Blocked` and `🔄 Design Change Request` packets — each carrying 3 fields: `Reason`, `Requested Change`, `Impact`.

### 4. `/pb-build <feature-name>` — Generator/Evaluator Implementation

Implements tasks using a **Generator/Evaluator dual-persona workflow** with **Wave-Based parallel execution** (4 Invariants) and **Escalation protocol**:

```text
Generator (subagent) → READY_FOR_EVAL → Evaluator (independent context) → PASS / FAIL
On PASS  → mark task DONE
On FAIL  → fresh Generator subagent → retry
On 2nd FAIL → Escalate to stronger model for root-cause analysis
On 3rd FAIL → DCR packet to /pb-refine
```

Key principles: BDD-First, RFC 2119 constraints BINDING, fresh context per subagent (Evaluator never inherits Generator context), escalation over thrashing, interactive (default) or `--auto` mode.

### 5. `/pb-improve` — Codebase Audit & Plan Generation

Audits any codebase and writes pb-plan-compatible specs for other agents to execute. Never modifies source code — only produces specs under `specs/`.

```text
/pb-improve                        full audit → prioritized findings → specs
/pb-improve quick                  cheap pass: hotspots, top findings only
/pb-improve deep                   exhaustive: every package, every category
/pb-improve security               focused audit (also: perf, tests, bugs, ...)
/pb-improve branch                 audit only what the current branch changes
/pb-improve next                   feature suggestions — where to take the project
/pb-improve plan <description>     skip the audit, spec one thing
/pb-improve review-spec <feature>  critique and tighten an existing spec
/pb-improve reconcile              refresh the backlog: verify, unblock, retire
```

## BDD-First Integration

The core innovation: `.feature` files are the **absolute source of truth**. All design and tasks derive FROM scenarios.

```text
features/*.feature (Source of Truth) → design.md → tasks.md → /pb-build (RED→GREEN→REFACTOR)
```

### RFC 2119 Constraints

`design.md` carries a `§Architectural Constraints` section with MUST/SHOULD/MAY keywords — binding for the Builder. Example: `[C-01] Database interactions MUST use the existing ORM layer; raw SQL MUST NOT be introduced.`

### 4-Field Task Schema

```markdown
### Task 2.1: "Successful login" — User authenticates

- **TaskID:** `T1` - **DependsOn:** `None` - **Complexity:** `High`
- **Context:** Implement JWT auth guard for login endpoint. Key files: src/auth/jwt.ts, src/routes/login.ts.
- **Verification:** `behave --tags=@login_success` exits 0; `pytest tests/auth/test_jwt.py` all pass.
- **Status:** 🔴 TODO
- **Scenario Coverage:** @auth-login-success, @auth-login-invalid-credentials
```

| Field | Required | Description |
|---|---|---|
| `Context:` | Yes | Why this task exists, what to do, key files, dependencies |
| `Verification:` | Yes | Exact command(s) + expected output proving task is done |
| `Status:` | Yes | 🔴 TODO / 🟡 IN_PROGRESS / 🟢 DONE / 🔄 DCR / ⛔ OBSOLETE |
| `Scenario Coverage:` | Yes | @scenario-id list from .feature files, or `N/A` for non-BDD tasks |

### Build Blocked / DCR Packets

Both `🛑 Build Blocked` and `🔄 Design Change Request` packets carry 3 fields: `Reason` (one sentence), `Requested Change` (one paragraph), `Impact` (affected task IDs and scenario tags).

### Escalation Protocol

| Failure Count | Action |
|---|---|
| 1 | Retry with same model |
| 2 | Escalate — auto-upgrade to stronger model for root-cause analysis |
| 3 | File DCR, stop build |

## Verification

```bash
just format && just lint && just test && just bdd && just test-all
```

## Supported AI Tools

Compatible with any tool supporting the `agentskills.io` specification: Cursor, Claude Code, GitHub Copilot / GitHub Spark, OpenCode, Gemini CLI, Codex.

## License

[Apache-2.0](LICENSE)
