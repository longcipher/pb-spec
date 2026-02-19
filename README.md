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
| [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Grounding, context hygiene, recovery, observability | State checks, minimal context handoff, task-local rollback guidance |
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Prefer simple composable workflows over framework complexity | Small adapter-based CLI + explicit workflow prompts |

### Practical Principles in pb-spec

- **Context Before Code:** `/pb-init` and `/pb-plan` establish project and requirement context before implementation starts.
- **Verification by Design:** Planning requires explicit verification commands so completion is measurable.
- **Strict TDD Execution:** `/pb-build` enforces Red → Green → Refactor with per-task status tracking.
- **Safe Failure Recovery:** Failed attempts use scoped recovery guidance to avoid polluting unrelated workspace state.
- **Composable Architecture:** Platform differences stay in adapters; workflow semantics stay in shared templates.

## Features

- **4 agent skills**: `pb-init`, `pb-plan`, `pb-refine`, `pb-build` — covering project analysis, design planning, iterative refinement, and TDD implementation
- **5 platforms**: Claude Code, VS Code Copilot, OpenCode, Gemini CLI, Codex
- **Zero config**: run `pb-spec init` and start using AI prompts immediately
- **Idempotent**: safe to re-run; use `--force` to overwrite existing files
- **Built with**: Python 3.12+, [click](https://click.palletsprojects.com/), [uv](https://docs.astral.sh/uv/)

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

# 2. Open the project in your AI coding assistant and use the installed commands/prompts:
#    /pb-init                          → Generate AGENTS.md project context
#    /pb-plan Add WebSocket auth       → Generate specs/YYYY-MM-DD-01-add-websocket-auth/
#    /pb-refine add-websocket-auth     → (Optional) Refine design based on feedback
#    /pb-build add-websocket-auth      → Implement tasks via TDD subagents
#
#    Note for Codex: prompts are loaded from .codex/prompts and typically run via /prompts:<name>.
```

## Supported AI Tools

| AI Tool | Target Directory | File Format |
|---|---|---|
| Claude Code | `.claude/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown |
| VS Code Copilot | `.github/prompts/pb-<name>.prompt.md` | Markdown (no frontmatter) |
| OpenCode | `.opencode/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown |
| Gemini CLI | `.gemini/commands/pb-<name>.toml` | TOML (`description` + `prompt`) |
| Codex | `.codex/prompts/pb-<name>.md` | YAML frontmatter + Markdown |

## CLI Reference

```text
pb-spec init --ai <platform> [--force]
```

Install skill files into the current project.

- `--ai` — Target platform: `claude`, `copilot`, `opencode`, `gemini`, `codex`, or `all`
- `--force` — Overwrite existing files

```text
pb-spec version
```

Print the installed pb-spec version.

```text
pb-spec update
```

Update pb-spec to the latest version (requires `uv`).

## Workflow

four agent skills that chain together:

```text
/pb-init → /pb-plan → [/pb-refine] → /pb-build
```

### 1. `/pb-init` — Project Initialization

Analyzes your project and generates an `AGENTS.md` file at the project root. This file captures the tech stack, directory structure, conventions, and testing patterns. **Preserves user-added context** so manual notes aren't lost on re-runs.

### 2. `/pb-plan <requirement>` — Design & Task Planning

Takes a natural-language requirement and produces a complete feature spec:

```text
specs/<YYYY-MM-DD-NO-feature-name>/
├── design.md    # Architecture, API contracts, data models
└── tasks.md     # Ordered implementation tasks (logical units of work)
```

The spec directory follows the naming format `YYYY-MM-DD-NO-feature-name` (e.g., `2026-02-15-01-add-websocket-auth`). The feature-name part must be unique across all specs.

### 3. `/pb-refine <feature-name>` — Design Iteration (Optional)

Reads user feedback or Design Change Requests (from failed builds) and intelligently updates `design.md` and `tasks.md`. It maintains a revision history and cascades design changes to the task list without overwriting completed work.

### 4. `/pb-build <feature-name>` — Subagent-Driven Implementation

Reads `specs/<YYYY-MM-DD-NO-feature-name>/tasks.md` and implements each task sequentially. Every task is executed by a fresh subagent following strict TDD (Red → Green → Refactor). Supports **Design Change Requests** if the planned design proves infeasible during implementation. Only the `<feature-name>` part is needed when invoking — the agent resolves the full directory automatically.

## Skills Overview

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-init` | `/pb-init` | `AGENTS.md` | Detect stack, scan structure, generate project context |
| `pb-plan` | `/pb-plan <requirement>` | `specs/<YYYY-MM-DD-NO-feature-name>/design.md` + `tasks.md` | Design proposal + ordered task breakdown |
| `pb-refine` | `/pb-refine <feature>` | Revised spec files | Apply feedback or Design Change Requests |
| `pb-build` | `/pb-build <feature-name>` | Code + tests | TDD implementation via subagents |

## Design Philosophy: Agent Harness

pb-spec's prompt design is inspired by Anthropic's research on [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). The core idea: place AI agents inside a strict, observable, recoverable execution environment — a "harness" — rather than relying on the agent's autonomous judgment alone.

### Key Harness Principles

| Principle | How pb-spec Implements It |
|---|---|
| **State Grounding** | Subagents must verify workspace state (`ls`, `find`, `read_file`) before writing any code — preventing path hallucination |
| **Error Quoting** | Subagents must quote specific error messages before attempting fixes — preventing blind debugging |
| **Context Hygiene** | Orchestrator passes only minimal, relevant context to each subagent — preventing context window pollution |
| **Recovery Loop** | Failed tasks trigger `git checkout .` (workspace revert) before retry — ensuring each attempt starts from a known-good state |
| **Verification Harness** | Design docs define explicit verification commands at planning time — subagents execute, not invent, verification |
| **Agent Rules** | `AGENTS.md` embeds project-specific "laws of physics" that all subagents inherit as system-level constraints |

### Where Each Principle Lives

- **Worker (Implementer):** `implementer_prompt.md` enforces grounding-first workflow and error quoting
- **Architect (Planner):** `design_template.md` includes Critical Path Verification table
- **Orchestrator (Builder):** `pb-build` SKILL enforces context hygiene and workspace revert on failure
- **Foundation (Init):** `AGENTS.md` template includes Agent Harness Rules as global conventions

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
