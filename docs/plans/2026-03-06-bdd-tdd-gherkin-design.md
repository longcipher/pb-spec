# BDD + TDD Gherkin Workflow Design

| Metadata | Details |
| :--- | :--- |
| **Status** | Implemented |
| **Created** | 2026-03-06 |
| **Scope** | `pb-plan`, `pb-build`, `pb-refine`, shared templates, contract tests |
| **Decision** | Adopt spec-native BDD assets with outside-in execution |

## Summary

`pb-spec` already enforces TDD in its generated build workflow, but it does not treat business behavior as a first-class artifact. This change upgrades the generated workflow from "plan -> tasks -> TDD implementation" to "Gherkin BDD outer loop + TDD inner loop", so downstream projects can define user-visible behavior in `.feature` files and implement each scenario through strict Red -> Green -> Refactor cycles.

The chosen approach is to make BDD assets part of the spec itself. `pb-plan` will generate `design.md`, `tasks.md`, and `features/*.feature`; `pb-build` will execute scenario-first double loops; and `pb-refine` will update feature files alongside design and task changes. The workflow remains grounded in live repo analysis rather than hard-coded directory assumptions.

## Goals

1. Make Gherkin scenarios first-class planning artifacts in generated specs.
2. Preserve the current TDD rigor while adding a user-facing BDD acceptance layer.
3. Support language-aware BDD runner guidance:
   - TypeScript/JavaScript -> `@cucumber/cucumber`
   - Python -> `behave`
   - Rust -> `cucumber`
4. Keep `pb-spec` project-aware: reuse existing repo structure and commands before proposing new BDD directories or scripts.
5. Extend refinement and failure handling so scenario changes remain synchronized with tasks and design.

## Non-Goals

1. Installing downstream dependencies automatically.
2. Generating fully implemented step definitions or runnable feature harnesses in downstream repos. Note: `pb-build` expects the first `BDD+TDD` task (typically in Phase 1: BDD Harness & Scaffolding) to set up step-definition skeletons so that subsequent scenarios can execute. The tasks template already encodes this phasing.
3. Forcing all tasks into BDD. Pure infrastructure tasks may stay `TDD-only`.
4. Adding a new persistent spec-tracking file beyond `design.md`, `tasks.md`, and `features/*.feature`.

### TDD-only Judgment Criteria

`TDD-only` is appropriate when a task produces **no user-visible behavior change**. Examples:

- Build/CI pipeline configuration
- Dependency upgrades or lock-file changes
- Pure internal refactoring with identical external contracts
- Scaffolding that has no observable input/output (e.g., directory creation, config file generation)

If a task changes any input/output contract observable by an end user, an API consumer, or another service, it should be `BDD+TDD`.

## Current State

The current workflow is:

```text
/pb-init -> /pb-plan -> [/pb-refine] -> /pb-build
```

Current strengths:

- `pb-plan` already performs live codebase analysis.
- `pb-build` already enforces TDD and verification evidence.
- `pb-refine` already supports DCR-based iteration.
- Contract tests already protect shared template semantics.

Current gaps:

- No first-class Gherkin artifact in generated specs.
- No explicit mapping from business scenarios to implementation tasks.
- `pb-build` stops at TDD and runtime verification instead of enforcing outside-in behavior.
- `pb-refine` cannot currently revise `.feature` files because they do not exist in the spec model.

## Chosen Approach

## 1. Spec-Native BDD Assets

Each generated spec becomes:

```text
specs/<spec-dir>/
├── design.md
├── tasks.md
└── features/
    ├── <feature-name>.feature
    └── ...
```

The `.feature` files inside `specs/` are **planning-phase artifacts** — they define the acceptance criteria that `pb-build` must satisfy. During build execution, the agent copies or references these scenarios into the project's actual test location (e.g., `tests/features/`, `features/`, or wherever the detected BDD runner expects them). `pb-plan` must check the repo for an existing feature-file location and reuse it; it only proposes `specs/<spec-dir>/features/` as the canonical planning location.

Rules:

- At least one `.feature` file must be generated per spec.
- Each `.feature` file must contain standard Gherkin `Feature` / `Scenario` / `Given` / `When` / `Then`.
- `tasks.md` must map implementation work back to scenarios.
- `pb-refine` must treat `.feature` files as mutable planning artifacts.

## 2. Language-Aware, Repo-Aware Planning

`pb-plan` keeps its live analysis model and adds BDD runner detection:

- `package.json` primary -> TypeScript/JavaScript -> recommend `@cucumber/cucumber`
- `pyproject.toml` or Python project signals -> Python -> recommend `behave`
- `Cargo.toml` primary -> Rust -> recommend `cucumber`
- **Fallback**: For languages not listed above, search the project for an existing BDD tool (e.g., `godog` for Go, `cucumber-jvm` for Java). If none is found, ask the user to specify a BDD runner or fall back to `TDD-only` with acceptance-level integration tests.

The planner must:

- record the primary language
- record the BDD runner and suggested command
- record the unit test runner and command
- reuse existing `features/`, `steps/`, scripts, and test commands if they already exist
- only propose new BDD directories when the repo lacks an established place for them

This preserves `pb-plan`'s current truth model: infer from the actual repo, do not invent a standard layout unless needed.

## 3. Scenario-to-Task Mapping

No new mapping file is introduced. Traceability lives inside existing artifacts:

- `design.md` gains a `BDD Scenario Inventory` section
- each task in `tasks.md` gains:
  - `Scenario Coverage`
  - `Loop Type` (`BDD+TDD` or `TDD-only`)
  - `BDD Verification`

This is enough for `pb-build` to drive execution without adding another file format.

## 4. Outside-In Build Execution

`pb-build` becomes a double-loop executor.

For each `BDD+TDD` task:

1. Read `Scenario Coverage`
2. Find the referenced `.feature` scenario(s)
3. Run the BDD scenario and confirm the outer loop is red
4. Enter the inner loop:
   - write failing unit/component test
   - confirm red
   - write minimal implementation
   - confirm green
   - refactor
5. Re-run the BDD scenario until it passes
6. Run the task's existing verification and runtime checks

Completion gates expand from:

- tests pass
- runtime evidence captured when applicable

to:

- referenced BDD scenario failed first, then passed
- supporting TDD loop completed
- existing verification and runtime evidence remain satisfied

`TDD-only` tasks keep the current TDD flow.

## 5. Refinement and DCR Behavior

`pb-refine` must understand that behavior may live in `.feature` files rather than only in prose.

Rules:

- behavior changes -> update `.feature` first, then cascade to `design.md` and `tasks.md`
- implementation-only corrections -> update design/tasks without casually rewriting Gherkin
- revision history must mention scenario additions/removals/changes
- if completed work is affected by scenario changes, warn explicitly instead of silently mutating progress

`pb-build` DCR packets must also include:

- scenario name
- failing step or acceptance expectation
- whether the issue is in scenario definition, step contract, unit-level design, or implementation

## Component Changes

## `pb-plan`

Required changes:

1. Generate `specs/<spec-dir>/features/`.
2. Add BDD asset generation to the behavior specification.
3. Add language-to-runner guidance for JS/TS, Python, and Rust.
4. Update `design.md` expectations:
   - `BDD/TDD Strategy`
   - `BDD Scenario Inventory`
   - BDD command + unit test command
5. Update `tasks.md` expectations:
   - `Scenario Coverage`
   - `Loop Type`
   - `BDD Verification`
   - phase structure that explicitly includes BDD harness/setup and scenario implementation

## `pb-build`

Required changes:

1. Parse the new task fields.
2. Treat `.feature` files as required inputs for `BDD+TDD` tasks.
3. Enforce outer-loop red before inner-loop TDD work.
4. Require outer-loop green before task closure.
5. Expand failure reporting and DCR packets with scenario-level evidence.

## `pb-refine`

Required changes:

1. Load and modify `.feature` files in `specs/<spec-dir>/features/`.
2. Cascade behavior changes across `.feature`, `design.md`, and `tasks.md`.
3. Preserve completed tasks unless explicitly invalidated by user decision.
4. Update summary output to mention feature-file changes.

## Shared Templates and Docs

Required changes:

1. `design_template.md` gains BDD/TDD strategy and scenario inventory sections.
2. `tasks_template.md` gains scenario mapping and loop metadata.
3. Prompt/skill templates for `pb-plan`, `pb-build`, and `pb-refine` gain the new workflow rules.
4. README and project design docs should describe the new BDD+TDD workflow so generated behavior matches project docs.

## Template Shape

### `design.md`

New required sections:

- `BDD/TDD Strategy`
- `BDD Scenario Inventory`
- explicit `BDD Runner`, `BDD Command`, `Unit Test Command`

### `tasks.md`

New required task fields:

- `Scenario Coverage`
- `Loop Type`
- `BDD Verification`

Recommended phase shape:

1. BDD harness/setup
2. Scenario implementation via TDD
3. Integration/runtime verification
4. Polish/docs

### `.feature`

Generated files must:

- use business language rather than implementation detail
- stay executable in standard Gherkin form
- align with the task inventory

## Testing Strategy

This repo's enforcement point is template testing, so changes should be protected there first.

### Contract Tests

Extend template tests to assert:

1. `pb-plan` templates mention:
   - `features/`
   - `BDD/TDD Strategy`
   - `BDD Scenario Inventory`
   - language-specific BDD runner guidance
2. `tasks_template.md` mentions:
   - `Scenario Coverage`
   - `Loop Type`
   - `BDD Verification`
3. `pb-build` templates require:
   - BDD red before TDD inner loop
   - BDD green before completion
   - scenario-aware DCR evidence
4. `pb-refine` templates explicitly allow `.feature` updates

### Regression Scope

Run the existing suite to ensure:

- template loading still works
- rendered frontmatter remains valid across platforms
- new prompt text does not break markdown fence or placeholder rules

## Risks and Controls

| Risk | Impact | Control |
| :--- | :--- | :--- |
| Over-prescribing downstream directory layout | Planner invents structures that do not fit the repo | Keep "reuse existing structure first" language in every template |
| Prompt/skill drift across platforms | Different tools follow different workflow rules | Centralize wording in shared templates and lock with contract tests |
| Build instructions become too long | Lower determinism in long prompts | Keep rules focused on gates and artifact flow, not step-definition implementation detail |
| Scenario churn invalidates completed tasks | Confusing build/refine behavior | Require explicit warnings and revision history entries |

## Acceptance Criteria

1. `pb-plan` templates instruct the agent to create `.feature` files as part of the spec.
2. `pb-plan` templates explicitly encode BDD runner guidance for JS/TS, Python, and Rust.
3. `design_template.md` and `tasks_template.md` expose the new BDD/TDD fields.
4. `pb-build` templates describe the double-loop execution model and scenario-aware failure handling.
5. `pb-refine` templates include `.feature` files in incremental refinement.
6. Template contract tests fail if any of the above rules regress.
