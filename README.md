# pb-spec — Plan-Build Spec

[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/longcipher/pb-spec)
[![Context7](https://img.shields.io/badge/Website-context7.com-blue)](https://context7.com/longcipher/pb-spec)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pb-spec.svg)](https://pypi.org/project/pb-spec/)

![pb-spec](https://socialify.git.ci/longcipher/pb-spec/image?font=Source+Code+Pro&language=1&name=1&owner=1&pattern=Circuit+Board&theme=Auto)

pb-spec is a set of [Agent Skills Specification](https://agentskills.io) compliant AI Coding assistant workflow skill packages. It provides a structured process — `plan` → `build` — that turns natural-language requirements into well-architected, TDD/BDD-driven, tested code.

## Design Philosophy

Compared to letting AI "just write code", pb-spec provides a hardened execution harness (guardrails). It requires context-first design, contract-based architecture, and dual-loop verification through logging and health checks.

### Design Standards

`design.md` artifacts conform to four industry-standard specification formats:

| Standard | Purpose | pb-spec Application |
|---|---|---|
| **EARS Notation** | Eliminate ambiguous requirements with 5 sentence patterns (Ubiquitous, State-driven, Event-driven, Unwanted, Exception) | Every requirement in `design.md` uses EARS syntax with `[REQ-XX]` IDs |
| **C4 Model + Mermaid** | Architecture topology in parseable text (Context, Container, Component diagrams) | Architecture sections use `` ```mermaid `` blocks with C4 hierarchy |
| **DBML / Prisma Schema** | Structured data models with strict types, relationships, and indexes | Data model sections use DBML or Prisma Schema DSL — natural language forbidden |
| **MADR (ADR Records)** | Architecture decision records with Context/Decision/Consequences | Every AD has `[Context]`, `[Decision]`, `[Consequences]` subsections |
| **API-First Type Signatures** | Contracts defined before implementation (OpenAPI, Protocol, Trait) | Interface sections use type signatures — narrative descriptions forbidden |

### Best-Practice Alignment

| Source | Core Idea | How pb-spec Applies It |
|---|---|---|
| [RPI Strategy](https://patrickarobinson.com/blog/introducing-rpi-strategy/) | Separate research, planning, and implementation | `/pb-init` + `/pb-plan` precede `/pb-build` |
| [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091) | Plan first to reduce missing-step errors | `design.md` + `tasks.md` are mandatory artifacts |
| [ReAct](https://arxiv.org/abs/2210.03629) | Interleave reasoning and actions with environment feedback | `/pb-build` executes task-by-task with test/tool feedback loops |
| [Reflexion](https://arxiv.org/abs/2303.11366) | Learn from failure signals via iterative retries | Retry/skip/abort and DCR flow in `pb-build` |
| [Harness Engineering (OpenAI, 2026-02-11)](https://openai.com/index/harness-engineering/) | Treat runtime signals and checklists as first-class harness inputs | `pb-plan` requires runtime verification hooks; `pb-build` validates logs/health evidence before task closure |
| [openai/symphony](https://github.com/openai/symphony) | Long-running agents need explicit observability and deterministic escalation | `pb-build` enforces bounded retries and emits standardized DCR packets for `pb-refine` |
| [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Grounding, context hygiene, recovery, observability | State checks, minimal context handoff, task-local rollback guidance |
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Prefer simple composable workflows over framework complexity | Small adapter-based CLI + explicit workflow prompts |
| [Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps) | Generator/Evaluator separation; adversarial evaluation with MCP-driven live verification | `pb-build` dual-persona: Generator builds, independent Evaluator audits with fresh context; adaptive evaluation by task complexity |
| [Stop Using /init for AGENTS.md](https://addyosmani.com/blog/agents-md/) | Keep AGENTS.md focused and maintainable | `/pb-init` updates a managed snapshot block in `AGENTS.md` while preserving all user-authored constraints outside that block |
| [Ensuring Correctness Through the Type System](https://lindbakk.com/blog/ensuring-correctness-through-the-type-system) | Use the type system to encode invariants and catch errors early | Encode contracts as type-level assertions in `design.md` and add type checks to verification; `pb-plan` adds type guidance and `pb-build` runs the type checker when applicable |
| [shadcn/improve](https://github.com/shadcn/improve) | Audit codebase, write self-contained plans for cheaper executors | `/pb-improve` surveys codebase, produces prioritized findings and handoff plans |
| [Superpowers](https://github.com/obra/superpowers) | Composable skills, evidence-based claims, systematic debugging, skill auto-triggering | `using-pb-spec` bootstrap; `pb-verification-before-completion`; `pb-systematic-debugging`; supporting skills ecosystem |

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
npx skills add longcipher/pb-spec --skill improve
```

*(After installation, skills will be placed in `.agents/skills/` or the compatible local directory for your environment, and automatically indexed by your AI.)*

## Quick Start

Invoke these skills directly in your IDE / Agent terminal:

1. **/pb-init**: Audit the current project and non-destructively create or update the `AGENTS.md` architecture snapshot.
2. **/pb-plan "requirement description"**: For example `/pb-plan Add WebSocket auth`, AI will generate `design.md`, `tasks.md`, and `.feature` test specs with Architecture Decisions.
3. **/pb-build "feature-name"**: Automatically reads `tasks.md`, starts the outer BDD and inner TDD dual-loop with Subagents, closing and verifying each task one by one.
4. **/pb-refine "feature-name"**: *(Optional)* When encountering design blocks (Build Blocked) or architectural flaws, iteratively modify specs based on feedback.
5. **/pb-improve**: Audit the codebase and generate prioritized implementation plans for other agents to execute.

## Skills Overview

### Workflow Skills

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-init` | `/pb-init` | `AGENTS.md` | Audit repo and safely update/append a managed snapshot block without rewriting user-authored constraints |
| `pb-plan` | `/pb-plan <requirement>` | `specs/<spec-dir>/design.md` + `tasks.md` + `features/*.feature` | Design proposal + Gherkin scenarios + ordered task breakdown |
| `pb-refine` | `/pb-refine <feature>` | Revised spec files | Apply feedback or Design Change Requests |
| `pb-build` | `/pb-build <feature-name>` | Code + tests | BDD+TDD via Generator (builds) + Evaluator (adversarial review) dual-persona workflow |
| `pb-improve` | `/pb-improve` | `plans/*.md` | Codebase audit → prioritized findings → self-contained handoff plans |

### Supporting Skills

| Skill | Trigger | Description |
|---|---|---|
| `using-pb-spec` | Session start | Bootstrap: establishes skill invocation discipline |
| `pb-brainstorming` | Before creative work | Explores intent, requirements, and design before implementation |
| `pb-test-driven-development` | Before writing code | Red → Green → Refactor cycle, non-negotiable TDD |
| `pb-systematic-debugging` | Any bug or failure | Find root cause before attempting fixes |
| `pb-verification-before-completion` | Before claiming done | Evidence before assertions, always |
| `pb-requesting-code-review` | Before merge | Dispatch independent reviewer subagent |
| `pb-receiving-code-review` | Processing feedback | Technical evaluation, not performative agreement |
| `pb-dispatching-parallel-agents` | Multiple independent tasks | One agent per problem domain, concurrent execution |
| `pb-subagent-driven-development` | Executing plans | Fresh context per task, two-stage review |
| `pb-finishing-a-development-branch` | Work complete | Verify tests → Present options → Execute choice |
| `pb-writing-skills` | Creating/editing skills | Skills are code, not prose — test them |

## Supported AI Tools

This skill library uses the standard `SKILL.md` specification. Fully compatible with:

- **Cursor**
- **Claude Code**
- **GitHub Copilot / GitHub Spark**
- **OpenCode**
- **Gemini CLI** & **Codex**
- Any tool that supports `agentskills.io` specification or reads `.agents/skills/`.

## Workflow

Five agent skills that chain together:

```text
/pb-init → /pb-plan → [/pb-refine] → /pb-build
                    ↘
                    /pb-improve → plans/ → any executor
```

Supporting skills activate automatically during the workflow:

- `pb-brainstorming` — before `/pb-plan` when requirements are unclear
- `pb-test-driven-development` — during `/pb-build` for every task
- `pb-systematic-debugging` — when tasks fail repeatedly
- `pb-verification-before-completion` — before marking any task DONE
- `pb-requesting-code-review` / `pb-receiving-code-review` — review cycles
- `pb-dispatching-parallel-agents` — parallel audit in `/pb-improve`
- `pb-finishing-a-development-branch` — finalization after `/pb-build`

### 1. `/pb-init` — AGENTS.md Snapshot & Safe Merge

Audits your project and writes a `pb-init` snapshot into `AGENTS.md` using managed markers:

- `<!-- BEGIN PB-INIT MANAGED BLOCK -->`
- `<!-- END PB-INIT MANAGED BLOCK -->`

Merge behavior is non-destructive:

- If markers exist, only that managed block is replaced.
- If markers do not exist, the managed block is appended.
- All existing content outside the managed block is preserved verbatim.

The managed snapshot includes an **Architecture Decision Snapshot** so later agents inherit repo-level conventions instead of re-deciding them every run.

### 2. `/pb-plan <requirement>` — Design & Task Planning

Takes source material in arbitrary format and produces a complete feature spec:

```text
specs/<YYYY-MM-DD-NO-feature-name>/
├── design.md    # Architecture, API contracts, data models
├── tasks.md     # Ordered implementation tasks
└── features/    # Gherkin acceptance artifacts
```

Key capabilities:

- **EARS Requirements**: All acceptance criteria use 5 sentence patterns for machine-checkable verification
- **C4 + Mermaid Architecture**: Architecture diagrams in parseable Mermaid syntax
- **MADR Decisions**: Architecture decisions with Context/Decision/Consequences
- **DBML Data Models**: Structured data models in DSL (natural language forbidden)
- **API-First Contracts**: Type signatures before implementation (OpenAPI, Protocol, Trait)
- **Risk-based testing**: Property tests by default for broad input domains; fuzzing and benchmarks conditional
- **Template identity alignment**: Renames generic scaffold names to project-matching identifiers
- **Source requirement normalization**: Converts arbitrary-format input into a structured requirement ledger
- **Self-reconciliation**: Verifies all requirements are covered across design, tasks, and scenarios before finalizing

### 3. `/pb-refine <feature-name>` — Design Iteration (Optional)

Reads user feedback or Design Change Requests and updates `design.md` and `tasks.md`. Maintains a revision history and cascades changes without overwriting completed work.

Validates `🛑 Build Blocked` and `🔄 Design Change Request` packets for required sections before modifying spec artifacts.

### 4. `/pb-build <feature-name>` — Subagent-Driven Implementation

Implements tasks sequentially using a **Generator/Evaluator dual-persona workflow**:

```text
Generator (subagent) → READY_FOR_EVAL → Evaluator (independent context) → PASS / FAIL
                                                ├── Diff Audit (git diff + scope + architecture)
                                                ├── MCP Live Verification (Playwright / HTTP / CLI)
                                                └── Edge Case Probing (boundaries, errors, security)

On PASS  → Orchestrator marks task DONE in tasks.md
On FAIL  → Evaluator feedback → fresh Generator subagent → retry loop (max 3)
```

Key principles:

- **TDD is non-negotiable**: Every task starts with a failing test (Red → Green → Refactor)
- **Fresh context per subagent**: No inherited assumptions; Evaluator never inherits Generator context
- **Architecture decisions are binding**: Executes the approved design; does not invent a different architecture
- **Escalation over thrashing**: 3 consecutive failures → suspend task + DCR packet to `/pb-refine`

### 5. `/pb-improve` — Codebase Audit & Plan Generation

Audits any codebase and writes self-contained implementation plans for other agents to execute. The skill never modifies source code — only produces plans under `plans/`.

```text
/pb-improve                        full audit → prioritized findings → plans
/pb-improve quick                  cheap pass: hotspots, top findings only
/pb-improve deep                   exhaustive: every package, every category
/pb-improve security               focused audit (also: perf, tests, bugs, ...)
/pb-improve branch                 audit only what the current branch changes
/pb-improve next                   feature suggestions — where to take the project
/pb-improve plan <description>     skip the audit, spec one thing
/pb-improve review-plan <file>     critique and tighten an existing plan
/pb-improve execute <plan>         dispatch a cheaper executor, review its work
/pb-improve reconcile              refresh the backlog: verify, unblock, retire
/pb-improve ... --issues           also publish plans as GitHub issues
```

How it works:

1. **Recon** — Maps the repo: stack, conventions, build/test/lint commands (verification gates).
2. **Audit** — Fans out parallel subagents across 9 categories: correctness, security, performance, test coverage, tech debt, dependencies, DX, docs, direction.
3. **Vet** — Re-reads every cited location to drop false positives and correct mis-attributions.
4. **Prioritize** — Findings ordered by leverage (impact ÷ effort, weighted by confidence).
5. **Plan** — One file per selected finding in `plans/` with self-contained context, verification gates, and STOP conditions.

## Design Philosophy: Agent Harness

pb-spec's design is inspired by Anthropic's research on [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) and the [Superpowers](https://github.com/obra/superpowers) methodology. Core idea: place AI agents inside a strict, observable, recoverable execution environment.

| Principle | How pb-spec Implements It |
|---|---|
| **State Grounding** | Subagents verify workspace state before writing code |
| **Architecture Continuity** | `pb-init` records Architecture Decisions; `pb-build` verifies conformance |
| **Error Quoting** | Subagents quote specific error messages before attempting fixes |
| **Context Hygiene** | Only minimal, relevant context passed to each subagent |
| **Recovery Loop** | Pre-task snapshots + file-scoped recovery |
| **Verification Harness** | Design docs define explicit verification commands |
| **Observability as Context** | Task verification includes runtime signals (logs/health) |
| **Escalation Loop** | 3 consecutive failures → DCR handoff to `pb-refine` |
| **Generator/Evaluator Isolation** | Generator builds; Evaluator judges with fresh context |
| **Evidence Before Claims** | `pb-verification-before-completion`: no success claims without fresh verification |
| **Systematic Debugging** | `pb-systematic-debugging`: root cause before fixes, scientific method |
| **Skill Auto-Triggering** | `using-pb-spec` bootstrap ensures skills activate at the right moments |

## License

[Apache-2.0](LICENSE)
