# Workflow Type Contracts — Implementation Tasks

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | `specs/2026-03-09-01-workflow-type-contracts/design.md` |
| **Owner** | pb-build agent |
| **Start Date** | 2026-03-09 |
| **Target Date** | 2026-03-09 |
| **Status** | Planning |

## Summary & Phasing

Strengthen the current markdown workflow contract in place. The work starts by defining contract completeness in `pb-plan`, then adds a mandatory build validation gate and explicit task-state rules in `pb-build`, then formalizes blocked-build/DCR packet requirements in `pb-refine`, and finally aligns tests plus docs so the rules remain enforceable.

- **Property Testing Rule:** Add `Hypothesis` coverage only if implementation introduces reusable pure helpers for task-state or packet parsing. If the work remains string-assertion based inside existing tests, example-based coverage is sufficient.
- **Fuzzing Rule:** `Atheris` is out of scope unless implementation introduces a dedicated parser with crash-safety risk.
- **Benchmark Rule:** `pytest-benchmark` is out of scope because no hot-path or latency contract is being changed.
- **Identity Alignment Rule:** No template identity rename work is required; repo identity already matches `pb-spec` / `pb_spec`.
- **Architecture Decisions Rule:** Follow `AD-01` through `AD-04` from the design. Do not add a new schema language or command surface.
- **Dependency Injection Rule:** Keep workflow semantics in shared templates and tests. Do not push contract logic into platform adapters.
- **Behavior Preservation Rule:** Preserve existing `/pb-init`, `/pb-plan`, `/pb-refine`, `/pb-build` workflow semantics while making artifact contracts stricter.
- **Simplification Rule:** Prefer fixed markdown headings and explicit validation gates over parallel YAML blocks or free-form prose.
- **Clarity Guardrail:** Keep the contract vocabulary consistent across skills, prompts, docs, and tests.
- **Phase 1: BDD Harness & Scaffolding** — Contract vocabulary, planner artifacts, and acceptance coverage.
- **Phase 2: Scenario Implementation** — Build validation gate and task-state machine.
- **Phase 3: Integration & Features** — Refine packet validation and cross-template parity.
- **Phase 4: Polish, QA & Docs** — Regression suite, docs, and final verification.

---

## Phase 1: BDD Harness & Scaffolding

### Task 1.1: Define the planner-side contract surface

> **Context:** Reuse the existing `pb-plan` skill/prompt plus `design_template.md` and `tasks_template.md`. This task converts the current prose-heavy guarantees into explicit markdown contract fields while preserving `Task X.Y`, `Scenario Coverage`, `Loop Type`, and the current spec directory layout.
> **Verification:** The updated planner templates describe a build-eligible spec contract, explicit task states, and typed blocked-build/DCR packet expectations without introducing a new schema or command.

- **Priority:** P0
- **Scope:** Planner contract templates
- **Scenario Coverage:** `features/workflow_type_contracts.feature` — Planner emits a build-eligible spec contract
- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Preserve existing planning workflow while making contract completeness explicit in the current markdown artifacts.
- **Simplification Focus:** consolidate related logic
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] **Step 1:** Update `src/pb_spec/templates/skills/pb-plan/SKILL.md` and `src/pb_spec/templates/prompts/pb-plan.prompt.md` so they describe a contract-complete spec, explicit task-state rules, and markdown-carried packet requirements.
- [x] **Step 2:** Update `src/pb_spec/templates/skills/pb-plan/references/design_template.md` and `src/pb_spec/templates/skills/pb-plan/references/tasks_template.md` so the required design sections and task fields act as the planner's type contract.
- [x] **BDD Verification:** Run `uv run behave features/workflow_type_contracts.feature` and confirm the planner-contract scenario fails first, then passes.
- [x] **Verification:** Run `uv run pytest tests/test_templates.py tests/test_template_contracts.py -q` and confirm planner contract assertions pass.
- [x] **Advanced Test Verification:** `N/A` because this task changes static template contracts and does not introduce a reusable parser helper.
- [x] **Runtime Verification (if applicable):** `N/A` because this task does not affect a running service or runtime probe surface.

### Task 1.2: Add acceptance and regression coverage for the contract vocabulary

> **Context:** Reuse the existing behave harness in `features/` and the existing template assertions in `tests/test_templates.py` and `tests/test_template_contracts.py`. The goal is to encode the new workflow contract as executable acceptance and regression checks.
> **Verification:** The repo has explicit pytest and behave coverage for planner completeness, builder validation, task-state transitions, and refine packet completeness.

- **Priority:** P0
- **Scope:** Test harness updates
- **Scenario Coverage:** `features/workflow_type_contracts.feature` — all scenarios in the file
- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Preserve existing test harness layout while expanding it to the stronger workflow contract.
- **Simplification Focus:** improve naming
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] **Step 1:** Add a new feature file and step definitions, or extend the existing template-contract feature coverage, so workflow contract scenarios are expressed in business-facing Gherkin.
- [x] **Step 2:** Add or extend pytest assertions for the same contract language in `tests/test_templates.py` and `tests/test_template_contracts.py`.
- [x] **BDD Verification:** Run `uv run behave features/workflow_type_contracts.feature` and confirm all scenarios fail first where appropriate, then pass.
- [x] **Verification:** Run `uv run pytest tests/test_templates.py tests/test_template_contracts.py -q` and confirm the new assertions pass.
- [x] **Advanced Test Verification:** `N/A` unless a reusable parser/helper is introduced during implementation.
- [x] **Runtime Verification (if applicable):** `N/A` because the behavior is prompt/template contract validation.

---

## Phase 2: Scenario Implementation

### Task 2.1: Add a mandatory pb-build spec validation gate

> **Context:** Reuse `src/pb_spec/templates/skills/pb-build/SKILL.md`, `src/pb_spec/templates/prompts/pb-build.prompt.md`, and `src/pb_spec/templates/skills/pb-build/references/implementer_prompt.md`. This task must align with `AD-02` and `AD-03`: builder validation happens before execution and uses the repo's real markdown section names, not an invented schema.
> **Verification:** `pb-build` instructions resolve the spec directory, validate contract completeness, and stop with a precise error before spawning task work when required fields are missing.

- **Priority:** P0
- **Scope:** Build validation gate
- **Scenario Coverage:** `features/workflow_type_contracts.feature` — Builder rejects an incomplete spec before execution
- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Preserve existing build workflow order while adding an explicit Phase 0 validation gate.
- **Simplification Focus:** reduce nesting
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] **Step 1:** Update `pb-build` skill/prompt instructions to add a named pre-execution validation phase for required design sections, task fields, and feature scenarios.
- [x] **Step 2:** Update the implementer/orchestrator instructions so malformed specs stop immediately with specific missing-field output instead of reaching task execution.
- [x] **BDD Verification:** Run `uv run behave features/workflow_type_contracts.feature` and confirm the incomplete-spec scenario fails first, then passes.
- [x] **Verification:** Run `uv run pytest tests/test_templates.py tests/test_template_contracts.py -q` and confirm the build-validation assertions pass.
- [x] **Advanced Test Verification:** `N/A` unless implementation introduces a reusable parser/helper.
- [x] **Runtime Verification (if applicable):** `N/A` because this task affects workflow instructions, not a running service.

### Task 2.2: Formalize task-state transitions and completion gates

> **Context:** Reuse the existing task-status and checkbox conventions already described in `pb-build` and `tasks_template.md`. This task should add explicit allowed transitions, preserve legacy `TODO` compatibility, and forbid direct closeout without evidence-backed checks.
> **Verification:** The task contract and build instructions together make `TODO -> IN PROGRESS -> DONE` explicit, preserve `SKIPPED` and `DCR`, and require BDD/test/verification evidence before completion.

- **Priority:** P0
- **Scope:** Task state machine
- **Scenario Coverage:** `features/workflow_type_contracts.feature` — Builder uses allowed task state transitions only
- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Preserve existing task execution semantics while making state transitions explicit and reviewable.
- **Simplification Focus:** remove redundancy
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] **Step 1:** Update `tasks_template.md`, `pb-plan`, and `pb-build` instructions to define the allowed status markers and transitions, including legacy-compatibility handling.
- [x] **Step 2:** Ensure completion rules require `BDD Verification`, `Verification`, and runtime evidence when applicable before a task can become `🟢 DONE`.
- [x] **BDD Verification:** Run `uv run behave features/workflow_type_contracts.feature` and confirm the task-state scenario fails first, then passes.
- [x] **Verification:** Run `uv run pytest tests/test_templates.py tests/test_template_contracts.py -q` and confirm state-transition assertions pass.
- [x] **Advanced Test Verification:** `N/A` because this task kept example-based coverage and did not introduce a reusable state-transition helper.
- [x] **Runtime Verification (if applicable):** `N/A` because this task changes markdown workflow state, not a runtime service.

---

## Phase 3: Integration & Features

### Task 3.1: Strengthen pb-refine blocked-build and DCR packet validation

> **Context:** Reuse `src/pb_spec/templates/skills/pb-refine/SKILL.md` and `src/pb_spec/templates/prompts/pb-refine.prompt.md`. The packet format must remain the repo's current markdown block style (`🛑 Build Blocked`, `🔄 Design Change Request`) rather than switching to YAML.
> **Verification:** `pb-refine` accepts only structurally complete blocked-build or DCR packets and reports missing evidence fields instead of guessing what failed.

- **Priority:** P0
- **Scope:** Refine packet validation
- **Scenario Coverage:** `features/workflow_type_contracts.feature` — Refiner accepts only complete blocked-build packets
- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Preserve the existing refine workflow and packet family while making packet completeness mandatory.
- **Simplification Focus:** consolidate related logic
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] **Step 1:** Update `pb-refine` skill/prompt instructions so `Build Blocked` and `Design Change Request` packets have explicit required sections.
- [x] **Step 2:** Ensure `pb-refine` reports malformed packets clearly and only updates affected spec files after packet validation passes.
- [x] **BDD Verification:** Run `uv run behave features/workflow_type_contracts.feature` and confirm the refine-packet scenario fails first, then passes.
- [x] **Verification:** Run `uv run pytest tests/test_templates.py tests/test_template_contracts.py -q` and confirm refine packet assertions pass.
- [x] **Advanced Test Verification:** `N/A` unless implementation introduces a reusable packet parser/helper.
- [x] **Runtime Verification (if applicable):** `N/A` because this task affects workflow documents, not runtime service behavior.

### Task 3.2: Align prompt-only and skill-based surfaces with the same contract

> **Context:** Reuse the shared prompt and skill template files and the existing install/render tests in `tests/test_init.py` and `tests/test_e2e.py`. This task prevents contract drift between skill-capable and prompt-only platforms.
> **Verification:** Contract language is present in both shared skill templates and prompt-only renderings, and platform install tests still pass.

- **Priority:** P1
- **Scope:** Cross-platform parity
- **Scenario Coverage:** `N/A`
- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Preserve existing platform adapter behavior while aligning the installed contract content across platforms.
- **Simplification Focus:** consolidate related logic
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] **Step 1:** Update prompt-only templates wherever the contract wording diverges from skill-based templates.
- [x] **Step 2:** Extend install/render regression coverage so the stronger contract survives platform rendering.
- [x] **BDD Verification:** `N/A` because this task is about cross-platform template parity, not a direct behavior scenario.
- [x] **Verification:** Run `uv run pytest tests/test_init.py tests/test_e2e.py -q` and confirm prompt/skill rendering still succeeds.
- [x] **Advanced Test Verification:** `N/A` because this task does not add broad input-domain logic.
- [x] **Runtime Verification (if applicable):** `N/A` because this task does not change runtime service behavior.

---

## Phase 4: Polish, QA & Docs

### Task 4.1: Update workflow documentation and run the full verification suite

> **Context:** Reuse the current documented workflow in `README.md` and `docs/design.md`. The docs must describe the strengthened contract truthfully, including what changed from the current implementation review: no new commands, markdown as the type carrier, and packet/state validation in the existing workflow.
> **Verification:** Docs, pytest, behave, lint, and combined verification all pass and match the implemented contract.

- **Priority:** P2
- **Scope:** Documentation and final verification
- **Scenario Coverage:** `features/workflow_type_contracts.feature` — all scenarios remain covered by final verification
- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Preserve current workflow documentation while updating it to the stronger contract semantics.
- **Simplification Focus:** improve naming
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] **Step 1:** Update `README.md` and `docs/design.md` so their workflow claims match the strengthened contract and the corrected technical review outcomes.
- [x] **Step 2:** Run the required repo verification commands and capture any failures instead of claiming success without evidence.
- [x] **BDD Verification:** Run `uv run behave features/workflow_type_contracts.feature` and confirm the workflow contract scenarios pass as documented.
- [x] **Verification:** Run `just lint`, `just test`, `just bdd`, and `just test-all`.
- [x] **Advanced Test Verification:** `N/A` unless implementation introduced `Hypothesis`-backed helpers earlier in the plan.
- [x] **Runtime Verification (if applicable):** `N/A` because this feature does not introduce runtime logs or health probes.

---

## Summary & Timeline

| Phase | Tasks | Target Date |
| :--- | :---: | :--- |
| **1. Foundation** | 2 | 03-09 |
| **2. Core Logic** | 2 | 03-09 |
| **3. Integration** | 2 | 03-09 |
| **4. Polish** | 1 | 03-09 |
| **Total** | **7** | |

## Definition of Done

1. [x] **Linted:** No lint errors in the touched template, test, and doc files.
2. [x] **Tested:** Pytest assertions cover planner, builder, refine, and platform parity contract changes.
3. [x] **BDD Covered:** Behave scenarios prove the user-visible workflow contract.
4. [x] **Formatted:** Repo formatting requirements are satisfied.
5. [x] **Verified:** The task's verification criteria are met with command-backed evidence.
6. [x] **Advanced-Tested (when applicable):** `Hypothesis` coverage exists only if reusable contract-parsing helpers were introduced.
7. [x] **Runtime-Evidenced (when applicable):** Explicitly `N/A` for this feature because no runtime service surface changed.
8. [x] **Behavior-Preserved or Documented:** No new workflow or command was introduced; any compatibility adjustment is documented.
9. [x] **Simplified Responsibly:** Contract hardening stayed within prompts/templates/tests/docs and did not sprawl into unrelated CLI or adapter refactors.
