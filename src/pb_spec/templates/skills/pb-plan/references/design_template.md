# Design Document: [Feature Name]

| Metadata | Details |
| :--- | :--- |
| **Author** | [Name or "pb-plan agent"] |
| **Status** | Draft |
| **Created** | YYYY-MM-DD |
| **Reviewers** | [Name 1], [Name 2] |
| **Related Issues** | #[Issue ID] or N/A |

## 1. Executive Summary

> 2-3 sentences: What problem are we solving? What is the proposed solution?

**Problem:** ...
**Solution:** ...

---

## 2. Requirements & Goals

### 2.1 Problem Statement

> Describe current pain points or missing functionality. Be specific.

### 2.2 Functional Goals

> Must-have features. Numbered list.

1. **[Goal A]:** Description...
2. **[Goal B]:** Description...

### 2.3 Non-Functional Goals

> Performance, reliability, security, observability, etc.

- **Performance:** ...
- **Reliability:** ...
- **Security:** ...

### 2.4 Out of Scope

> What is explicitly NOT being done. Prevents scope creep.

### 2.5 Assumptions

> Any assumptions or constraints. List decisions made when requirements were ambiguous.

### 2.6 Code Simplification Constraints

> Document the maintainability rules that should shape implementation decisions.

- **Behavior Preservation Boundary:** What must remain unchanged unless an acceptance scenario or explicit requirement says otherwise.
- **Repo Standards To Follow:** Language- and framework-specific coding standards inferred from `AGENTS.md`, `CLAUDE.md`, and the live codebase. Only include standards that are actually relevant to this repo.
- **Readability Priorities:** Prefer explicit control flow, clear naming, reduced nesting, and removal of redundant abstractions when that improves maintainability.
- **Refactoring Non-Goals:** Unrelated cleanup stays out of scope unless the design explicitly justifies a broader refactor.
- **Clarity Guardrails:** Avoid dense or clever rewrites. In languages where it applies, avoid nested ternary operators in favor of clearer branching.

---

## 3. Architecture Overview

### 3.1 System Context

> How does this feature fit into the existing system? Describe interactions with other modules, services, or external systems. Use a diagram if helpful.

### 3.2 Key Design Principles

> Core ideas guiding this design. Examples: "Separation of concerns", "Fail-fast", "Backward-compatible API".

### 3.3 Existing Components to Reuse

> **Mandatory:** Before designing new modules, search the existing codebase for reusable components. List any existing utilities, clients, base classes, or patterns that this feature MUST reuse instead of reimplementing.

| Component | Location | How to Reuse |
| :--- | :--- | :--- |
| [e.g., RedisClient] | [src/utils/redis.py] | [Use for all cache operations] |
| [e.g., BaseModel] | [src/models/base.py] | [Extend for new data models] |

> If no reusable components exist, state "No existing components identified for reuse" and explain why.

### 3.4 Project Identity Alignment

> If the repository appears to come from a template/scaffold, identify any generic crate/package/module names that must be renamed to match the current project or product identity before feature work is complete.

| Current Identifier | Location | Why It Is Generic or Misaligned | Planned Name / Action |
| :--- | :--- | :--- | :--- |
| `[e.g., template_app]` | `[e.g., pyproject.toml, src/template_app/]` | `[Placeholder copied from scaffold]` | `[Rename to current project package]` |

> If no identity cleanup is needed, state "No template identity mismatches detected.".

### 3.5 BDD/TDD Strategy

> Describe how this feature will use outside-in development. Define the business-facing Gherkin loop and the supporting TDD loop.

- **BDD Runner:** `[e.g., @cucumber/cucumber | behave | cucumber]`
- **BDD Command:** `[e.g., npm exec cucumber-js features/auth.feature]`
- **Unit Test Command:** `[e.g., pytest tests/auth/test_service.py -v]`
- **Property Test Tool:** `[e.g., fast-check | Hypothesis | proptest | N/A with reason]`
- **Fuzz Test Tool:** `[e.g., jazzer.js | Atheris | cargo-fuzz | N/A with reason]`
- **Benchmark Tool:** `[e.g., Vitest Bench | pytest-benchmark | criterion | N/A with reason]`
- **Outer Loop:** `[Which`.feature`scenarios prove the behavior works end-to-end]`
- **Inner Loop:** `[Which unit/component tests will drive the underlying implementation]`
- **Step Definition Location:** `[e.g., features/steps/, tests/bdd/, crates/app/tests/]`

> Property testing should be planned by default for large input domains such as parsers, serializers, normalization, versioning rules, combinatorial business logic, or boundary-heavy validation. Fuzzing is conditional for parser/protocol/unsafe/untrusted-input crash-safety work. Benchmarks are conditional for explicit performance-sensitive paths.

### 3.6 BDD Scenario Inventory

> List every scenario that should be planned as a first-class acceptance artifact.

| Feature File | Scenario | Business Outcome | Primary Verification | Supporting TDD Focus |
| :--- | :--- | :--- | :--- | :--- |
| `features/[feature-name].feature` | `[Scenario Name]` | `[User-visible result]` | `[BDD command or acceptance check]` | `[Unit/component logic to drive with TDD]` |

### 3.7 Simplification Opportunities in Touched Code

> Identify the specific cleanup that should happen alongside the feature without broadening scope.

| Area | Current Complexity or Smell | Planned Simplification | Why It Preserves or Clarifies Behavior |
| :--- | :--- | :--- | :--- |
| `[e.g., version parser]` | `[Nested branching and duplicate normalization paths]` | `[Flatten control flow and centralize normalization]` | `[Keeps existing outputs while making the logic easier to reason about]` |

---

## 4. Detailed Design

### 4.1 Module Structure

> File/directory layout for the new or modified code. If the repo still exposes scaffold placeholders, show the project-matching module/package/crate names after the planned rename.

```text
src/
├── module_name/
│   ├── __init__.py
│   ├── core.py
│   ├── models.py
│   └── utils.py
```

### 4.2 Data Structures & Types

> Define core data models, classes, enums, or schemas.

```text
# Example pseudo-code — adapt to project language
class FeatureConfig:
    enabled: bool
    max_retries: int
    timeout_seconds: float

class FeatureState:
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
```

### 4.3 Interface Design

> Public APIs, function signatures, abstract interfaces, or protocols this feature exposes or consumes.

```text
class FeatureInterface:
    def execute(input: InputType) -> OutputType:
        """Describe purpose and contract."""
        ...
```

### 4.4 Logic Flow

> Describe key workflows, state transitions, or processing pipelines. Use step-by-step descriptions or diagrams.
>
> Keep the proposed flow explicit and easy to follow. Prefer straightforward branching and cohesive helper boundaries over compact but opaque control flow.

### 4.5 Configuration

> Any new config values, environment variables, or feature flags introduced.

### 4.6 Error Handling

> Error types, failure modes, and recovery strategy.

### 4.7 Maintainability Notes

> Call out any implementation guardrails that keep the change readable and easy to extend.

- Prefer focused helpers over oversized multi-purpose functions when a split improves clarity.
- Do not remove abstractions that the codebase already uses effectively for separation of concerns.
- Keep refactor scope limited to touched modules unless the design explicitly expands it.

---

## 5. Verification & Testing Strategy

### 5.1 Unit Testing

> What pure logic to test. Scope and tooling.
>
> Include regression checks that prove any planned simplification preserves behavior, not just happy-path outcomes.

### 5.2 Property Testing

> Identify where example-based tests leave too much input space uncovered. Use the language-appropriate property-testing tool (`Hypothesis`, `fast-check`, or `proptest`) unless you can justify that the logic is too trivial or already fully covered by a smaller deterministic domain.

| Target Behavior | Why Property Testing Helps | Tool / Command | Planned Invariants |
| :--- | :--- | :--- | :--- |
| `[e.g., version string normalization]` | `[Large combinatorial input space]` | `[e.g., uv run pytest tests/test_version_properties.py -q]` | `[Round-trip, idempotence, monotonicity, etc.]` |

### 5.3 Integration Testing

> How modules work together. Mock strategies, sandbox environments.

### 5.4 BDD Acceptance Testing

> Which `.feature` files and scenarios must fail first and then pass. Include the exact BDD runner command.

| Scenario ID | Feature File | Command | Success Criteria |
| :--- | :--- | :--- | :--- |
| **BDD-01** | `[e.g., features/auth.feature]` | `[e.g., npm exec cucumber-js features/auth.feature]` | `[e.g., Scenario passes with 0 failed steps]` |

### 5.5 Robustness & Performance Testing

> Plan these only when the task profile requires them.

| Test Type | When It Is Required | Tool / Command | Planned Coverage or Reason Not Needed |
| :--- | :--- | :--- | :--- |
| **Fuzz** | `[Parser/protocol/unsafe/untrusted-input paths only]` | `[e.g., cargo fuzz run parser]` | `[Crash-safety target, or N/A with reason]` |
| **Benchmark** | `[Explicit latency/throughput/hot-path requirements only]` | `[e.g., uv run pytest tests/benchmarks/test_cli.py --benchmark-only]` | `[Regression budget, or N/A with reason]` |

### 5.6 Critical Path Verification (The "Harness")

> Define the exact command(s) or script(s) that prove this feature works end-to-end. The `pb-build` agent will use these to verify the final result. This acts as the acceptance test for the entire feature.

| Verification Step | Command | Success Criteria |
| :--- | :--- | :--- |
| **VP-01** | `[e.g., python scripts/verify_auth.py]` | `[e.g., "Output contains 'Authenticated'"]` |
| **VP-02** | `[e.g., curl -v http://localhost:8000/health]` | `[e.g., "Response code 200"]` |
| **VP-03** | `[e.g., pytest tests/ -v --tb=short]` | `[e.g., "All tests pass, 0 failures"]` |

> **Why this matters:** By defining verification commands at design time, the build agent does not need to invent its own verification strategy — it simply executes these commands and checks the criteria. This dramatically improves reliability.

### 5.7 Validation Rules

| Test Case ID | Action | Expected Outcome | Verification Method |
| :--- | :--- | :--- | :--- |
| **TC-01** | [Action] | [Expected result] | [How to verify] |
| **TC-02** | [Action] | [Expected result] | [How to verify] |
| **TC-03** | [Action] | [Expected result] | [How to verify] |

---

## 6. Implementation Plan

> Phase checklist — high-level roadmap mapping to tasks.md.

- [ ] **Phase 1: Foundation** — Scaffolding, config, core types
- [ ] **Phase 2: Core Logic** — Primary feature implementation
- [ ] **Phase 3: Integration** — Wire into existing system, end-to-end flow
- [ ] **Phase 4: Polish** — Tests, docs, error handling, CI

---

## 7. Cross-Functional Concerns

> Security review, backward compatibility, migration plan, documentation updates, monitoring/alerting, or rollback strategy — if applicable.
