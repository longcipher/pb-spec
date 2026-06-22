# Integrate Ponytail into pb-spec Skills — Tasks (BDD-Driven)

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | specs/2026-06-22-01-integrate-ponytail/design.md |
| **Status** | Planning |
| **Mode** | Full |

## Task Right-Sizing

Each task modifies one file (or related set) and ends with a grep verification.

## Execution Strategy

> Each task edits a specific skill file or reference file. Verification: grep for "ponytail" and related terms to confirm integration.

## Phase 1: Core Integration

### Task 1.1: Integrate ponytail ladder into pb-plan

> **Context:** pb-plan currently says "code-simplification lens" (line 24) and "prefer explicit readable solutions" (line 298). These are vague. Replace with the specific ponytail ladder.
> **Feature:** `features/integrate-ponytail.feature` → `pb-plan applies ponytail ladder to architecture decisions`
> **Tags:** `@integrate`, `@pb-plan`

- **TaskID:** `T1`
- **DependsOn:** `None`
- **Complexity:** `Medium`
- **Required Skills:** Markdown, ponytail philosophy
- **EvalRule:** `grep -c "ponytail" skills/pb-plan/SKILL.md` ≥ 3
- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Preserve all existing pb-plan behavior. Only add/inject ponytail ladder at existing decision points.
- **Simplification Focus:** Replace vague "simplification" references with specific ponytail ladder. The ladder IS the simplification.
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-plan/SKILL.md` lines 20-30 (execution contract)
- [x] Step 2: At line 24, replace "code-simplification lens" with ponytail ladder reference
- [x] Step 3: Read lines 115-127 (Architecture Decision Snapshot)
- [x] Step 4: Add ponytail ladder after Architecture Decision Snapshot
- [x] Step 5: Read lines 298-304 (Code Simplification Constraints)
- [x] Step 6: Replace the generic section with ponytail-specific constraints
- [x] Step 7: Read lines 478-501 (Key Principles)
- [x] Step 8: Add ponytail-first principle as #1
- [x] Step 9: Verify: `grep -c "ponytail" skills/pb-plan/SKILL.md` = 4 ≥ 3 ✅
- [x] BDD Verification: N/A
- [x] Advanced Test Verification: N/A
- [x] Runtime Verification: N/A

### Task 1.2: Integrate ponytail ladder into pb-build

> **Context:** pb-build says "follow YAGNI" (line 546) and implementer_prompt says "minimum code" (line 102) but neither gives the specific ladder. The Evaluator flags "over-engineering" as a red flag (evaluator_prompt:75) but doesn't have a systematic check.
> **Feature:** `features/integrate-ponytail.feature` → `pb-build Generator applies ladder` + `Evaluator detects over-engineering`
> **Tags:** `@integrate`, `@pb-build`

- **TaskID:** `T2`
- **DependsOn:** `None`
- **Complexity:** `High`
- **Required Skills:** Markdown, ponytail philosophy, pb-build workflow
- **EvalRule:** `grep -c "ponytail" skills/pb-build/SKILL.md` ≥ 2 AND `grep -c "ponytail" skills/pb-build/references/implementer_prompt.md` ≥ 1 AND `grep -c "ponytail" skills/pb-build/references/evaluator_prompt.md` ≥ 1
- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Preserve all existing pb-build behavior. Add ponytail ladder at decision points.
- **Simplification Focus:** The ladder itself is the simplification mechanism. Inject it where code decisions are made.
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-build/SKILL.md` line 546 ("ALWAYS follow YAGNI")
- [x] Step 2: Expand to ponytail ladder
- [x] Step 3: Read `skills/pb-build/references/implementer_prompt.md` lines 100-105 (GREEN step)
- [x] Step 4: Add ponytail ladder before GREEN step
- [x] Step 5: Read `skills/pb-build/references/implementer_prompt.md` lines 155-158 (Scope Check)
- [x] Step 6: Add Simplicity Check after Scope Check
- [x] Step 7: Read `skills/pb-build/references/evaluator_prompt.md` lines 70-76 (Code quality red flags)
- [x] Step 8: Expand over-engineering bullet with ponytail criteria
- [x] Step 9: Read `skills/pb-build/references/evaluator_prompt.md` lines 128-138 (Check C)
- [x] Step 10: Add Check D — Simplicity Audit after Check C
- [x] Step 11: Verify pb-build SKILL.md: 2 ≥ 2 ✅
- [x] Step 12: Verify implementer_prompt.md: 3 ≥ 1 ✅
- [x] Step 13: Verify evaluator_prompt.md: 4 ≥ 1 ✅
- [x] BDD Verification: N/A
- [x] Advanced Test Verification: N/A
- [x] Runtime Verification: N/A

### Task 1.3: Integrate ponytail into pb-improve

> **Context:** pb-improve has "Code Simplification Constraints" (line 284) that is generic. The audit-playbook.md has 9 categories but no over-engineering category. Generated specs don't carry the ponytail ladder.
> **Feature:** `features/integrate-ponytail.feature` → `pb-improve audits for over-engineering`
> **Tags:** `@integrate`, `@pb-improve`

- **TaskID:** `T3`
- **DependsOn:** `None`
- **Complexity:** `Medium`
- **Required Skills:** Markdown, ponytail philosophy
- **EvalRule:** `grep -c "ponytail" skills/pb-improve/SKILL.md` ≥ 2 AND `grep -c "ponytail" skills/pb-improve/references/audit-playbook.md` ≥ 1
- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Preserve all existing pb-improve behavior. Add over-engineering audit and ponytail to generated specs.
- **Simplification Focus:** Add over-engineering as a finding category; generated specs carry the ladder forward.
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-improve/SKILL.md` lines 284-289 (Code Simplification Constraints)
- [x] Step 2: Replace with ponytail ladder
- [x] Step 3: Read `skills/pb-improve/references/audit-playbook.md` section 5
- [x] Step 4: Add Over-engineering category after section 5
- [x] Step 5: Read `skills/pb-improve/SKILL.md` Phase 4 section
- [x] Step 6: Add ponytail ladder instruction to spec writing
- [x] Step 7: Read `skills/pb-improve/references/plan-template.md` line 124
- [x] Step 8: Replace Code Simplification Constraints with ponytail ladder
- [x] Step 9: Verify pb-improve SKILL.md: 2 ≥ 2 ✅
- [x] Step 10: Verify audit-playbook.md: 1 ≥ 1 ✅
- [x] BDD Verification: N/A
- [x] Advanced Test Verification: N/A
- [x] Runtime Verification: N/A

## Phase 2: Template Updates

### Task 2.1: Add Simplification Strategy to design template

> **Context:** The design_template.md has "Code Simplification Constraints" (line 87) but it's generic. Need to replace with ponytail ladder.
> **Feature:** `features/integrate-ponytail.feature` → `design template includes ponytail section`
> **Tags:** `@template`, `@design`

- **TaskID:** `T4`
- **DependsOn:** `T1`
- **Complexity:** `Low`
- **Required Skills:** Markdown
- **EvalRule:** `grep -c "ponytail" skills/pb-plan/references/design_template.md` ≥ 1
- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Preserve existing template structure. Replace generic simplification with ponytail ladder.
- **Simplification Focus:** The ladder IS the simplification strategy.
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-plan/references/design_template.md` lines 85-90
- [x] Step 2: Replace Code Simplification Constraints with ponytail ladder
- [x] Step 3: Verify: `grep -c "ponytail" skills/pb-plan/references/design_template.md` = 2 ≥ 1 ✅
- [x] BDD Verification: N/A
- [x] Advanced Test Verification: N/A
- [x] Runtime Verification: N/A

### Task 2.2: Update tasks template with ponytail reference

> **Context:** tasks_template.md has "Simplification Focus" fields (lines 49, 68, 91, 111, 135, 158) but the placeholder text is generic.
> **Feature:** `features/integrate-ponytail.feature` → `Generated specs include ponytail ladder`
> **Tags:** `@template`, `@tasks`

- **TaskID:** `T5`
- **DependsOn:** `T1`
- **Complexity:** `Low`
- **Required Skills:** Markdown
- **EvalRule:** `grep -c "ponytail" skills/pb-plan/references/tasks_template.md` ≥ 1
- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Preserve existing template structure.
- **Simplification Focus:** Simplification Focus field should reference the ponytail ladder.
- **Status:** 🟢 DONE
- [x] Step 1: Read `skills/pb-plan/references/tasks_template.md`
- [x] Step 2: Replace all Simplification Focus placeholder text with ponytail ladder reference
- [x] Step 3: Add ponytail Simplification Rule at top of template
- [x] Step 4: Verify: `grep -c "ponytail" skills/pb-plan/references/tasks_template.md` = 7 ≥ 1 ✅
- [x] BDD Verification: N/A
- [x] Advanced Test Verification: N/A
- [x] Runtime Verification: N/A

## Phase 3: Verification

### Task 3.1: Verify all integrations

> **Context:** Confirm ponytail is present in all target files and no existing behavior was lost.
> **Feature:** `features/integrate-ponytail.feature` → all scenarios
> **Tags:** `@verify`

- **TaskID:** `T6`
- **DependsOn:** `T1`, `T2`, `T3`, `T4`, `T5`
- **Complexity:** `Low`
- **Required Skills:** Shell
- **EvalRule:** All grep checks pass
- **Loop Type:** `TDD-only`
- **Behavioral Contract:** No behavior loss
- **Simplification Focus:** N/A — verification only
- **Status:** 🟢 DONE
- [x] Step 1: `grep -c "ponytail" skills/pb-plan/SKILL.md` = 4 ≥ 3 ✅
- [x] Step 2: `grep -c "ponytail" skills/pb-build/SKILL.md` = 2 ≥ 2 ✅
- [x] Step 3: `grep -c "ponytail" skills/pb-build/references/implementer_prompt.md` = 3 ≥ 1 ✅
- [x] Step 4: `grep -c "ponytail" skills/pb-build/references/evaluator_prompt.md` = 4 ≥ 1 ✅
- [x] Step 5: `grep -c "ponytail" skills/pb-improve/SKILL.md` = 2 ≥ 2 ✅
- [x] Step 6: `grep -c "ponytail" skills/pb-improve/references/audit-playbook.md` = 1 ≥ 1 ✅
- [x] Step 7: `grep -c "ponytail" skills/pb-plan/references/design_template.md` = 2 ≥ 1 ✅
- [x] Step 8: `grep -c "ponytail" skills/pb-plan/references/tasks_template.md` = 7 ≥ 1 ✅
- [x] Step 9: Manual review: all edits preserve existing behavior ✅
- [x] BDD Verification: N/A
- [x] Advanced Test Verification: N/A
- [x] Runtime Verification: N/A
