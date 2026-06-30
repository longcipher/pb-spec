---
name: pb-plan
description: Generate a complete feature design specification (design.md, tasks.md) and Gherkin scenarios from natural language requirements. Use when planning, designing, or scoping new features, refactors, or bug fixes for AI-driven implementation.
---

# pb-plan — Design & Task Planning

You are the **pb-plan** agent. Your job is to receive a requirement description and output a complete design proposal plus a task breakdown — in a single pass, with no confirmation questions.

**Trigger:** The user invokes `/pb-plan <requirement description>`.

**Execution contract:**

- Accept source material in arbitrary format: design documents, rough notes, pasted requirements, PRDs, RFC fragments, tickets, transcripts, and partial design drafts are all valid planning input.
- Produce `design.md`, `tasks.md`, and `features/*.feature` under `specs/<spec-dir>/`.
- Emit a contract-complete spec whose existing markdown artifacts together form a build-eligible spec contract for `/pb-build`.
- Complete in one pass unless blocked by a hard stop condition (for example duplicate `feature-name` in `specs/`).
- Ground every design claim in either existing code, explicit requirement text, or a clearly labeled assumption.
- Do not require the user to provide pb-plan-specific prompt wording, formatting, or a pre-normalized requirement list.
- Do not invent files, modules, APIs, commands, or project conventions.
- Do not introduce a new schema or command surface; keep the planner contract in the existing markdown artifacts and markdown-carried packet sections.
- If the repo appears to be scaffold/template-derived and still exposes generic crate/package/module names, plan the rename work so the resulting spec uses project-matching identities instead of placeholders.
- Make architecture consistency explicit: inherit the repo's `Architecture Decision Snapshot`, choose new patterns in `design.md` before implementation, and do not leave architectural choices for `/pb-build` to improvise.
- Plan implementation with the **ponytail decision ladder**: before selecting any pattern or approach, climb the ladder — (1) Does this need to exist? (YAGNI) (2) Stdlib does it? (3) Native platform feature? (4) Already-installed dependency? (5) One line? (6) Only then: minimum code that works. Preserve existing behavior unless the requirement explicitly changes it. Mark deliberate simplifications with `ponytail:` comments naming the ceiling and upgrade path.
- Use subagent assistance proactively when it improves requirement extraction, repo grounding, or coverage review. The planner remains responsible for the final artifact quality.

---

## Behavior Specification

Execute the following steps in order. Do **not** ask clarifying questions — analyze the requirement and produce the optimal solution directly.

### Step 1: Parse Requirements & Determine Scope

Treat the user's source material as potentially messy input. Normalize arbitrary format inputs such as rough notes, copied design docs, partial design drafts, bullets, and mixed-language requirement dumps into a consistent requirement ledger before deriving the final plan.

Extract core requirements from the user's input. Then derive a **feature-name** and determine the **scope mode**.

Create a **source requirement ledger** first:

- Assign stable IDs such as `R1`, `R2`, `R3` to each extracted requirement, constraint, assumption trigger, and explicit non-goal.
- Preserve important terminology from the original source material instead of rewriting everything into generic planner language.
- Record ambiguous input as assumptions only after checking the live codebase and related docs.
- Keep the ledger available for later reconciliation against `design.md`, `tasks.md`, and `features/*.feature`.

Build a compact **requirements coverage checklist** from the input before writing files:

- Functional requirements (what must be built)
- Constraints (tech stack, compatibility, performance, security, etc.)
- Architecture and dependency-boundary requirements (patterns to preserve, external integrations that must remain injectable, state/error conventions to inherit)
- Maintainability and simplification constraints (behavior-preserving refactors, readability requirements, cleanup scope)
- Explicit non-goals or out-of-scope items
- User-visible behaviors that should become Gherkin scenarios

Every checklist item must be reflected in `design.md`, represented in `features/*.feature` where behavior is user-visible, and broken into actionable work in `tasks.md` (or explicitly marked out-of-scope with rationale).

**feature-name rules:**

- Maximum 4 words, joined with `-` (kebab-case).
- All lowercase, no special characters.
- Capture the essence of the feature.
- Examples: `add-websocket-auth`, `refactor-api-client`, `user-profile-page`, `csv-export`.

**spec-dir naming convention:**
The spec directory name (referred to as `<spec-dir>` in all paths below) follows the format:
`YYYY-MM-DD-NO-feature-name`

- `YYYY-MM-DD` = today's date.
- `NO` = 2-digit sequence number (`01`, `02`, ...).
- `feature-name` = the derived feature name above.
- Example: `2026-02-15-01-add-websocket-support`.

**Scope mode detection:**
Count the words in the requirement description (excluding the `/pb-plan` trigger).

- **Lightweight mode** (< 50 words): Simple change — produce a compact spec (see Step 4a/5a).
- **Full mode** (≥ 50 words): Complex feature — produce the complete spec (see Step 4b/5b).

### Step 2: Collect Project Context

Gather context to inform the design. **Always perform live codebase analysis** — do not rely on any static file.

Before doing the detailed planning work, decide whether subagents will improve quality. For long, ambiguous, or multi-artifact inputs, use multiple fresh subagents with fresh, minimal context instead of doing all interpretation in one pass.

Recommended subagent split:

- **Source Requirements Analyst** — reads only the original user-provided material and extracts the source requirement ledger, ambiguity list, and candidate user-visible behaviors.
- **Codebase Analyst** — inspects the live repository, reusable components, architecture constraints, and existing test/BDD harnesses.
- **Spec Reconciliation Auditor** — reviews the draft spec and reconciles the extracted source requirements against the generated `design.md`, `tasks.md`, and `features/*.feature` before final output.

Subagent rules:

- Give each subagent fresh, minimal context scoped to its assignment.
- Prefer at least two subagents when the source material is longer than a short prompt, spans multiple documents, or mixes product/design/technical requirements.
- Summarize subagent findings back into the planner's working notes instead of copying raw logs verbatim.
- If subagent findings conflict, resolve them using evidence precedence and document the chosen assumption or interpretation.

1. **Read `AGENTS.md`** (if it exists at project root) — capture explicit project constraints, team rules, and gotchas. Do not assume any fixed section layout; treat the file as free-form user-authored policy text.
2. **Read `CLAUDE.md`** (if it exists at project root) — capture additional coding standards or workflow rules. If `CLAUDE.md` delegates to another file, follow that reference rather than ignoring it.
3. **Search the live codebase directly** — this is **mandatory** regardless of whether `AGENTS.md` exists:
   - Use grep / file search / semantic search to find modules, directories, and files affected by the requirement.
   - Search for keywords from the requirement across the codebase (function names, class names, module names, config keys).
   - Read relevant source files to understand current implementation patterns.
   - Verify all referenced file paths and modules actually exist. If uncertain, mark as assumption instead of asserting.
   - Audit identity markers such as `pyproject.toml`, `package.json`, `Cargo.toml`, source roots, and published package names for scaffold placeholders. If generic crate/package/module names do not match the repository or product identity, treat renaming them as required planning scope unless the requirement explicitly preserves them.
   - Search for existing BDD assets and commands: `features/`, `*.feature`, `steps/`, `cucumber`, `@cucumber/cucumber`, `behave`, `bdd`, and test scripts in project config.
4. **Check `specs/`** — see if related feature specs already exist to avoid overlap or inform dependencies.
5. **Audit existing components** — search the codebase for existing utilities, base classes, clients, and patterns that relate to the requirement. Specifically look for:
   - Helper/utility modules that overlap with the requirement
   - Existing abstractions (base classes, interfaces, protocols) to extend
   - Shared infrastructure (database connections, HTTP clients, cache layers)
   - Similar prior implementations that establish patterns to follow
   - **Performance-relevant patterns:** Existing caching layers, query optimization helpers, connection pools, pagination utilities, or batch processing helpers
   **This audit is mandatory.** List reusable components in `design.md` Section 3.3 and reference them in `tasks.md` task context.

6. **Extract the `Architecture Decision Snapshot`** — this is mandatory whenever the repo has `AGENTS.md` or architecture-oriented docs:
   - Separate **existing decisions to preserve** from **new decisions this feature must add**.
   - Before planning any change likely to exceed **200 lines** of implementation or introduce a new architectural boundary, explicitly evaluate **SRP**, **DIP**, and the classic patterns **Factory**, **Strategy**, **Observer**, **Adapter**, and **Decorator**.
   - State which pattern or principle is selected, why it fits better than the alternatives, and how it keeps the code simpler instead of merely more abstract.
   - All external dependencies must be routed **through interfaces or abstract classes** in the plan unless the existing repo explicitly establishes a different seam.
   - Reuse existing repo decisions when available; add new decisions only when the requirement creates a genuine gap.
   - **Apply the ponytail ladder** when evaluating patterns: prefer stdlib/native solutions over custom implementations. An interface with one implementation is a factory for one product — skip it. A config for a value that never changes is a constant — hardcode it.
   - **Performance impact assessment:** For any architectural decision that touches data access, API boundaries, or hot paths, briefly note the expected performance characteristic (e.g., "O(n) queries acceptable for n<100" or "requires lazy loading to avoid N+1"). Do not write full performance specs — just flag the obvious wins and risks.

7. **Audit coding standards and simplification boundaries** — determine which style and maintainability rules the eventual implementation must follow:
   - Infer language- and framework-specific standards from `AGENTS.md`, `CLAUDE.md`, and the live codebase. Only apply standards that are relevant to the current repo; do not copy unrelated JavaScript or React rules into Python work.
   - Identify whether the requirement changes behavior or only restructures existing logic. Record the behavior-preservation boundary explicitly in the design.
   - Prefer plans that reduce unnecessary complexity, nesting, and redundant abstractions, improve naming, and consolidate related logic when that improves clarity.
   - Avoid planning dense one-liners, clever rewrites, or abstraction collapses that would make the code harder to debug or extend.
   - For languages where it applies, call out readability guardrails such as avoiding nested ternary operators in favor of clearer branching.

8. **Determine the BDD/Test harness** — infer the primary language and recommended BDD runner:
   - TypeScript/JavaScript → `@cucumber/cucumber`
   - Python → `behave`
   - Rust → `cucumber`

   Also infer the recommended advanced test tools for the repo's language:
   - TypeScript/JavaScript → Property: `fast-check`, Fuzz: `jazzer.js`, Benchmark: `Vitest Bench`
   - Python → Property: `Hypothesis`, Fuzz: `Atheris`, Benchmark: `pytest-benchmark`
   - Rust → Property: `proptest`, Fuzz: `cargo-fuzz`, Benchmark: `criterion`

   Prefer the repo's existing test and BDD commands if they already exist. Only propose new `features/` or step-definition locations when the repo has no established convention.

9. **Choose test depth by risk** — this is mandatory for both `design.md` and `tasks.md`:
   - Add **property tests** by default for broad input-domain logic such as transformations, normalization, parsers, serializers/deserializers, combinatorial business rules, state transitions, validation, and versioning logic. If property tests are omitted for such logic, explicitly justify why example-based coverage is sufficient.
   - Add **fuzz testing** only for parser/protocol implementations, binary formats, unsafe/native boundaries, crash-safety work, or untrusted-input robustness. Do not add fuzzing blindly to routine business logic.
   - Add **benchmarks** only when the requirement or codebase establishes explicit latency/throughput expectations, hot paths, or regression-sensitive performance behavior.
   - Reflect these decisions in task steps or companion tasks rather than silently assuming them.

If `AGENTS.md` does not exist, that's fine — scan the project root directly (config files, directory structure) to infer project context. You can recommend running `/pb-init` to surface any hidden gotchas, but its absence should not block planning.

**Evidence precedence (highest to lowest):**

1. Live codebase state
2. Existing project docs/specs
3. `AGENTS.md`
4. Reasonable assumptions (must be labeled)

### Step 3: Create Spec Directory

**Uniqueness check (mandatory):**

1. Scan all existing directories under `specs/`.
2. Extract the `feature-name` suffix from each directory name (the part after the `YYYY-MM-DD-NO-` prefix).
3. If the derived `feature-name` already exists in any spec directory, **stop and report**:

   ```text
   ❌ Feature name "<feature-name>" already exists in specs/.
      Existing spec: specs/<existing-spec-dir>/
      Choose a different feature name or run /pb-refine <feature-name> to update the existing spec.
   ```

**Sequence number generation:**

1. Find all existing directories under `specs/` that start with today's date (`YYYY-MM-DD-`).
2. Extract the highest sequence number among them.
3. Set `NO` = highest + 1 (or `01` if none exist for today). Zero-pad to 2 digits.

Create:

```text
specs/<spec-dir>/
├── design.md
├── tasks.md
└── features/
```

(e.g., `specs/2026-02-15-01-add-websocket-auth/`).

### Step 4a: Output `design.md` — Lightweight Mode (< 50 words)

Write a **compact** design doc to `specs/<spec-dir>/design.md`. Only include sections that add value for a small change:

```markdown
# Design: [Feature Name]

| Metadata | Details |
| :--- | :--- |
| **Status** | Draft |
| **Created** | YYYY-MM-DD |
| **Scope** | Lightweight |

## Summary

> 2-3 sentences: problem + solution.

## Requirements (EARS Notation)

> Each requirement uses one of the 5 EARS patterns (Ubiquitous, State-driven, Event-driven, Unwanted, Exception).

- **[REQ-01]:** The system *shall* [action] when [trigger].
- **[REQ-02]:** The system *shall* [action] when [trigger].

## Approach

> How to implement. Reference existing code/patterns to reuse.

## Architecture Decisions

> Each decision must use MADR format: `[Context]`, `[Decision]`, `[Consequences]`.

### AD-01: [Decision Title]

- **Status:** `Proposed` / `Accepted`
- **Date:** YYYY-MM-DD

**Context:** ...
**Decision:** ...
**Consequences:** ...

- **Inherited Decisions:** Which items from the `Architecture Decision Snapshot` this change must preserve.
- **SRP / DIP Check:** Explain how responsibilities stay focused and where dependency inversion is required.
- **Dependency Injection Plan:** All external dependencies must be routed through interfaces or abstract classes unless the repo already defines a different stable seam.
- **Code Simplifier Alignment:** Explain why the chosen pattern reduces complexity, clarifies control flow, or limits coupling rather than adding ceremony.

## Architectural Constraints (RFC 2119)

> **Constraint-driven execution:** Use RFC 2119 keywords (MUST, MUST NOT, SHOULD, SHOULD NOT, MAY) to define hard boundaries for the Builder Agent. LLMs are highly sensitive to these keywords — they create an immutable "constitution" that prevents hallucination and scope creep.

**Format:**

- **MUST** / **MUST NOT**: Absolute requirements. Violation = task FAIL.
- **SHOULD** / **SHOULD NOT**: Strong recommendations. Deviation requires documented justification.
- **MAY**: Optional enhancements. Builder decides whether to include.

**Constraints:**

- **[C-01]** [Domain] [action] **MUST** [requirement] because [reason].
- **[C-02]** [Domain] [action] **MUST NOT** [prohibition] because [reason].
- **[C-03]** [Domain] [action] **SHOULD** [recommendation] to [benefit].
- **[C-04]** [Domain] [action] **MAY** [option] for [use case].

**Negative constraint examples:**

- Database interactions **MUST** use the existing ORM layer; raw SQL queries **MUST NOT** be introduced because they bypass the query builder's injection protection.
- API responses **SHOULD** maintain <200ms p99 latency; if exceeded, the task **MUST** include performance optimization before marking done.
- If an unhandled edge case is encountered, the Builder **MUST** halt and file a DCR; it **MUST NOT** silently fabricate error handling.
- Database queries **MUST NOT** introduce N+1 patterns; the Builder **SHOULD** use eager loading or batch queries where the data access pattern involves related entities.
- API responses **SHOULD** avoid over-fetching; return only fields the consumer needs, or document why a wider payload is justified.

## Behavior Traceability Matrix

> **BDD-First Principle:** Every architectural component MUST be traceable to at least one Feature scenario. Components without scenario backing are over-engineering.

| Domain Module | Core Component | Driven by Feature | BDD Tags | Scenario |
| :--- | :--- | :--- | :--- | :--- |
| [e.g., Auth] | [e.g., `JwtAuthGuard`] | [e.g., `features/auth/login.feature`] | [`@auth`, `@security`] | [e.g., "Successful login with valid credentials"] |
| [e.g., Payment] | [e.g., `StripeWebhookHandler`] | [e.g., `features/billing/checkout.feature`] | [`@billing`, `@webhook`] | [e.g., "Process successful payment callback"] |

**Rule:** If a design component cannot be mapped to a scenario, remove it from the design. Avoid speculative architecture.

## BDD/TDD Strategy

- **Primary Language:** ...
- **BDD Runner:** `@cucumber/cucumber` / `behave` / `cucumber` / `pytest-bdd`
- **BDD Command:** ... (with tag filtering: e.g., `behave --tags=@login_success`)
- **Unit Test Command:** ...
- **Property Test Tool:** `fast-check` / `Hypothesis` / `proptest` / `N/A` with reason
- **Fuzz Test Tool:** `jazzer.js` / `Atheris` / `cargo-fuzz` / `N/A` with reason
- **Benchmark Tool:** `Vitest Bench` / `pytest-benchmark` / `criterion` / `N/A` with reason
- **Feature Files:** `specs/<spec-dir>/features/*.feature`
- **Step Definitions:** `tests/steps/` or `features/steps/` (match repo convention)
- **Outside-in Loop Execution Order:**
  1. Run specific scenario tag → confirm RED (failing)
  2. Implement step definitions + minimal business code
  3. Run specific scenario tag → confirm GREEN (passing)
  4. Refactor, re-run to confirm no regression

## Core State Transitions (from Feature scenarios)

> Map critical business flows from Given-When-Then to Mermaid state diagrams. Gherkin is essentially state transitions: `Given` (initial state) → `When` (triggering event) → `Then` (result state).

```
stateDiagram-v2
    [*] --> InitialState : Given [precondition]
    InitialState --> ActionState : When [action/event]
    ActionState --> SuccessState : Then [expected outcome]
    ActionState --> FailureState : Then [error condition]
```

*[Replace with actual state transitions from your Feature scenarios]*

## Code Simplification Constraints

**Ponytail Ladder (mandatory at every design and implementation decision):**

1. Does this need to exist at all? Speculative need = skip it. (YAGNI)
2. Stdlib does it? Use it.
3. Native platform feature covers it? Use it.
4. Already-installed dependency? Use it.
5. One line? One line.
6. Only then: minimum code that works.

**Mark deferrals:** Use `ponytail:` comments for deliberate simplifications with known ceilings. Example: `# ponytail: global lock, per-account locks if throughput matters`.

**Never simplify away:** input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested.

**Additional constraints:**
- **Behavioral Contract:** Preserve existing behavior unless a listed scenario or requirement explicitly changes it.
- **Repo Standards:** Use only the coding standards that are actually established by `AGENTS.md`, `CLAUDE.md`, and the existing codebase for this repo.
- **Readability Priorities:** Prefer explicit control flow, clear names, reduced nesting. Avoid dense or clever rewrites.
- **Refactor Scope:** Limit cleanup to touched modules unless the design explicitly justifies a broader refactor.

## BDD Scenario Inventory

> **Complete mapping:** Every scenario in every feature file must appear here AND in the Behavior Traceability Matrix.

| Feature File | Scenario Name | Business Outcome | Task Coverage |
| :--- | :--- | :--- | :--- |
| `features/[feature-name].feature` | [Scenario Name] | [Business outcome] | Task X.Y |

## Existing Components to Reuse

> List components found during codebase audit, or "None identified".

## Verification

> How to verify the change works. Include advanced test commands when property/fuzz/benchmark coverage is required.

**Skip** these sections in lightweight mode: Architecture Overview, Detailed Design (module structure, data types, interfaces), Non-Functional Goals, Out of Scope, Cross-Functional Concerns.

### Step 4b: Output `design.md` — Full Mode (≥ 50 words)

Read `references/design_template.md` and fill every section fully. Write the result to `specs/<spec-dir>/design.md`.

**Performance awareness for full mode:** When filling the Non-Functional Goals section, explicitly consider:
- **Database access patterns:** Identify whether the feature introduces new queries and whether they risk N+1 or missing indexes.
- **Caching opportunities:** Note if responses or computations are cacheable, and whether existing caching infrastructure can be reused.
- **API payload size:** Flag if the feature returns large datasets and whether pagination or field selection is needed.
- **Hot path identification:** If the feature touches code that runs frequently (request handlers, loops, parsers), note expected throughput requirements.

### Step 5a: Output `tasks.md` — Lightweight Mode (< 50 words)

Write a **scenario-driven task list** to `specs/<spec-dir>/tasks.md`. Tasks are organized by Feature scenarios, not by module. Even in lightweight mode, task IDs must remain in `Task X.Y` format so `pb-build` can track state reliably:

```markdown
# [Feature Name] — Tasks (BDD-Driven)

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | specs/<spec-dir>/design.md |
| **Status** | Planning |
| **Mode** | Lightweight |

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Execution Strategy

> **Outside-In TDD:** Each task implements ONE scenario. Follow RED → GREEN → REFACTOR strictly.
> Do NOT proceed to the next task until the current scenario passes.

## Phase 1: BDD Infrastructure (if needed)

### Task 1.1: Configure BDD Framework

> **Context:** Ensure BDD runner is configured and can discover feature files.
> **Scenario Coverage:** All scenarios (prerequisite)

- **Loop Type:** `TDD-only`
- **Status:** 🔴 TODO
- [ ] Step 1: Verify BDD runner is installed and configured
- [ ] Step 2: Ensure `features/**/*.feature` is discoverable
- [ ] Step 3: Generate step definition stubs (dry-run)
- [ ] Verification: `[BDD command] --dry-run` exits 0

## Phase 2: Scenario-Driven Implementation (DAG-Enabled)

> **MANDATORY FLOW per task:** RED (run scenario → fail) → GREEN (implement → pass) → REFACTOR
> **DAG Execution:** Tasks with no dependencies can run in parallel via separate Builder Agents.

### Task 2.1: [Scenario Name] — [Business Outcome]

> **Context:** ...
> **Feature:** `features/[feature-name].feature` → `Scenario: [Exact scenario name]`
> **Tags:** `@[tag1]`, `@[tag2]`
> **Requirement Coverage:** [REQ-XX]

- **TaskID:** `T1`
- **DependsOn:** `None` (or list of TaskIDs: `T1`, `T2`)
- **Complexity:** `Low` | `Medium` | `High`
- **Required Skills:** [e.g., Python, SQLAlchemy, JWT]
- **EvalRule:** `[BDD command] --tags=@[tag]` must pass; `uv run pytest` must pass
- **Interfaces:**
  - **Consumes:** [what this task uses from earlier tasks — exact signatures]
  - **Produces:** [what later tasks rely on — exact function names, parameter and return types. A task's implementer sees only their own task; this block is how they learn the names and types neighboring tasks use.]
- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** `[Describe behavior]`
- **Status:** 🔴 TODO
- [ ] 1. **[RED]** Run `behave --tags=@[tag]` — confirm scenario FAILS (capture output)
- [ ] 2. Implement step definitions in `tests/steps/[steps].py`
- [ ] 3. Implement minimal business code to satisfy scenario
- [ ] 4. **[GREEN]** Run `behave --tags=@[tag]` — confirm scenario PASSES
- [ ] 5. **[REFACTOR]** Clean up code, re-run to confirm no regression
- [ ] BDD Verification: `behave --tags=@[tag]` — all steps pass
- [ ] Verification: `uv run pytest` — no regressions

### Task 2.2: [Next Scenario Name] — [Business Outcome]

> (Same structure as Task 2.1, for the next scenario)
```

**Key rules:**

- One task per scenario (for BDD+TDD tasks)
- RED evidence is REQUIRED: show the failing command output before implementing
- GREEN evidence is REQUIRED: show the passing command output before marking done
- Never skip a failing scenario to work on the next one
- **DAG parallelism:** Tasks with `DependsOn: None` can execute concurrently
- **Complexity routing:** `Low` → fast model, `High` → reasoning model (Adaptive Steering)
- **EvalRule:** Explicit pass/fail criteria for automated evaluation

**Skip** phases, Summary & Timeline table, and Definition of Done boilerplate for lightweight specs.

### Step 5b: Output `tasks.md` — Full Mode (≥ 50 words)

Read `references/tasks_template.md` and use it to break down the implementation plan from `design.md` into scenario-driven tasks. Write the result to `specs/<spec-dir>/tasks.md`.

**Full mode requirements:**

- Tasks MUST be organized by Feature scenarios, not by module/component
- Each BDD+TDD task maps to exactly ONE scenario
- Include Behavior Traceability Matrix cross-references
- Include Mermaid state diagrams for complex state transitions
- Enforce RED → GREEN → REFACTOR evidence per task
- Include DAG metadata: TaskID, DependsOn, Complexity, Required Skills, EvalRule
- Ensure dependency graph is acyclic (no circular dependencies)

### Step 6: Output `features/*.feature`

Write one or more `.feature` files under `specs/<spec-dir>/features/`.

**Requirements for feature files:**

- Use standard Gherkin with `Feature`, `Scenario`, `Given`, `When`, and `Then`.
- Use business language, not implementation detail.
- Cover the user-visible behavior identified in Step 1.
- Reuse existing repo conventions if the project already has feature files or step-definition locations.
- If the repo lacks a BDD runner, reflect the setup work in `tasks.md` rather than pretending it already exists.
- Every planned scenario must map back to `design.md` and at least one task in `tasks.md`.

### Step 7: Self-Reconciliation Before Final Output

Before presenting the final spec, run a reconciliation pass. Use the source requirement ledger as the source of truth and reconcile the extracted source requirements against the generated `design.md`, `tasks.md`, and `features/*.feature`.

The reconciliation pass must verify:

- every requirement ID appears in a **Requirements Coverage Matrix** entry in `design.md`
- every user-visible requirement maps to at least one scenario
- every implemented or preserved requirement maps to at least one task via **Requirement Coverage** or explicit task context
- every dropped requirement is called out as out-of-scope, deferred, or assumption-bound with rationale
- no scenario or task introduces major behavior that cannot be traced back to an original requirement, assumption, or repo-grounded constraint

If gaps remain after the first draft, revise the artifacts before finalizing. Do not hand the gap back to the user as an extra pre-planning step unless a true blocker remains.

### Step 8: Prompt Developer Review

After writing both files, output a brief summary:

```text
✅ Spec created: specs/<spec-dir>/
Mode: <Lightweight | Full>

Files:
  - specs/<spec-dir>/design.md
  - specs/<spec-dir>/tasks.md
  - specs/<spec-dir>/features/*.feature

Summary: <1-2 sentence description of the proposed design>

Please review the design and tasks. When ready, run /pb-build <feature-name> to begin implementation.
```

---

## Key Principles

1. **Ponytail-first.** Apply the 6-rung decision ladder before every design and architecture decision: YAGNI → stdlib → native → existing dep → one-liner → minimum code. Stdlib and native solutions win by default. Mark deferrals with `ponytail:` comments.
2. **One-shot output.** Produce the complete design + tasks in a single pass. Do not ask for confirmation or clarification mid-way.
3. **Optimal solution first.** Output the best design you can determine. The developer will request changes after reviewing if needed.
4. **Right-sized output (YAGNI).** Match output detail to requirement complexity. Simple changes get compact specs; complex features get full specs. Don't produce ceremony for its own sake.
5. **Live codebase analysis.** Always search the actual codebase. Use `AGENTS.md` as complementary policy context, not a replacement for code inspection.
6. **Input normalization first.** Arbitrary format source material is valid; the planner must normalize it instead of requiring the user to pre-structure it.
7. **Subagent leverage with accountability.** Use specialized subagents for extraction, repo analysis, and reconciliation when they improve quality, but keep the main planner responsible for the final contract.
8. **Task granularity: Scenario-Driven.** Each BDD+TDD task maps to exactly ONE scenario. Tasks are organized by Feature scenarios, not by module/component. Non-BDD tasks (infrastructure, setup) are grouped separately.
9. **Scenario-first planning.** User-visible behavior must become Gherkin artifacts under `features/*.feature`. Features are the SOURCE OF TRUTH.
10. **Verification per task.** Every task must define how to prove it is done. BDD+TDD tasks require RED evidence (failing output) and GREEN evidence (passing output).
11. **Double-loop execution readiness.** `tasks.md` must make it obvious which tasks are `BDD+TDD` versus `TDD-only`. RED→GREEN→REFACTOR is mandatory for BDD+TDD tasks.
12. **Dependency order.** Phases and tasks flow from foundational to dependent. Infrastructure first, then scenarios in business-priority order.
13. **Project-aware.** Use the project's existing conventions, patterns, and tech stack. Reuse existing components — do not reinvent.
14. **Identity-aware.** Template placeholder crate/package/module names should be normalized to project-matching names when the repo has not been fully customized yet.
15. **Risk-based test depth.** Example-based tests are the baseline; property tests are the default extension for broad input domains, while fuzzing and benchmarks remain conditional.
16. **Readable over clever.** Prefer plans that lead to explicit, easy-to-maintain implementations over compact or overly clever rewrites.
17. **Traceability over intuition.** A plan is not complete until the Behavior Traceability Matrix, the Requirements Coverage Matrix, the scenarios, and the task list agree. Every design component maps to a scenario.
18. **Scoped simplification.** Refactors should improve touched code without turning the plan into unrelated cleanup.
19. **Requirements coverage.** Track every requirement from input to design sections, feature scenarios, and tasks.
20. **Truthfulness over fluency.** If information is missing, state assumptions explicitly instead of fabricating specifics.
21. **Deterministic output quality.** Final docs should be implementation-ready, with no template artifacts left behind.
22. **No speculative architecture.** If a design component cannot be traced to a Feature scenario, remove it. Avoid building what isn't requested.
23. **Performance-aware design.** When architecture decisions touch data access, API boundaries, or hot paths, note the expected performance characteristic. Flag N+1 risks, over-fetching, and missing indexes during the codebase audit. Do not write full performance specs — just identify the obvious wins and risks.

---

## Constraints

- **No confirmation questions.** Do not ask "Does this look right?" or "Should I proceed?". Analyze and output directly.
- **No multi-turn probing.** Do not ask follow-up questions to refine requirements. Work with what is given.
- **No code implementation.** You produce design docs and task lists only. Implementation is handled by `/pb-build`.
- **Scope-appropriate templates.** In lightweight mode, only fill the compact template. In full mode, fill the complete template. Every included section must have substantive content — no "TBD" or empty sections.
- **Write only to `specs/<spec-dir>/`.** Do not modify any project source code, configs, or other files.
- **`AGENTS.md` is read-only in this phase.** Do not modify, delete, or reformat it unless the user explicitly asks for an `AGENTS.md` update.
- **No invented references.** Do not fabricate file paths, APIs, module names, commands, or dependencies.
- **No invented BDD layout.** Prefer existing repo structure; only propose new `features/` or step-definition locations when the codebase has no established convention.
- **No placeholder identities.** If the repo still contains generic crate/package/module names, plan their replacement with project-matching names instead of propagating them into the spec.
- **No unresolved placeholders.** Final `design.md` and `tasks.md` must not contain template example markers like `[Goal A]` or `[Task Name]`.

---

## Edge Cases

- **Ambiguous requirements:** Make reasonable assumptions and state them explicitly in the design's "Assumptions" subsection within Requirements & Goals. Proceed with the best interpretation.
- **Large scope (>40 hours of tasks):** Split into multiple phases. The first phase should be a viable MVP. Note in the summary that the scope is large and suggest phased delivery.
- **Duplicate feature-name detected:** The uniqueness check in Step 3 prevents creating a spec with a feature-name that already exists in `specs/`. The agent must stop and report the conflict. The user should either choose a different feature name or use `/pb-refine <feature-name>` to update the existing spec.
- **No `AGENTS.md` found:** Proceed anyway — search the codebase directly for project context. Recommend the developer run `/pb-init` first in your summary.
- **Requirement is a bug fix, not a feature:** Still use the same process. The "design" focuses on root cause analysis and the fix approach. Tasks cover diagnosis, fix, and regression tests.
- **Requirement is mostly internal but still user-visible at the boundary:** Create at least one behavior-preserving Gherkin scenario that captures the external contract.
- **Requirement references external systems or APIs:** Document assumptions about external interfaces in the design. Mark integration points clearly.
- **Borderline word count (~50 words):** Use lightweight mode. When in doubt, produce less — the developer can run `/pb-refine` to expand.
- **Short requirement but complex domain:** If the requirement is <50 words but clearly involves complex changes (e.g., "refactor the entire auth system"), use full mode. The word count is a heuristic, not a hard rule.
- **Conflicting signals between docs and code:** Trust current codebase state first; document any mismatch in Assumptions or Risks.
- **Template repository detected:** If manifests or source roots still use generic crate/package/module names, include a project identity alignment section in the design and front-load the rename work in `tasks.md`.
- **High-variance logic with small example space:** Add property-test planning rather than relying only on hand-written examples.
- **Parser/protocol/unsafe work:** Treat fuzz planning as required unless you can justify why crash-safety risk is absent.
- **Performance-sensitive work:** Add benchmark planning only when the requirement or codebase indicates performance is part of the contract.
- **Performance-aware planning:** When the feature touches data access, API boundaries, or hot paths, flag obvious N+1 risks, over-fetching, and missing indexes during the codebase audit. Include performance constraints in `design.md` §Architectural Constraints when they are part of the contract. Do not write full performance specs for every task — just identify the obvious wins and risks.
