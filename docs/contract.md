# pb-spec Workflow Contract Specification

| Metadata | Details |
| :--- | :--- |
| **Status** | Implemented |
| **Last Updated** | 2026-03-19 |
| **Audience** | Maintainers, tool authors, prompt authors |
| **Related** | `docs/design.md`, `docs/tasks.md`, `docs/plans/2026-03-19-specifica-inspired-evolution.md` |

## 1. Purpose

This document defines the canonical workflow contract for pb-spec's existing planning artifacts.

The contract covers:

- `design.md`
- `tasks.md`
- `features/*.feature`
- markdown-carried `🛑 Build Blocked` and `🔄 Design Change Request` blocks

The goal is to make the current markdown workflow explicit, validator-ready, and stable enough to support future parser and validation tooling.

## 2. Scope and Non-Goals

### 2.1 In Scope

This specification defines:

- required and conditional sections
- task block structure
- allowed task states
- scenario coverage expectations
- blocked-build and DCR block requirements
- validation categories for build eligibility

### 2.2 Out of Scope

This specification does not:

- add a new feature-level `spec.md`
- replace markdown artifacts with YAML or JSON
- change the existing command surface
- redefine prompt behavior beyond the artifact contract
- require one AI platform or runtime

## 3. Workflow Surface

pb-spec's workflow surface remains:

```text
/pb-init -> /pb-plan -> /pb-refine -> /pb-build
```

This document defines the contract carried by the planning artifacts produced and consumed by that workflow.

## 4. Artifact Family

The canonical feature-level artifact family is:

```text
specs/<spec-dir>/
├── design.md
├── tasks.md
└── features/
    └── *.feature
```

### 4.1 Artifact Responsibilities

| Artifact | Primary Role | Consumer |
| :--- | :--- | :--- |
| `design.md` | Architecture, planning rationale, verification strategy | `pb-plan`, `pb-refine`, `pb-build`, maintainers |
| `tasks.md` | Task sequencing, execution contract, verification evidence fields | `pb-plan`, `pb-refine`, `pb-build` |
| `features/*.feature` | Business-visible behavior contract | `pb-plan`, `pb-build`, BDD runner |

### 4.2 No Additional Feature-Level Spec File

The current contract does not require or introduce a separate feature-level `spec.md` artifact. `design.md`, `tasks.md`, and `features/*.feature` remain the contract-carrying artifacts.

## 5. Contract Levels

This specification uses three requirement levels.

| Level | Meaning |
| :--- | :--- |
| **Required** | Must be present for a build-eligible spec |
| **Conditional** | Required only when the stated condition applies |
| **Optional** | Allowed but not required |

## 6. `design.md` Contract

### 6.1 Modes

`design.md` supports two planning modes.

| Mode | Trigger | Expectation |
| :--- | :--- | :--- |
| **Lightweight** | Small, low-complexity change | Compact design with reduced section set |
| **Full** | Medium or complex feature | Full section set, explicit architecture and verification strategy |

Note: Complexity levels (lightweight, medium, high) are orthogonal to mode. Both medium and high complexity specs use full mode. Test fixtures reflect this: `medium_spec` and `full_spec` are both full-mode specs at different complexity levels.

### 6.2 Required Sections for Full Mode

The following sections are required for a build-eligible full-mode `design.md`:

1. `Executive Summary`
2. `Requirements & Goals`
3. `Architecture Overview`
4. `Detailed Design`
5. `Verification & Testing Strategy`
6. `Implementation Plan`

### 6.3 Conditional Sections for Full Mode

The following sections are conditional:

| Section | Condition |
| :--- | :--- |
| `Architecture Decisions` | Required when the change introduces a new boundary or is likely to exceed 200 lines of implementation |
| `Project Identity Alignment` | Required when the repository still exposes template or scaffold identifiers |
| `Existing Components to Reuse` | Required unless no reusable component exists; if none exists, the section must explicitly say so |
| `BDD Scenario Inventory` | Required when feature behavior is user-visible or acceptance-tested |
| `Property Testing` planning | Required for broad input-domain logic unless explicitly justified as unnecessary |
| `Fuzz Testing` planning | Required only for parser, protocol, unsafe, binary, or untrusted-input crash-safety work |
| `Benchmark` planning | Required only for performance-sensitive or regression-sensitive paths |

### 6.4 Lightweight Mode Requirements

A lightweight `design.md` must still include:

1. `Summary`
2. `Approach`
3. `Architecture Decisions`
4. `BDD/TDD Strategy`
5. `Code Simplification Constraints`
6. `BDD Scenario Inventory`
7. `Existing Components to Reuse`
8. `Verification`

Lightweight mode may omit the full-mode `Detailed Design` and `Implementation Plan` sections as standalone top-level sections if the same information is captured compactly in the required lightweight sections.

### 6.5 Lightweight-to-Full Mapping

For validation purposes, lightweight mode satisfies the full contract through the following mapping:

| Lightweight Section | Full-Mode Equivalent Responsibility |
| :--- | :--- |
| `Summary` | `Executive Summary` |
| `Approach` | `Architecture Overview` plus compact `Detailed Design` |
| `Architecture Decisions` | `Architecture Decisions` |
| `BDD/TDD Strategy` | `Verification & Testing Strategy` |
| `Code Simplification Constraints` | `Requirements & Goals` maintainability constraints |
| `BDD Scenario Inventory` | `BDD Scenario Inventory` |
| `Existing Components to Reuse` | `Existing Components to Reuse` |
| `Verification` | compact `Verification & Testing Strategy` plus compact `Implementation Plan` closure criteria |

The validator should treat this mapping as authoritative for lightweight mode rather than requiring full-mode section names to appear literally.

### 6.6 `design.md` Validation Rules

For validation purposes:

- headings are matched by section title
- empty placeholders such as `TBD`, `[To be written]`, or bracket-only templates do not satisfy a required section
- a section may satisfy a conditional requirement by explicitly stating why it is `N/A`
- repo-specific standards must be grounded in actual repo docs or code, not generic boilerplate

## 7. `tasks.md` Contract

### 7.1 Task File Structure

`tasks.md` must contain one or more task blocks identified by headings of this form:

```text
### Task X.Y: <Task Name>
```

Where:

- `X` is the phase number
- `Y` is the task number within that phase
- `Task Name` is free text

The canonical identifier pattern is:

```text
Task ([0-9]+)\.([0-9]+)
```

### 7.2 Task Field Requirement Matrix

The following table is the authoritative source for task field requirement levels.

| Field | Requirement Level | Condition |
| :--- | :--- | :--- |
| `Context` | Required | Always |
| `Verification` | Required | Always |
| `Scenario Coverage` | Required | Always |
| `Loop Type` | Required | Always |
| `Behavioral Contract` | Required | Always |
| `Simplification Focus` | Required | Always |
| `Status` | Required | Always |
| Step checkboxes | Required | At least one checkbox step must exist |
| `BDD Verification` | Required | Always; may be `N/A` with reason for `TDD-only` tasks |
| `Advanced Test Verification` | Required | Always; may be `N/A` with reason when no advanced test category applies |
| `Runtime Verification` | Required | Always; may be `N/A` with reason for non-runtime work |
| `Advanced Test Coverage` | Conditional | Required when the template or plan explicitly classifies advanced test intent |
| `Priority` | Optional | Recommended but not required for parsing |
| `Scope` | Optional | Recommended but not required for parsing |

### 7.3 Advanced Test Categories

For this contract, advanced test categories are:

- property testing
- fuzz testing
- benchmark testing

If any of these are planned or required by the design, the task should classify that intent explicitly and `Advanced Test Verification` must contain a concrete command rather than `N/A`.

### 7.4 Step Checkbox Requirement

Each task block must include at least one checkbox step using markdown checkbox syntax.

Example:

```text
- [ ] Step 1: Write the failing test
```

### 7.5 Allowed `Loop Type` Values

Allowed values are:

- `BDD+TDD`
- `TDD-only`

### 7.6 Allowed Task States

Allowed task status values are:

- `🔴 TODO`
- `🟡 IN PROGRESS`
- `🟢 DONE`
- `⏭️ SKIPPED`
- `🔄 DCR`
- `⛔ OBSOLETE`

Legacy `TODO` is accepted only as an input-compatibility state and must be treated as `🔴 TODO` before execution begins.

### 7.7 Allowed State Transitions

The normal transition path is:

```text
🔴 TODO -> 🟡 IN PROGRESS -> 🟢 DONE
```

Exceptional states are:

- `⏭️ SKIPPED`
- `🔄 DCR`
- `⛔ OBSOLETE`

Validation rules:

Execution guidance:

- builders should move tasks through `🔴 TODO -> 🟡 IN PROGRESS -> 🟢 DONE`
- `🟢 DONE` requires completion evidence for required verification fields
- `⛔ OBSOLETE` should only be applied by refinement or replanning logic
- `🔄 DCR` indicates design blockage and should halt normal forward progress for the affected task

Current static validation is intentionally narrower than the execution model. It enforces allowed status values and completion evidence for `🟢 DONE`, but it does not attempt to reconstruct prior status history from a single markdown snapshot.

### 7.8 Verification Field Semantics

| Field | Requirement Level | Meaning |
| :--- | :--- | :--- |
| `BDD Verification` | Required | Concrete behavior-level verification command or `N/A` with reason for `TDD-only` infrastructure work |
| `Verification` | Required | Concrete verification command or direct measurable check |
| `Advanced Test Verification` | Required | Concrete advanced-test command when property, fuzz, or benchmark testing applies, otherwise `N/A` with reason |
| `Runtime Verification` | Required | Concrete runtime evidence check for runtime-facing work, otherwise `N/A` with reason |

### 7.9 `tasks.md` Validation Rules

For validation purposes:

- at least one valid `### Task X.Y:` block must exist
- every task block must be independently parseable
- duplicate task IDs are invalid
- a task heading without required fields is invalid
- a required verification field is not satisfied by an empty placeholder
- `N/A` is valid only when accompanied by a brief reason

## 8. `features/*.feature` Contract

### 8.1 Minimum Requirement

A build-eligible spec must contain at least one `.feature` file under `features/` with at least one `Scenario`.

### 8.2 Scenario Coverage Expectations

The contract expects:

- user-visible or acceptance-tested behavior to be represented by Gherkin scenarios
- `Scenario Coverage` in `tasks.md` to reference concrete scenarios rather than vague summaries
- future validator support to confirm that referenced scenarios exist

### 8.3 Current Validation Baseline

The minimum current baseline is:

- at least one `.feature` file exists
- at least one `Scenario` exists

Stronger scenario-to-task traceability is part of the intended future contract and should be introduced through validator support.

## 9. `Scenario Coverage` Contract

`Scenario Coverage` is the linkage field between `tasks.md` and `features/*.feature`.

### 9.1 Required Behavior

For `BDD+TDD` tasks, `Scenario Coverage` must name one or more concrete scenarios.

For `TDD-only` tasks, `Scenario Coverage` may be:

- a concrete scenario reference, if the task supports a visible scenario
- `N/A` with reason, if the task is purely internal scaffolding or non-behavioral infrastructure

### 9.2 Orphan Scenario Detection

The following invariant is enforced:

- each executable behavior scenario must map to one or more task blocks
- each `BDD+TDD` task must map to real scenarios
- orphaned scenario references are reported as validation errors

## 10. Blocked-Build and DCR Block Contract

pb-spec carries blocked-build and design-change information in markdown blocks, not sidecar files.

### 10.1 `🛑 Build Blocked` Block

The required header format is:

```text
🛑 Build Blocked — Task X.Y: <Task Name>
```

Required sections:

1. `Reason`
2. `Loop Type`
3. `Scenario Coverage`
4. `What We Tried`
5. `Failure Evidence`
6. `Failing Step`
7. `Suggested Design Change`
8. `Impact`
9. `Next Action`

`Failing Step` may be `N/A` when there is no meaningful Gherkin step to quote.

### 10.2 `🔄 Design Change Request` Block

The required header format is:

```text
🔄 Design Change Request — Task X.Y: <Task Name>
```

Required sections:

1. `Scenario Coverage`
2. `Problem`
3. `What We Tried`
4. `Failure Evidence`
5. `Failing Step`
6. `Suggested Change`
7. `Impact`

`Failing Step` may be `N/A` when there is no meaningful Gherkin step to quote.

The DCR block is intentionally smaller than the blocked-build block because it does not need `Reason`, `Loop Type`, or `Next Action` as separate mandatory sections when the requested design change itself is the actionable output.

### 10.3 Block Validation Rules

For validation purposes:

- missing required sections make the block incomplete
- incomplete blocks must be rejected by refiner-side validation
- failure evidence must contain concrete command output or quoted error text, not generic summaries alone

## 11. Build Eligibility

A spec is build-eligible when all of the following are true:

1. the required `design.md` sections for its mode are present
2. `tasks.md` contains at least one valid task block
3. each task block contains the required task fields
4. task statuses are valid
5. `features/` contains at least one `.feature` file with at least one `Scenario`
6. required verification fields are present and non-empty

Future validator versions may extend build eligibility checks to include stronger cross-link validation.

## 12. Future Validation Architecture (Roadmap)

This section describes the intended evolution of the validation system. The types and
functions listed here are **roadmap targets**, not yet implemented in the current CLI.

### 12.1 Planned Structured Validation Results

A future validation system should use structured types for better error handling and reporting:

| Planned Type | Purpose |
| :--- | :--- |
| `ValidationResult` | Collection of errors and warnings with severity levels |
| `ValidationError` | Single validation issue with file, line, column context |
| `ErrorLevel` | Severity enum: `ERROR`, `WARNING`, `INFO` |

### 12.2 Planned Validation Interfaces

A future refactoring should expose validation as a library with both legacy and structured interfaces:

| Planned Function | Return Type | Purpose |
| :--- | :--- | :--- |
| `validate_design_file()` | `list[str]` | Legacy interface returning error strings |
| `validate_design_file_structured()` | `ValidationResult` | New interface with structured errors |
| `validate_task_file()` | `list[str]` | Legacy interface returning error strings |
| `validate_task_file_structured()` | `ValidationResult` | New interface with structured errors |

### 12.3 Planned Feature Parsing Types

A future feature parser should expose structured access to Gherkin scenarios:

| Planned Type | Purpose |
| :--- | :--- |
| `FeatureScenario` | Parsed Gherkin scenario with file, line number, and outline flag |
| `parse_feature_file()` | Returns `list[FeatureScenario]` for structured access |
| `get_scenario_by_name()` | Finds a specific scenario by name |

## 13. Validator-Ready Priorities

The first validator tranche should prioritize the narrowest high-value checks:

1. parse `tasks.md` task blocks
2. validate required task fields
3. validate task state transitions
4. inventory `.feature` scenario names
5. verify `Scenario Coverage` references resolve when they claim concrete coverage

Later validator stages can expand to:

1. `design.md` section completeness by mode
2. blocked-build and DCR block completeness
3. stronger scenario-to-task traceability
4. placeholder detection and empty-section rejection

## 13. Compatibility Guidance

This contract is designed to preserve compatibility with the current workflow.

Compatibility notes:

- existing specs using legacy `TODO` may be normalized during execution
- stronger validation should prefer explicit diagnostics over silent coercion
- new validator rules should be introduced incrementally and documented clearly when they become mandatory

## 14. Summary

pb-spec's contract is already richer than a generic single-file spec model. The purpose of this document is not to introduce new workflow artifacts, but to make the current contract explicit enough for:

- maintainers
- prompt authors
- parser and validator implementations
- CI and tooling integrations

The canonical planning surface remains `design.md + tasks.md + features/*.feature`.
