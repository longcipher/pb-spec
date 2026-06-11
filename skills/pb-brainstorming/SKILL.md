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

## Checklist

You MUST complete these items in order:

1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to their complexity, get user approval after each section
5. **Transition to implementation** — invoke `pb-plan` to create implementation plan

## Design Presentation Format

For simple changes (1-3 files):

```text
Here's my design for [feature]:

**Approach:** [1-2 sentences]

**Key decisions:**
- [Decision 1]
- [Decision 2]

**Files to create/modify:**
- [file list]

**Risks:** [any concerns]

Does this look right?
```

For complex features:

```text
Here's my design for [feature], broken into sections:

## Section 1: [topic]
[content]

## Section 2: [topic]
[content]

Please review each section. I'll proceed to the next after your approval.
```

## Integration with pb-spec

- **Pre-pb-plan:** Use this skill before `/pb-plan` to ensure requirements are clear
- **Pre-pb-build:** Use when requirements are ambiguous and need clarification
- **Standalone:** Use for any design brainstorming need
