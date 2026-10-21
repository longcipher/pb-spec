---
name: pb-plan
description: Generate design.md and tasks.md from a natural-language requirement. TDD-first, multi-layer test matrix, selective mutation strategy. Drives /pb-build.
---

# pb-plan

Transform a natural-language requirement into a build-eligible spec under `specs/<spec-dir>/`.

## Workflow

### 1. Understand the requirement

- Read the requirement, `AGENTS.md`, and the affected code yourself (search, read key files, reuse what exists).
- Restate the goal in one sentence, list scope boundaries (in scope / out of scope), and surface assumptions.
- Only proceed when the behavior is pin-downable to testable cases.

### 2. Design — write design.md

Required sections (schema in `docs/contract.md`): `Summary`, `Approach`, `Architecture Decisions`,
`TDD & Mutation Testing Strategy`, `Verification`. Add optional sections only when the aspect changes
(topology → Mermaid, data → DBML/Prisma). Decisions use MADR (Context / Decision / Consequences);
constraints use RFC 2119 keywords. Prefer the ladder: YAGNI → stdlib → existing dep → minimum code.

**TDD & Mutation Testing Strategy** must define:

- **Type contracts:** input/output shapes, invariants, boundary conditions, error codes.
- **Test matrix — multi-layer, per the project testing principle.** Cover all business scenarios,
  all branches, and boundary/exception paths, combining:
  - Unit tests for every branch and edge (happy path, error path, boundary values).
  - Property tests (hypothesis/proptest) for parsers and pure logic — invariants over randomized inputs.
  - Fuzz tests where input is untrusted or complex (malformed input, adversarial payloads).
  - Integration tests for cross-module behavior (real filesystem/db/IPC as appropriate).
  - E2E tests for user-visible flows through the public entry point.
- **Mutation strategy — selective and scope-bounded.** Mutation testing is slow: declare WHICH
  files/functions get mutated (core logic with subtle correctness risk only), the score target
  (default ≥ 85%), and the tool (`mutmut` / `cargo-mutants` / `stryker`). Explicitly mark
  infra/trivial/UI code as mutation-exempt. Never plan whole-repo mutation runs.

### 3. Tasks — write tasks.md

- 4 fields per task: `Context:`, `Verification:`, `Status:`, `Test Coverage:` (schema in `docs/contract.md`).
- Order tasks by dependency (DAG); each `Verification:` MUST be a machine-checkable command.
- Map every task to its test paths via `Test Coverage:`.
- Mark tasks needing mutation testing explicitly; leave it out of infra/trivial tasks.

### 4. Validate

Run `uv run pb-spec validate --plan <spec-dir>` and fix all errors.

## Decision protocol

Modern models resolve most ambiguity themselves. Default: pick the best option, state it as an
assumption in `design.md` (Architecture Decisions), and proceed. **Ask the user only when all of
these hold — and stop and wait for the answer:**

1. The choice is irreversible or expensive to undo, or changes user-visible behavior;
2. Two or more options have genuinely incomparable trade-offs — there is no best answer from the
   code, conventions, or requirement;
3. The requirement or codebase cannot resolve it.

Never ask about style details, naming, or anything with a clear convention-based default.

**Non-interactive fallback:** if the harness cannot ask (headless run, question tool
disabled), do not silently proceed either. Flag the decision in the final message as an
unresolved, load-bearing assumption, and guard the irreversible step inside the spec itself —
a task that emits a Build Blocked packet, or a benchmark/schema-freeze gate — so the choice
can still be overturned before it becomes permanent.

## Stopping conditions

- Requirement ambiguous after step 1 → ask the user (per decision protocol), wait.
- Behavior cannot be pinned to testable cases → requirement unclear, ask.
- Open architectural question matching the decision protocol → surface, ask, wait.

## Constraints

- Only write under `specs/<spec-dir>/`. Never modify source code. `AGENTS.md` is read-only.
