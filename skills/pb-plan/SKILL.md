---
name: pb-plan
description: Generate design.md, tasks.md, and features/*.feature from a natural-language requirement. BDD-First. Drives /pb-build.
---

# pb-plan

## Role

Transform natural-language requirements into a build-eligible spec under `specs/<spec-dir>/`.

## Workflow

### 1. Discover & Model

- Read the requirement, `AGENTS.md`, existing code conventions.
- Search codebase for affected modules, reusable components, BDD assets.
- Domain modeling: list nouns/verbs, sketch data shape.
- EARS quality pass: requirements use 5 EARS forms. Generate 2-3 alternative interpretations, pick best.
- Confirm understanding to user before proceeding.

### 2. BDD-First — Write features/*.feature

- Gherkin scenarios FIRST. Source of truth.
- Cover: happy path, error case, edge case per scenario.
- Tag scenarios `@<task-id>`.
- Validate: `uv run behave features/<spec>.feature --dry-run`.

### 3. Design — Write design.md

- 5 required + optional sections (see `docs/contract.md`).
- MADR for architecture decisions (Context / Decision / Consequences).
- RFC 2119 for constraints (MUST / SHOULD / MAY).
- C4 + Mermaid for topology, DBML/Prisma for data — only when those aspects change.
- Ponytail ladder: YAGNI → stdlib → native → existing dep → one-liner → minimum code.
- **Mutation Testing Strategy** (required): define mutation score target (default ≥ 80%),
  target files/functions, language-specific tooling, and assertion requirements for
  BDD/unit tests to ensure mutants are killed. Reference `./scripts/run-mutation-diff.sh`
  for incremental mutation testing during build.

### 4. Tasks — Write tasks.md

- 4 fields per task (see `docs/contract.md` for schema).
- DAG ordering: respect dependencies, no forward references.
- Each Verification field MUST be machine-checkable.
- Map tasks to scenarios via `@<task-id>` tags.

## Stopping Conditions

- Requirements ambiguous after Step 1 → STOP, ask.
- Scenario can't be expressed in Gherkin → requirement unclear, STOP.
- Open architectural questions → surface before writing tasks.

## Constraints

- Only write under `specs/<spec-dir>/`. Do not modify source code.
- `AGENTS.md` is read-only.
- Run `uv run pb-spec validate --plan <spec-dir>` before finishing.

---

name: pb-plan

## description: Generate design.md, tasks.md, and features/*.feature from a natural-language requirement. BDD-First. Drives /pb-build
