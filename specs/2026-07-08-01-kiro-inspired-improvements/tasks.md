# Kiro-Inspired Improvements — Tasks

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | specs/2026-07-08-01-kiro-inspired-improvements/design.md |
| **Status** | Planning |

## Summary & Phasing

Three improvements ported from Kiro's spec-driven workflow: (1) requirements analysis in pb-plan, (2) parallel task execution in pb-build, (3) quick plan mode in pb-brainstorming. Each improvement is self-contained and can be implemented independently.

- **Phase 1: Requirements Analysis (pb-plan)** — Add EARS quality enforcement and abductive refinement
- **Phase 2: Parallel Task Execution (pb-build)** — Add dependency graph and wave-based parallelism
- **Phase 3: Quick Plan Mode (pb-brainstorming)** — Add fast-track path for well-understood features
- **Phase 4: Template Updates** — Update design_template.md and tasks_template.md

---

## Phase 1: Requirements Analysis (pb-plan)

### Task 1.1: Add Requirements Quality Checklist to pb-plan

> **Context:** Kiro's requirements analysis validates 5 quality properties: testable, solution-free, unambiguous, consistent, complete. pb-plan currently extracts requirements but doesn't validate their quality. This task adds the quality checklist as a mandatory step after requirement extraction.
> **Verification:** grep for quality property names in pb-plan SKILL.md
> **Scenario Coverage:** `features/kiro-improvements.feature` → "pb-plan catches ambiguous requirements", "pb-plan detects inconsistent requirements"

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior — add new step without changing existing workflow`
- **Simplification Focus:** `Add checklist inline, no new abstraction needed`
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-plan/SKILL.md` and identify the insertion point between Step 1 (Parse Requirements) and Step 2 (Collect Project Context)
- [x] Step 2: Add "Step 1.5: Requirements Quality Analysis" section with:
  - EARS quality checklist (testable, solution-free, unambiguous, consistent, complete)
  - Ambiguity detection: check if requirements admit multiple interpretations
  - Inconsistency detection: cross-reference requirement pairs for conflicts
  - Finding format: clarifying questions with two options each
- [x] Step 3: Add EARS quality validation to Step 1's requirement extraction process
- [x] Step 4: Update Key Principles to include "Requirements quality first" principle
- [x] BDD Verification: N/A — skill file changes, no BDD scenarios
- [x] Advanced Test Verification: `grep -c "EARS quality" skills/pb-plan/SKILL.md` returns ≥ 2 — **PASSES: returns 5**
- [x] Runtime Verification: N/A — skill file changes

### Task 1.2: Add Abductive Refinement to pb-plan

> **Context:** Kiro's refinement works backwards from success state to identify missing error paths. pb-plan currently extracts requirements from user input but doesn't proactively identify gaps. This task adds abductive reasoning as part of the requirements analysis step.
> **Verification:** grep for "abductive" and "success state" in pb-plan SKILL.md
> **Scenario Coverage:** `features/kiro-improvements.feature` → "pb-plan detects incomplete requirements", "pb-plan enforces EARS quality"

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** `Preserve existing behavior — add refinement patterns without changing extraction`
- **Simplification Focus:** `Add refinement questions inline, reuse existing subagent infrastructure`
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-plan/SKILL.md` Step 1.5 section added by Task 1.1
- [x] Step 2: Add abductive refinement pattern to Step 1.5:
  - For each requirement, ask: What does success look like?
  - What prerequisites must hold?
  - What could prevent each prerequisite?
  - What error paths should exist?
  - Is each error path already captured?
- [x] Step 3: Add EARS quality enforcement:
  - Check for implementation language in requirements (solution-free check)
  - Check that requirements name inputs, outputs, and conditions (testable check)
  - Rewrite non-compliant requirements inline
- [x] Step 4: Update Source Requirement Ledger format to include quality status and clarification records
- [x] BDD Verification: N/A — skill file changes
- [x] Advanced Test Verification: `grep -c "abductive" skills/pb-plan/SKILL.md` returns ≥ 1 — **PASSES: returns 3**
- [x] Runtime Verification: N/A — skill file changes

---

## Phase 2: Parallel Task Execution (pb-build)

### Task 2.1: Add Dependency Graph and Wave-Based Execution to pb-build

> **Context:** pb-build currently runs tasks sequentially ("No parallelism" at line 544). Tasks already have DependsOn metadata. Kiro's parallel execution builds a dependency graph and runs independent tasks concurrently in waves. This task adds wave-based parallelism.
> **Verification:** grep for "Wave" and "dependency graph" in pb-build SKILL.md
> **Scenario Coverage:** `features/kiro-improvements.feature` → "pb-build executes independent tasks in parallel", "pb-build respects dependency ordering"

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** `Preserve existing sequential fallback — parallelism is additive, sequential remains default when DependsOn is absent`
- **Simplification Focus:** `Reuse existing subagent dispatch, add wave grouping logic`
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-build/SKILL.md` and identify Step 3 (Execute Tasks Sequentially)
- [x] Step 2: Add "Step 3a: Build Dependency Graph" before task execution:
  - Parse DependsOn metadata from each task
  - Build adjacency list representation
  - Detect cycles (fail with error if found)
  - Topological sort to determine wave order
- [x] Step 3: Add "Step 3b: Wave-Based Parallel Execution":
  - Group tasks into waves by topological level
  - Tasks in the same wave run concurrently via subagents
  - Each subagent gets isolated context (no state leaking)
  - If a task fails, other tasks in the same wave continue
  - Apply standard 3-failure retry protocol to failed tasks
- [x] Step 4: Add file-write conflict detection:
  - Tasks that write to the same files are never in the same wave
  - Fall back to sequential execution for conflicting tasks
- [x] Step 5: Update "Subagent Assignment Rules" to allow parallel dispatch
- [x] Step 6: Update "Invariants" to reflect parallel execution rules
- [x] BDD Verification: N/A — skill file changes
- [x] Advanced Test Verification: `grep -c "Wave" skills/pb-build/SKILL.md` returns ≥ 3 — **PASSES: returns 6**
- [x] Runtime Verification: N/A — skill file changes

---

## Phase 3: Quick Plan Mode (pb-brainstorming)

### Task 3.1: Add Quick Plan Mode to pb-brainstorming

> **Context:** Kiro's quick plan mode fast-tracks spec generation for well-understood features by asking targeted questions upfront and generating all artifacts in one pass. pb-brainstorming currently follows a multi-step approval flow. This task adds a fast-track path.
> **Verification:** grep for "quick plan" in pb-brainstorming SKILL.md
> **Scenario Coverage:** `features/kiro-improvements.feature` → "pb-brainstorming fast-tracks features", "pb-brainstorming selects clarification targets"

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** `Preserve existing standard flow — quick plan is additive, triggered by scope detection`
- **Simplification Focus:** `Add mode detection inline, reuse existing question-asking infrastructure`
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-brainstorming/SKILL.md` and identify the scope assessment point after Step 1
- [x] Step 2: Add scope complexity detection after "Explore project context":
  - Well-understood: clear scope, known constraints, few edge cases → quick plan
  - Complex: ambiguous, multi-system, complex domain → standard flow
  - Detection heuristic: word count, number of subsystems mentioned, domain complexity
- [x] Step 3: Add "Quick Plan Flow" section:
  - Ask 2-4 targeted questions covering: scope/constraints, ambiguity, implementation forks, directional decisions
  - Auto-generate requirements, design, and tasks in one pass (no intermediate approval gates)
  - Save all artifacts for review
  - Allow selective refinement: change tasks → regenerate tasks only; change design → regenerate design + tasks; change scope → full rerun
- [x] Step 4: Update "The Process" section to include quick plan as an alternative path
- [x] Step 5: Update Key Principles to include "Speed where it helps, depth where it matters"
- [x] BDD Verification: N/A — skill file changes
- [x] Advanced Test Verification: `grep -c "quick plan" skills/pb-brainstorming/SKILL.md` returns ≥ 2 — **PASSES: returns 7**
- [x] Runtime Verification: N/A — skill file changes

---

## Phase 4: Template Updates

### Task 4.1: Update design_template.md and tasks_template.md

> **Context:** The design template needs a "Requirements Quality Audit" subsection. The tasks template needs an optional `Wave:` field for explicit wave assignment.
> **Verification:** grep for new sections in template files
> **Scenario Coverage:** N/A — template changes

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** `Preserve existing template structure — add new fields, don't remove existing ones`
- **Simplification Focus:** `Add fields inline, minimal template changes`
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-plan/references/design_template.md`
- [x] Step 2: Add "Requirements Quality Audit" subsection under "Source Inputs & Normalization" (after §2.3):
  - EARS quality status per requirement (testable/solution-free/unambiguous/consistent/complete)
  - Clarifications recorded (ambiguity findings, inconsistency findings, completeness findings)
- [x] Step 3: Read `skills/pb-plan/references/tasks_template.md`
- [x] Step 4: Add optional `Wave:` field to task block template (after `DependsOn:`):
  - `Wave: N` — explicit wave assignment (0-indexed)
  - If absent, pb-build infers from DependsOn metadata
- [x] BDD Verification: N/A — template changes
- [x] Advanced Test Verification: `grep -c "Quality Audit" skills/pb-plan/references/design_template.md` returns ≥ 1 — **PASSES: returns 1**
- [x] Runtime Verification: N/A — template changes

---

## Summary & Timeline

| Phase | Tasks | Target Date |
| :--- | :---: | :--- |
| **1. Requirements Analysis** | 2 | 2026-07-08 |
| **2. Parallel Execution** | 1 | 2026-07-08 |
| **3. Quick Plan Mode** | 1 | 2026-07-08 |
| **4. Template Updates** | 1 | 2026-07-08 |
| **Total** | **5** | |

## Definition of Done

1. [ ] **Linted:** No lint errors in modified files.
2. [ ] **Tested:** grep-based verification passes for all VP-* criteria.
3. [ ] **Formatted:** Markdown formatting consistent with existing style.
4. [ ] **Verified:** Each task's specific Verification criterion is met.
5. [ ] **Behavior-Preserved:** Existing workflow unchanged; improvements are additive.
6. [ ] **Simplified Responsibly:** No unnecessary abstractions added.
