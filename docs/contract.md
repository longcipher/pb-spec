# pb-spec Workflow Contract Specification

| Metadata | Details |
| :--- | :--- |
| **Status** | Implemented |
| **Last Updated** | 2026-07-21 |
| **Audience** | Maintainers, tool authors, prompt authors |
| **Related** | `docs/design.md`, `docs/tasks.md` |

## 1. Purpose

This document defines the canonical workflow contract for pb-spec's planning artifacts:

- `design.md`
- `tasks.md`
- `features/*.feature`
- markdown-carried `🛑 Build Blocked` and `🔄 Design Change Request` blocks

The goal is to make the markdown workflow explicit, validator-ready, and stable enough to support parser and validation tooling.

## 2. Scope and Non-Goals

### 2.1 In Scope

- required and conditional sections
- task block structure (4-field schema)
- allowed task states
- scenario coverage expectations
- blocked-build and DCR block requirements (3-field each)
- validation categories for build eligibility

### 2.2 Out of Scope

- adding a new feature-level `spec.md`
- replacing markdown artifacts with YAML or JSON
- changing the existing command surface
- redefining prompt behavior beyond the artifact contract
- requiring one AI platform or runtime

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
| `tasks.md` | Task sequencing, 4-field execution contract | `pb-plan`, `pb-refine`, `pb-build` |
| `features/*.feature` | Business-visible behavior contract | `pb-plan`, `pb-build`, BDD runner |

### 4.2 No Additional Feature-Level Spec File

The contract does not require a separate feature-level `spec.md`. `design.md`, `tasks.md`, and `features/*.feature` remain the contract-carrying artifacts.

## 5. Contract Levels

This specification uses three requirement levels.

| Level | Meaning |
| :--- | :--- |
| **Required** | Must be present for a build-eligible spec |
| **Conditional** | Required only when the stated condition applies |
| **Optional** | Allowed but not required |

## 6. `design.md` Scalable Template

`design.md` uses a single scalable template: 5 required sections plus 5 optional sections. The author chooses which optional sections to include based on change complexity.

### 6.1 Required Sections

1. `Summary` — what the change is and why
2. `Approach` — how the change is implemented, compact
3. `Architecture Decisions` — **MADR** format with `[Context]`, `[Decision]`, `[Consequences]`
4. `BDD/TDD Strategy` — scenario-first planning; BDD scenarios derive from feature files
5. `Verification` — concrete commands and measurable checks

### 6.2 Optional Sections

1. `Requirements & Goals` — use **EARS** notation with `[REQ-XX]` IDs
2. `Architecture Overview` — **C4 Model** rendered in **Mermaid.js** (Context, Container, Component diagrams)
3. `Data Models` — **DBML** or **Prisma Schema** DSL
4. `Interface Contracts` — **API-First** type signatures (OpenAPI YAML, TypeScript interfaces, Python Protocols, Rust traits)
5. `Implementation Plan` — phase sequencing and closure criteria

### 6.3 Validation Rules

The validator **MUST** match headings by section title. The following rules apply:

- Empty placeholders such as `TBD`, `[To be written]`, or bracket-only templates **MUST NOT** satisfy a required section.
- Repo-specific standards **MUST** be grounded in actual repo docs or code, not generic boilerplate.

**Format-specific validation rules:**

- **EARS Requirements:** Each requirement **MUST** use one of the 5 EARS patterns (Ubiquitous, State-driven, Event-driven, Unwanted, Exception). Vague goals ("the system should be fast") are invalid.
- **C4/Mermaid Architecture:** Architecture sections **MUST** contain at least one ````mermaid` code block. Natural language architecture descriptions alone do **NOT** satisfy the Architecture Overview requirement.
- **MADR Decisions:** Each Architecture Decision **MUST** have `Context`, `Decision`, and `Consequences` subsections. Decisions without consequences are incomplete.
- **DBML/Prisma Data Models:** Data model sections **MUST** use DBML or Prisma Schema syntax inside a fenced code block. Natural language table descriptions are invalid.
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

The canonical identifier pattern is `Task ([0-9]+)\.([0-9]+)`.

### 7.2 Task Field Requirement Matrix

The 4-field schema is authoritative.

| Field | Required | Description |
| :--- | :--- | :--- |
| `Context:` | Yes | Why this task exists, what to do, key files, dependencies |
| `Verification:` | Yes | Exact command(s) + expected output proving task is done |
| `Status:` | Yes | 🔴 TODO / 🟡 IN_PROGRESS / 🟢 DONE / 🔄 DCR / ⛔ OBSOLETE |
| `Scenario Coverage:` | Yes | @scenario-id list from .feature files, or `N/A` for non-BDD tasks |

### 7.3 DAG Metadata (Optional)

Task blocks **MAY** carry DAG metadata for parallel execution and adaptive model routing:

| Field | Purpose |
| :--- | :--- |
| `TaskID` | Unique identifier for DAG resolution |
| `DependsOn` | Lists prerequisite TaskIDs; `None` = can run in parallel |
| `Complexity` | `Low` → fast model, `High` → reasoning model |

### 7.4 Step Checkbox Requirement

Each task block **MUST** include at least one checkbox step using markdown checkbox syntax:

```text
- [ ] Step 1: Write the failing test
```

### 7.5 Allowed Task States

Allowed task status values are:

- `🔴 TODO`
- `🟡 IN_PROGRESS`
- `🟢 DONE`
- `🔄 DCR`
- `⛔ OBSOLETE`

Legacy `TODO` (without emoji) and `IN PROGRESS` (with space) are accepted only as input-compatibility states and must be normalized before execution begins.

### 7.6 Allowed State Transitions

Normal path: `🔴 TODO -> 🟡 IN PROGRESS -> 🟢 DONE`. Exceptional states: `🔄 DCR` (design blockage; halts forward progress) and `⛔ OBSOLETE` (only by refinement or replanning logic).

- `🟢 DONE` requires completion evidence in `Verification:`.
- The validator does NOT reconstruct transition history from a single markdown snapshot.

### 7.7 `N/A` Semantics

`Scenario Coverage: N/A` is valid literal for non-BDD tasks (e.g., pure infrastructure scaffolding). No reason text is required — the literal `N/A` is sufficient.

### 7.8 `tasks.md` Validation Rules

The following rules **MUST** be enforced by the validator:

- At least one valid `### Task X.Y:` block **MUST** exist.
- Every task block **MUST** be independently parseable.
- Duplicate task IDs **MUST NOT** be accepted.
- A task heading without the 4 required fields is invalid.
- A required field **MUST NOT** be satisfied by an empty placeholder.

## 8. `features/*.feature` Contract

### 8.1 Minimum Requirement

A build-eligible spec **MUST** contain at least one `.feature` file under `features/` with at least one `Scenario`.

### 8.2 Scenario Coverage Expectations

The contract expects:

- user-visible or acceptance-tested behavior to be represented by Gherkin scenarios
- `Scenario Coverage:` in `tasks.md` to reference concrete scenarios (or literal `N/A` for non-BDD tasks)
- future validator support to confirm that referenced scenarios exist

### 8.3 Current Validation Baseline

The minimum current baseline is:

- At least one `.feature` file **MUST** exist.
- At least one `Scenario` **MUST** exist.

## 9. `Scenario Coverage` Contract

`Scenario Coverage` is the linkage field between `tasks.md` and `features/*.feature`.

### 9.1 Required Behavior

- For BDD tasks, `Scenario Coverage:` **MUST** name one or more concrete scenarios via `@scenario-id`.
- For non-BDD tasks (pure infrastructure, scaffolding), `Scenario Coverage:` **MAY** be the literal `N/A`.

### 9.2 Orphan Scenario Detection

The following invariant **MUST** be enforced:

- Each executable behavior scenario **MUST** map to one or more task blocks.
- Each BDD task **MUST** map to real scenarios.
- Orphaned scenario references **MUST** be reported as validation errors.

## 10. Blocked-Build and DCR Block Contract

pb-spec carries blocked-build and design-change information in markdown blocks, not sidecar files. Both block types carry 3 required fields.

### 10.1 `🛑 Build Blocked` Block

The required header format is:

```text
🛑 Build Blocked — Task X.Y: <Task Name>
```

Required fields:

| Field | Required | Description |
| :--- | :--- | :--- |
| `Reason` | Yes | One sentence: why the build is stuck |
| `Requested Change` | Yes | One paragraph: what should change in `design.md` / `tasks.md` |
| `Impact` | Yes | List of affected task IDs and scenario tags |

### 10.2 `🔄 Design Change Request` Block

The required header format is:

```text
🔄 Design Change Request — Task X.Y: <Task Name>
```

Required fields (same 3-field schema as Build Blocked):

| Field | Required | Description |
| :--- | :--- | :--- |
| `Reason` | Yes | One sentence: why the design needs to change |
| `Requested Change` | Yes | One paragraph: what should change in `design.md` / `tasks.md` |
| `Impact` | Yes | List of affected task IDs and scenario tags |

### 10.3 Block Validation Rules

The following rules **MUST** be enforced:

- Missing required fields **MUST** make the block incomplete.
- Incomplete blocks **MUST** be rejected by refiner-side validation.
- `Reason` and `Requested Change` **MUST NOT** be empty placeholders.
- `Impact` **MUST** list concrete task IDs or scenario tags.

## 11. Build Eligibility

A spec **MUST** satisfy all of the following to be build-eligible:

1. The 5 required `design.md` sections **MUST** be present and non-empty.
2. `tasks.md` **MUST** contain at least one valid task block.
3. Each task block **MUST** contain the 4 required fields.
4. Task statuses **MUST** be valid.
5. `features/` **MUST** contain at least one `.feature` file with at least one `Scenario`.

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

Required sections, task fields, and validation rules are loaded from `validation/contract_sections.toml` — the single source of truth. The TOML config must stay synchronized with this contract document.

## 13. RFC 2119 Constraint Language

This contract uses [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) keywords to define requirement levels for agent behavior.

| Keyword | Meaning | Usage in This Contract |
| :--- | :--- | :--- |
| **MUST** | Absolute requirement — the agent SHALL NOT skip this action | Required sections, required fields, build-eligibility gates |
| **MUST NOT** | Absolute prohibition — the agent SHALL NOT perform this action | Validation must not modify source files, must not guess spec dirs |
| **SHOULD** | Recommended practice — valid reasons to deviate must be documented | Optional fields, suggested patterns, formatting preferences |
| **SHOULD NOT** | Not recommended — acceptable only with explicit justification | Avoiding placeholder content, avoiding generic boilerplate |
| **MAY** | Truly optional — implementation is entirely at the agent's discretion | Conditional sections, optional DAG metadata |

### 13.1 Constraint Application Rules

- Every validation error **MUST** be reported with file path, line number (when available), and severity level.
- Every required section **MUST** contain substantive content — empty placeholders (`TBD`, `[To be written]`) do NOT satisfy a requirement.
- The validator **MUST** exit with non-zero status code when any CRITICAL or HIGH severity error is found.
- The validator **SHOULD** exit with non-zero status code when any MEDIUM severity error is found.
- The validator **MAY** continue past LOW severity issues without failing.
- `rumdl` formatting checks **SHOULD** run when the tool is available, but the validator **MUST NOT** fail when `rumdl` is not installed.
- Task status transitions **SHOULD** follow `🔴 TODO → 🟡 IN PROGRESS → 🟢 DONE`. The validator **MUST NOT** enforce transition history from a single snapshot.
- The validator **MUST NOT** modify source files — all operations are read-only.
- Build-blocked and DCR blocks **MUST** contain all 3 required fields; incomplete blocks **MUST** be rejected.

## 14. Parameterization

The `pb-spec validate` command supports parameterized configuration to adapt validation rules across different projects and workflow scales.

### 14.1 CLI Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--plan` | flag | — | Validate spec documents after /pb-plan |
| `--build` | flag | — | Validate task completion after /pb-build |
| `--task` | flag | — | Subagent self-check before READY_FOR_EVAL |
| `--specs-dir` | path | `specs/` | Path to specs directory |

**MUST** specify exactly one of `--plan`, `--build`, or `--task`. The validator **MUST** reject combined flags (e.g., `--plan --build`).

### 14.2 Contract Configuration

Validation rules are loaded from `contract_sections.toml` at import time. Projects **MAY** override rules by placing a `contract_sections.toml` in the spec directory. When a project-specific config exists, the validator **MUST** use it instead of the default.

### 14.3 Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PB_SPEC_GIT_TIMEOUT` | `60` | Timeout for git commands (seconds) |
| `PB_SPEC_RUMDL_CHECK_TIMEOUT` | `10` | Timeout for rumdl availability check (seconds) |
| `PB_SPEC_RUMDL_FORMAT_TIMEOUT` | `30` | Timeout for rumdl formatting (seconds) |

## 15. Validator-Ready Priorities

The validator implements the following checks in priority order:

1. parse `tasks.md` task blocks
2. validate the 4 required task fields
3. validate task state values
4. inventory `.feature` scenario names
5. verify `Scenario Coverage:` references resolve when they claim concrete coverage
6. `design.md` section completeness (5 required + 5 optional)
7. blocked-build and DCR block completeness (3 fields each)
8. placeholder detection and empty-section rejection

## 16. Summary

pb-spec's contract makes the current markdown workflow explicit for:

- maintainers
- prompt authors
- parser and validator implementations
- CI and tooling integrations

The canonical planning surface remains `design.md + tasks.md + features/*.feature`. All validation rules are expressed using RFC 2119 constraint language and loaded from `contract_sections.toml` as the single source of truth.
