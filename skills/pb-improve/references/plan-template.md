# Spec Template for pb-improve Findings

Every spec is written for a `/pb-build` executor that has **zero context**: it has not seen the advisor session, the audit, the other specs, or any prior conversation. It may be a smaller/cheaper model. Assume it is competent at following explicit instructions and weak at filling gaps, recovering from ambiguity, or knowing when to stop.

Three properties make a spec executable by a weaker model:

1. **Self-contained context** — everything needed is in the files: paths, code excerpts, conventions, commands.
2. **Verification gates** — every step ends with a command and its expected result. The builder never has to *judge* whether it succeeded.
3. **Hard boundaries and escape hatches** — explicit out-of-scope list, and "STOP and report" conditions instead of letting the model improvise when reality doesn't match the spec.

---

## design.md Template

```markdown
# Design: <Imperative title — what will be true after this spec>

| Metadata | Details |
| :--- | :--- |
| **Status** | Draft |
| **Created** | YYYY-MM-DD |
| **Mode** | Lightweight |
| **Priority** | P1 |
| **Planned at** | commit `<short SHA>`, <YYYY-MM-DD> |

## Summary

> 2-3 sentences: overall problem + overall solution covering all findings.

## Why this matters

2–5 sentences. The combined problem, concrete cost, and what improves when all findings land. Written so the builder (and a human reviewer) understands the intent.

## Approach

> Overall implementation approach across all findings. Reference existing code/patterns to reuse.

## Findings

> One section per finding. Each finding is self-contained with its own requirements, context, and approach.

### Finding 1: <Title>

- **Category:** bug / security / performance / test-coverage / tech-debt / ...
- **Impact:** HIGH / MEDIUM / LOW
- **Effort:** S / M / L
- **Confidence:** HIGH / MEDIUM / LOW

#### Requirements (EARS Notation)

> Each requirement uses one of the 5 EARS patterns (Ubiquitous, State-driven, Event-driven, Unwanted, Exception).

- **[REQ-01-F1]:** The system *shall* [action] when [trigger].

#### Current state

The facts the builder needs, inlined — never "as discussed" or "see audit":

- The relevant files, each with one line on its role:
  - `src/orders/api.py` — order-list endpoint; contains the N+1 (lines 130–160)
- Excerpts of the code as it exists today (short, with `file:line` markers).

#### Approach

> How to implement this finding. Reference existing code/patterns to reuse.

#### Scope for this finding

**In scope:** ...
**Out of scope:** ...

### Finding 2: <Title>

- **Category:** ...
- **Impact:** ...
- **Effort:** ...

#### Requirements (EARS Notation)

- **[REQ-01-F2]:** ...

#### Current state

...

#### Approach

...

(Repeat for each finding)

## Architecture Decisions

> Consolidated MADR decisions across all findings. Reference finding sections above.
>
> Each decision must use MADR format: `[Context]`, `[Decision]`, `[Consequences]`.

### AD-01: [Decision Title]

- **Status:** `Proposed` / `Accepted`
- **Date:** YYYY-MM-DD

**Context:** ...
**Decision:** ...
**Consequences:** ...

- **Inherited Decisions:** Which items from the `Architecture Decision Snapshot` this change must preserve.
- **SRP / DIP Check:** Explain how responsibilities stay focused and where dependency inversion is required.
- **Dependency Injection Plan:** All external dependencies must be routed through interfaces or abstract classes unless the repo already defines a different stable seam.
- **Code Simplifier Alignment:** Explain why the chosen pattern reduces complexity, clarifies control flow, or limits coupling rather than adding ceremony.

## BDD/TDD Strategy

- **Primary Language:** ...
- **BDD Runner:** `@cucumber/cucumber` / `behave` / `cucumber`
- **BDD Command:** ...
- **Unit Test Command:** ...
- **Property Test Tool:** `fast-check` / `Hypothesis` / `proptest` / `N/A` with reason
- **Fuzz Test Tool:** `jazzer.js` / `Atheris` / `cargo-fuzz` / `N/A` with reason
- **Benchmark Tool:** `Vitest Bench` / `pytest-benchmark` / `criterion` / `N/A` with reason
- **Feature Files:** `specs/<spec-dir>/features/*.feature`
- **Outside-in Loop:** Which Gherkin scenarios fail first and then pass

## Code Simplification Constraints

- **Behavioral Contract:** Preserve existing behavior unless a listed scenario or requirement explicitly changes it.
- **Repo Standards:** Use only the coding standards that are actually established by `AGENTS.md`, `CLAUDE.md`, and the existing codebase for this repo.
- **Readability Priorities:** Prefer explicit control flow, clear names, reduced nesting, and removal of redundant abstractions when that improves maintainability.
- **Refactor Scope:** Limit cleanup to touched modules unless the design explicitly justifies a broader refactor.
- **Clarity Guardrails:** Avoid dense or clever rewrites; where relevant, avoid nested ternary operators in favor of clearer branching.

## BDD Scenario Inventory

> Complete list of ALL scenarios across ALL findings with task coverage.

- `features/correctness.feature` — [Scenario Name]: [Business outcome] → Task X.Y
- `features/security.feature` — [Scenario Name]: [Business outcome] → Task X.Y
...

## Existing Components to Reuse

> List components found during codebase audit, or "None identified".

## Verification

> How to verify the change works. Include exact commands and expected results.

| Purpose   | Command                          | Expected on success |
|-----------|----------------------------------|---------------------|
| Install   | `uv sync --all-groups`           | exit 0              |
| Lint      | `uv run ruff check`              | exit 0, no errors   |
| Typecheck | `uv run ty check`                | exit 0, no errors   |
| Tests     | `uv run pytest`                  | all pass            |
| BDD       | `uv run behave`                  | all pass            |

(Exact commands from this repo — verified during recon, not guessed.)

## Maintenance notes

For the human/agent who owns this code after the change lands:

- What future changes will interact with this (e.g. "if pagination is added
  to this endpoint, the batching in step 2 must be revisited").
- What a reviewer should scrutinize in the PR.
- Any follow-up explicitly deferred out of this spec (and why).
```

---

## tasks.md Template

> **CRITICAL:** Every task block MUST include all 10 required fields or pb-build validation will fail.
> Required fields: `Context:`, `Verification:`, `Scenario Coverage:`, `Loop Type:`,
> `Behavioral Contract:`, `Simplification Focus:`, `Status:`, `BDD Verification:`,
> `Advanced Test Verification:`, `Runtime Verification:`

```markdown
# <Feature Name> — Tasks

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | specs/<spec-dir>/design.md |
| **Status** | Planning |

## Tasks

> Tasks are numbered across ALL findings: Phase X = Finding X.
> Order by dependency: infrastructure/scaffolding first, then findings in priority order.
> Cross-finding dependencies: if Finding B depends on Finding A, place A's tasks first.

### Task 1.1: [Task Name — Finding 1 infrastructure or first task]

> **Context:** ...
> **Verification:** ...
> **Scenario Coverage:** [Feature/scenario names, or `N/A` with reason]

- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Status:** 🔴 TODO
- [ ] Step 1: ...
- [ ] Step 2: ...
- [ ] BDD Verification: [Concrete scenario check — e.g., "run `behave features/auth.feature` and confirm Scenario X fails first, then passes"]
- [ ] Advanced Test Verification: [Command or `N/A` with reason]
- [ ] Runtime Verification: [Logs + probe result, or `N/A` with reason]

### Task 1.2: [Task Name — Finding 1 next task]

> **Context:** ...
> **Verification:** ...
> **Scenario Coverage:** ...

- **Loop Type:** ...
- **Behavioral Contract:** ...
- **Simplification Focus:** ...
- **Status:** 🔴 TODO
- [ ] Step 1: ...
- [ ] BDD Verification: ...
- [ ] Advanced Test Verification: ...
- [ ] Runtime Verification: ...

### Task 2.1: [Task Name — Finding 2 first task]

> **Context:** ... (note dependency on Finding 1 if applicable)
> **Verification:** ...
> **Scenario Coverage:** ...

- **Loop Type:** ...
- **Behavioral Contract:** ...
- **Simplification Focus:** ...
- **Status:** 🔴 TODO
- [ ] Step 1: ...
- [ ] BDD Verification: ...
- [ ] Advanced Test Verification: ...
- [ ] Runtime Verification: ...
```

---

## feature file Template

```gherkin
Feature: <Feature Name>
  As a [role]
  I want [capability]
  So that [benefit]

  Background:
    Given [common preconditions]

  Scenario: [Happy path scenario name]
    Given [precondition]
    When [action]
    Then [expected outcome]

  Scenario: [Edge case scenario name]
    Given [precondition with edge case]
    When [action]
    Then [expected outcome]
```

---

## specs/README.md Template

```markdown
# Implementation Specs

Generated by pb-improve on <date>. Execute via `/pb-build <feature-name>`.

## Execution order & status

| Spec                 | Findings                        | Priority | Effort                         | Status                             |
| -------------------- | ------------------------------- | -------- | ------------------------------ | ---------------------------------- |
| 2026-MM-DD-01-<slug> | Finding 1, Finding 2, Finding 3 | P1       | M                              | TODO                               |
| Status values: TODO  | IN PROGRESS                     | DONE     | BLOCKED (with one-line reason) | REJECTED (with one-line rationale) |

## Finding details

| # | Finding | Category | Effort | Tasks |
|---|---------|----------|--------|-------|
| 1 | <title> | bug | S | Task 1.1, 1.2 |
| 2 | <title> | security | M | Task 2.1, 2.2, 2.3 |
| 3 | <title> | performance | S | Task 3.1 |

## Dependency notes

- Finding 2 tasks come after Finding 1 because <reason>.

## Findings considered and rejected

- <finding>: not worth doing because <one line>. (So nobody re-audits it.)
```

---

## Quality bar — check before finishing each spec

- Could a model that has never seen this repo execute this with only the spec files and the repo? If any step requires knowledge from the advisor session, inline that knowledge.
- Is every verification a command with an expected result, not a judgment ("make sure it works")?
- Does every step name exact files and symbols, not "the relevant module"?
- Are the STOP conditions specific to this spec's actual risks, not boilerplate?
- Would a reviewer reading only "Why this matters" + the Done criteria understand what they're approving?
- No secret values anywhere in the files — locations and credential types only.
- "Planned at" SHA is filled in and the in-scope paths in the drift check match the Scope section.
- Every requirement from the finding maps to at least one task.
- Every task has a verification command.
- Every BDD+TDD task references a specific scenario in a feature file.
