# Design: <feature-name>

> Scalable design document. The 5 required sections MUST be present. The 5
> optional sections MAY be added when the work is non-trivial. Skip optional
> sections rather than writing "N/A".

## Metadata

| Field | Value |
| :--- | :--- |
| Spec Directory | specs/<spec-dir>/ |
| Status | Draft |
| Date | YYYY-MM-DD |
| Commit | <git rev-parse --short HEAD> |

## Summary <!-- REQUIRED -->

<2-4 sentences: what changes, why, user-visible impact>

## Approach <!-- REQUIRED -->

<Chosen approach in 1-2 paragraphs. Compare 1-2 alternatives considered and
why this one wins. Reference ponytail ladder: YAGNI → stdlib → native →
existing dep → one-liner → minimum code.>

## Architecture Decisions <!-- REQUIRED -->

<!-- Use MADR format. One sub-section per decision. -->

### [ADR-001] <decision title>

- **Context:** <why this decision is needed>
- **Decision:** <what was decided>
- **Consequences:** <trade-offs, risks, follow-ups>

## BDD/TDD Strategy <!-- REQUIRED -->

<List the Gherkin scenarios from features/*.feature that this design realizes.
State the TDD inner-loop: Red → Green → Refactor. Note any Hypothesis property
tests needed.>

## Verification <!-- REQUIRED -->

<Exact commands and expected outputs. Cover: lint, type-check, unit tests, BDD
scenarios.>

---

Optional sections below — include only when the work is non-trivial

## Requirements & Goals <!-- OPTIONAL -->

<EARS notation with [REQ-XX] IDs. Only when the feature has multiple distinct
requirements that need explicit tracing.>

## Architecture Overview        <!-- OPTIONAL -->

<C4 Model + Mermaid.js diagrams. Only when the change touches system topology.>

## Data Models <!-- OPTIONAL -->

<DBML or Prisma Schema. Only when the schema changes.>

## Interface Contracts <!-- OPTIONAL -->

<Public API surface, request/response shapes, error codes. Only when the public
API changes.>

## Implementation Plan <!-- OPTIONAL -->

<High-level task ordering with dependencies. Only when the task graph is
non-obvious.>

## Revision History

| Date | Change | Reason |
| :--- | :--- | :--- |
| YYYY-MM-DD | Initial draft | /pb-plan |
