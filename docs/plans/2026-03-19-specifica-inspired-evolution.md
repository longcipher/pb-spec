# Specifica-Inspired Evolution Plan for pb-spec

| Metadata | Details |
| :--- | :--- |
| **Status** | Proposed |
| **Date** | 2026-03-19 |
| **Audience** | pb-spec maintainers |
| **Scope** | Format, validation, ecosystem, documentation |

## 1. Executive Summary

pb-spec should keep its current workflow surface and artifact family:

- `/pb-init -> /pb-plan -> /pb-refine -> /pb-build`
- `design.md + tasks.md + features/*.feature`

The project should not add a new feature-level `spec.md` file and should not replace the existing markdown workflow with YAML, JSON, or a side-channel schema language.

The strongest ideas to borrow from Specifica are not its exact file model, but its treatment of format as a first-class product surface. pb-spec already has stronger workflow and execution semantics in areas such as bounded retries, recovery loops, explicit design change requests, and BDD plus TDD build discipline. The next step is to make the existing artifact contract more explicit, machine-readable, and toolable without changing how users work.

## 2. What pb-spec Should Preserve

### 2.1 Workflow Stability

The current workflow is a strength, not a weakness:

- `pb-init` captures repo constraints and architecture context.
- `pb-plan` creates implementation-ready markdown artifacts.
- `pb-refine` updates only the affected planning artifacts.
- `pb-build` executes work through BDD and TDD loops with bounded recovery.

This flow should remain the primary user experience.

### 2.2 Artifact Family

The current artifact model is differentiated and worth preserving:

- `design.md` carries architecture and planning rationale.
- `tasks.md` carries task execution state and verification requirements.
- `features/*.feature` carries business-visible behavioral contracts.

This separation is already stronger than a generic `spec.md` because it splits architecture, execution, and acceptance behavior into independently inspectable artifacts.

### 2.3 Harness-First Execution

pb-spec should continue to prioritize:

- explicit verification
- architecture continuity
- bounded retries
- recovery loops
- design change requests

These are core product advantages and should not be diluted in pursuit of a simpler format story.

## 3. What Specifica Gets Right

Specifica demonstrates five ideas that are valuable for pb-spec:

1. The format itself is treated as a product, not just an implementation detail.
2. Human readability, AI readability, and tool readability are designed together.
3. Optionality is explicit. The project clearly distinguishes convention from hard requirements, which reduces ambiguity for users and tooling.
4. Parser and validator boundaries are clear, which makes ecosystem tooling possible.
5. The public story is layered: format, packages, and product are distinct.

For pb-spec, these ideas translate into clearer field optionality, a more explicit contract specification, and clearer parser versus validator boundaries around the existing markdown artifacts.

pb-spec should adopt these ideas at the contract and tooling layers while keeping its current workflow and artifact model.

## 4. Current Gaps in pb-spec

### 4.1 Contract Definition Is Distributed

The current contract lives across:

- prompt templates
- template reference files
- README prose
- design documentation
- tests that assert the presence of key phrases

This is workable, but it is less stable than having a canonical format definition.

### 4.2 Artifact Validation Before Execution Is Not Yet a First-Class Capability

`pb-build` describes a strong validation gate before implementation begins, but the repository does not yet expose the same contract as executable validation logic. In practice this means `design.md` completeness, task coherence, and scenario coverage are defined primarily in prose rather than in reusable validation code.

### 4.3 The Artifact Contract Is Not Machine-Readable Enough

Important parts of the workflow still rely on text interpretation rather than formal parsing:

- required `design.md` sections
- required task block fields
- allowed task state transitions
- block completeness for `🛑 Build Blocked` and `🔄 Design Change Request` sections
- scenario coverage linking between `tasks.md` and `features/*.feature`

### 4.4 Ecosystem Surface Is Underdeveloped

Today pb-spec is best understood as a workflow installer and template source. It is not yet equally strong as:

- a format specification
- a parser library
- a validator
- a CI-friendly contract tool

## 5. Evolution Direction

The recommended direction is:

**Keep the workflow. Keep the artifacts. Formalize the contract. Add tooling around the contract.**

This can be done without adding a new feature-level file and without changing the user-facing command surface.

## 6. Recommended Improvements

### 6.1 Must: Publish a Canonical Format and Contract Specification

Add a repository-level format document that defines the current contract precisely.

Suggested coverage:

- `design.md` required sections
- lightweight versus full-mode expectations
- `tasks.md` task block grammar
- required versus conditional task fields
- allowed task statuses and state transitions
- block schemas for `🛑 Build Blocked` and `🔄 Design Change Request`
- scenario coverage expectations for `features/*.feature`
- explicit rules for `N/A` in verification fields

This document should describe the existing workflow contract rather than invent a new one.

### 6.2 Must: Implement Internal Parsing and Validation for Existing Artifacts

Add parser and validator support for the current markdown artifacts.

The goal is not to introduce a new schema language. The goal is to make the current markdown contract executable.

The first implementation tranche should stay narrow:

- parse `tasks.md` task blocks
- validate required task fields
- validate task state transitions
- inventory `.feature` scenario names
- verify that `Scenario Coverage` references resolve to real scenarios

Suggested internal responsibilities:

- parse `design.md` into a section inventory
- parse `tasks.md` into typed task blocks
- parse `features/*.feature` into a scenario inventory
- validate required fields and cross-links
- validate task state transitions
- validate blocked-build and DCR block completeness

This should become the basis for `pb-build` Phase 0 checks and `pb-refine` packet validation.

### 6.3 Must: Add a Standalone Validation Command

Add a non-invasive validation command, for example:

```text
pb-spec validate <spec-dir>
```

This command should:

- verify that the spec is build-eligible
- report precise missing fields or malformed blocks
- validate scenario coverage references
- validate packet completeness where applicable

This strengthens the workflow without changing it.

### 6.4 Should: Make Optionality Explicit

Borrow Specifica's clarity around optionality, but apply it to fields and sections rather than files.

Examples:

- which `design.md` sections are mandatory in full mode
- which sections may be omitted in lightweight mode
- when `Runtime Verification` is required
- when `Advanced Test Verification` may be `N/A`
- when a task must be `BDD+TDD` rather than `TDD-only`

Example clarifications could include whether a lightweight `design.md` may omit implementation-plan detail, and whether a non-runtime task may mark `Runtime Verification` as `N/A` without failing validation.

This reduces ambiguity for both maintainers and agents.

### 6.5 Should: Strengthen Scenario-to-Task Traceability

pb-spec should turn `Scenario Coverage` into a stronger invariant.

Recommended rule set:

- each executable behavior scenario should map to one or more task blocks
- each `BDD+TDD` task should name concrete scenarios, not vague summaries
- validation should detect missing or orphaned scenario references

This is an intended future invariant. It is not yet fully enforced in the current repository and should be introduced through parsing and validation rather than through prose alone.

This will strengthen the build harness and make progress reporting more defensible.

### 6.6 Should: Reposition the Project in Three Layers

The public story should be clarified into three layers:

1. **Workflow layer** — the four commands and their execution semantics
2. **Contract layer** — `design.md + tasks.md + features/*.feature`
3. **Tooling layer** — validation, parsing, CI integration, and future ecosystem tools

This does for pb-spec what Specifica does with format, packages, and product, but without changing pb-spec's artifact model.

### 6.7 Could: Publish a Contract Library

Once parsing and validation stabilize, the project can expose them as a library surface.

Potential future uses:

- CI linting
- spec dashboards
- drift detection
- exporters to issue trackers or structured reports
- third-party agent tooling

This should happen after the internal contract is stable.

### 6.8 Could: Build an Artifact Gallery

Add a small set of canonical examples showing:

- a lightweight change
- a medium-sized feature
- a more architecture-heavy change

Each example should include `design.md`, `tasks.md`, and `features/*.feature` that satisfy the formal contract.

This would improve onboarding and reduce planner drift.

## 7. Explicit Non-Goals

The following changes are not recommended:

1. Do not add a new feature-level `spec.md` artifact.
2. Do not replace markdown artifacts with YAML or JSON.
3. Do not change the current command surface.
4. Do not weaken the existing harness model to match a simpler format story.
5. Do not couple validation to one AI platform or runtime.

## 8. Proposed Roadmap

### Phase 1: Contract Formalization

- write the canonical contract specification
- define required, conditional, and optional fields
- document task status transitions and block schemas
- update README positioning to reflect workflow, contract, and tooling layers

### Phase 2: Executable Validation

- implement internal markdown parsers
- implement validation over current artifacts
- add `pb-spec validate <spec-dir>`
- reuse the validator from `pb-build` and `pb-refine`

### Phase 3: Quality and Ecosystem

- add generated-artifact tests that validate build eligibility
- add canonical example specs
- expose contract parsing and validation for CI and downstream tools

## 9. Expected Outcome

If pb-spec follows this direction, it keeps its strongest differentiators while becoming more stable and more ecosystem-ready.

The end state is not "pb-spec becomes Specifica." The end state is:

- Specifica-level clarity about format and tooling boundaries
- pb-spec-level strength in execution harness, architecture continuity, and BDD/TDD workflow

That combination would make pb-spec more stable, more complete, and more advanced without changing the current workflow structure.
