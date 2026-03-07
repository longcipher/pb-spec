# [Feature Name] — Implementation Tasks

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | [Link to specs/YYYY-MM-DD-NO-feature-name/design.md] |
| **Owner** | [Name] |
| **Start Date** | YYYY-MM-DD |
| **Target Date** | YYYY-MM-DD |
| **Status** | Planning / In Progress / Completed |

## Summary & Phasing

> Brief implementation strategy.

- **Property Testing Rule:** Add property-test coverage with `Hypothesis`, `fast-check`, or `proptest` for broad input-domain logic unless the task explicitly justifies why example-based tests are sufficient.
- **Fuzzing Rule:** Add `Atheris`, `jazzer.js`, or `cargo-fuzz` only for parsers, protocols, unsafe/native boundaries, binary formats, or other untrusted-input crash-safety work.
- **Benchmark Rule:** Add `pytest-benchmark`, `Vitest Bench`, or `criterion` only when the requirement or codebase defines performance-sensitive behavior.
- **Identity Alignment Rule:** If the repo still contains generic crate/package/module names from a template, front-load rename work before dependent implementation tasks.
- **Behavior Preservation Rule:** State whether each task preserves existing behavior or intentionally changes it; validate that with scenario and regression coverage.
- **Simplification Rule:** Prefer explicit, readable implementation steps that reduce unnecessary nesting, redundancy, or naming ambiguity without broadening scope.
- **Clarity Guardrail:** Avoid planning dense or clever rewrites; where relevant, avoid nested ternary operators in favor of clearer branching.
- **Phase 1: BDD Harness & Scaffolding** — Feature files, runner setup, task skeletons
- **Phase 2: Scenario Implementation** — Primary behavior implemented via TDD
- **Phase 3: Integration & Features** — Connecting pieces, end-to-end
- **Phase 4: Polish, QA & Docs** — Tests, cleanup, documentation

---

## Phase 1: BDD Harness & Scaffolding

### Task 1.1: [Task Name]

> **Context:** Why this task exists and what it enables. Reference existing components to reuse if applicable.
> **Verification:** How to prove this task is done.

- **Priority:** P0 / P1 / P2
- **Scope:** [Logical Unit of Work — e.g., "Model layer", "API endpoint", "Service integration"]
- **Scenario Coverage:** `[Feature/scenario names, or N/A for infrastructure-only work]`
- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Advanced Test Coverage:** `Example-based only` / `Property` / `Fuzz` / `Benchmark` / `Combination`
- **Status:** 🔴 TODO
- [ ] **Step 1:** ...
- [ ] **Step 2:** ...
- [ ] **BDD Verification:** [Concrete scenario check — e.g., "run `behave features/auth.feature` and confirm Scenario X fails first, then passes"]
- [ ] **Verification:** [Concrete check — e.g., "run `pytest tests/test_config.py` and all pass"]
- [ ] **Advanced Test Verification:** [Concrete command for `Hypothesis`, `fast-check`, `proptest`, `Atheris`, `jazzer.js`, `cargo-fuzz`, `pytest-benchmark`, `Vitest Bench`, or `criterion`; if not needed, write `N/A` with reason]
- [ ] **Runtime Verification (if applicable):** [Capture runtime signals — e.g., `tail -n 50 app.log` and `curl http://localhost:8080/health`; if not applicable, write `N/A` with reason]

### Task 1.2: [Task Name]

> **Context:** ...
> **Verification:** ...

- **Priority:** P0
- **Scope:** [Logical Unit of Work]
- **Scenario Coverage:** `[Feature/scenario names, or N/A]`
- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Advanced Test Coverage:** `Example-based only` / `Property` / `Fuzz` / `Benchmark` / `Combination`
- **Status:** 🔴 TODO
- [ ] **Step 1:** ...
- [ ] **Step 2:** ...
- [ ] **BDD Verification:** [Run scenario command and confirm expected red/green outcome]
- [ ] **Verification:** ...
- [ ] **Advanced Test Verification:** [Command or `N/A` with reason]
- [ ] **Runtime Verification (if applicable):** [Logs + probe result, or `N/A` with reason]

---

## Phase 2: Scenario Implementation

### Task 2.1: [Task Name]

> **Context:** ...
> **Verification:** ...

- **Priority:** P0
- **Scope:** [Logical Unit of Work]
- **Scenario Coverage:** `[Feature/scenario names, or N/A]`
- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Advanced Test Coverage:** `Example-based only` / `Property` / `Fuzz` / `Benchmark` / `Combination`
- **Status:** 🔴 TODO
- [ ] **Step 1:** ...
- [ ] **Step 2:** ...
- [ ] **Step 3:** ...
- [ ] **BDD Verification:** [Run scenario command and confirm expected red/green outcome]
- [ ] **Verification:** ...
- [ ] **Advanced Test Verification:** [Command or `N/A` with reason]
- [ ] **Runtime Verification (if applicable):** [Logs + probe result, or `N/A` with reason]

### Task 2.2: [Task Name]

> **Context:** ...
> **Verification:** ...

- **Priority:** P1
- **Scope:** [Logical Unit of Work]
- **Scenario Coverage:** `[Feature/scenario names, or N/A]`
- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Advanced Test Coverage:** `Example-based only` / `Property` / `Fuzz` / `Benchmark` / `Combination`
- **Status:** 🔴 TODO
- [ ] **Step 1:** ...
- [ ] **Step 2:** ...
- [ ] **BDD Verification:** [Run scenario command and confirm expected red/green outcome]
- [ ] **Verification:** ...
- [ ] **Advanced Test Verification:** [Command or `N/A` with reason]
- [ ] **Runtime Verification (if applicable):** [Logs + probe result, or `N/A` with reason]

---

## Phase 3: Integration & Features

### Task 3.1: [Task Name]

> **Context:** ...
> **Verification:** ...

- **Priority:** P1
- **Scope:** [Logical Unit of Work]
- **Scenario Coverage:** `[Feature/scenario names, or N/A]`
- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Status:** 🔴 TODO
- [ ] **Step 1:** ...
- [ ] **Step 2:** ...
- [ ] **BDD Verification:** [Run scenario command and confirm expected red/green outcome]
- [ ] **Verification:** ...
- [ ] **Runtime Verification (if applicable):** [Logs + probe result, or `N/A` with reason]

---

## Phase 4: Polish, QA & Docs

### Task 4.1: [Task Name]

> **Context:** ...
> **Verification:** ...

- **Priority:** P2
- **Scope:** [Logical Unit of Work]
- **Scenario Coverage:** `[Feature/scenario names, or N/A]`
- **Loop Type:** `BDD+TDD` / `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior` / `[Describe intentional behavior change]`
- **Simplification Focus:** `[Reduce nesting / remove redundancy / improve naming / consolidate related logic / N/A]`
- **Advanced Test Coverage:** `Example-based only` / `Property` / `Fuzz` / `Benchmark` / `Combination`
- **Status:** 🔴 TODO
- [ ] **Step 1:** ...
- [ ] **Step 2:** ...
- [ ] **BDD Verification:** [Run scenario command and confirm expected red/green outcome]
- [ ] **Verification:** ...
- [ ] **Advanced Test Verification:** [Command or `N/A` with reason]

---

## Summary & Timeline

| Phase | Tasks | Target Date |
| :--- | :---: | :--- |
| **1. Foundation** | N | MM-DD |
| **2. Core Logic** | N | MM-DD |
| **3. Integration** | N | MM-DD |
| **4. Polish** | N | MM-DD |
| **Total** | **N** | |

## Definition of Done

> Every task must meet these criteria before being marked complete.

1. [ ] **Linted:** No lint errors (project linter passes).
2. [ ] **Tested:** Unit tests covering the added logic.
3. [ ] **Formatted:** Code formatter applied.
4. [ ] **Verified:** The task's specific Verification criterion is met.
5. [ ] **Advanced-Tested (when applicable):** Property/fuzz/benchmark verification is captured, or `N/A` is explicitly justified.
6. [ ] **Runtime-Evidenced (when applicable):** Runtime logs and health/probe results are captured, or `N/A` is explicitly justified.
7. [ ] **Behavior-Preserved or Documented:** The task confirms behavior preservation or documents the intentional behavior change.
8. [ ] **Simplified Responsibly:** Cleanup stayed within the planned scope and improved readability rather than introducing clever compaction.
