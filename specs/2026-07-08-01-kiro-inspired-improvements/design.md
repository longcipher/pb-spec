# Design: Kiro-Inspired Improvements to pb-spec

| Metadata | Details |
| :--- | :--- |
| **Status** | Draft |
| **Created** | 2026-07-08 |
| **Planned at** | commit `HEAD`, 2026-07-08 |

## Summary

Kiro's spec-driven workflow uses neuro-symbolic requirements analysis, parallel task execution, and fast-track planning to catch requirement bugs before code and speed up implementation. This design ports three high-impact concepts to pb-spec: (1) a requirements analysis step in pb-plan that catches ambiguities, inconsistencies, and completeness gaps using EARS quality enforcement and abductive reasoning; (2) parallel task execution in pb-build using the existing DependsOn metadata; and (3) a quick-plan mode in pb-brainstorming for well-understood features. Requirement bugs propagate through design, tasks, and code — they are expensive to fix late, and research shows Pass@1 drops 20-40% when prompts are ambiguous (Larci et al., 2025); underspecified prompts are about twice as likely to regress across model changes (Yang et al., 2025). Catches earlier = cheaper fixes.

## Approach

### Integration Points

**pb-plan (skills/pb-plan/SKILL.md):**

1. **New Step 1.5: Requirements Analysis** — After extracting the source requirement ledger (Step 1) and before collecting project context (Step 2), add a requirements analysis phase that:
   - Validates EARS quality properties (testable, solution-free, unambiguous, consistent, complete)
   - Performs abductive refinement: works backwards from success state to identify missing error paths
   - Detects ambiguities by checking if requirements admit multiple interpretations
   - Detects inconsistencies by cross-referencing requirement pairs
   - Surfaces findings as clarifying questions with two options each
   - Records resolutions in the Source Requirement Ledger

2. **EARS Quality Checklist** — Add to Step 1 a mandatory quality check for each extracted requirement:
   - **Testable:** Names inputs, outputs, and conditions on observable quantities
   - **Solution-free:** Describes *what* the system does, not *how*
   - **Unambiguous:** Two independent readers would formalize it the same way
   - **Consistent:** No pair of requirements demands incompatible behaviors
   - **Complete:** Behavior specified under any input combination

3. **Abductive Refinement Pattern** — For each requirement, ask:
   - What does the success state look like?
   - What prerequisites must hold for success?
   - What could prevent each prerequisite?
   - What error paths should exist?
   - Is each error path already captured by an existing requirement?

**pb-build (skills/pb-build/SKILL.md + references/):**

1. **Dependency Graph Construction** — In Step 2 (Parse Unfinished Tasks), build a dependency graph from DependsOn metadata:
   - Each task's DependsOn lists TaskIDs it depends on
   - Tasks with DependsOn: None are root nodes
   - Tasks that share file writes are never parallelized
   - Setup/infrastructure tasks run first

2. **Wave-Based Parallel Execution** — Replace "Execute Tasks Sequentially" with wave-based execution:
   - Wave 0: Tasks with DependsOn: None (and no shared file writes)
   - Wave N: Tasks whose dependencies are all in waves 0..N-1
   - Each wave runs tasks concurrently via subagents
   - Each subagent gets isolated context (no state leaking)
   - If a task in a wave fails, other tasks in the same wave continue
   - Failed tasks get retry budget (same 3-failure protocol)

3. **Wave Metadata in tasks.md** — Add optional `Wave:` field to tasks for explicit wave assignment (when the planner knows the optimal grouping). If absent, pb-build infers from DependsOn.

**pb-brainstorming (skills/pb-brainstorming/SKILL.md):**

1. **Quick Plan Mode Detection** — After Step 1 (Explore project context), assess whether the feature is well-understood:
   - Clear scope, known constraints, few edge cases → quick plan
   - Ambiguous, multi-system, complex domain → standard flow

2. **Targeted Clarification Questions** — For quick plan mode, ask 2-4 questions covering:
   - Scope and constraints
   - Ambiguity in the description
   - Implementation forks (when multiple valid approaches exist)
   - Directional decisions about the feature's shape

3. **One-Pass Artifact Generation** — After questions are answered, generate requirements, design, and tasks in one pass (no intermediate approval gates). Artifacts are saved for review.

4. **Selective Refinement Loop** — If the user changes tasks, only tasks regenerate. If they change design, design + tasks rebuild. If they change scope, full pipeline reruns.

**Templates (references/):**

1. **design_template.md** — Add "Requirements Quality Audit" subsection under Source Inputs & Normalization
2. **tasks_template.md** — Add optional `Wave:` field to task blocks

### Ponytail Ladder (mandatory at every decision point)

1. Does this need to exist at all? Speculative need = skip it. (YAGNI)
2. Stdlib does it? Use it.
3. Native platform feature covers it? Use it.
4. Already-installed dependency? Use it.
5. One line? One line.
6. Only then: minimum code that works.

Mark deferrals: Use `ponytail:` comments for deliberate simplifications with known ceilings. Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested.

### Existing Components to Reuse

| Component | Location | How to Reuse |
| :--- | :--- | :--- |
| Source Requirement Ledger | pb-plan:58-63 | Add quality properties and clarification records |
| DependsOn metadata | tasks_template.md:445-456 | Use for dependency graph construction |
| Subagent dispatch | pb-build:194-216 | Extend for parallel wave execution |
| pb-brainstorming checklist | pb-brainstorming:24-31 | Add quick plan mode detection |
| EARS notation | design_template.md:40-69 | Add quality validation checklist |

### What NOT to change

- Don't rename skills or add new skills
- Don't change the pb-spec workflow contract
- Don't remove existing validation, error handling, or security requirements
- Don't add dependencies
- Don't change the BDD/TDD cycle structure
- Don't change the Generator/Evaluator isolation model

## Architecture Decisions

### AD-01: Requirements Analysis as Inline Step, Not Separate Skill

- **Status:** `Accepted`
- **Date:** 2026-07-08

**Context:** Kiro implements requirements analysis as a separate pipeline stage. pb-plan already has a Step 1 (Parse Requirements) that extracts the source requirement ledger. Adding analysis as a separate step within pb-plan keeps the workflow simple and avoids a new skill.

**Decision:** Add requirements analysis as Step 1.5 within pb-plan, between requirement extraction and project context collection. The analysis is inline, not a separate command.

**Consequences:**

- Positive: No new skill to maintain; analysis happens automatically during planning
- Negative: pb-plan becomes slightly longer
- Neutral: Analysis findings are recorded in the same Source Requirement Ledger

### AD-02: Wave-Based Parallelism with File-Write Conflict Detection

- **Status:** `Accepted`
- **Date:** 2026-07-08

**Context:** pb-build currently runs tasks sequentially. Tasks already have DependsOn metadata. Kiro's parallel execution groups tasks into waves based on dependency structure.

**Decision:** Build a dependency graph from DependsOn metadata and group tasks into waves. Tasks in the same wave run concurrently. Tasks that write to the same files are never in the same wave. Each wave runs via subagents with isolated context.

**Consequences:**

- Positive: 2-4x speedup for specs with independent tasks (Kiro reports ~4x for complex specs)
- Negative: Slightly more complex orchestrator logic; failed tasks in a wave don't block others
- Neutral: The DependsOn metadata already exists in tasks.md; no new metadata format needed

### AD-03: Quick Plan as Mode Detection, Not Separate Command

- **Status:** `Accepted`
- **Date:** 2026-07-08

**Context:** Kiro has a "quick plan mode" that fast-tracks spec generation. pb-brainstorming already asks questions and produces designs. Adding a mode flag keeps the interface simple.

**Decision:** pb-brainstorming detects scope complexity after Step 1 (Explore project context) and switches between standard flow (multi-step approval) and quick plan flow (targeted questions → one-pass generation). No new command needed.

**Consequences:**

- Positive: Users don't need to learn a new command; the system adapts automatically
- Negative: Detection heuristics may occasionally misclassify; user can always override
- Neutral: The standard flow remains available for complex features

### AD-04: EARS Quality Properties as Checklist, Not Formal Verification

- **Status:** `Accepted`
- **Date:** 2026-07-08

**Context:** Kiro uses SMT solvers for formal verification of requirements. pb-spec operates in a text-based agent context without formal verification tools. EARS quality properties can be enforced through structured checklist analysis.

**Decision:** Use EARS quality properties (testable, solution-free, unambiguous, consistent, complete) as a structured checklist that the planner evaluates for each requirement. Findings are surfaced as clarifying questions, not formal proofs.

**Consequences:**

- Positive: No external tools needed; works within agent context
- Negative: Less rigorous than formal verification; some edge cases may slip through
- Neutral: Catches the most common requirement bugs (the 80/20)

## Requirements & Goals

**Ubiquitous:**

- **[REQ-01]:** pb-plan *shall* validate each extracted requirement against EARS quality properties (testable, solution-free, unambiguous, consistent, complete) before generating design.
- **[REQ-02]:** pb-plan *shall* perform abductive refinement for each requirement, working backwards from success state to identify missing error paths.
- **[REQ-03]:** pb-plan *shall* surface ambiguity, inconsistency, and completeness findings as clarifying questions with two options each.

**State-driven:**

- **[REQ-04]:** While tasks.md contains tasks with DependsOn metadata, pb-build *shall* build a dependency graph and execute independent tasks concurrently.
- **[REQ-05]:** While running tasks in parallel, pb-build *shall* isolate each task's context to prevent state leaking between concurrent tasks.

**Event-driven:**

- **[REQ-06]:** When pb-brainstorming detects a well-understood feature scope, it *shall* offer quick plan mode with targeted clarification questions.
- **[REQ-07]:** When the user answers quick plan questions, pb-brainstorming *shall* generate requirements, design, and tasks in one pass without intermediate approval gates.

**Unwanted:**

- **[REQ-08]:** pb-build *shall not* parallelize tasks that write to the same files.
- **[REQ-09]:** The requirements analysis step *shall not* block planning when findings are ambiguous — it *shall* label them as assumptions and proceed.

**Exception:**

- **[REQ-10]:** Where a task fails during parallel execution, pb-build *shall* continue other independent tasks and apply the standard 3-failure retry protocol to the failed task.

## BDD/TDD Strategy

- **Primary Language:** Markdown (skill files)
- **Verification:** grep for key patterns, manual review for behavior preservation, test execution for functional correctness
- **Feature Files:** `specs/2026-07-08-01-kiro-inspired-improvements/features/kiro-improvements.feature`
- **TDD inner-loop:** Red → Green → Refactor; grep-based checks act as the regression gate for skill-file edits.

### BDD Scenario Inventory

| Feature File | Scenario Name | Business Outcome | Task Coverage |
| :--- | :--- | :--- | :--- |
| `features/kiro-improvements.feature` | pb-plan catches ambiguous requirements | Ambiguity surfaced as clarifying question | Task 1.1 |
| `features/kiro-improvements.feature` | pb-plan detects inconsistent requirements | Conflict surfaced as clarifying question | Task 1.1 |
| `features/kiro-improvements.feature` | pb-plan detects incomplete requirements | Missing error paths identified | Task 1.2 |
| `features/kiro-improvements.feature` | pb-plan enforces EARS quality | Requirements rewritten to be testable | Task 1.2 |
| `features/kiro-improvements.feature` | pb-build executes independent tasks in parallel | Concurrent execution with isolation | Task 2.1 |
| `features/kiro-improvements.feature` | pb-build respects dependency ordering | Dependent tasks wait for prerequisites | Task 2.1 |
| `features/kiro-improvements.feature` | pb-brainstorming fast-tracks features | Quick plan with targeted questions | Task 3.1 |
| `features/kiro-improvements.feature` | pb-brainstorming selects clarification targets | Questions cover 4 dimensions | Task 3.1 |

## Verification

| Step | Command | Success |
| :--- | :--- | :--- |
| VP-01 | `grep -c "Requirements Analysis" skills/pb-plan/SKILL.md` | ≥ 3 |
| VP-02 | `grep -c "EARS quality" skills/pb-plan/SKILL.md` | ≥ 2 |
| VP-03 | `grep -c "abductive" skills/pb-plan/SKILL.md` | ≥ 1 |
| VP-04 | `grep -c "Wave" skills/pb-build/SKILL.md` | ≥ 3 |
| VP-05 | `grep -c "dependency graph" skills/pb-build/SKILL.md` | ≥ 2 |
| VP-06 | `grep -c "quick plan" skills/pb-brainstorming/SKILL.md` | ≥ 2 |
| VP-07 | `grep -c "Wave:" skills/pb-plan/references/tasks_template.md` | ≥ 1 |
| VP-08 | Manual review: all existing behavior preserved | No behavior loss |

## Revision History

| Date | Change | Reason |
| :--- | :--- | :--- |
| 2026-07-21 | Schema migration to 4-field tasks / scalable design template | pb-spec refactor |
