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
```

*(After installation, skills will be placed in `.agents/skills/` or the compatible local directory for your environment, and automatically indexed by your AI.)*

## Quick Start

Invoke these skills directly in your IDE / Agent terminal:

1. **/pb-init**: Audit the current project and non-destructively create or update the `AGENTS.md` architecture snapshot.
2. **/pb-plan "requirement description"**: For example `/pb-plan Add WebSocket auth`, AI will generate `design.md`, `tasks.md`, and `.feature` test specs with Architecture Decisions.
3. **/pb-build "feature-name"**: Automatically reads `tasks.md`, starts the outer BDD and inner TDD dual-loop with Subagents, closing and verifying each task one by one.
4. **/pb-refine "feature-name"**: *(Optional)* When encountering design blocks (Build Blocked) or architectural flaws, iteratively modify specs based on feedback.

## Skills Overview

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-init` | `/pb-init` | `AGENTS.md` | Audit repo and safely update/append a managed snapshot block without rewriting user-authored constraints |
| `pb-plan` | `/pb-plan <requirement>` | `specs/<spec-dir>/design.md` + `tasks.md` + `features/*.feature` | Design proposal + Gherkin scenarios + ordered task breakdown |
| `pb-refine` | `/pb-refine <feature>` | Revised spec files | Apply feedback or Design Change Requests |
| `pb-build` | `/pb-build <feature-name>` | Code + tests | BDD+TDD via Generator (builds) + Evaluator (adversarial review) dual-persona workflow |

## Supported AI Tools

This skill library uses the standard `SKILL.md` specification. Fully compatible with:

- **Cursor**
- **Claude Code**
- **GitHub Copilot / GitHub Spark**
- **OpenCode**
- **Gemini CLI** & **Codex**
- Any tool that supports `agentskills.io` specification or reads `.agents/skills/`.

## Workflow

Four agent skills that chain together:

```text
/pb-init → /pb-plan → [/pb-refine] → /pb-build
```

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

- **Architecture Decisions**: Explicit `Architecture Decisions` section with SRP, DIP, and pattern evaluation
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

## Design Philosophy: Agent Harness

pb-spec's design is inspired by Anthropic's research on [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). Core idea: place AI agents inside a strict, observable, recoverable execution environment.

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

## License

[Apache-2.0](LICENSE)
