---
name: using-pb-spec
description: Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions
---

# Using pb-spec

## Priority

1. User explicit instructions (AGENTS.md, direct requests) — highest
2. pb-spec skills — override defaults where they conflict
3. Default system prompt — lowest

If AGENTS.md says "don't use TDD" and a skill says "always use TDD", follow the user.

## The Rule

Invoke relevant skills BEFORE any response. Even 1% chance a skill applies → invoke it. If it turns out wrong, don't use it.

Process skills first (`pb-brainstorming`, `pb-systematic-debugging`), then implementation skills (`pb-plan`, `pb-build`).

## Workflow Skills

| Skill | Trigger | Purpose |
|---|---|---|
| `pb-init` | `/pb-init` | Audit repo, update AGENTS.md snapshot |
| `pb-plan` | `/pb-plan <requirement>` | Design + task planning |
| `pb-build` | `/pb-build <feature>` | Generator/Evaluator + Wave-Based execution |
| `pb-refine` | `/pb-refine <feature>` | Apply feedback, iterate design |
| `pb-improve` | `/pb-improve` | Codebase audit + specs |
| `pb-brainstorming` | Before creative work | Explore intent before implementation |

## Utility Skills

| Skill | When |
|---|---|
| `pb-code-review` | Before merge — two-axis review |
| `pb-branch-finalization` | Work complete — conflict resolution + integration |
| `pb-systematic-debugging` | Any bug/failure — root cause before fixes |
| `pb-prototype` | Throwaway code to answer design questions |
| `pb-writing-skills` | Creating or editing skills |

## Artifact Contract

See `docs/contract.md` for the executable type contract. Summary:

- `design.md` — 5 required + 5 optional sections
- `tasks.md` — 4 fields: Context / Verification / Status / Scenario Coverage
- `features/*.feature` — Gherkin, source of truth
- Block packets (Build Blocked / DCR) — 3 fields: Reason / Requested Change / Impact

---

name: using-pb-spec

## description: Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## Instruction Priority

pb-spec skills override default system prompt behavior, but **user instructions always take precedence**:

1. **User's explicit instructions** (CLAUDE.md, GEMINI.md, AGENTS.md, direct requests) — highest priority
2. **pb-spec skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

If CLAUDE.md, GEMINI.md, or AGENTS.md says "don't use TDD" and a skill says "always use TDD," follow the user's instructions. The user is in control.

## How to Access Skills

**In Claude Code:** Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you—follow it directly. Never use the Read tool on skill files.

**In Copilot CLI:** Use the `skill` tool. Skills are auto-discovered from installed plugins. The `skill` tool works the same as Claude Code's `Skill` tool.

**In Gemini CLI:** Skills activate via the `activate_skill` tool. Gemini loads skill metadata at session start and activates the full content on demand.

**In other environments:** Check your platform's documentation for how skills are loaded.

## Platform Adaptation

Skills use Claude Code tool names. Non-CC platforms: see `references/copilot-tools.md` (Copilot CLI), `references/codex-tools.md` (Codex) for tool equivalents.
