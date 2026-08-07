# Spec Template for pb-improve Findings

Every spec is written for a `/pb-build` executor that has **zero context**: it has not seen the advisor session, the audit, the other specs, or any prior conversation. Assume it is competent at following explicit instructions and weak at filling gaps, recovering from ambiguity, or knowing when to stop. Three properties make a spec executable by a weaker model:

1. **Self-contained context** — paths, code excerpts, conventions, commands all inlined.
2. **Verification gates** — every step ends with a command and its expected result.
3. **Hard boundaries and escape hatches** — explicit out-of-scope list and "STOP and report" conditions instead of improvisation.

---

## design.md Template

```markdown
# Design: <Imperative title — what will be true after this spec>

| Metadata | Details |
| :--- | :--- |
| **Status** | Draft |
| **Created** | YYYY-MM-DD |
| **Priority** | P1 |
| **Planned at** | commit `<short SHA>`, <YYYY-MM-DD> |

## Summary

> 2-3 sentences: overall problem + overall solution covering all findings.

## Approach

> Overall implementation approach across all findings. Reference existing code/patterns to reuse.

**Ponytail Ladder (apply at every decision point):** (1) YAGNI — does it need to exist? (2) stdlib? (3) native platform feature? (4) already-installed dep? (5) one line? one line. (6) only then: minimum code that works. Mark deferrals with `ponytail:` comments. Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested.

## Findings — one sub-section per finding; each is self-contained (requirements, context, approach)

### Finding 1: <Title>

- **Category:** bug / security / performance / test-coverage / tech-debt
- **Impact / Effort / Confidence:** HIGH / MEDIUM / LOW • S / M / L • HIGH / MEDIUM / LOW

#### Requirements (EARS Notation)

> EARS patterns: Ubiquitous, State-driven, Event-driven, Unwanted, Exception.

- **[REQ-01-F1]:** The system *shall* [action] when [trigger].

#### Current state

> Inlined facts — never "as discussed" or "see audit": `file:line` markers + short code excerpts. Example: `src/orders/api.py` — order-list endpoint; contains the N+1 (lines 130–160).

#### Approach

> How to implement this finding. Reference existing code/patterns to reuse.

#### Scope

**In scope:** ... **Out of scope:** ...

### Finding 2: <Title> — (repeat the structure above per finding.)

## Architecture Decisions — consolidated MADR across all findings. Each: `[Context]`, `[Decision]`, `[Consequences]`

### AD-01: [Decision Title]

- **Status:** `Proposed` / `Accepted` — **Date:** YYYY-MM-DD

**Context:** ... **Decision:** ... **Consequences:** ...

## TDD & Mutation Testing Strategy

- **Unit Test Command:** `pytest` / `vitest` / `cargo test` — `<exact command>`
- **Parallel Execution:** `pytest -n auto` (pytest-xdist) / vitest `--pool` / cargo nextest
- **Property / Fuzz / Benchmark Tool:** `fast-check` / `Hypothesis` / `proptest` / `N/A`; `jazzer.js` / `Atheris` / `cargo-fuzz` / `N/A`; `Vitest Bench` / `pytest-benchmark` / `criterion` / `N/A`
- **Type contracts & invariants:** state input/output shapes, boundary conditions, error codes.

## Mutation Testing Strategy

- **Mutation score target:** ≥ 85% (override per finding if needed).
- **Language-specific tooling:**
  - Rust: `cargo-mutants` (config in `.cargo/mutants.toml`)
  - Python: `mutmut` (config in `pyproject.toml [tool.mutmut]`)
  - TypeScript: `@stryker-mutator/core` (config in `stryker.config.json`)
- **Incremental mode:** `./scripts/run-mutation-diff.sh` during `pb-build` for per-task mutation.
- **Target files:** list critical source files and functions that require mutation testing.
- **Assertion requirements:** unit/property tests MUST include boundary checks and specific value assertions.

## Verification — exact commands and expected results, verified during recon (not guessed)

| Purpose   | Command                              | Expected on success |
|-----------|--------------------------------------|---------------------|
| Lint      | `uv run ruff check`                  | exit 0, no errors   |
| Typecheck | `uv run ty check`                    | exit 0, no errors   |
| Tests     | `uv run pytest -n auto`              | all pass            |
| Property  | `uv run pytest -m property`          | all pass            |
| Mutation  | `./scripts/run-mutation-diff.sh`     | exit 0, score ≥ 85% |

## Revision History — append a row per substantive revision (date, author, change)

| Date | Author | Change |
|------|--------|--------|
| YYYY-MM-DD | ... | Initial draft. |
```

**Optional sections** (only when non-trivial): `## Requirements & Goals` (EARS), `## Architecture Overview` (C4 + Mermaid), `## Data Models` (DBML / Prisma), `## Interface Contracts`, `## Implementation Plan`.

---

## tasks.md Template

> **⚠️ pb-build REJECTS tasks.md if ANY of these 4 fields is missing:** `Context:` · `Verification:` · `Status:` · `Test Coverage:`

```markdown
# <Feature Name> — Tasks

> Design Doc: `specs/<spec-dir>/design.md` • Status: Planning

## Tasks

> Tasks are numbered across ALL findings: Phase X = Finding X (Task X.Y). Order by dependency: infrastructure/scaffolding first, then findings in priority order.

### Task 1.1: [Task Name]

> **Context:** ...
> **Verification:** ...
> **Test Coverage:** `tests/test_foo.py::test_bar` — or `N/A` for infrastructure-only tasks

- **Status:** 🔴 TODO
- [ ] Step 1: ...
- [ ] Step 2: ...

### Task 2.1: [Task Name — depends on Finding 1] — same 4 fields; numbered X.Y where X = Finding index
```

**Status values:** `🔴 TODO` / `🟡 IN PROGRESS` / `🟢 DONE` / `🔄 DCR` / `⛔ OBSOLETE`. **Test Coverage:** tasks list the pytest test paths (unit + hypothesis property tests) that prove the task; infrastructure-only tasks use literal `N/A`.

---

## Build Blocked / DCR Packet

When a task cannot proceed, emit a packet with exactly these 3 fields (`Reason`, `Requested Change`, `Impact`):

```markdown
> 🛑 BUILD BLOCKED — Task <X.Y>
>
> **Reason:** <why the task cannot proceed — e.g., upstream design ambiguity, missing dependency, spec contradicts code>
> **Requested Change:** <concrete change to design.md / tasks.md / the test matrix that would unblock>
> **Impact:** <what is blocked downstream — list affected task IDs and any verification gate that won't run>
```

---

## Test Matrix Template

Define the strict TDD contract per finding in design.md:

```markdown
### Finding N — <Title>

#### Type Contracts
- Input: <dataclass/pydantic shape + constraints>
- Output: <shape>
- Errors: <error codes / exceptions>

#### Invariants
- <invariant 1>
- <invariant 2>

#### Boundary Conditions
- <boundary value / expected behavior>

#### Test Matrix
| Test Case | Type | File::test | Verifies |
|-----------|------|------------|----------|
| Happy path | unit | tests/...py::test_x | <behavior> |
| Boundary | unit | tests/...py::test_x_edge | <boundary> |
| Property | hypothesis | tests/...py::test_x_property | <invariant> |
```

---

## specs/README.md Template

```markdown
# Implementation Specs — generated by pb-improve on <date>. Execute via `/pb-build <feature-name>`

## Execution order & status

| Spec                 | Findings                        | Priority | Effort | Status                             |
| -------------------- | ------------------------------- | -------- | ------ | ---------------------------------- |
| 2026-MM-DD-01-<slug> | Finding 1, Finding 2, Finding 3 | P1       | M      | TODO                               |
| Status values: TODO  | IN PROGRESS                     | DONE     | BLOCKED (with one-line reason) | REJECTED (with one-line rationale) |

## Finding details

| # | Finding | Category | Effort | Tasks |
|---|---------|----------|--------|-------|
| 1 | <title> | bug | S | Task 1.1, 1.2 |
| 2 | <title> | security | M | Task 2.1, 2.2 |

## Dependency notes

- Finding 2 tasks come after Finding 1 because <reason>.

## Findings considered and rejected

- <finding>: not worth doing because <one line>. (So nobody re-audits it.)
```

---

## Quality bar — check before finishing each spec

- Could a model that has never seen this repo execute this with only the spec files and the repo? Inline any knowledge from the advisor session.
- Is every verification a command with an expected result, not a judgment ("make sure it works")?
- Does every step name exact files and symbols, not "the relevant module"?
- Are the STOP conditions specific to this spec's actual risks, not boilerplate?
- Would a reviewer reading only `## Summary` + the Done criteria understand what they're approving?
- No secret values anywhere in the files — locations and credential types only. "Planned at" SHA is filled in; in-scope paths in the drift check match the Scope section.
- Every requirement maps to at least one task; every task has a verification command; every task references its `Test Coverage:` pytest paths.
- Every task has exactly 4 required fields: Context, Verification, Status, Test Coverage.
