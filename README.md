# pb-spec — Plan-Build Spec

[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/longcipher/pb-spec)
[![Context7](https://img.shields.io/badge/Website-context7.com-blue)](https://context7.com/longcipher/pb-spec)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pb-spec.svg)](https://pypi.org/project/pb-spec/)

![pb-spec](https://socialify.git.ci/longcipher/pb-spec/image?font=Source+Code+Pro&language=1&name=1&owner=1&pattern=Circuit+Board&theme=Auto)

**pb-spec** is a CLI tool that installs AI coding assistant skills into your project. It provides a structured workflow — **init → plan → build** — that turns natural-language requirements into implemented, tested code through AI agent prompts.

## 🧠 Design Philosophy

pb-spec follows a **harness-first** philosophy: reliability comes from process design, explicit checks, and recoverability, not from assuming one-shot model correctness.

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
| [Ensuring Correctness Through the Type System](https://lindbakk.com/blog/ensuring-correctness-through-the-type-system) | Use the type system to encode invariants and catch errors early | Encode contracts as type-level assertions in `design.md` and add type checks to verification; `pb-plan` adds type guidance and `pb-build` runs the type checker when applicable. |

### Practical Principles in pb-spec

- **Context Before Code:** `/pb-init` and `/pb-plan` establish project and requirement context before implementation starts.
- **Type System:** pb-spec recommends explicit type annotations and type-level contracts in Architecture Decisions and verification. For strongly-typed projects, `pb-plan` suggests type contracts and adds the project's type-check command to verification so `pb-build` runs it in Phase 0 and at task closure.
- **Behavior Before Code:** `/pb-plan` turns user-visible requirements into Gherkin `.feature` scenarios before implementation begins.
- **Verification by Design:** Planning requires explicit verification commands so completion is measurable.
- **Observability as Context:** Service-facing tasks must capture runtime evidence (log tails and/or health probes), not only test output.
- **Architecture Before Implementation:** `/pb-init` snapshots established architecture decisions, `/pb-plan` records explicit `Architecture Decisions`, and `/pb-build` executes against that contract instead of inventing a new one.
- **Double-Loop Execution:** `/pb-build` enforces a BDD outer loop plus a TDD inner loop with per-task status tracking.
- **Escalation Over Thrashing:** Three consecutive failures suspend the current task and route a standardized DCR packet to `/pb-refine`.
- **Safe Failure Recovery:** Failed attempts use scoped recovery guidance to avoid polluting unrelated workspace state.
- **Composable Architecture:** Platform differences stay in adapters; workflow semantics stay in shared templates.

## Features

- **4 agent skills**: `pb-init`, `pb-plan`, `pb-refine`, `pb-build` — covering project analysis, Gherkin-first design planning, iterative refinement, and BDD+TDD implementation
- **5 platforms**: Claude Code, VS Code Copilot, OpenCode, Gemini CLI, Codex
- **Zero config**: run `pb-spec init` and start using AI prompts immediately
- **Idempotent**: safe to re-run; use `--force` to overwrite existing files
- **Built with**: Python 3.12+, [click](https://click.palletsprojects.com/), [uv](https://docs.astral.sh/uv/)

## Project Layers

pb-spec is organized into three layers:

| Layer | Role | Artifacts |
|-------|------|-----------|
| **Workflow** | Agent-driven development lifecycle | `/pb-init` → `/pb-plan` → `/pb-refine` → `/pb-build` |
| **Contract** | Machine-readable artifact specification | `design.md` + `tasks.md` + `features/*.feature` |
| **Tooling** | Validation, parsing, and CI integration | `pb-spec validate`, internal parsers, future ecosystem tools |

The **workflow layer** defines the four commands and their execution semantics. The **contract layer** carries the explicit field requirements, state transitions, and scenario coverage rules described in [docs/contract.md](docs/contract.md). The **tooling layer** makes the contract executable through validation commands and reusable parsing libraries.

## Installation

```bash
# Recommended
uv tool install pb-spec

# Alternative
pipx install pb-spec
```

## Quick Start

```bash
# 1. Install skills/prompts for your AI tool
cd my-project
pb-spec init --ai claude       # or: copilot, opencode, gemini, codex, all
pb-spec init --ai all -g       # install globally to each agent's home/config dir

# 2. Open the project in your AI coding assistant and use the installed commands/prompts:
#    /pb-init                          → Audit repo, append/update a managed AGENTS.md snapshot block (non-destructive)
#    /pb-plan Add WebSocket auth       → Generate design/tasks/features spec artifacts
#    /pb-refine add-websocket-auth     → (Optional) Refine design based on feedback
#    /pb-build add-websocket-auth      → Implement tasks via BDD outer loop + TDD inner loop
#
#    Note for Codex: prompts are loaded from .codex/prompts and typically run via /prompts:<name>.
```

## Supported AI Tools

All platform adapters are **fully implemented** and production-ready. Each platform has been tested for path generation, content rendering, and file installation.

| AI Tool | Status | Target Directory | File Format | Global Install |
|---|---|---|---|---|
| Claude Code | ✅ Complete | `.claude/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown | ✅ `~/.claude/skills/` |
| VS Code Copilot | ✅ Complete | `.github/prompts/pb-<name>.prompt.md` | Markdown (no frontmatter) | ✅ `~/.copilot/prompts/` |
| OpenCode | ✅ Complete | `.opencode/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown | ✅ `~/.config/opencode/skills/` |
| Gemini CLI | ✅ Complete | `.gemini/commands/pb-<name>.toml` | TOML (`description` + `prompt`) | ✅ `~/.gemini/commands/` |
| Codex | ✅ Complete | `.codex/prompts/pb-<name>.md` | YAML frontmatter + Markdown | ✅ `~/.codex/prompts/` |

For detailed implementation information, see [docs/platform-implementation-status.md](docs/platform-implementation-status.md).

## CLI Reference

```text
pb-spec init --ai <platform> [-g, --global] [--force]
```

Install skill files into the current project, or into global agent config directories with `-g`.

- `--ai` — Target platform: `claude`, `copilot`, `opencode`, `gemini`, `codex`, or `all`
- `-g, --global` — Install into each AI tool's home/config directory (instead of current project)
- `--force` — Overwrite existing files

```text
pb-spec version
```

Print the installed pb-spec version.

```text
pb-spec update
```

Update pb-spec to the latest version (requires `uv`).

```text
pb-spec validate <target>
```

Validate either a generated spec directory or a markdown feedback packet file. For spec directories, the current validator checks `design.md` required sections, `tasks.md` task blocks for required fields, allowed status values, and `DONE` completion evidence, inventories `features/*.feature` scenario names, and verifies `Scenario Coverage` references for `BDD+TDD` tasks. It does not currently fail build eligibility on an otherwise valid spec just because an extra scenario is not yet referenced by a task. For feedback files, it validates `🛑 Build Blocked` and `🔄 Design Change Request` packet completeness and requires concrete failure evidence rather than generic summaries.

## Workflow

four agent skills that chain together:

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

This design avoids relying on any fixed `AGENTS.md` section layout and protects user-maintained constraints across re-runs.

The managed snapshot now also includes an **Architecture Decision Snapshot** so later agents inherit repo-level conventions instead of re-deciding them every run. Typical entries include established patterns, dependency-injection boundaries, error-handling conventions, and workflow/state-modeling rules.

This stronger contract does not add a new command or side-channel validator. The existing markdown workflow remains the source of truth, with `AGENTS.md` carrying repo-level constraints forward into planning, refinement, and execution.

### 2. `/pb-plan <requirement>` — Design & Task Planning

Takes source material in arbitrary format and produces a complete feature spec. You can hand it raw design docs, rough notes, copied requirements, partial design drafts, or mixed-format planning input without wrapping that material in a special pb-plan prompt recipe:

```text
specs/<YYYY-MM-DD-NO-feature-name>/
├── design.md    # Architecture, API contracts, data models
├── tasks.md     # Ordered implementation tasks (logical units of work)
└── features/    # Gherkin acceptance artifacts
```

The spec directory follows the naming format `YYYY-MM-DD-NO-feature-name` (e.g., `2026-02-15-01-add-websocket-auth`). The feature-name part must be unique across all specs. During planning, `AGENTS.md` is treated as read-only policy context (free-form, no fixed layout assumptions). `pb-plan` also maps the primary repo language to a BDD runner:

- TypeScript/JavaScript → `@cucumber/cucumber`
- Python → `behave`
- Rust → `cucumber`

It also performs two additional planning audits before implementation starts:

- Template identity alignment: if the repo still contains generic crate/package/module names from a scaffold, `pb-plan` must front-load renaming those identifiers to project-matching names.
- Risk-based advanced testing: property testing is planned by default for broad input-domain logic, while fuzzing and benchmarks are added only when the feature profile justifies them. Tool selection follows repo language conventions: `Hypothesis` / `fast-check` / `proptest`, `Atheris` / `jazzer.js` / `cargo-fuzz`, and `pytest-benchmark` / `Vitest Bench` / `criterion`.

It should also normalize the incoming source material into a source requirement ledger and use multiple fresh subagents when that improves quality, typically separating source requirement extraction, live codebase analysis, and spec reconciliation. Before finalizing the spec, `pb-plan` should reconcile the extracted source requirements against the generated `design.md`, `tasks.md`, and `features/*.feature` so missing requirements are closed in the planning phase instead of being discovered later during `pb-build`.

It also adds an explicit **Architecture Decisions** section to `design.md`. For work that introduces a new boundary or is likely to exceed 200 lines, planning must evaluate **SRP**, **DIP**, and the classic patterns **Factory**, **Strategy**, **Observer**, **Adapter**, and **Decorator**. The chosen pattern must be justified against alternatives and checked against the code-simplification lens so the design stays simpler, not just more abstract.

The resulting `design.md`, `tasks.md`, and `features/*.feature` files are also the workflow's type carrier in plain markdown. `pb-plan` keeps the current artifact family and command surface, but those artifacts now need explicit contract fields so downstream stages can validate readiness without inventing a separate YAML or JSON schema.

### 3. `/pb-refine <feature-name>` — Design Iteration (Optional)

Reads user feedback or Design Change Requests (from failed builds, including standardized 3-failure build-block packets) and intelligently updates `design.md` and `tasks.md`. It maintains a revision history and cascades design changes to the task list without overwriting completed work. `AGENTS.md` remains read-only in this phase.

`/pb-refine` stays on the same workflow and packet family. It now validates `🛑 Build Blocked` and `🔄 Design Change Request` markdown packets for required sections such as failure evidence and impact before it updates affected spec artifacts.

### 4. `/pb-build <feature-name>` — Subagent-Driven Implementation

Reads `specs/<YYYY-MM-DD-NO-feature-name>/tasks.md` and implements each task sequentially. Every `BDD+TDD` task is executed by a fresh subagent following an outside-in double loop: run the Gherkin scenario first so the BDD outer loop is red, drive the implementation with TDD (Red → Green → Refactor) in the inner loop, then re-run the scenario until it passes. Runtime verification (log/health evidence when applicable) still applies. Supports **Design Change Requests** if the planned design proves infeasible during implementation, and auto-escalates to DCR after three consecutive task failures. Only the `<feature-name>` part is needed when invoking — the agent resolves the full directory automatically. `AGENTS.md` is read-only unless the user explicitly requests an `AGENTS.md` change.

`/pb-build` is now explicitly architecture-bound: it reads the repo's **Architecture Decision Snapshot**, follows the feature's **Architecture Decisions**, re-checks **SRP** and **DIP** during execution, and keeps external dependencies behind interfaces or abstract classes when the design requires that seam. It should not improvise a different Factory, Strategy, Observer, Adapter, or Decorator choice mid-build.

Before parsing tasks or spawning subagents, `/pb-build` now runs a mandatory Phase 0 validation gate against the existing markdown contract: required design sections, required `Task X.Y` fields, and at least one feature scenario. If any item is missing, the build stops before implementation work starts. The builder still manages explicit task-state transitions during execution, while the current static validator focuses on allowed status values and evidence-backed completion gates rather than reconstructing prior state history from a single markdown snapshot.

#### Generator/Evaluator Dual-Persona Flow

Each task in `/pb-build` follows a dual-persona workflow inspired by [Anthropic's GAN-inspired harness research](https://www.anthropic.com/engineering/harness-design-long-running-apps). The agent that builds cannot be the agent that judges:

```text
Generator (subagent) → READY_FOR_EVAL → Evaluator (independent context) → PASS / FAIL
                                                ├── Diff Audit (git diff + scope + architecture)
                                                ├── MCP Live Verification (Playwright / HTTP / CLI)
                                                └── Edge Case Probing (boundaries, errors, security)

On PASS  → Orchestrator marks task DONE in tasks.md
On FAIL  → Evaluator feedback → fresh Generator subagent → retry loop (max 3)
```

The Generator's sole objective is to make tests green. The Evaluator starts with **fresh context** (no Generator conversation history) and performs three independent checks:

1. **Diff Audit** — scope compliance, architecture conformance (SRP/DIP), code quality red flags
2. **MCP Live Verification** — browser automation for frontend tasks, HTTP endpoint testing for backend tasks
3. **Edge Case Probing** — boundary values, missing inputs, error paths, security basics

Evaluation intensity adapts to task complexity: `BDD+TDD` and runtime-facing tasks get full adversarial evaluation; simple `TDD-only` tasks use a lightweight diff review.

## Skills Overview

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-init` | `/pb-init` | `AGENTS.md` | Audit repo and safely update/append a managed snapshot block without rewriting user-authored constraints |
| `pb-plan` | `/pb-plan <requirement>` | `specs/<YYYY-MM-DD-NO-feature-name>/design.md` + `tasks.md` + `features/*.feature` | Design proposal + Gherkin scenarios + ordered task breakdown |
| `pb-refine` | `/pb-refine <feature>` | Revised spec files | Apply feedback or Design Change Requests |
| `pb-build` | `/pb-build <feature-name>` | Code + tests | BDD+TDD via Generator (builds) + Evaluator (adversarial review) dual-persona workflow |

## Design Philosophy: Agent Harness

pb-spec's prompt design is inspired by Anthropic's research on [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). The core idea: place AI agents inside a strict, observable, recoverable execution environment — a "harness" — rather than relying on the agent's autonomous judgment alone.

### Key Harness Principles

| Principle | How pb-spec Implements It |
|---|---|
| **State Grounding** | Subagents must verify workspace state (`ls`, `find`, `read_file`) before writing any code — preventing path hallucination |
| **Architecture Continuity** | `pb-init` records an Architecture Decision Snapshot, `pb-plan` makes Architecture Decisions explicit, and `pb-build` verifies implementation still conforms to that contract |
| **Error Quoting** | Subagents must quote specific error messages before attempting fixes — preventing blind debugging |
| **Context Hygiene** | Orchestrator passes only minimal, relevant context to each subagent — preventing context window pollution |
| **Recovery Loop** | Failed tasks use pre-task snapshots + file-scoped recovery (`git restore` + task-local cleanup), and avoid workspace-wide restore in dirty trees |
| **Verification Harness** | Design docs define explicit verification commands at planning time — subagents execute, not invent, verification |
| **Observability as Context** | Task verification includes runtime signals (logs/health) for service-facing work, and build closure requires command-backed evidence |
| **Escalation Loop** | Three consecutive failures trigger task suspension + standardized DCR handoff to `pb-refine` |
| **Agent Rules** | `AGENTS.md` is treated as free-form policy context: `pb-init` manages only its marker block; `pb-plan`/`pb-refine`/`pb-build` read it without rewriting |
| **Generator/Evaluator Isolation** | Generator builds (makes tests green), Evaluator judges (finds what Generator missed) — with fresh context separation to prevent self-evaluation bias |

### Where Each Principle Lives

- **Worker (Generator):** `implementer_prompt.md` enforces grounding-first workflow, error quoting, and the `READY_FOR_EVAL` signal (no self-marking authority)
- **Critic (Evaluator):** `evaluator_prompt.md` enforces adversarial review with diff audit, MCP live verification, and edge case probing — fresh context, no Generator empathy
- **Architect (Planner):** `design_template.md` + `tasks_template.md` enforce verification criteria, including runtime signals when applicable
- **Orchestrator (Builder):** `pb-build` SKILL enforces context hygiene, runtime verification gates, bounded retries, DCR escalation, and Generator/Evaluator persona switching
- **Foundation (Init):** `pb-init` updates only the managed marker block in `AGENTS.md`, preserving all external user-authored constraints

## Library API

The validation module is importable for CI pipelines and tooling integration:

```python
from pathlib import Path
from pb_spec.validation import (
    validate_design_file,
    validate_task_file,
    collect_feature_scenarios,
    parse_task_blocks,
    parse_feedback_packets,
    validate_feedback_file,
)

spec_dir = Path("specs/my-feature")

# Validate design.md sections
errors = validate_design_file(spec_dir / "design.md")

# Validate tasks.md with scenario cross-referencing
scenario_inventory = collect_feature_scenarios(spec_dir / "features")
errors.extend(validate_task_file(spec_dir / "tasks.md", scenario_inventory=scenario_inventory))

# Parse task blocks programmatically
task_blocks = parse_task_blocks(spec_dir / "tasks.md")
for block in task_blocks:
    print(block.task_id, block.name, block.fields.get("Status"))

# Validate feedback packets
errors = validate_feedback_file(Path("feedback.md"))
```

CI usage with the CLI:

```bash
pb-spec validate specs/my-feature && echo "Build eligible" || echo "Validation failed"
```

## Development

```bash
# Clone
git clone https://github.com/longcipher/pb-spec.git
cd pb-spec

# Install dependencies
uv sync --group dev

# Run tests
uv run pytest -v

# Install locally for testing
uv pip install -e .
```

## License

[Apache-2.0](LICENSE) © 2025 Bob Liu
