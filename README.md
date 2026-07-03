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

Skill prompts follow principles from the [GPT-5.5 Prompting Guide](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5): outcome-first goals, concise style controls, explicit stopping conditions, preamble for perceived responsiveness, and validation loops.

### Core Principles

| Principle | Description |
|---|---|
| **BDD-First** | Feature scenarios are the source of truth. Design and tasks derive FROM scenarios. |
| **RFC 2119 Constraints** | Architectural constraints use MUST/SHOULD/MAY keywords — binding for the Builder. |
| **DAG Execution** | Tasks include DependsOn metadata for parallel execution of independent tasks. |
| **Adaptive Steering** | Tasks with Complexity=High route to reasoning models; Low to fast models. |
| **Escalation Protocol** | Repeated failures auto-escalate to stronger models for root-cause analysis. |
| **Generator/Evaluator Isolation** | Generator builds; Evaluator judges with fresh context — never inherits Generator state. |

### Design Standards

`design.md` artifacts conform to industry-standard specification formats:

| Standard | Purpose | pb-spec Application |
|---|---|---|
| **EARS Notation** | Eliminate ambiguous requirements with 5 sentence patterns | Every requirement uses EARS syntax with `[REQ-XX]` IDs |
| **C4 Model + Mermaid** | Architecture topology in parseable text | Architecture sections use `` ```mermaid `` blocks |
| **DBML / Prisma Schema** | Structured data models with strict types | Data model sections use DBML or Prisma Schema DSL |
| **MADR (ADR Records)** | Architecture decision records | Every AD has `[Context]`, `[Decision]`, `[Consequences]` |
| **RFC 2119 Constraints** | Binding behavioral constraints for agents | `§Architectural Constraints` with MUST/SHOULD/MAY |
| **Behavior Traceability Matrix** | Every component maps to a Feature scenario | No scenario = remove from design |

### Best-Practice Alignment

| Source | Core Idea | How pb-spec Applies It |
|---|---|---|
| [RPI Strategy](https://patrickarobinson.com/blog/introducing-rpi-strategy/) | Separate research, planning, and implementation | `/pb-init` + `/pb-plan` precede `/pb-build` |
| [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091) | Plan first to reduce missing-step errors | `design.md` + `tasks.md` are mandatory artifacts |
| [ReAct](https://arxiv.org/abs/2210.03629) | Interleave reasoning and actions with environment feedback | `/pb-build` executes task-by-task with test/tool feedback loops |
| [Reflexion](https://arxiv.org/abs/2303.11366) | Learn from failure signals via iterative retries | Escalation protocol + DCR flow in `pb-build` |
| [Harness Engineering (OpenAI, 2026-02-11)](https://openai.com/index/harness-engineering/) | Treat runtime signals and checklists as first-class harness inputs | `pb-plan` requires runtime verification hooks; `pb-build` validates logs/health evidence |
| [openai/symphony](https://github.com/openai/symphony) | Long-running agents need explicit observability and deterministic escalation | `pb-build` enforces bounded retries and emits standardized DCR packets |
| [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Grounding, context hygiene, recovery, observability | State checks, minimal context handoff, task-local rollback |
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Prefer simple composable workflows over framework complexity | Small adapter-based CLI + explicit workflow prompts |
| [Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps) | Generator/Evaluator separation; adversarial evaluation | `pb-build` dual-persona with adaptive evaluation by task complexity |
| [shadcn/improve](https://github.com/shadcn/improve) | Audit codebase, write self-contained plans for cheaper executors | `/pb-improve` surveys codebase, produces prioritized specs |
| [Agent-SOP](https://github.com/strands-agents/agent-sop) | RFC 2119 constraints, DAG tasks, adaptive model routing | RFC 2119 in `design.md`, DAG metadata in `tasks.md`, Escalation protocol |
| [Superpowers](https://github.com/obra/superpowers) | Composable skills, evidence-based claims, systematic debugging | `using-pb-spec` bootstrap; supporting skills ecosystem |
| [GPT-5.5 Prompting Guide](https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5) | Outcome-first prompts, stopping conditions, preamble, validation loops | Role/Preamble/Goal/Success Criteria sections, Stopping Conditions, concise invariants |

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

Invoke these skills directly in your IDE / Agent terminal:

1. **/pb-init**: Audit the current project and non-destructively create or update the `AGENTS.md` architecture snapshot.
2. **/pb-plan "requirement description"**: For example `/pb-plan Add WebSocket auth`, AI will generate `design.md`, `tasks.md`, and `.feature` test specs with Architecture Decisions and RFC 2119 constraints.
3. **/pb-build "feature-name"**: Automatically reads `tasks.md`, starts the outer BDD and inner TDD dual-loop with Subagents, closing and verifying each task one by one.
4. **/pb-refine "feature-name"**: *(Optional)* When encountering design blocks (Build Blocked) or architectural flaws, iteratively modify specs based on feedback.
5. **/pb-improve**: Audit the codebase and generate prioritized implementation specs for other agents to execute.

## Skills Overview

### Workflow Skills

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-init` | `/pb-init` | `AGENTS.md` | Audit repo and safely update/append a managed snapshot block without rewriting user-authored constraints |
| `pb-plan` | `/pb-plan <requirement>` | `specs/<spec-dir>/design.md` + `tasks.md` + `features/*.feature` | Design proposal + Gherkin scenarios + ordered task breakdown with RFC 2119 constraints and DAG metadata |
| `pb-refine` | `/pb-refine <feature>` | Revised spec files | Apply feedback or Design Change Requests |
| `pb-build` | `/pb-build <feature-name>` | Code + tests | BDD+TDD via Generator (builds) + Evaluator (adversarial review) with Escalation protocol |
| `pb-improve` | `/pb-improve` | `specs/<spec-dir>/` + `specs/context.md` | Codebase audit → prioritized findings → pb-plan-compatible specs |

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
                    /pb-improve → specs/ → /pb-build
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
├── design.md    # Architecture, API contracts, data models, RFC 2119 constraints
├── tasks.md     # Ordered implementation tasks with DAG metadata
└── features/    # Gherkin acceptance artifacts (Source of Truth)
```

Key capabilities:

- **BDD-First**: Feature scenarios are written FIRST; design and tasks derive FROM scenarios
- **EARS Requirements**: All acceptance criteria use 5 sentence patterns for machine-checkable verification
- **RFC 2119 Constraints**: `§Architectural Constraints` section with MUST/SHOULD/MAY keywords — binding for Builder
- **Behavior Traceability Matrix**: Every design component maps to a Feature scenario (no scenario = remove from design)
- **C4 + Mermaid Architecture**: Architecture diagrams in parseable Mermaid syntax
- **MADR Decisions**: Architecture decisions with Context/Decision/Consequences
- **DBML Data Models**: Structured data models in DSL (natural language forbidden)
- **API-First Contracts**: Type signatures before implementation (OpenAPI, Protocol, Trait)
- **DAG-Enabled Tasks**: `TaskID`, `DependsOn`, `Complexity`, `Required Skills`, `EvalRule` metadata
- **Risk-based testing**: Property tests by default for broad input domains; fuzzing and benchmarks conditional
- **Template identity alignment**: Renames generic scaffold names to project-matching identifiers
- **Source requirement normalization**: Converts arbitrary-format input into a structured requirement ledger
- **Self-reconciliation**: Verifies all requirements are covered across design, tasks, and scenarios before finalizing

### 3. `/pb-refine <feature-name>` — Design Iteration (Optional)

Reads user feedback or Design Change Requests and updates `design.md` and `tasks.md`. Maintains a revision history and cascades changes without overwriting completed work.

Validates `🛑 Build Blocked` and `🔄 Design Change Request` packets for required sections before modifying spec artifacts.

### 4. `/pb-build <feature-name>` — Subagent-Driven Implementation

Implements tasks sequentially using a **Generator/Evaluator dual-persona workflow** with **Escalation protocol**:

```text
Generator (subagent) → READY_FOR_EVAL → Evaluator (independent context) → PASS / FAIL
                                                ├── Diff Audit (git diff + scope + architecture)
                                                ├── BDD Evidence Verification (independent re-run)
                                                ├── MCP Live Verification (Playwright / HTTP / CLI)
                                                └── Edge Case Probing (boundaries, errors, security)

On PASS  → Orchestrator marks task DONE in tasks.md
On FAIL  → Evaluator feedback → fresh Generator subagent → retry loop
On 2nd FAIL → Escalation: auto-upgrade to stronger model for root-cause analysis
On 3rd FAIL → DCR packet to /pb-refine
```

Key principles:

- **BDD-First**: Feature scenarios are the source of truth; all business code must satisfy scenarios
- **RFC 2119 Constraints**: All constraints from `design.md` §Architectural Constraints are BINDING
- **TDD is non-negotiable**: Every task starts with a failing test (Red → Green → Refactor)
- **Fresh context per subagent**: No inherited assumptions; Evaluator never inherits Generator context
- **Architecture decisions are binding**: Executes the approved design; does not invent a different architecture
- **Escalation over thrashing**: 2nd failure auto-escalates to stronger model; 3rd failure → DCR packet
- **Mode Behavior**: Interactive mode (default) or Auto mode (`--auto` flag)

### 5. `/pb-improve` — Codebase Audit & Plan Generation

Audits any codebase and writes pb-plan-compatible specs for other agents to execute. The skill never modifies source code — only produces specs under `specs/`.

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
/pb-improve ... --issues           also publish specs as GitHub issues
```

How it works:

1. **Recon** — Maps the repo: stack, conventions, build/test/lint commands (verification gates). Generates `specs/context.md` with project context.
2. **Audit** — Fans out parallel subagents across 9 categories: correctness, security, performance, test coverage, tech debt, dependencies, DX, docs, direction.
3. **Vet** — Re-reads every cited location to drop false positives and correct mis-attributions.
4. **Prioritize** — Findings ordered by leverage (impact ÷ effort, weighted by confidence).
5. **Spec** — One spec per selected finding in `specs/<spec-dir>/` with design.md (RFC 2119 constraints), tasks.md (DAG metadata), and features/*.feature (Source of Truth).

## BDD-First Integration

The core innovation: `.feature` files are the **absolute source of truth**. All design and tasks derive FROM scenarios.

### Feature-Driven Workflow

```text
features/*.feature (Source of Truth)
        ↓
design.md (derives FROM features)
        ↓
tasks.md (driven BY scenarios)
        ↓
/pb-build (executes with RED→GREEN→REFACTOR)
```

### Behavior Traceability Matrix

Every design component MUST map to a Feature scenario:

| Domain Module | Core Component | Driven by Feature | BDD Tags |
|---|---|---|---|
| Auth | `JwtAuthGuard` | `features/auth/login.feature` | `@auth`, `@security` |
| Payment | `StripeWebhookHandler` | `features/billing/checkout.feature` | `@billing`, `@webhook` |

**Rule:** If a design component cannot be mapped to a scenario, remove it from the design.

### RFC 2119 Constraints

Design constraints use RFC 2119 keywords — binding for the Builder:

```markdown
## Architectural Constraints (RFC 2119)

- **[C-01]** Database interactions **MUST** use the existing ORM layer; raw SQL **MUST NOT** be introduced.
- **[C-02]** API responses **SHOULD** maintain <200ms p99 latency.
- **[C-03]** If an unhandled edge case is encountered, the Builder **MUST** halt and file a DCR.
```

### DAG-Enabled Tasks

Tasks include metadata for parallel execution and adaptive model routing:

```markdown
### Task 2.1: "Successful login" — User authenticates

- **TaskID:** `T1`
- **DependsOn:** `None`
- **Complexity:** `High`
- **Required Skills:** Python, JWT, SQLAlchemy
- **EvalRule:** `behave --tags=@login_success` must pass
```

| Field | Purpose |
|---|---|
| `TaskID` | Unique identifier for DAG resolution |
| `DependsOn` | Lists prerequisite TaskIDs; `None` = can run in parallel |
| `Complexity` | `Low` → fast model, `High` → reasoning model |
| `Required Skills` | Skills the Builder Agent needs |
| `EvalRule` | Explicit pass/fail criteria |

### Escalation Protocol

| Failure Count | Action | Model Strategy |
|---|---|---|
| 1 | Retry with same model | Same model |
| 2 | **Escalate** — auto-upgrade to stronger model for root-cause analysis | +1 tier (Haiku→Sonnet, Sonnet→Opus) |
| 3 | File DCR, stop build | N/A |

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
| **Escalation Loop** | 2nd failure auto-escalates; 3rd failure → DCR handoff to `pb-refine` |
| **Generator/Evaluator Isolation** | Generator builds; Evaluator judges with fresh context |
| **Evidence Before Claims** | `pb-verification-before-completion`: no success claims without fresh verification |
| **RFC 2119 Constraints** | Binding behavioral constraints prevent hallucination and scope creep |
| **DAG Execution** | Parallel task execution for independent tasks |
| **Adaptive Steering** | Complexity-based model routing for cost/speed optimization |
| **Systematic Debugging** | `pb-systematic-debugging`: root cause before fixes, scientific method |
| **Skill Auto-Triggering** | `using-pb-spec` bootstrap ensures skills activate at the right moments |

## License

[Apache-2.0](LICENSE)
