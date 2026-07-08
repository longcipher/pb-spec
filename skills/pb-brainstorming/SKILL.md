---
name: pb-brainstorming
description: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get user approval.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.

**Autonomous override:** When no user is available to approve, this HARD-GATE does not apply: skip design presentation and approval, proceed directly to implementation, treating every approval gate as auto-approved.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

You MUST complete these items in order:

1. **Explore project context** — check files, docs, recent commits
2. **Assess scope complexity** — classify as well-understood (quick plan) or complex (standard flow):
   - **Well-understood:** clear scope, known constraints, few edge cases, single subsystem, straightforward domain → quick plan path
   - **Complex:** ambiguous requirements, multi-system interactions, complex domain logic, unclear boundaries → standard flow
   - **Heuristic:** if the request describes changes to ≤3 files with clear intent and no cross-cutting concerns, it qualifies as well-understood
3. **Ask clarifying questions** — one at a time (standard) or 2-4 targeted questions (quick plan), understand purpose/constraints/success criteria
4. **Propose 2-3 approaches** — with trade-offs and your recommendation (skipped in quick plan for well-understood scope)
5. **Present design** — in sections scaled to their complexity, get user approval after each section (one-pass in quick plan)
6. **Spec self-review** — quick inline check for placeholders, contradictions, ambiguity, scope
7. **Transition to implementation** — invoke `pb-plan` to create implementation plan

## The Process

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Before asking detailed questions, assess scope: if the request describes multiple independent subsystems, flag this immediately. Don't spend questions refining details of a project that needs to be decomposed first.
- If the project is too large for a single spec, help the user decompose into sub-projects. Each sub-project gets its own spec → plan → implementation cycle.
- For appropriately-scoped projects, ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs (standard flow only — skipped in quick plan)
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Quick plan path (well-understood scope):**

- Skip multi-approach exploration — move directly to targeted questions
- See "Quick Plan Flow" section below for the fast-track process

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently
- For each unit, answer: what does it do, how do you use it, and what does it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work, include targeted improvements as part of the design.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

## Quick Plan Flow

When scope assessment classifies a feature as well-understood, use this fast-track path instead of the standard multi-step flow. Quick plan generates all artifacts in one pass with minimal questions.

### Targeted Questions (2-4 max)

Ask all questions in a single message (unlike standard flow's one-at-a-time). Cover:

1. **Scope & constraints** — Confirm boundaries: what's in, what's explicitly out, any hard constraints?
2. **Ambiguity resolution** — Surface the 1-2 things most likely to cause rework if assumed wrong
3. **Implementation forks** — Where there's a genuine choice (e.g., sync vs async, file vs in-memory), present the fork with your recommendation
4. **Directional decisions** — Any taste/preference calls the user should make (naming, API shape, UI approach)

### One-Pass Generation

After receiving answers, generate ALL artifacts in a single pass:

- **Requirements** — structured with EARS notation and `[REQ-XX]` IDs
- **Design** — architecture, components, data flow (scaled to complexity)
- **Tasks** — implementation breakdown in `tasks.md` format

No intermediate approval gates between sections. Present the complete design for review.

### Refinement

Allow the user to refine selectively without full rerun:

- **Change tasks only** → regenerate tasks from unchanged design
- **Change design** → regenerate design + tasks (keep requirements)
- **Change scope** → full rerun through quick plan flow

## Spec Self-Review

After writing the spec, look at it with fresh eyes:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single implementation plan, or does it need decomposition?
4. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.

Fix any issues inline. No need to re-review — just fix and move on.

## Design Standards

All design artifacts MUST conform to these industry-standard specification formats:

| Standard | Purpose | pb-spec Application |
|---|---|---|
| **EARS Notation** | Eliminate ambiguous requirements with 5 sentence patterns | Every requirement uses EARS syntax with `[REQ-XX]` IDs |
| **C4 Model + Mermaid** | Architecture topology in parseable text | Architecture sections use `` ```mermaid `` blocks |
| **DBML / Prisma Schema** | Structured data models with strict types | Data model sections use DBML or Prisma Schema DSL |
| **MADR (ADR Records)** | Architecture decision records | Every AD has `[Context]`, `[Decision]`, `[Consequences]` |
| **RFC 2119 Constraints** | Binding behavioral constraints for agents | `§Architectural Constraints` with MUST/SHOULD/MAY |
| **Behavior Traceability Matrix** | Every component maps to a Feature scenario | No scenario = remove from design |

These standards are applied by `pb-plan` when generating `design.md`. During brainstorming, keep requirements and decisions structured in a way that maps cleanly to these formats.

## Design Presentation Format

For simple changes (1-3 files):

```text
Here's my design for [feature]:

**Approach:** [1-2 sentences]

**Key decisions:**
- [Decision 1] (→ MADR AD-01)

**Requirements:**
- [REQ-01]: The system *shall* [action] when [trigger]. (→ EARS)

**Files to create/modify:**
- [file list]

**Risks:** [any concerns]

Does this look right?
```

For complex features:

```text
Here's my design for [feature], broken into sections:

## Section 1: [topic]
[content — structured per Design Standards]

## Section 2: [topic]
[content — architecture in Mermaid, data models in DBML/Prisma]

Please review each section. I'll proceed to the next after your approval.
```

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions (standard flow)
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling (standard flow)
- **Incremental validation** - Present design, get approval before moving on
- **Speed where it helps, depth where it matters** - Quick plan for well-understood scope, full process for complex features
- **Be flexible** - Go back and clarify when something doesn't make sense

## Integration with pb-spec

- **Pre-pb-plan:** Use this skill before `/pb-plan` to ensure requirements are clear
- **Pre-pb-build:** Use when requirements are ambiguous and need clarification
- **Standalone:** Use for any design brainstorming need
