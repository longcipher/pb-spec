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
2. `Requirements & Goals` — must use **EARS (Easy Approach to Requirements Syntax)** notation with 5 sentence patterns (Ubiquitous, State-driven, Event-driven, Unwanted, Exception)
3. `Architecture Overview` — must use **C4 Model** rendered in **Mermaid.js** syntax (Context, Container, Component diagrams)
4. `Architecture Decisions` — must use **MADR (Markdown Any Decision Records)** format with `[Context]`, `[Decision]`, `[Consequences]`
5. `Data Models` — must use **DBML** or **Prisma Schema** DSL (natural language table descriptions forbidden)
6. `Interface Contracts` — must use **API-First** type signatures (OpenAPI YAML for external APIs, language-native type syntax for internal modules)
7. `Detailed Design`
8. `Verification & Testing Strategy`
9. `Implementation Plan`

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
3. `Architecture Decisions` — must use **MADR** format even in lightweight mode
4. `BDD/TDD Strategy`
5. `Code Simplification Constraints`
6. `BDD Scenario Inventory`
7. `Existing Components to Reuse`
8. `Verification`

Lightweight mode may omit the full-mode `Detailed Design` and `Implementation Plan` sections as standalone top-level sections if the same information is captured compactly in the required lightweight sections.

Lightweight mode may also omit C4 diagrams, DBML/Prisma schemas, and full API contracts when the change is too small to warrant them — but Architecture Decisions must still use MADR format.

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

The validator **MUST** match headings by section title. The following rules apply:

- Empty placeholders such as `TBD`, `[To be written]`, or bracket-only templates **MUST NOT** satisfy a required section.
- A section **MAY** satisfy a conditional requirement by explicitly stating why it is `N/A`.
- Repo-specific standards **MUST** be grounded in actual repo docs or code, not generic boilerplate.

**Format-specific validation rules:**

- **EARS Requirements:** Each requirement **MUST** use one of the 5 EARS patterns (Ubiquitous, State-driven, Event-driven, Unwanted, Exception). Requirements written as vague goals ("the system should be fast") are invalid.
- **C4/Mermaid Architecture:** Architecture sections **MUST** contain at least one ````mermaid` code block. Natural language architecture descriptions alone do **NOT** satisfy the Architecture Overview requirement.
- **MADR Decisions:** Each Architecture Decision **MUST** have `Context`, `Decision`, and `Consequences` subsections. Decisions without consequences are incomplete.
- **DBML/Prisma Data Models:** Data model sections **MUST** use DBML or Prisma Schema syntax inside a fenced code block. Natural language table descriptions ("users table has an id and name") are invalid.
- **API-First Contracts:** Interface sections **MUST** use type signatures (OpenAPI YAML, TypeScript interfaces, Python Protocols, Rust traits). Narrative API descriptions without type definitions are invalid.

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

The following rules **MUST** be enforced by the validator:

- At least one valid `### Task X.Y:` block **MUST** exist.
- Every task block **MUST** be independently parseable.
- Duplicate task IDs **MUST NOT** be accepted.
- A task heading without required fields is invalid.
- A required verification field **MUST NOT** be satisfied by an empty placeholder.
- `N/A` is valid only when accompanied by a brief reason.

## 8. `features/*.feature` Contract

### 8.1 Minimum Requirement

A build-eligible spec **MUST** contain at least one `.feature` file under `features/` with at least one `Scenario`.

### 8.2 Scenario Coverage Expectations

The contract expects:

- user-visible or acceptance-tested behavior to be represented by Gherkin scenarios
- `Scenario Coverage` in `tasks.md` to reference concrete scenarios rather than vague summaries
- future validator support to confirm that referenced scenarios exist

### 8.3 Current Validation Baseline

The minimum current baseline is:

- At least one `.feature` file **MUST** exist.
- At least one `Scenario` **MUST** exist.

Stronger scenario-to-task traceability **SHOULD** be introduced through future validator support.

## 9. `Scenario Coverage` Contract

`Scenario Coverage` is the linkage field between `tasks.md` and `features/*.feature`.

### 9.1 Required Behavior

For `BDD+TDD` tasks, `Scenario Coverage` **MUST** name one or more concrete scenarios.

For `TDD-only` tasks, `Scenario Coverage` **MAY** be:

- a concrete scenario reference, if the task supports a visible scenario
- `N/A` with reason, if the task is purely internal scaffolding or non-behavioral infrastructure

### 9.2 Orphan Scenario Detection

The following invariant **MUST** be enforced:

- Each executable behavior scenario **MUST** map to one or more task blocks.
- Each `BDD+TDD` task **MUST** map to real scenarios.
- Orphaned scenario references **MUST** be reported as validation errors.

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

The following rules **MUST** be enforced:

- Missing required sections **MUST** make the block incomplete.
- Incomplete blocks **MUST** be rejected by refiner-side validation.
- Failure evidence **MUST** contain concrete command output or quoted error text, not generic summaries alone.

## 11. Build Eligibility

A spec **MUST** satisfy all of the following to be build-eligible:

1. The required `design.md` sections for its mode **MUST** be present.
2. `tasks.md` **MUST** contain at least one valid task block.
3. Each task block **MUST** contain the required task fields.
4. Task statuses **MUST** be valid.
5. `features/` **MUST** contain at least one `.feature` file with at least one `Scenario`.
6. Required verification fields **MUST** be present and non-empty.

Future validator versions **SHOULD** extend build eligibility checks to include stronger cross-link validation.

## 12. Validation Architecture

The validation system uses structured types for error handling and reporting.

### 12.1 Structured Validation Results

| Type | Purpose | Location |
| :--- | :--- | :--- |
| `ValidationResult` | Collection of errors and warnings with severity levels | `validation/result.py` |
| `ValidationError` | Single validation issue with file, line, field context | `validation/result.py` |
| `ErrorSeverity` | Severity enum: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` | `validation/result.py` |

### 12.2 Validation Interfaces

| Function | Return Type | Purpose |
| :--- | :--- | :--- |
| `validate_plan(spec_dir)` | `ValidationResult` | Validate design.md + tasks.md + features/ |
| `validate_build(spec_dir)` | `ValidationResult` | Validate task completion + code quality |
| `validate_task()` | `ValidationResult` | Subagent self-check (git-modified files) |

### 12.3 Contract-Driven Configuration

Required sections, task fields, and validation rules are loaded from
`validation/contract_sections.toml` — the single source of truth.
The TOML config must stay synchronized with this contract document.

## 13. RFC 2119 Constraint Language

This contract uses [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) keywords
to define requirement levels for agent behavior. Every validation rule and workflow
expectation is expressed with the following keywords:

| Keyword | Meaning | Usage in This Contract |
| :--- | :--- | :--- |
| **MUST** | Absolute requirement — the agent SHALL NOT skip this action | Required sections, required fields, build-eligibility gates |
| **MUST NOT** | Absolute prohibition — the agent SHALL NOT perform this action | Validation must not modify source files, must not guess spec dirs |
| **SHOULD** | Recommended practice — valid reasons to deviate must be documented | Optional fields, suggested patterns, formatting preferences |
| **SHOULD NOT** | Not recommended — acceptable only with explicit justification | Avoiding placeholder content, avoiding generic boilerplate |
| **MAY** | Truly optional — implementation is entirely at the agent's discretion | Conditional sections, advanced test categories |

### 13.1 Constraint Application Rules

- Every validation error MUST be reported with file path, line number (when available), and severity level.
- Every required section MUST contain substantive content — empty placeholders (`TBD`, `[To be written]`) do NOT satisfy a requirement.
- `N/A` in a required verification field MUST be accompanied by a brief reason.
- The validator MUST exit with non-zero status code when any CRITICAL or HIGH severity error is found.
- The validator SHOULD exit with non-zero status code when any MEDIUM severity error is found.
- The validator MAY continue past LOW severity issues without failing.
- `rumdl` formatting checks SHOULD run when the tool is available, but the validator MUST NOT fail when `rumdl` is not installed.
- Task status transitions SHOULD follow `🔴 TODO → 🟡 IN PROGRESS → 🟢 DONE`. The validator MUST NOT enforce transition history from a single snapshot.
- The validator MUST NOT modify source files — all operations are read-only.
- Build-blocked and DCR blocks MUST contain all required sections; incomplete blocks MUST be rejected.

## 14. Parameterization

The `pb-spec validate` command supports parameterized configuration to adapt validation
rules across different projects and workflow scales.

### 14.1 CLI Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--plan` | flag | — | Validate spec documents after /pb-plan |
| `--build` | flag | — | Validate task completion after /pb-build |
| `--task` | flag | — | Subagent self-check before READY_FOR_EVAL |
| `--specs-dir` | path | `specs/` | Path to specs directory |

**MUST** specify exactly one of `--plan`, `--build`, or `--task`.
The validator MUST reject combined flags (e.g., `--plan --build`).

### 14.2 Contract Configuration

Validation rules are loaded from `contract_sections.toml` at import time.
Projects MAY override rules by placing a `contract_sections.toml` in the spec directory.
When a project-specific config exists, the validator MUST use it instead of the default.

### 14.3 Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PB_SPEC_GIT_TIMEOUT` | `60` | Timeout for git commands (seconds) |
| `PB_SPEC_RUMDL_CHECK_TIMEOUT` | `10` | Timeout for rumdl availability check (seconds) |
| `PB_SPEC_RUMDL_FORMAT_TIMEOUT` | `30` | Timeout for rumdl formatting (seconds) |

## 15. Validator-Ready Priorities

The validator implements the following checks in priority order:

1. parse `tasks.md` task blocks
2. validate required task fields
3. validate task state transitions
4. inventory `.feature` scenario names
5. verify `Scenario Coverage` references resolve when they claim concrete coverage
6. `design.md` section completeness by mode
7. blocked-build and DCR block completeness
8. placeholder detection and empty-section rejection

## 16. Compatibility Guidance

This contract is designed to preserve compatibility with the current workflow.

- existing specs using legacy `TODO` MUST be treated as `🔴 TODO` before execution begins.
- stronger validation SHOULD prefer explicit diagnostics over silent coercion.
- new validator rules MUST be introduced incrementally and documented clearly when they become mandatory.

## 17. Summary

pb-spec's contract is richer than a generic single-file spec model. The purpose of this document is not to introduce new workflow artifacts, but to make the current contract explicit enough for:

- maintainers
- prompt authors
- parser and validator implementations
- CI and tooling integrations

The canonical planning surface remains `design.md + tasks.md + features/*.feature`.
All validation rules are expressed using RFC 2119 constraint language and loaded from
`contract_sections.toml` as the single source of truth.
