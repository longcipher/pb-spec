# pb-spec — Plan-Build Spec

[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/longcipher/pb-spec)
[![Context7](https://img.shields.io/badge/Website-context7.com-blue)](https://context7.com/longcipher/pb-spec)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

![pb-spec](https://socialify.git.ci/longcipher/pb-spec/image?font=Source+Code+Pro&language=1&name=1&owner=1&pattern=Circuit+Board&theme=Auto)

**pb-spec** is a CLI tool that installs AI coding assistant skills into your project. It provides a structured workflow — **init → plan → build** — that turns natural-language requirements into implemented, tested code through AI agent prompts.

## Features

- **3 agent skills**: `pb-init`, `pb-plan`, `pb-build` — covering project analysis, design planning, and TDD implementation
- **3 platforms**: Claude Code, VS Code Copilot, OpenCode
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
# 1. Install skills for your AI tool
cd my-project
pb-spec init --ai claude       # or: copilot, opencode, all

# 2. Open the project in your AI coding assistant and use the skills:
#    /pb-init                          → Generate AGENTS.md project context
#    /pb-plan Add WebSocket auth       → Generate design.md + tasks.md
#    /pb-build add-websocket-auth      → Implement tasks via TDD subagents
```

## Supported AI Tools

| AI Tool | Target Directory | File Format |
|---|---|---|
| Claude Code | `.claude/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown |
| VS Code Copilot | `.github/prompts/pb-<name>.prompt.md` | Markdown (no frontmatter) |
| OpenCode | `.opencode/skills/pb-<name>/SKILL.md` | YAML frontmatter + Markdown |

## CLI Reference

```text
pb-spec init --ai <platform> [--force]
```

Install skill files into the current project.

- `--ai` — Target platform: `claude`, `copilot`, `opencode`, or `all`
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

pb-spec provides three agent skills that chain together:

```text
/pb-init → /pb-plan → /pb-build
```

### 1. `/pb-init` — Project Initialization

Analyzes your project and generates an `AGENTS.md` file at the project root. This file captures the tech stack, directory structure, conventions, and testing patterns so that subsequent agents have full project context.

### 2. `/pb-plan <requirement>` — Design & Task Planning

Takes a natural-language requirement and produces a complete feature spec:

```text
specs/<feature-name>/
├── design.md    # Architecture, API contracts, data models
└── tasks.md     # Ordered implementation tasks with acceptance criteria
```

### 3. `/pb-build <feature-name>` — Subagent-Driven Implementation

Reads `specs/<feature-name>/tasks.md` and implements each task sequentially. Every task is executed by a fresh subagent following strict TDD (Red → Green → Refactor) with self-review before completion.

## Skills Overview

| Skill | Trigger | Output | Description |
|---|---|---|---|
| `pb-init` | `/pb-init` | `AGENTS.md` | Detect stack, scan structure, generate project context |
| `pb-plan` | `/pb-plan <requirement>` | `specs/<name>/design.md` + `tasks.md` | Design proposal + ordered task breakdown |
| `pb-build` | `/pb-build <feature-name>` | Code + tests | TDD implementation via subagents |

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
