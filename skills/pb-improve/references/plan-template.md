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
| **Effort** | S |
| **Risk** | LOW |
| **Category** | bug |
| **Planned at** | commit `<short SHA>`, <YYYY-MM-DD> |

## Summary

> 2-3 sentences: problem + solution.

## Why this matters

2–5 sentences. The problem, its concrete cost, and what improves when this lands. Written so the builder (and a human reviewer) understands the intent — intent is what lets a correct judgment call happen when a detail is off.

## Requirements (EARS Notation)

> Each requirement uses one of the 5 EARS patterns (Ubiquitous, State-driven, Event-driven, Unwanted, Exception).

- **[REQ-01]:** The system *shall* [action] when [trigger].
- **[REQ-02]:** The system *shall* [action] when [trigger].

## Current state

The facts the builder needs, inlined — never "as discussed" or "see audit":

- The relevant files, each with one line on its role:
  - `src/orders/api.py` — order-list endpoint; contains the N+1 (lines 130–160)
- Excerpts of the code as it exists today (short, with `file:line` markers),
  enough that the builder can confirm it's looking at the right thing.
- The repo conventions that apply here, with a pointer to one exemplar file:
  "Error handling follows the Result pattern — see `src/lib/result.py` and its
  use in `src/users/api.py:40-60`. Match it."

## Approach

> How to implement. Reference existing code/patterns to reuse.

## Scope

**In scope** (the only files you should modify):

- `src/orders/api.py`
- `tests/test_orders_api.py` (create)

**Out of scope** (do NOT touch, even though they look related):

- `src/orders/legacy_api.py` — deprecated path, scheduled for deletion;
  changing it wastes effort and risks the v1 clients still pinned to it.
- Any change to the public response shape — clients depend on it.

## Architecture Decisions (MADR Format)

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

- `features/[feature-name].feature` — [Scenario Name]: [Business outcome]

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

```markdown
# <Feature Name> — Tasks

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | specs/<spec-dir>/design.md |
| **Status** | Planning |

## Tasks

### Task 1.1: [Task Name]

> **Context:** ...
> **Verification:** ...
> **Requirement Coverage:** [Requirement IDs from source requirement ledger, or `N/A` with reason]
> **Scenario Coverage:** [Feature/scenario names]

- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Advanced Test Coverage:** `Example-based only` / `Property` / `Fuzz` / `Benchmark` / `Combination`
- **Status:** 🔴 TODO
- [ ] Step 1: ...
- [ ] Step 2: ...
- [ ] BDD Verification: ...
- [ ] Verification: ...
- [ ] Advanced Test Verification: [Command or `N/A` with reason]
- [ ] Runtime Verification (if applicable): [Logs + probe result, or `N/A` with reason]
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

Generated by pb-improve on <date>. Execute via `/pb-build <feature-name>` in the order below unless dependencies say otherwise. Each builder: read the spec fully before starting, honor its STOP conditions, and update the spec's tasks.md when done.

## Execution order & status

| Spec | Feature | Priority | Effort | Depends on | Status |
|------|---------|----------|--------|------------|--------|
| 2026-MM-DD-01-<slug> | <title> | P1 | S | — | TODO |
| 2026-MM-DD-02-<slug> | <title> | P1 | M | 01 | TODO |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with one-line reason) | REJECTED (with one-line rationale)

## Dependency notes

- 02 requires 01 because <reason>.

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
