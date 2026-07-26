---
name: pb-brainstorming
description: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. Contains the reusable grilling loop and domain-modeling discipline.
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs through collaborative dialogue. Understand the project context, ask questions, present a design, get approval, then transition to `pb-plan`.

<HARD-GATE>
Do NOT invoke implementation skills or write code until you have presented a design and the user has approved it.
Autonomous override: when no user is available, skip approval gates and proceed directly to implementation.
</HARD-GATE>

## Workflow

### 1. Explore project context

Check files, docs, recent commits, `CONTEXT.md` (if exists). Assess scope:

- **Well-understood** (≤3 files, clear intent, no cross-cutting concerns) → quick plan path
- **Complex** (ambiguous, multi-system, unclear boundaries) → standard flow

### 2. Grilling loop (standard flow)

Interview the user to refine the idea:

- **One question at a time.** Wait for feedback before continuing.
- For each question, provide your recommended answer with reasoning.
- Look up facts yourself; ask about decisions only.
- Stress-test with concrete scenarios that probe edge cases.

### 2a. Quick plan path (well-understood scope)

Ask 2-4 targeted questions in a single message: scope/constraints, ambiguity resolution, implementation forks, directional decisions. Then generate all artifacts in one pass.

### 3. Propose 2-3 approaches (standard flow only)

Present approaches with trade-offs and your recommendation. Lead with your recommended option. Skip in quick plan.

### 4. Present design

Scale each section to its complexity. Ask after each section whether it looks right (one-pass in quick plan). Cover: architecture, components, data flow, error handling, testing.

### 5. Spec self-review

Check for placeholders, internal contradictions, scope focus, ambiguity. Fix inline.

### 6. Transition to implementation

Invoke `pb-plan` to create the implementation plan.

## Domain Modeling (inline discipline)

During brainstorming, actively sharpen the domain model:

- **Challenge the glossary:** When a term conflicts with `CONTEXT.md`, call it out.
- **Sharpen fuzzy language:** Propose precise canonical terms. "You're saying 'account' — Customer or User?"
- **Cross-reference with code:** When the user states how something works, verify against code. Surface contradictions.
- **Update `CONTEXT.md` inline** as terms resolve. Format: term definition + `_Avoid:` alternatives. Be opinionated. Create lazily.

## ADR Criteria

Offer an ADR only when ALL three are true:

1. Hard to reverse
2. Surprising without context
3. Result of a real trade-off

ADR format (`docs/adr/0001-slug.md`): 1-3 sentences — context, decision, why. Create the directory lazily.

## Design Standards

All design artifacts conform to: EARS notation, C4+Mermaid, DBML/Prisma, MADR, RFC 2119, Behavior Traceability Matrix. See `docs/contract.md` for the complete type contract. `pb-plan` applies these when generating `design.md`.

## Constraints

- One question at a time (standard flow). Multiple choice preferred.
- YAGNI ruthlessly.
- Explore alternatives before settling (standard flow).
- Go back and clarify when something doesn't make sense.
- Update CONTEXT.md and ADRs inline as decisions land.

---

name: pb-brainstorming

## description: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. Contains the reusable grilling loop and domain-modeling discipline
