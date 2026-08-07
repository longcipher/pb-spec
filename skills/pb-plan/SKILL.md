---
name: pb-plan
description: Generate design.md and tasks.md from a natural-language requirement. TDD-First with a strict mutation-testing strategy. Drives /pb-build.
---

# pb-plan

## Role

Transform natural-language requirements into a build-eligible spec under `specs/<spec-dir>/`.

## Workflow

### 1. Discover & Model

- Read the requirement, `AGENTS.md`, existing code conventions.
- Search codebase for affected modules and reusable components.
- Domain modeling: list nouns/verbs, sketch data shape.
- EARS quality pass: requirements use 5 EARS forms. Generate 2-3 alternative interpretations, pick best.
- Confirm understanding to user before proceeding.

### 2. TDD-First — Define the Test Matrix

- For each requirement, specify the **type contract** (input/output shapes), **invariants**, **boundary conditions**, and **error codes**.
- Define the **test matrix**: the pytest test paths (unit + integration) and the **hypothesis property tests** that prove each behavior.
- Boundary-first: happy path, error path, and edge case each get explicit test cases.
- Tag each task with its test coverage in `tasks.md` via the `Test Coverage:` field.

### 3. Design — Write design.md

- 5 required + optional sections (see `docs/contract.md`).
- MADR for architecture decisions (Context / Decision / Consequences).
- RFC 2119 for constraints (MUST / SHOULD / MAY).
- C4 + Mermaid for topology, DBML/Prisma for data — only when those aspects change.
- Ponytail ladder: YAGNI → stdlib → native → existing dep → one-liner → minimum code.
- **TDD & Mutation Testing Strategy** (required): state the type contracts, invariants, the test matrix, and the mutation score target (default ≥ 85%), target files/functions, language-specific tooling, and assertion requirements so mutants are killed. Reference `./scripts/run-mutation-diff.sh` for incremental mutation testing during build.

### 4. Tasks — Write tasks.md

- 4 fields per task (see `docs/contract.md` for schema).
- DAG ordering: respect dependencies, no forward references.
- Each Verification field MUST be machine-checkable.
- Map tasks to tests via the `Test Coverage:` field (pytest paths + hypothesis cases).

## Stopping Conditions

- Requirements ambiguous after Step 1 → STOP, ask.
- Behavior can't be pinned down to testable cases → requirement unclear, STOP.
- Open architectural questions → surface before writing tasks.

## Constraints

- Only write under `specs/<spec-dir>/`. Do not modify source code.
- `AGENTS.md` is read-only.
- Run `uv run pb-spec validate --plan <spec-dir>` before finishing.

---

name: pb-plan

## description: Generate design.md and tasks.md from a natural-language requirement. TDD-First with a strict mutation-testing strategy. Drives /pb-build
